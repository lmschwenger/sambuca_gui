"""
Sambuca GUI Package

Graphical user interface for the sambuca_core bio-optical modeling package.
"""

__version__ = "1.2.0"
__author__ = "Lasse M. Schwenger"
__email__ = "lasse.m.schwenger@gmail.com"

# Package metadata
__title__ = "sambuca.gui"
__description__ = "Graphical User Interface for sambuca_core bio-optical modeling"
__url__ = "https://github.com/lmschwenger/sambuca_gui"
__license__ = "MIT"

# Import main components for easy access
try:
    from .app import SambucaGuiApp, main
    from .controllers.workflow_controller import WorkflowController
    from .views.main_window import MainWindow
    
    __all__ = [
        'SambucaGuiApp',
        'main', 
        'WorkflowController',
        'MainWindow',
        '__version__'
    ]
    
except ImportError as e:
    # Handle missing dependencies gracefully
    import warnings
    warnings.warn(f"Some GUI components could not be imported: {e}")
    
    __all__ = ['__version__']

# Version compatibility check
import sys
if sys.version_info < (3, 8):
    raise RuntimeError("sambuca_gui requires Python 3.8 or later")

# Check for sambuca_core availability  
def check_sambuca_core():
    """Check if sambuca_core is available and compatible."""
    try:
        import sambuca.core
        from sambuca.core import __version__ as core_version
        return True, core_version
    except ImportError:
        return False, None

# Module-level configuration
DEFAULT_CONFIG = {
    'theme': 'clam',
    'window_size': (1000, 700),
    'auto_check_updates': True,
    'default_sensor': 'sentinel2',
    'default_method': 'lut'
}
