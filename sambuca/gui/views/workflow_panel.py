"""
Workflow Panel View

Panel for configuring and running bathymetry workflows.
"""

import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox


class WorkflowPanel:
    """Panel for workflow configuration and execution."""

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.parameters_panel = None  # Will be set by main window

        self._setup_ui()
        self._setup_bindings()

    def _setup_ui(self):
        """Set up the workflow panel UI."""
        # Main frame
        self.frame = ttk.LabelFrame(self.parent, text="Workflow Configuration", padding="10")

        # File selection section
        file_frame = ttk.Frame(self.frame)
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        # SIOP Directory
        ttk.Label(file_frame, text="SIOP Directory:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.siop_dir_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.siop_dir_var, state="readonly").grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2
        )
        ttk.Button(file_frame, text="Browse", command=self._browse_siop_dir).grid(
            row=0, column=2, pady=2
        )

        # Input Image
        ttk.Label(file_frame, text="Input Image:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.image_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.image_path_var, state="readonly").grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2
        )
        ttk.Button(file_frame, text="Browse", command=self._browse_image).grid(
            row=1, column=2, pady=2
        )

        # Output Directory
        ttk.Label(file_frame, text="Output Directory:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.output_dir_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.output_dir_var, state="readonly").grid(
            row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2
        )
        ttk.Button(file_frame, text="Browse", command=self._browse_output_dir).grid(
            row=2, column=2, pady=2
        )

        # Processing options
        options_frame = ttk.Frame(self.frame)
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)

        # Sensor selection
        ttk.Label(options_frame, text="Sensor:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.sensor_var = tk.StringVar(value="sentinel2")
        sensor_combo = ttk.Combobox(options_frame, textvariable=self.sensor_var,
                                    values=["sentinel2", "landsat8"], state="readonly")
        sensor_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        sensor_combo.bind('<<ComboboxSelected>>', self._on_sensor_changed)

        # Processing method
        ttk.Label(options_frame, text="Method:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.method_var = tk.StringVar(value="lut")  # Changed default to LUT
        method_combo = ttk.Combobox(options_frame, textvariable=self.method_var,
                                    values=["lut", "optimization"], state="readonly")
        method_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        method_combo.bind('<<ComboboxSelected>>', self._on_method_changed)

        # Number of processes
        ttk.Label(options_frame, text="Processes:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.n_processes_var = tk.IntVar(value=4)
        processes_spin = ttk.Spinbox(options_frame, from_=1, to=16,
                                     textvariable=self.n_processes_var, width=10)
        processes_spin.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # Method description
        self.method_desc_var = tk.StringVar()
        method_desc_label = ttk.Label(options_frame, textvariable=self.method_desc_var, 
                                     font=('TkDefaultFont', 8), foreground='gray')
        method_desc_label.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))

        # Action buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        button_frame.columnconfigure(1, weight=1)  # Make progress bar expand

        # Left side buttons
        left_buttons = ttk.Frame(button_frame)
        left_buttons.grid(row=0, column=0, sticky=tk.W)
        
        self.build_lut_button = ttk.Button(left_buttons, text="Build LUT",
                                          command=self._build_lookup_table, width=12)
        self.build_lut_button.grid(row=0, column=0, padx=(0, 5), pady=5)
        
        self.process_button = ttk.Button(left_buttons, text="Process Image",
                                         command=self._process_image, style="Accent.TButton", width=12)
        self.process_button.grid(row=0, column=1, pady=5)

        # Progress section (center-right)
        progress_frame = ttk.Frame(button_frame)
        progress_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        progress_frame.columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            length=250, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var, 
                                font=('TkDefaultFont', 8))
        status_label.grid(row=1, column=0, sticky=tk.W)

    def _setup_bindings(self):
        """Set up event bindings."""
        # Set default paths if they exist
        default_siop = Path("../data/siops")
        if default_siop.exists():
            self.siop_dir_var.set(str(default_siop.resolve()))
            
        # Update method description on startup
        self._update_method_description()

    def _browse_siop_dir(self):
        """Browse for SIOP directory."""
        directory = filedialog.askdirectory(title="Select SIOP Directory")
        if directory:
            self.siop_dir_var.set(directory)

    def _browse_image(self):
        """Browse for input image file."""
        filename = filedialog.askopenfilename(
            title="Select Input Image",
            filetypes=[
                ("TIFF files", "*.tif *.tiff"),
                ("IMG files", "*.img"),
                ("NetCDF files", "*.nc"),
                ("HDF files", "*.hdf *.h5"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.image_path_var.set(filename)
            self.status_var.set(f"Selected: {Path(filename).name}")

    def _browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)

    def _validate_inputs(self):
        """Validate user inputs before processing."""
        if not self.image_path_var.get():
            messagebox.showerror("Error", "Please select an input image")
            return False

        if not self.output_dir_var.get():
            messagebox.showerror("Error", "Please select an output directory")
            return False

        # Check if paths exist
        if not Path(self.image_path_var.get()).exists():
            messagebox.showerror("Error", "Input image does not exist")
            return False

        # SIOP directory is optional - will use default if not specified
        siop_dir = self.siop_dir_var.get()
        if siop_dir and not Path(siop_dir).exists():
            messagebox.showerror("Error", "SIOP directory does not exist")
            return False
            
        # Validate image file format
        image_path = Path(self.image_path_var.get())
        valid_extensions = {'.tif', '.tiff', '.img', '.dat', '.nc', '.hdf'}
        if image_path.suffix.lower() not in valid_extensions:
            result = messagebox.askyesno(
                "Warning", 
                f"Image format '{image_path.suffix}' might not be supported.\n"
                "Supported formats: TIFF, IMG, NetCDF, HDF.\n"
                "Continue anyway?"
            )
            if not result:
                return False

        return True

    def _build_lookup_table(self):
        """Build lookup table separately."""
        self.build_lut_button.config(state="disabled")
        self.status_var.set("Building lookup table...")
        self.progress_var.set(0)

        # Get the current workflow configuration
        config = self.controller.get_workflow_config()

        if not config['sambuca_core_available']:
            messagebox.showerror("Error", "sambuca_core is not available. Please install sambuca_core first.")
            return

        # Start LUT building
        success = self.controller.build_lookup_table(self._on_lut_progress)

        if success:
            self.status_var.set("Lookup table built successfully")
            messagebox.showinfo("Success", "Lookup table built successfully")
        else:
            self.status_var.set("Failed to build lookup table")
            messagebox.showerror("Error", "Failed to build lookup table. Check console for details.")

            
    def _on_lut_progress(self, progress):
        """Handle LUT building progress updates."""
        self.progress_var.set(progress)
        if progress < 100:
            self.status_var.set(f"Building lookup table... {progress:.0f}%")
        self.parent.update_idletasks()

    def _process_image(self):
        """Process the selected image."""
        if not self._validate_inputs():
            return

        # Check if LUT is needed and available
        if self.method_var.get() == "lut":
            config = self.controller.get_workflow_config()
            if not config.get('lookup_table_built', False):
                result = messagebox.askyesno(
                    "Lookup Table Required",
                    "Lookup table method selected but no LUT is built.\n"
                    "Build lookup table now? (This may take a few minutes)"
                )
                if result:
                    if not self.controller.build_lookup_table(self._on_lut_progress):
                        messagebox.showerror("Error", "Failed to build lookup table. Cannot proceed.")
                        return
                else:
                    return

        # Disable buttons during processing
        self.process_button.config(state="disabled")
        self.build_lut_button.config(state="disabled")
        self.progress_var.set(0)
        self.status_var.set("Starting image processing...")

        try:
            # Prepare parameters
            params = {
                'siop_dir': self.siop_dir_var.get() or None,  # Use None for default
                'image_path': self.image_path_var.get(),
                'output_dir': self.output_dir_var.get(),
                'sensor': self.sensor_var.get(),
                'method': self.method_var.get(),
                'n_processes': self.n_processes_var.get()
            }

            # Start processing (this will be handled by the controller)
            self.controller.process_image(params, self._on_progress, self._on_complete)

        except Exception as e:
            messagebox.showerror("Error", f"Processing failed: {str(e)}")
            self._reset_ui_state()

    def _on_progress(self, progress):
        """Handle progress updates."""
        self.progress_var.set(progress)
        
        # Update status based on progress
        if progress < 10:
            self.status_var.set("Initializing...")
        elif progress < 30:
            self.status_var.set("Loading data...")
        elif progress < 70:
            self.status_var.set("Processing image...")
        elif progress < 90:
            self.status_var.set("Finalizing results...")
        elif progress < 100:
            self.status_var.set("Saving outputs...")
        else:
            self.status_var.set("Complete")
            
        self.parent.update_idletasks()

    def _on_complete(self, success, message):
        """Handle processing completion."""
        self._reset_ui_state()
        
        if success:
            self.progress_var.set(100)
            self.status_var.set("Processing completed successfully")
            messagebox.showinfo("Success", message)
        else:
            self.progress_var.set(0)
            self.status_var.set("Processing failed")
            messagebox.showerror("Error", message)
            
    def _reset_ui_state(self):
        """Reset UI state after processing."""
        self.process_button.config(state="normal")
        self.build_lut_button.config(state="normal")

    def _on_sensor_changed(self, event):
        """Handle sensor selection change."""
        if self.parameters_panel:
            self.parameters_panel.update_sensor_selection(self.sensor_var.get())
        self.status_var.set(f"Sensor changed to {self.sensor_var.get()}")
        
        # Clear LUT when sensor changes since wavelengths will be different
        self.controller.clear_lookup_table()
        
    def _on_method_changed(self, event):
        """Handle method selection change."""
        self._update_method_description()
        
    def _update_method_description(self):
        """Update method description text."""
        method = self.method_var.get()
        descriptions = {
            'lut': 'Lookup Table: Fast processing using pre-computed spectra grid. Requires LUT building.',
            'optimization': 'Optimization: Higher accuracy using fine-resolution temporary LUT. Slower but more precise.'
        }
        self.method_desc_var.set(descriptions.get(method, ''))

    def set_parameters_panel(self, parameters_panel):
        """Set reference to parameters panel for sensor updates."""
        self.parameters_panel = parameters_panel
