"""
Utilities package for Sambuca GUI

Common utility functions and classes for configuration, validation, and error handling.
"""

from .config import ConfigManager, SettingsDialog
from .validation import (
    validate_image_file,
    validate_output_directory, 
    validate_parameter_ranges,
    validate_band_configuration,
    validate_numpy_array,
    sanitize_filename,
    format_file_size,
    get_memory_usage_mb,
    estimate_processing_time,
    create_error_report,
    ValidationError
)

__all__ = [
    'ConfigManager',
    'SettingsDialog', 
    'validate_image_file',
    'validate_output_directory',
    'validate_parameter_ranges',
    'validate_band_configuration',
    'validate_numpy_array',
    'sanitize_filename',
    'format_file_size',
    'get_memory_usage_mb',
    'estimate_processing_time',
    'create_error_report',
    'ValidationError'
]
