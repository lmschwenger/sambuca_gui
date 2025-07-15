"""
Main Window View

The primary window interface for the Sambuca Core GUI with configuration management.
"""

import tkinter as tk
from tkinter import ttk

from .parameters_panel import ParametersPanel
from .results_panel import ResultsPanel
from .workflow_panel import WorkflowPanel
from ..controllers.workflow_controller import WorkflowController


class MainWindow:
    """Main window view for the Sambuca Core GUI with enhanced functionality."""

    def __init__(self, root, config_manager=None):
        self.root = root
        self.config_manager = config_manager
        self.controller = WorkflowController()
        
        # Apply configuration to controller if available
        if self.config_manager:
            self._apply_config_to_controller()

        self._setup_layout()
        self._setup_panels()
        
        # Load saved parameters if available
        self._load_saved_state()

    def _apply_config_to_controller(self):
        """Apply configuration settings to the workflow controller."""
        try:
            # Get default values from config
            default_sensor = self.config_manager.get('processing.default_sensor', 'sentinel2')
            default_method = self.config_manager.get('processing.default_method', 'lut')
            default_grid_size = self.config_manager.get('processing.default_grid_size', 20)
            
            # Update controller parameters
            config_params = {
                'sensor': default_sensor,
                'lut_params': {
                    'grid_size': default_grid_size,
                    'memory_optimized': False,
                    'batch_size': 1000
                }
            }
            
            self.controller.update_parameters(config_params)
            
        except Exception as e:
            print(f"Warning: Could not apply configuration to controller: {e}")

    def _setup_layout(self):
        """Set up the main window layout."""
        # Create main container with padding
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)

    def _setup_panels(self):
        """Set up the main GUI panels."""
        # Left panel for workflow and parameters
        left_frame = ttk.Frame(self.main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))

        # Right panel for results
        right_frame = ttk.Frame(self.main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))

        # Create panels with configuration support
        self.workflow_panel = WorkflowPanel(left_frame, self.controller)
        self.parameters_panel = ParametersPanel(left_frame, self.controller)
        self.results_panel = ResultsPanel(right_frame, self.controller)

        # Connect panels for communication
        self.workflow_panel.set_parameters_panel(self.parameters_panel)
        
        # Apply configuration defaults to panels if available
        if self.config_manager:
            self._apply_config_to_panels()

        # Position panels
        self.workflow_panel.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), pady=(0, 10))
        self.parameters_panel.frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N), pady=(0, 10))
        self.results_panel.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure weights
        left_frame.columnconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
    def _apply_config_to_panels(self):
        """Apply configuration settings to panels."""
        try:
            # Apply sensor default
            default_sensor = self.config_manager.get('processing.default_sensor', 'sentinel2')
            if hasattr(self.workflow_panel, 'sensor_var'):
                self.workflow_panel.sensor_var.set(default_sensor)
                
            # Apply method default
            default_method = self.config_manager.get('processing.default_method', 'lut')
            if hasattr(self.workflow_panel, 'method_var'):
                self.workflow_panel.method_var.set(default_method)
                
            # Apply parameter defaults
            param_defaults = self.config_manager.get('parameters', {})
            if hasattr(self.parameters_panel, 'depth_min_var') and 'depth_range' in param_defaults:
                depth_range = param_defaults['depth_range']
                self.parameters_panel.depth_min_var.set(depth_range[0])
                self.parameters_panel.depth_max_var.set(depth_range[1])
                
            # Apply grid size default
            default_grid_size = self.config_manager.get('processing.default_grid_size', 20)
            if hasattr(self.parameters_panel, 'grid_size_var'):
                self.parameters_panel.grid_size_var.set(default_grid_size)
                
            # Update sensor information
            self.parameters_panel.update_sensor_selection(default_sensor)
            
        except Exception as e:
            print(f"Warning: Could not apply configuration to panels: {e}")
            
    def _load_saved_state(self):
        """Load saved application state from configuration."""
        if not self.config_manager:
            return
            
        try:
            # Load last used directories
            last_image_dir = self.config_manager.get('paths.last_image_dir')
            last_output_dir = self.config_manager.get('paths.last_output_dir')
            last_siop_dir = self.config_manager.get('paths.last_siop_dir')
            
            # These would be applied to file dialogs when they're opened
            # Store them as instance variables for use in file dialogs
            self.last_image_dir = last_image_dir
            self.last_output_dir = last_output_dir
            self.last_siop_dir = last_siop_dir
            
        except Exception as e:
            print(f"Warning: Could not load saved state: {e}")
            
    def save_current_state(self):
        """Save current application state to configuration."""
        if not self.config_manager:
            return
            
        try:
            # Save current parameter values
            if hasattr(self.parameters_panel, 'get_parameters'):
                current_params = self.parameters_panel.get_parameters()
                
                # Save parameter ranges
                if 'parameter_ranges' in current_params:
                    ranges = current_params['parameter_ranges']
                    if 'depth' in ranges:
                        self.config_manager.set('parameters.depth_range', list(ranges['depth']))
                    if 'chl' in ranges:
                        self.config_manager.set('parameters.chl_range', list(ranges['chl']))
                    if 'cdom' in ranges:
                        self.config_manager.set('parameters.cdom_range', list(ranges['cdom']))
                    if 'nap' in ranges:
                        self.config_manager.set('parameters.nap_range', list(ranges['nap']))
                        
                # Save LUT settings
                if 'lut_params' in current_params:
                    lut_params = current_params['lut_params']
                    if 'grid_size' in lut_params:
                        self.config_manager.set('processing.default_grid_size', lut_params['grid_size'])
                        
            # Save workflow settings
            if hasattr(self.workflow_panel, 'sensor_var'):
                self.config_manager.set('processing.default_sensor', self.workflow_panel.sensor_var.get())
            if hasattr(self.workflow_panel, 'method_var'):
                self.config_manager.set('processing.default_method', self.workflow_panel.method_var.get())
                
            # Save file paths
            if hasattr(self.workflow_panel, 'image_path_var'):
                image_path = self.workflow_panel.image_path_var.get()
                if image_path:
                    from pathlib import Path
                    self.config_manager.set('paths.last_image_dir', str(Path(image_path).parent))
                    self.config_manager.add_recent_image(image_path)
                    
            if hasattr(self.workflow_panel, 'output_dir_var'):
                output_dir = self.workflow_panel.output_dir_var.get()
                if output_dir:
                    self.config_manager.set('paths.last_output_dir', output_dir)
                    
            if hasattr(self.workflow_panel, 'siop_dir_var'):
                siop_dir = self.workflow_panel.siop_dir_var.get()
                if siop_dir:
                    self.config_manager.set('paths.last_siop_dir', siop_dir)
                    
        except Exception as e:
            print(f"Warning: Could not save current state: {e}")
            
    def get_recent_files_menu(self):
        """Get recent files for menu display."""
        if not self.config_manager:
            return []
            
        try:
            return self.config_manager.get_recent_images()
        except Exception:
            return []
            
    def open_recent_file(self, file_path):
        """Open a recent file."""
        try:
            if hasattr(self.workflow_panel, 'image_path_var'):
                self.workflow_panel.image_path_var.set(file_path)
                self.workflow_panel.status_var.set(f"Loaded: {Path(file_path).name}")
        except Exception as e:
            print(f"Error opening recent file: {e}")
            
    def create_recent_files_menu(self, parent_menu):
        """Create recent files submenu."""
        if not self.config_manager:
            return
            
        recent_files = self.get_recent_files_menu()
        
        if recent_files:
            recent_menu = tk.Menu(parent_menu, tearoff=0)
            parent_menu.add_cascade(label="Recent Files", menu=recent_menu)
            
            for file_path in recent_files[:10]:  # Limit to 10 recent files
                from pathlib import Path
                filename = Path(file_path).name
                recent_menu.add_command(
                    label=filename,
                    command=lambda path=file_path: self.open_recent_file(path)
                )
                
            recent_menu.add_separator()
            recent_menu.add_command(
                label="Clear Recent Files",
                command=self._clear_recent_files
            )
        else:
            parent_menu.add_command(label="Recent Files (empty)", state="disabled")
            
    def _clear_recent_files(self):
        """Clear the recent files list."""
        if self.config_manager:
            self.config_manager.set('paths.recent_images', [])
            
    def __del__(self):
        """Cleanup when window is destroyed."""
        # Save state before destruction
        try:
            self.save_current_state()
        except Exception:
            pass
