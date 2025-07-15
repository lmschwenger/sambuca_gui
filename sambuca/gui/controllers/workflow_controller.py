"""
Workflow Controller

Handles workflow execution and coordinates between GUI and sambuca_core.
"""

import threading
import numpy as np
from pathlib import Path
from typing import Dict, Callable, Any, List

# Import actual sambuca.core functions with current API
try:
    from sambuca.core.forward_model import forward_model, ForwardModelResults
    from sambuca.core.lookup_table import LookUpTable, ParameterType
    from sambuca.core.siop_manager import SIOPManager
    from sambuca.core.inversion_handler import InversionHandler, InversionResult
    import rasterio
    SAMBUCA_CORE_AVAILABLE = True
    print("sambuca.core imported successfully")
except ImportError as e:
    print(f"Warning: sambuca.core not available: {e}")
    SAMBUCA_CORE_AVAILABLE = False
    # Create dummy classes to prevent errors
    class ForwardModelResults: pass
    class LookUpTable: 
        @staticmethod
        def load(filename, siop_manager): return None
    class SIOPManager: 
        def __init__(self, siop_directory=None): pass
        def get_siops_for_wavelengths(self, wavelengths): return {}
    class InversionHandler: 
        def invert_image_from_lookup_table(self, *args, **kwargs): return None
    class InversionResult: pass
    class ParameterType:
        @staticmethod
        def FIXED(value): return ('fixed', value)
        @staticmethod  
        def RANGE(min_val, max_val, n): return ('range', min_val, max_val, n)

# Sensor definitions - centralized for easy access
SENSOR_DEFINITIONS = {
    'sentinel2': {
        'name': 'Sentinel-2',
        'bands': {
            'B1': 443,    # Coastal aerosol
            'B2': 490,    # Blue
            'B3': 560,    # Green
            'B4': 665,    # Red
            'B5': 705,    # Red edge 1
            'B6': 740,    # Red edge 2
            'B7': 783,    # Red edge 3
            'B8': 842,    # NIR
            'B8A': 865,   # NIR narrow
            'B9': 945,    # Water vapour
            'B10': 1375,  # SWIR cirrus
            'B11': 1610,  # SWIR 1
            'B12': 2190   # SWIR 2
        }
    },
    'landsat8': {
        'name': 'Landsat-8',
        'bands': {
            'B1': 443,  # Coastal
            'B2': 482,  # Blue
            'B3': 562,  # Green
            'B4': 655,  # Red
            'B5': 865,  # NIR
            'B6': 1610,  # SWIR 1
            'B7': 2200,  # SWIR 2
            'B8': 590,  # Panchromatic
            'B9': 1375  # Cirrus
        }
    }
}


def get_sensor_wavelengths(selected_bands, sensor_name):
    """Get wavelengths for selected bands from sensor definition."""
    if sensor_name not in SENSOR_DEFINITIONS:
        raise ValueError(f"Unknown sensor: {sensor_name}")

    sensor_def = SENSOR_DEFINITIONS[sensor_name]
    wavelengths = []

    for band in selected_bands:
        if band in sensor_def['bands']:
            wavelengths.append(sensor_def['bands'][band])
        else:
            raise ValueError(f"Band {band} not available for sensor {sensor_name}")

    return wavelengths


class SambucaLookupTable:
    """Wrapper for sambuca.core LookUpTable."""
    
    def __init__(self, wavelengths: list, siop_manager: SIOPManager):
        self.wavelengths = np.array(wavelengths)
        self.siop_manager = siop_manager
        self.lut = None
        
    def build_table(self, parameter_ranges: Dict, fixed_parameters: Dict, n_points: int = 50):
        """Build lookup table using sambuca.core LookUpTable with current API."""
        if not SAMBUCA_CORE_AVAILABLE:
            raise ImportError("sambuca_core is required for lookup table generation")

        # Create parameter options using current ParameterType API
        options = {}

        # Add range parameters
        for param_name, (min_val, max_val) in parameter_ranges.items():
            options[param_name] = ParameterType.RANGE(min_val, max_val, n_points)

        # Add fixed parameters (only the ones needed for LUT generation)
        sambuca_core_params = {'chl', 'cdom', 'nap', 'depth', 'substrate_fraction'}
        for param_name, value in fixed_parameters.items():
            if param_name in sambuca_core_params and param_name not in parameter_ranges:
                options[param_name] = ParameterType.FIXED(value)

        print(f"LUT parameters: {list(options.keys())}")
        print(f"Range parameters: {list(parameter_ranges.keys())}")
        print(f"Fixed parameters: {[k for k in fixed_parameters.keys() if k in sambuca_core_params]}")

        print(parameter_ranges)
        # Create the LookUpTable instance with current API
        self.lut = LookUpTable(
            siop_manager=self.siop_manager,
            wavelengths=self.wavelengths,
            options=options
        )

        # Build the lookup table using current API
        self.lut.build_table()
        # Calculate actual entries (product of range parameter dimensions)
        n_range_params = len(parameter_ranges)
        total_entries = n_points ** n_range_params if n_range_params > 0 else 1
        return total_entries



class WorkflowController:
    """Controller for managing bathymetry workflows using actual sambuca_core."""

    def __init__(self):
        self.current_parameters = {}
        self.lookup_table = None
        self.siop_manager = None
        self.inversion_handler = None
        self._callbacks = {}
        
        # Initialize default parameters
        self._initialize_default_parameters()
        
        # Initialize sambuca.core components
        self._initialize_sambuca_components()

    def _initialize_default_parameters(self):
        """Initialize default processing parameters for sambuca_core."""
        self.current_parameters = {
            # Parameter ranges for lookup table (these will vary)
            'parameter_ranges': {
                'chl': (0.01, 20.0),     # Chlorophyll
                'cdom': (0.0001, 2.0),   # CDOM
                'nap': (0.001, 5.0),     # Non-algal particulates
                'depth': (0.1, 25.0)     # Water depth
            },
            # Fixed parameters (these won't vary)
            'fixed_params': {
                # Core sambuca parameters that can be fixed or varied
                'substrate_fraction': 1.0,  # Can be made variable through GUI
                
                # Always fixed sambuca_core parameters 
                'a_cdom_slope': 0.0168052,
                'a_nap_slope': 0.00977262,
                'bb_ph_slope': 0.878138,
                'lambda0cdom': 550.0,
                'lambda0nap': 550.0,
                'lambda0x': 546.0,
                'x_ph_lambda0x': 0.00157747,
                'x_nap_lambda0x': 0.0225353,
                'a_cdom_lambda0cdom': 1.0,
                'a_nap_lambda0nap': 0.00433,
                'bb_lambda_ref': 550.0,
                'water_refractive_index': 1.33784,
                'theta_air': 30.0,
                'off_nadir': 0.0,
                'q_factor': 3.14159
            },
            # LUT configuration
            'lut_params': {
                'grid_size': 20,
                'memory_optimized': False,
                'batch_size': 1000
            },
            # Band selection
            'selected_bands': ['B2', 'B3', 'B4', 'B5'],
            'band_indices': [1, 2, 3, 4],
            'sensor': 'sentinel2'
        }
        
    def _initialize_sambuca_components(self):
        """Initialize sambuca.core components with current API."""
        if SAMBUCA_CORE_AVAILABLE:
            try:
                # Initialize SIOP manager - current API takes optional siop_directory parameter
                self.siop_manager = SIOPManager(siop_directory=None)  # Uses default directory
                
                # Initialize inversion handler - current API
                self.inversion_handler = InversionHandler()
                
                print("Sambuca core components initialized successfully")
            except Exception as e:
                print(f"Warning: Could not initialize sambuca components: {e}")
                self.siop_manager = None
                self.inversion_handler = None

    def subscribe(self, event: str, callback: Callable):
        """Subscribe to controller events."""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def _notify(self, event: str, data: Any = None):
        """Notify subscribers of an event."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Error in callback for event {event}: {e}")

    def update_parameters(self, parameters: Dict):
        """Update processing parameters."""
        self.current_parameters.update(parameters)

    def load_siop_data(self, siop_dir: str = None):
        """Load SIOP data using sambuca.core SIOPManager with current API."""
        if not SAMBUCA_CORE_AVAILABLE or not self.siop_manager:
            print("Warning: sambuca_core not available or not initialized")
            return False
            
        try:
            if siop_dir and Path(siop_dir).exists():
                # Load SIOP libraries from directory using current API
                self.siop_manager.load_libraries(siop_dir)
                print(f"Loaded SIOP libraries from {siop_dir}")
                return True
            else:
                print("Using default sambuca_core SIOP libraries")
                return True
                
        except Exception as e:
            print(f"Error loading SIOP data: {e}")
            return False

    def build_lookup_table(self, progress_callback: Callable = None):
        """Build lookup table using sambuca.core LookUpTable."""
        if not SAMBUCA_CORE_AVAILABLE or not self.siop_manager:
            raise ImportError("sambuca_core is required for lookup table generation")

        # Get wavelengths for selected bands
        wavelengths = get_sensor_wavelengths(
            self.current_parameters['selected_bands'],
            self.current_parameters['sensor']
        )

        if progress_callback:
            progress_callback(10)

        # Create lookup table with SIOP manager
        self.lookup_table = SambucaLookupTable(wavelengths, self.siop_manager)

        if progress_callback:
            progress_callback(20)

        # Get LUT configuration
        lut_params = self.current_parameters.get('lut_params', {'grid_size': 20})
        grid_size = lut_params.get('grid_size', 20)
        print(self.current_parameters)
        # Build the table with both range and fixed parameters
        n_entries = self.lookup_table.build_table(
            parameter_ranges=self.current_parameters['parameter_ranges'],
            fixed_parameters=self.current_parameters['fixed_params'],
            n_points=grid_size
        )

        if progress_callback:
            progress_callback(100)

        print(f"Built lookup table with {n_entries} entries")
        return True

    def process_image(self, params: Dict, progress_callback: Callable = None,
                      completion_callback: Callable = None):
        """Process an image using sambuca_core."""

        def run_processing():
            try:
                if progress_callback:
                    progress_callback(5)

                # Load SIOP data
                self.load_siop_data(params.get('siop_dir'))
                
                if progress_callback:
                    progress_callback(10)

                # Build lookup table if using LUT method
                if params.get('method') == 'lut':
                    if self.lookup_table is None:
                        if not self.build_lookup_table(lambda p: progress_callback(10 + p * 0.3)):
                            raise Exception("Failed to build lookup table")
                    
                    result = self._process_with_lut(params, progress_callback)
                else:
                    result = self._process_with_forward_model(params, progress_callback)

                # Save results
                if progress_callback:
                    progress_callback(90)
                    
                output_dir = Path(params['output_dir'])
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Save parameter maps as numpy arrays for now
                np.save(output_dir / 'chl.npy', result['chl'])
                np.save(output_dir / 'cdom.npy', result['cdom'])
                np.save(output_dir / 'nap.npy', result['nap'])
                np.save(output_dir / 'depth.npy', result['depth'])

                if progress_callback:
                    progress_callback(100)

                # Notify completion
                if completion_callback:
                    completion_callback(True, f"Processing completed. Results saved to {output_dir}")

                # Notify result update
                self._notify('result_updated', result)

            except Exception as e:
                if completion_callback:
                    completion_callback(False, f"Processing failed: {str(e)}")

        # Run processing in separate thread
        processing_thread = threading.Thread(target=run_processing, daemon=True)
        processing_thread.start()

    def _process_with_forward_model(self, params: Dict, progress_callback: Callable = None):
        """Process image using optimization (requires building a lookup table first)."""
        # Note: Current sambuca_core API requires a lookup table for inversion
        # Direct optimization without LUT is not available in the current API
        
        if not SAMBUCA_CORE_AVAILABLE or not self.siop_manager:
            raise ImportError("sambuca_core is required for processing")
        
        try:
            # Load and prepare image data
            if progress_callback:
                progress_callback(10)
            
            image_data = self._load_image_data(params['image_path'], params)
            
            if progress_callback:
                progress_callback(30)
            
            # Build a temporary lookup table for optimization-based processing
            wavelengths = get_sensor_wavelengths(
                self.current_parameters['selected_bands'],
                self.current_parameters['sensor']
            )
            
            if progress_callback:
                progress_callback(40)
            
            print("Building temporary lookup table for optimization method...")
            
            # Create a temporary LUT with finer grid for this processing
            temp_lut = SambucaLookupTable(wavelengths, self.siop_manager)
            temp_lut.build_table(
                parameter_ranges=self.current_parameters['parameter_ranges'],
                fixed_parameters=self.current_parameters['fixed_params'],
                n_points=40  # Higher resolution for optimization method
            )
            
            if progress_callback:
                progress_callback(60)
                
            # Create mask for valid pixels
            mask = np.all(np.isfinite(image_data), axis=2) & np.any(image_data > 0, axis=2)
            
            # Use the lookup table for inversion with optimization-style settings
            result = self.inversion_handler.invert_image_from_lookup_table(
                lookup_table=temp_lut.lut,
                observed_image=image_data,
                metric='euclidean',  # Use Euclidean distance for optimization-like behavior
                use_kdtree=True,  # Enable KD-tree for faster searches
                mask=mask,
                chunk_size=2000  # Smaller chunks for finer processing
            )
            
            if progress_callback:
                progress_callback(80)
            
            print(f"Optimization-style processing completed using fine LUT")
            
            # Extract results in the expected format
            processed_result = self._format_inversion_result(result)
            
            return processed_result
            
        except Exception as e:
            print(f"Forward model processing error: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _process_with_lut(self, params: Dict, progress_callback: Callable = None):
        """Process image using sambuca.core lookup table method with current API."""
        if self.lookup_table is None or self.lookup_table.lut is None:
            raise ValueError("Lookup table not built")
        
        if not SAMBUCA_CORE_AVAILABLE or not self.inversion_handler:
            raise ImportError("sambuca_core is required for LUT-based processing")
            
        try:
            # Load and prepare image data
            if progress_callback:
                progress_callback(10)
            
            image_data = self._load_image_data(params['image_path'], params)
            
            if progress_callback:
                progress_callback(30)
            
            # Validate data dimensions
            expected_bands = len(self.lookup_table.wavelengths)
            if image_data.shape[2] != expected_bands:
                raise ValueError(f"Image has {image_data.shape[2]} bands but LUT expects {expected_bands}")
            
            print(f"Starting inversion with image shape: {image_data.shape}")
            print(f"LUT grid shape: {self.lookup_table.lut.grid_shape}")
            print(f"LUT parameter names: {self.lookup_table.lut.param_names}")
            
            # Create mask for valid pixels (non-zero and finite values)
            mask = np.all(np.isfinite(image_data), axis=2) & np.any(image_data > 0, axis=2)
            valid_pixels = np.sum(mask)
            total_pixels = mask.size
            
            print(f"Valid pixels: {valid_pixels}/{total_pixels} ({valid_pixels/total_pixels*100:.1f}%)")
            
            if valid_pixels == 0:
                raise ValueError("No valid pixels found in image")
            
            if progress_callback:
                progress_callback(40)
            
            # Use current API: InversionHandler.invert_image_from_lookup_table()
            result = self.inversion_handler.invert_image_from_lookup_table(
                lookup_table=self.lookup_table.lut,
                observed_image=image_data,
                metric='rmse',  # Distance metric for matching
                use_kdtree=True,  # Use KD-tree for faster lookups
                mask=mask,  # Provide the mask for valid pixels
                chunk_size=5000  # Process in chunks for memory efficiency
            )
            
            if progress_callback:
                progress_callback(70)
            
            print(f"Inversion completed. Result type: {type(result)}")
            
            # Format results
            processed_result = self._format_inversion_result(result)
            
            if progress_callback:
                progress_callback(80)
                
            return processed_result
            
        except Exception as e:
            print(f"LUT processing error: {e}")
            import traceback
            traceback.print_exc()
            raise

    def get_workflow_config(self):
        """Get current workflow configuration."""
        return {
            'parameters': self.current_parameters,
            'siop_manager_initialized': self.siop_manager is not None,
            'lookup_table_built': self.lookup_table is not None,
            'sambuca_core_available': SAMBUCA_CORE_AVAILABLE,
            'inversion_handler_available': self.inversion_handler is not None
        }

    def clear_lookup_table(self):
        """Clear the current lookup table to force rebuilding."""
        self.lookup_table = None
        
    def get_available_sensors(self):
        """Get list of available sensors."""
        return list(SENSOR_DEFINITIONS.keys())
        
    def get_sensor_bands(self, sensor_name: str):
        """Get available bands for a sensor."""
        if sensor_name in SENSOR_DEFINITIONS:
            return list(SENSOR_DEFINITIONS[sensor_name]['bands'].keys())
        return []
    
    def _load_image_data(self, image_path: str, params: Dict):
        """Load image data using rasterio."""
        if not SAMBUCA_CORE_AVAILABLE:
            raise ImportError("rasterio is required for image loading")
            
        try:
            with rasterio.open(image_path) as dataset:
                # Get band indices from parameters or use defaults
                band_indices = params.get('band_indices', 
                                        self.current_parameters.get('band_indices', [1, 2, 3, 4]))
                
                # Handle string input (comma-separated)
                if isinstance(band_indices, str):
                    band_indices = [int(i.strip()) for i in band_indices.split(',')]
                
                # Ensure band indices are valid
                num_bands = dataset.count
                valid_bands = [b for b in band_indices if 1 <= b <= num_bands]
                
                if not valid_bands:
                    raise ValueError(f"No valid bands found. Image has {num_bands} bands, requested: {band_indices}")
                
                # Read band data
                image_data = dataset.read(valid_bands)
                
                # Convert to (height, width, bands) format required by sambuca_core
                if image_data.ndim == 3:
                    image_data = np.transpose(image_data, (1, 2, 0))
                elif image_data.ndim == 2:
                    # Single band image
                    image_data = image_data[:, :, np.newaxis]
                
                # Ensure we have float64 data type for sambuca_core
                image_data = image_data.astype(np.float64)
                
                # Basic validation
                if image_data.shape[2] != len(valid_bands):
                    raise ValueError(f"Expected {len(valid_bands)} bands, got {image_data.shape[2]}")
                
                print(f"Loaded image data: shape={image_data.shape}, bands={valid_bands}, dtype={image_data.dtype}")
                print(f"Value range: [{image_data.min():.6f}, {image_data.max():.6f}]")
                
                return image_data
                
        except rasterio.errors.RasterioIOError as e:
            raise ValueError(f"Could not read image file {image_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading image data: {e}")
    
    def _get_parameter_bounds(self):
        """Get parameter bounds for inversion."""
        ranges = self.current_parameters['parameter_ranges']
        return {
            'chl': ranges['chl'],
            'cdom': ranges['cdom'],
            'nap': ranges['nap'],
            'depth': ranges['depth']
        }
    
    def _format_inversion_result(self, result):
        """Format sambuca.core InversionResult for GUI consumption."""
        try:
            # Handle current sambuca.core InversionResult format (from latest API)
            if hasattr(result, 'parameters') and hasattr(result, 'errors'):
                # Current API: InversionResult with parameters dict and errors array
                formatted = {
                    'chl': result.parameters.get('chl', np.array([])),
                    'cdom': result.parameters.get('cdom', np.array([])),
                    'nap': result.parameters.get('nap', np.array([])),
                    'depth': result.parameters.get('depth', np.array([])),
                    'error': result.errors if hasattr(result, 'errors') else np.array([]),
                    'modeled_spectra': result.modeled_spectra if hasattr(result, 'modeled_spectra') else None,
                    'metadata': result.metadata if hasattr(result, 'metadata') else {},
                    'timing': result.timing if hasattr(result, 'timing') else {}
                }
                
                # Log processing statistics if available
                if hasattr(result, 'metadata'):
                    meta = result.metadata
                    print(f"Processed {meta.get('n_valid_pixels', 'unknown')} valid pixels")
                    print(f"Total pixels: {meta.get('n_total_pixels', 'unknown')}")
                    print(f"Image shape: {meta.get('image_shape', 'unknown')}")
                    print(f"Metric used: {meta.get('metric', 'unknown')}")
                    
                if hasattr(result, 'timing'):
                    timing = result.timing
                    print(f"Processing time: {timing.get('total', 0):.2f}s")
                    print(f"Time per pixel: {timing.get('per_pixel', 0):.4f}s")
                    
            elif hasattr(result, 'inverted_parameters'):
                # Legacy format
                formatted = {
                    'chl': result.inverted_parameters.get('chl', np.array([])),
                    'cdom': result.inverted_parameters.get('cdom', np.array([])),
                    'nap': result.inverted_parameters.get('nap', np.array([])),
                    'depth': result.inverted_parameters.get('depth', np.array([])),
                    'error': result.error_values if hasattr(result, 'error_values') else np.array([])
                }
            elif isinstance(result, dict):
                # Dictionary result fallback
                formatted = {
                    'chl': result.get('chl', np.array([])),
                    'cdom': result.get('cdom', np.array([])),
                    'nap': result.get('nap', np.array([])),
                    'depth': result.get('depth', np.array([])),
                    'error': result.get('error', result.get('rmse', np.array([])))
                }
            else:
                # Debug unknown result format
                attrs = [attr for attr in dir(result) if not attr.startswith('_')]
                print(f"Unknown InversionResult format. Available attributes: {attrs}")
                
                # Try to access the most likely attributes
                formatted = {}
                if hasattr(result, 'parameters'):
                    params = result.parameters
                    formatted.update({
                        'chl': params.get('chl', np.array([])),
                        'cdom': params.get('cdom', np.array([])),
                        'nap': params.get('nap', np.array([])),
                        'depth': params.get('depth', np.array([]))
                    })
                if hasattr(result, 'errors'):
                    formatted['error'] = result.errors
                    
                # Fill missing data with empty arrays if we couldn't extract anything
                for param in ['chl', 'cdom', 'nap', 'depth', 'error']:
                    if param not in formatted:
                        formatted[param] = np.array([])
                        
                print(f"Extracted parameters: {list(formatted.keys())}")
            
            # Validate that we have some data
            has_data = any(len(arr) > 0 for arr in formatted.values() if isinstance(arr, np.ndarray))
            if not has_data:
                print("Warning: No valid data found in inversion result")
            
            return formatted
            
        except Exception as e:
            print(f"Error formatting inversion result: {e}")
            import traceback
            traceback.print_exc()
            
            # Return empty results to prevent complete failure
            return {
                'chl': np.array([]),
                'cdom': np.array([]),
                'nap': np.array([]),
                'depth': np.array([]),
                'error': np.array([])
            }
