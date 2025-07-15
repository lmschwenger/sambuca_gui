"""
Utility functions for validation and error handling in Sambuca GUI
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Optional, Union
import numpy as np

def validate_image_file(file_path: Union[str, Path]) -> Tuple[bool, str]:
    """Validate an image file for sambuca processing.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        file_path = Path(file_path)
        
        # Check if file exists
        if not file_path.exists():
            return False, f"File does not exist: {file_path}"
            
        # Check file size (should be reasonable)
        file_size = file_path.stat().st_size
        max_size = 5 * 1024 * 1024 * 1024  # 5 GB
        if file_size > max_size:
            return False, f"File too large: {file_size / (1024**3):.1f} GB"
            
        # Check file extension
        valid_extensions = {'.tif', '.tiff', '.img', '.dat', '.nc', '.hdf', '.h5'}
        if file_path.suffix.lower() not in valid_extensions:
            return False, f"Unsupported file format: {file_path.suffix}"
            
        # Try to open with rasterio if available
        try:
            import rasterio
            with rasterio.open(file_path) as dataset:
                # Check basic properties
                if dataset.count < 1:
                    return False, "No bands found in image"
                    
                if dataset.width < 10 or dataset.height < 10:
                    return False, f"Image too small: {dataset.width}x{dataset.height}"
                    
                if dataset.count > 500:
                    return False, f"Too many bands: {dataset.count} (max 500)"
                    
        except ImportError:
            # rasterio not available, skip detailed validation
            pass
        except Exception as e:
            return False, f"Cannot read image file: {str(e)}"
            
        return True, "File validation successful"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def validate_output_directory(dir_path: Union[str, Path]) -> Tuple[bool, str]:
    """Validate an output directory.
    
    Args:
        dir_path: Path to the output directory
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        dir_path = Path(dir_path)
        
        # Check if parent directory exists
        if not dir_path.parent.exists():
            return False, f"Parent directory does not exist: {dir_path.parent}"
            
        # Create directory if it doesn't exist
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                return False, f"No permission to create directory: {dir_path}"
            except Exception as e:
                return False, f"Cannot create directory: {str(e)}"
                
        # Check write permissions
        if not os.access(dir_path, os.W_OK):
            return False, f"No write permission for directory: {dir_path}"
            
        # Check available space (at least 100 MB)
        try:
            import shutil
            free_space = shutil.disk_usage(dir_path).free
            min_space = 100 * 1024 * 1024  # 100 MB
            if free_space < min_space:
                return False, f"Insufficient disk space: {free_space / (1024**2):.1f} MB available"
        except Exception:
            # Could not check disk space, continue anyway
            pass
            
        return True, "Output directory validation successful"
        
    except Exception as e:
        return False, f"Directory validation error: {str(e)}"


def validate_parameter_ranges(ranges: dict) -> Tuple[bool, List[str]]:
    """Validate parameter ranges for LUT building.
    
    Args:
        ranges: Dictionary of parameter ranges
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    required_params = ['chl', 'cdom', 'nap', 'depth']
    
    for param in required_params:
        if param not in ranges:
            errors.append(f"Missing parameter: {param}")
            continue
            
        param_range = ranges[param]
        
        # Check if it's a tuple/list with 2 elements
        if not isinstance(param_range, (list, tuple)) or len(param_range) != 2:
            errors.append(f"Parameter {param} must be a 2-element range [min, max]")
            continue
            
        min_val, max_val = param_range
        
        # Check if values are numeric
        if not isinstance(min_val, (int, float)) or not isinstance(max_val, (int, float)):
            errors.append(f"Parameter {param} values must be numeric")
            continue
            
        # Check if min < max
        if min_val >= max_val:
            errors.append(f"Parameter {param}: minimum ({min_val}) must be less than maximum ({max_val})")
            continue
            
        # Check reasonable ranges for each parameter
        param_limits = {
            'chl': (0.001, 1000.0),
            'cdom': (0.00001, 10.0),
            'nap': (0.0001, 100.0),
            'depth': (0.01, 1000.0)
        }
        
        if param in param_limits:
            abs_min, abs_max = param_limits[param]
            if min_val < abs_min or max_val > abs_max:
                errors.append(f"Parameter {param} range [{min_val}, {max_val}] outside reasonable limits [{abs_min}, {abs_max}]")
                
    return len(errors) == 0, errors


def validate_band_configuration(selected_bands: List[str], band_indices: List[int], 
                               sensor: str) -> Tuple[bool, List[str]]:
    """Validate band configuration.
    
    Args:
        selected_bands: List of selected band names
        band_indices: List of corresponding band indices
        sensor: Sensor name
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check if lists have same length
    if len(selected_bands) != len(band_indices):
        errors.append(f"Number of selected bands ({len(selected_bands)}) doesn't match number of indices ({len(band_indices)})")
        
    # Check minimum number of bands
    if len(selected_bands) < 3:
        errors.append("At least 3 bands are required for processing")
        
    # Check maximum number of bands
    if len(selected_bands) > 20:
        errors.append("Too many bands selected (maximum 20)")
        
    # Check if band indices are positive integers
    for i, idx in enumerate(band_indices):
        if not isinstance(idx, int) or idx < 1:
            errors.append(f"Band index {i+1} must be a positive integer (got {idx})")
            
    # Check for sensor-specific band validation
    if sensor == 'sentinel2':
        valid_bands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']
        for band in selected_bands:
            if band not in valid_bands:
                errors.append(f"Band '{band}' is not valid for Sentinel-2")
                
    elif sensor == 'landsat8':
        valid_bands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9']
        for band in selected_bands:
            if band not in valid_bands:
                errors.append(f"Band '{band}' is not valid for Landsat-8")
                
    return len(errors) == 0, errors


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe use across different operating systems.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '_', filename)
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed"
        
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
        
    return filename


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
        
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(units) - 1:
        size_bytes /= 1024.0
        i += 1
        
    return f"{size_bytes:.1f} {units[i]}"


def validate_numpy_array(arr: np.ndarray, name: str = "array") -> Tuple[bool, str]:
    """Validate a numpy array for sambuca processing.
    
    Args:
        arr: Numpy array to validate
        name: Name of the array for error messages
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check if it's actually a numpy array
        if not isinstance(arr, np.ndarray):
            return False, f"{name} is not a numpy array (type: {type(arr)})"
            
        # Check for valid dimensions
        if arr.ndim < 2 or arr.ndim > 3:
            return False, f"{name} must be 2D or 3D (got {arr.ndim}D)"
            
        # Check for reasonable size
        total_elements = arr.size
        max_elements = 100 * 1024 * 1024  # 100M elements
        if total_elements > max_elements:
            return False, f"{name} too large: {total_elements} elements (max {max_elements})"
            
        # Check data type
        if not np.issubdtype(arr.dtype, np.number):
            return False, f"{name} must contain numeric data (got {arr.dtype})"
            
        # Check for any finite values
        if not np.any(np.isfinite(arr)):
            return False, f"{name} contains no finite values"
            
        # Check value range (should be reasonable for reflectance data)
        finite_values = arr[np.isfinite(arr)]
        if len(finite_values) > 0:
            min_val, max_val = finite_values.min(), finite_values.max()
            if min_val < -1.0 or max_val > 2.0:
                return False, f"{name} values outside expected range [-1.0, 2.0]: [{min_val:.3f}, {max_val:.3f}]"
                
        return True, f"{name} validation successful"
        
    except Exception as e:
        return False, f"{name} validation error: {str(e)}"


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB.
    
    Returns:
        Memory usage in MB, or -1 if cannot determine
    """
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return -1
    except Exception:
        return -1


def estimate_processing_time(image_shape: Tuple[int, ...], method: str, 
                           grid_size: int = 20) -> str:
    """Estimate processing time for an image.
    
    Args:
        image_shape: Shape of the image (height, width, bands)
        method: Processing method ('lut' or 'optimization')
        grid_size: LUT grid size
        
    Returns:
        Estimated time as string
    """
    try:
        if len(image_shape) < 2:
            return "Unknown"
            
        n_pixels = image_shape[0] * image_shape[1]
        
        # Rough estimates based on typical performance
        if method == 'lut':
            # LUT is faster, ~1000 pixels per second after LUT building
            if n_pixels < 10000:
                return "< 30 seconds"
            elif n_pixels < 100000:
                return "1-5 minutes"
            elif n_pixels < 1000000:
                return "5-30 minutes"
            else:
                return "> 30 minutes"
        else:  # optimization
            # Optimization is slower but builds finer LUT
            lut_time = grid_size ** 4 * 0.001  # Rough estimate for LUT building
            processing_time = n_pixels * 0.002  # Slower per pixel
            
            total_minutes = (lut_time + processing_time) / 60
            
            if total_minutes < 1:
                return "< 1 minute"
            elif total_minutes < 10:
                return f"~{total_minutes:.0f} minutes"
            else:
                return f"~{total_minutes:.0f} minutes (may be long)"
                
    except Exception:
        return "Unknown"


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def create_error_report(errors: List[str], context: str = "") -> str:
    """Create a formatted error report.
    
    Args:
        errors: List of error messages
        context: Additional context information
        
    Returns:
        Formatted error report
    """
    if not errors:
        return "No errors found."
        
    report_lines = []
    if context:
        report_lines.append(f"Error Report - {context}")
        report_lines.append("=" * (len(context) + 15))
    else:
        report_lines.append("Error Report")
        report_lines.append("=" * 12)
        
    report_lines.append(f"Found {len(errors)} error(s):")
    report_lines.append("")
    
    for i, error in enumerate(errors, 1):
        report_lines.append(f"{i}. {error}")
        
    return "\n".join(report_lines)
