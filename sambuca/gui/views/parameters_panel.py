"""
Parameters Panel View

Panel for configuring bathymetry processing parameters.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class ParametersPanel:
    """Panel for parameter configuration."""

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller

        self._setup_ui()
        self._setup_sensor_definitions()
        self._load_default_parameters()

    def _setup_ui(self):
        """Set up the parameters panel UI."""
        # Main frame
        self.frame = ttk.LabelFrame(self.parent, text="Processing Parameters", padding="10")

        # Create notebook for parameter categories
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Physical parameters tab
        self._create_physical_params_tab()

        # Sensor parameters tab
        self._create_sensor_params_tab()

        # Action buttons (outside the notebook)
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        ttk.Button(button_frame, text="Reset to Defaults",
                   command=self._reset_parameters).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Apply Parameters",
                   command=self._apply_parameters).grid(row=0, column=1)

        # Configure grid weights
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

    def _create_physical_params_tab(self):
        """Create the physical parameters tab with flexible fixed/range configuration."""
        physical_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(physical_frame, text="Physical")

        # Instructions
        instructions = ttk.Label(physical_frame, 
                                text="Configure each parameter as either Fixed (single value) or Range (min-max for LUT):",
                                font=('TkDefaultFont', 9))
        instructions.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))

        # Headers
        ttk.Label(physical_frame, text="Parameter", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(physical_frame, text="Type", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=1, sticky=tk.W, padx=(0, 10))
        ttk.Label(physical_frame, text="Value(s)", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=2, sticky=tk.W, padx=(0, 10))
        ttk.Label(physical_frame, text="Units", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=3, sticky=tk.W)

        # Parameter configurations
        self.param_configs = {}
        
        # Depth configuration
        self._create_parameter_row(physical_frame, 2, "depth", "Depth", "m", 
                                  default_type="range", default_fixed=10.0, default_range=(0.1, 25.0))
        
        # Chlorophyll configuration  
        self._create_parameter_row(physical_frame, 3, "chl", "Chlorophyll", "mg/m³",
                                  default_type="range", default_fixed=1.0, default_range=(0.01, 20.0))
        
        # CDOM configuration
        self._create_parameter_row(physical_frame, 4, "cdom", "CDOM", "1/m",
                                  default_type="range", default_fixed=0.1, default_range=(0.0001, 2.0))
        
        # NAP configuration
        self._create_parameter_row(physical_frame, 5, "nap", "NAP", "mg/L",
                                  default_type="range", default_fixed=0.1, default_range=(0.001, 5.0))
        
        # Substrate fraction configuration
        self._create_parameter_row(physical_frame, 6, "substrate_fraction", "Substrate Fraction", "",
                                  default_type="fixed", default_fixed=1.0, default_range=(0.0, 1.0))
        
        # LUT configuration
        lut_frame = ttk.LabelFrame(physical_frame, text="Lookup Table Settings", padding="5")
        lut_frame.grid(row=7, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(15, 0))
        lut_frame.columnconfigure(1, weight=1)
        
        ttk.Label(lut_frame, text="Grid Size (points per dimension):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.grid_size_var = tk.IntVar(value=20)
        grid_spin = ttk.Spinbox(lut_frame, from_=10, to=100, textvariable=self.grid_size_var, width=10)
        grid_spin.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Help text
        help_text = "Higher grid size = more accurate but slower LUT building. Only applies to Range parameters."
        ttk.Label(lut_frame, text=help_text, font=('TkDefaultFont', 8), foreground='gray').grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=(2, 0)
        )
        
        # Configure grid weights
        physical_frame.columnconfigure(2, weight=1)
        
    def _create_parameter_row(self, parent, row, param_key, param_label, units, 
                             default_type="range", default_fixed=1.0, default_range=(0.1, 10.0)):
        """Create a parameter configuration row."""
        
        # Parameter label
        ttk.Label(parent, text=param_label).grid(row=row, column=0, sticky=tk.W, pady=2, padx=(0, 10))
        
        # Type selection (Fixed or Range)
        type_var = tk.StringVar(value=default_type)
        type_combo = ttk.Combobox(parent, textvariable=type_var, values=["fixed", "range"], 
                                 state="readonly", width=8)
        type_combo.grid(row=row, column=1, sticky=tk.W, pady=2, padx=(0, 10))
        
        # Value frame (will contain either single value or min/max)
        value_frame = ttk.Frame(parent)
        value_frame.grid(row=row, column=2, sticky=(tk.W, tk.E), pady=2, padx=(0, 10))
        value_frame.columnconfigure(0, weight=1)
        
        # Variables for fixed and range values
        fixed_var = tk.DoubleVar(value=default_fixed)
        range_min_var = tk.DoubleVar(value=default_range[0])
        range_max_var = tk.DoubleVar(value=default_range[1])
        
        # Create widgets (initially hidden)
        fixed_entry = ttk.Entry(value_frame, textvariable=fixed_var, width=12)
        
        range_frame = ttk.Frame(value_frame)
        ttk.Entry(range_frame, textvariable=range_min_var, width=8).grid(row=0, column=0, padx=(0, 2))
        ttk.Label(range_frame, text="to").grid(row=0, column=1, padx=2)
        ttk.Entry(range_frame, textvariable=range_max_var, width=8).grid(row=0, column=2, padx=(2, 0))
        
        # Units label
        ttk.Label(parent, text=units).grid(row=row, column=3, sticky=tk.W, pady=2)
        
        # Store configuration
        config = {
            'type_var': type_var,
            'fixed_var': fixed_var,
            'range_min_var': range_min_var,
            'range_max_var': range_max_var,
            'fixed_entry': fixed_entry,
            'range_frame': range_frame,
            'value_frame': value_frame
        }
        
        self.param_configs[param_key] = config
        
        # Set up type change callback
        def on_type_change(*args):
            self._update_parameter_widgets(param_key)
            
        type_var.trace('w', on_type_change)
        
        # Initialize display
        self._update_parameter_widgets(param_key)
        
    def _update_parameter_widgets(self, param_key):
        """Update parameter widgets based on selected type."""
        config = self.param_configs[param_key]
        param_type = config['type_var'].get()
        
        # Hide all widgets first
        config['fixed_entry'].grid_remove()
        config['range_frame'].grid_remove()
        
        # Show appropriate widget
        if param_type == "fixed":
            config['fixed_entry'].grid(row=0, column=0, sticky=(tk.W, tk.E))
        else:  # range
            config['range_frame'].grid(row=0, column=0, sticky=(tk.W, tk.E))

    def _create_sensor_params_tab(self):
        """Create the sensor parameters tab."""
        sensor_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(sensor_frame, text="Sensor")

        # Sensor information display
        info_frame = ttk.LabelFrame(sensor_frame, text="Sensor Information", padding="5")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)

        ttk.Label(info_frame, text="Selected Sensor:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.sensor_info_var = tk.StringVar(value="Sentinel-2")
        ttk.Label(info_frame, textvariable=self.sensor_info_var, font=('TkDefaultFont', 9, 'bold')).grid(
            row=0, column=1, sticky=tk.W, pady=2
        )

        # Available bands display
        ttk.Label(info_frame, text="Available Bands:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.available_bands_var = tk.StringVar(value="")
        available_label = ttk.Label(info_frame, textvariable=self.available_bands_var, wraplength=300)
        available_label.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

        # Band selection
        band_frame = ttk.LabelFrame(sensor_frame, text="Band Configuration", padding="5")
        band_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        band_frame.columnconfigure(1, weight=1)

        ttk.Label(band_frame, text="Bands to Use:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.selected_bands_var = tk.StringVar(value="B2, B3, B4, B5")
        ttk.Entry(band_frame, textvariable=self.selected_bands_var).grid(
            row=0, column=1, sticky=(tk.W, tk.E), pady=2
        )

        ttk.Label(band_frame, text="Image Band Indices:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.band_indices_var = tk.StringVar(value="1, 2, 3, 4")
        ttk.Entry(band_frame, textvariable=self.band_indices_var).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=2
        )

        # Help text
        help_text = "Bands to Use: Sensor bands (e.g., B2, B3, B4, B5)\nImage Band Indices: Corresponding indices in your image file (1-based)"
        ttk.Label(band_frame, text=help_text, font=('TkDefaultFont', 8), foreground='gray').grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0)
        )


    def _load_default_parameters(self):
        """Load default parameter values."""
        # This could be extended to load from a config file
        pass

    def _setup_sensor_definitions(self):
        """Set up sensor definitions with wavelengths and available bands."""
        # Import from controller to use centralized definitions
        from ..controllers.workflow_controller import SENSOR_DEFINITIONS
        self.sensor_definitions = SENSOR_DEFINITIONS

        # Initialize sensor display with default after definitions are loaded
        self._update_sensor_info("sentinel2")

    def _update_sensor_info(self, sensor_name):
        """Update sensor information display based on selected sensor."""
        if sensor_name in self.sensor_definitions:
            sensor_def = self.sensor_definitions[sensor_name]
            self.sensor_info_var.set(sensor_def['name'])

            # Format available bands
            bands_text = ", ".join([
                f"{band}({wavelength:.0f}nm)"
                for band, wavelength in sensor_def['bands'].items()
            ])
            self.available_bands_var.set(bands_text)
        else:
            self.sensor_info_var.set("Unknown Sensor")
            self.available_bands_var.set("No band information available")

    def update_sensor_selection(self, sensor_name):
        """Update sensor information when sensor selection changes."""
        self._update_sensor_info(sensor_name)

    def get_sensor_wavelengths(self, selected_bands, sensor_name):
        """Get wavelengths for selected bands from sensor definition."""
        from ..controllers.workflow_controller import get_sensor_wavelengths
        return get_sensor_wavelengths(selected_bands, sensor_name)

    def _reset_parameters(self):
        """Reset parameters to default values."""
        # Reset parameter configurations to defaults
        defaults = {
            'depth': {'type': 'range', 'fixed': 10.0, 'range': (0.1, 25.0)},
            'chl': {'type': 'range', 'fixed': 1.0, 'range': (0.01, 20.0)},
            'cdom': {'type': 'range', 'fixed': 0.1, 'range': (0.0001, 2.0)},
            'nap': {'type': 'range', 'fixed': 0.1, 'range': (0.001, 5.0)},
            'substrate_fraction': {'type': 'fixed', 'fixed': 1.0, 'range': (0.0, 1.0)}
        }
        
        for param_key, default_config in defaults.items():
            if param_key in self.param_configs:
                config = self.param_configs[param_key]
                config['type_var'].set(default_config['type'])
                config['fixed_var'].set(default_config['fixed'])
                config['range_min_var'].set(default_config['range'][0])
                config['range_max_var'].set(default_config['range'][1])
                self._update_parameter_widgets(param_key)
        
        # Reset LUT configuration
        self.grid_size_var.set(20)
        
        # Band configuration
        self.selected_bands_var.set("B2, B3, B4, B5")
        self.band_indices_var.set("1, 2, 3, 4")
        
        # Initialize with default sensor
        self._update_sensor_info("sentinel2")
        
        print("Parameters reset to default values")

    def _apply_parameters(self):
        """Apply current parameters to the controller."""
        try:
            params = self.get_parameters()
            self.controller.update_parameters(params)
            
            # Clear any existing lookup table to force rebuilding with new parameters
            self.controller.clear_lookup_table()
            
            # Show summary of configuration
            range_params = list(params['parameter_ranges'].keys())
            fixed_params = [k for k in params['fixed_params'].keys() 
                           if k in ['chl', 'cdom', 'nap', 'depth', 'substrate_fraction']]
            
            summary = f"Configuration applied:\n"
            summary += f"Range parameters: {', '.join(range_params)}\n"
            summary += f"Fixed parameters: {', '.join(fixed_params)}\n"
            summary += f"LUT grid size: {params['lut_params']['grid_size']}"
            
            messagebox.showinfo("Parameters Applied", summary)
            print(f"Applied parameters: {len(range_params)} ranges, {len(fixed_params)} fixed")
            
        except ValueError as e:
            messagebox.showerror("Parameter Error", str(e))

    def get_parameters(self):
        """Get current parameter values as a dictionary compatible with sambuca_core."""
        try:
            # Parse selected bands and indices
            selected_bands = [b.strip() for b in self.selected_bands_var.get().split(',')]
            band_indices = [int(i.strip()) for i in self.band_indices_var.get().split(',')]

            if len(selected_bands) != len(band_indices):
                raise ValueError("Number of selected bands must match number of band indices")

            # Process parameter configurations
            parameter_ranges = {}
            fixed_parameters = {}
            
            for param_key, config in self.param_configs.items():
                param_type = config['type_var'].get()
                
                if param_type == "fixed":
                    # Fixed parameter
                    value = config['fixed_var'].get()
                    fixed_parameters[param_key] = value
                else:
                    # Range parameter  
                    min_val = config['range_min_var'].get()
                    max_val = config['range_max_var'].get()
                    
                    if min_val >= max_val:
                        raise ValueError(f"Parameter {param_key}: minimum ({min_val}) must be less than maximum ({max_val})")
                        
                    parameter_ranges[param_key] = (min_val, max_val)
            
            # Validate that we have at least one range parameter for LUT building
            if not parameter_ranges:
                raise ValueError("At least one parameter must be set as 'range' for LUT building")
            
            # Update to match sambuca_core workflow controller expected format
            result = {
                # Parameter ranges for LUT building (these will vary)
                'parameter_ranges': parameter_ranges,
                
                # LUT configuration
                'lut_params': {
                    'grid_size': self.grid_size_var.get(),
                    'memory_optimized': False,
                    'batch_size': 1000
                },
                
                # Fixed parameters that won't vary during inversion
                'fixed_params': {
                    **fixed_parameters,  # User-configured fixed parameters
                    # Always include these sambuca_core parameters
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
                
                # Band and sensor configuration
                'selected_bands': selected_bands,
                'band_indices': band_indices,
                'sensor': 'sentinel2'  # This should come from the workflow panel
            }
            
            # Validate the configuration
            self._validate_parameter_config(result)
            
            return result
            
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid parameter format: {e}")
            
    def _validate_parameter_config(self, config):
        """Validate the parameter configuration."""
        # Check that required sambuca_core parameters are present
        required_params = {'chl', 'cdom', 'nap', 'depth', 'substrate_fraction'}
        
        all_params = set(config['parameter_ranges'].keys()) | set(config['fixed_params'].keys())
        missing_params = required_params - all_params
        
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
            
        # Validate parameter ranges
        for param, (min_val, max_val) in config['parameter_ranges'].items():
            if param == 'substrate_fraction' and (min_val < 0 or max_val > 1):
                raise ValueError(f"Substrate fraction must be between 0 and 1")
            elif param == 'depth' and min_val <= 0:
                raise ValueError(f"Depth minimum must be greater than 0")
            elif param in ['chl', 'cdom', 'nap'] and min_val <= 0:
                raise ValueError(f"Parameter {param} minimum must be greater than 0")
