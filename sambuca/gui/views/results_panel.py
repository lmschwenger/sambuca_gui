"""
Results Panel View

Panel for displaying processing results and visualizations.
"""

import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class ResultsPanel:
    """Panel for displaying processing results."""

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.current_result = None

        self._setup_ui()
        self._setup_bindings()

    def _setup_ui(self):
        """Set up the results panel UI."""
        # Main frame
        self.frame = ttk.LabelFrame(self.parent, text="Results", padding="10")

        # Create notebook for different result views
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Summary tab
        self._create_summary_tab()

        # Visualization tab
        self._create_visualization_tab()

        # Configure grid weights
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

    def _create_summary_tab(self):
        """Create the summary results tab."""
        summary_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(summary_frame, text="Summary")

        # Text widget for summary display
        text_frame = ttk.Frame(summary_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.summary_text = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED,
                                    font=('Courier', 10))
        self.summary_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbar for text widget
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.summary_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.summary_text.configure(yscrollcommand=scrollbar.set)

        # Configure grid weights
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)

    def _create_visualization_tab(self):
        """Create the visualization tab."""
        viz_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(viz_frame, text="Visualization")

        # Control panel for visualization options
        control_frame = ttk.Frame(viz_frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Plot type selection
        ttk.Label(control_frame, text="Plot Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.plot_type_var = tk.StringVar(value="depth")
        plot_combo = ttk.Combobox(control_frame, textvariable=self.plot_type_var,
                                  values=["depth", "error", "summary"], state="readonly")
        plot_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))

        # Update plot button
        ttk.Button(control_frame, text="Update Plot",
                   command=self._update_plot).grid(row=0, column=2)

        # Create a container for matplotlib components to avoid pack/grid conflicts
        plot_container = ttk.Frame(viz_frame)
        plot_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        plot_container.rowconfigure(0, weight=1)
        plot_container.columnconfigure(0, weight=1)
        
        # Matplotlib figure
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, plot_container)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Navigation toolbar in its own frame to avoid conflicts
        toolbar_container = ttk.Frame(viz_frame)
        toolbar_container.grid(row=2, column=0, sticky=(tk.W, tk.E))
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_container)

        # Configure grid weights
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.rowconfigure(1, weight=1)

    def _setup_bindings(self):
        """Set up event bindings."""
        # Subscribe to controller events
        self.controller.subscribe('result_updated', self.update_results)

    def update_results(self, result):
        """Update the results display with new processing results."""
        self.current_result = result

        # Update summary
        self._update_summary()

        # Update visualization
        self._update_plot()

    def _update_summary(self):
        """Update the summary text display."""
        if not self.current_result:
            return

        # Enable text widget for editing
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)

        try:
            # Get summary information
            summary_text = self._generate_summary_text()
            self.summary_text.insert(1.0, summary_text)
        except Exception as e:
            self.summary_text.insert(1.0, f"Error generating summary: {e}")
        finally:
            # Disable text widget
            self.summary_text.config(state=tk.DISABLED)

    def _generate_summary_text(self):
        """Generate summary text from current results."""
        if not self.current_result:
            return "No results available."

        lines = []
        lines.append("SAMBUCA PROCESSING RESULTS")
        lines.append("=" * 50)
        lines.append("")

        # Basic information
        if hasattr(self.current_result, 'image_path'):
            lines.append(f"Input Image: {self.current_result.image_path}")
        elif 'image_path' in self.current_result:
            lines.append(f"Input Image: {self.current_result['image_path']}")

        if hasattr(self.current_result, 'workflow_config'):
            config = self.current_result.workflow_config
            lines.append(f"Sensor: {config.get('sensor', 'Unknown')}")
            lines.append(f"Processing Method: {config.get('method', 'Unknown')}")
        elif 'workflow_config' in self.current_result:
            config = self.current_result['workflow_config']
            lines.append(f"Sensor: {config.get('sensor', 'Unknown')}")
            lines.append(f"Processing Method: {config.get('method', 'Unknown')}")

        # Add timing information if available
        if 'timing' in self.current_result:
            timing = self.current_result['timing']
            lines.append(f"Processing Time: {timing.get('total', 0):.2f} seconds")
            lines.append(f"Time per Pixel: {timing.get('per_pixel', 0):.4f} seconds")

        # Add metadata if available
        if 'metadata' in self.current_result:
            meta = self.current_result['metadata']
            lines.append(f"Valid Pixels: {meta.get('n_valid_pixels', 'unknown')}")
            lines.append(f"Total Pixels: {meta.get('n_total_pixels', 'unknown')}")
            if 'image_shape' in meta:
                lines.append(f"Image Shape: {meta['image_shape']}")
            lines.append(f"Distance Metric: {meta.get('metric', 'unknown')}")
            
        lines.append("")
        lines.append("PARAMETER RESULTS")
        lines.append("-" * 20)

        # Process each parameter
        for param_name in ['depth', 'chl', 'cdom', 'nap']:
            if param_name in self.current_result:
                param_data = self.current_result[param_name]
                
                # Handle empty arrays
                if isinstance(param_data, np.ndarray) and param_data.size > 0:
                    valid_data = param_data[np.isfinite(param_data)]
                    
                    if len(valid_data) > 0:
                        lines.append(f"")
                        lines.append(f"{param_name.upper()} Statistics:")
                        lines.append(f"  Valid values: {len(valid_data):,} / {param_data.size:,}")
                        lines.append(f"  Coverage: {len(valid_data) / param_data.size * 100:.1f}%")
                        lines.append(f"  Minimum: {valid_data.min():.4f}")
                        lines.append(f"  Maximum: {valid_data.max():.4f}")
                        lines.append(f"  Mean: {valid_data.mean():.4f}")
                        lines.append(f"  Median: {np.median(valid_data):.4f}")
                        lines.append(f"  Std Dev: {valid_data.std():.4f}")
                    else:
                        lines.append(f"")
                        lines.append(f"{param_name.upper()}: No valid values found")
                else:
                    lines.append(f"")
                    lines.append(f"{param_name.upper()}: No data available")

        # Add error statistics if available
        if 'error' in self.current_result:
            error_data = self.current_result['error']
            if isinstance(error_data, np.ndarray) and error_data.size > 0:
                valid_errors = error_data[np.isfinite(error_data)]

                if len(valid_errors) > 0:
                    lines.append("")
                    lines.append("INVERSION ERROR Statistics:")
                    lines.append(f"  Mean Error: {valid_errors.mean():.6f}")
                    lines.append(f"  Min Error: {valid_errors.min():.6f}")
                    lines.append(f"  Max Error: {valid_errors.max():.6f}")
                    lines.append(f"  Std Dev: {valid_errors.std():.6f}")
                else:
                    lines.append("")
                    lines.append("ERROR: No valid error values found")

        return "\n".join(lines)

    def _update_plot(self):
        """Update the visualization plot."""
        if not self.current_result:
            return

        # Clear previous plot
        self.fig.clear()

        try:
            plot_type = self.plot_type_var.get()

            if plot_type == "depth":
                self._plot_depth_map()
            elif plot_type == "error":
                self._plot_error_map()
            elif plot_type == "summary":
                self._plot_summary()

        except Exception as e:
            # Show error in plot
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, f"Error creating plot:\n{e}",
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Plot Error")

        # Refresh canvas
        self.canvas.draw()

    def _plot_depth_map(self):
        """Plot the depth map."""
        # Check different ways the depth data might be stored
        depth_data = None
        if 'depth' in self.current_result:
            depth_data = self.current_result['depth']
        elif hasattr(self.current_result, 'results') and 'depth' in self.current_result.results:
            depth_data = self.current_result.results['depth']
        
        ax = self.fig.add_subplot(111)
        
        if depth_data is None or (isinstance(depth_data, np.ndarray) and depth_data.size == 0):
            ax.text(0.5, 0.5, "No depth data available",
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Depth Map - No Data")
            return

        # Create masked array to handle NaN values
        masked_depth = np.ma.masked_invalid(depth_data)

        if masked_depth.count() > 0:
            im = ax.imshow(masked_depth, cmap='viridis_r', origin='upper')
            self.fig.colorbar(im, ax=ax, label='Depth (m)')
            ax.set_title(f'Bathymetry Map ({masked_depth.count()} valid pixels)')
            
            # Add statistics to title if data is available
            valid_data = depth_data[np.isfinite(depth_data)]
            if len(valid_data) > 0:
                min_depth, max_depth = valid_data.min(), valid_data.max()
                ax.set_title(f'Bathymetry Map\nRange: {min_depth:.2f} - {max_depth:.2f} m')
        else:
            ax.text(0.5, 0.5, "No valid depth data",
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Depth Map - No Valid Data")

        ax.set_xlabel('X (pixels)')
        ax.set_ylabel('Y (pixels)')

    def _plot_error_map(self):
        """Plot the error map."""
        # Check different ways the error data might be stored
        error_data = None
        if 'error' in self.current_result:
            error_data = self.current_result['error']
        elif hasattr(self.current_result, 'results') and 'error' in self.current_result.results:
            error_data = self.current_result.results['error']
        
        ax = self.fig.add_subplot(111)
        
        if error_data is None or (isinstance(error_data, np.ndarray) and error_data.size == 0):
            ax.text(0.5, 0.5, "No error data available",
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Error Map - No Data")
            return

        # Create masked array to handle NaN values
        masked_error = np.ma.masked_invalid(error_data)

        if masked_error.count() > 0:
            im = ax.imshow(masked_error, cmap='hot', origin='upper')
            self.fig.colorbar(im, ax=ax, label='Error')
            
            # Add statistics to title
            valid_errors = error_data[np.isfinite(error_data)]
            if len(valid_errors) > 0:
                mean_error = valid_errors.mean()
                ax.set_title(f'Inversion Error Map\nMean Error: {mean_error:.6f}')
            else:
                ax.set_title('Inversion Error Map')
        else:
            ax.text(0.5, 0.5, "No valid error data",
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Error Map - No Valid Data")

        ax.set_xlabel('X (pixels)')
        ax.set_ylabel('Y (pixels)')

    def _plot_summary(self):
        """Plot a summary figure with multiple subplots."""
        if not self.current_result:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "No results available",
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Summary Plot")
            return

        # Get data from current result format
        available_params = []
        param_data = {}
        
        for param in ['depth', 'chl', 'cdom', 'nap', 'error']:
            if param in self.current_result:
                data = self.current_result[param]
                if isinstance(data, np.ndarray) and data.size > 0:
                    valid_data = data[np.isfinite(data)]
                    if len(valid_data) > 0:
                        available_params.append(param)
                        param_data[param] = valid_data
            elif hasattr(self.current_result, 'results') and param in self.current_result.results:
                data = self.current_result.results[param]
                if isinstance(data, np.ndarray) and data.size > 0:
                    valid_data = data[np.isfinite(data)]
                    if len(valid_data) > 0:
                        available_params.append(param)
                        param_data[param] = valid_data

        if not available_params:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "No valid data available for summary plot",
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Summary Plot - No Data")
            return

        # Create subplots based on available data
        n_plots = len(available_params)
        if n_plots == 1:
            ax = self.fig.add_subplot(111)
            param = available_params[0]
            data = param_data[param]
            ax.hist(data, bins=50, alpha=0.7, edgecolor='black')
            ax.set_xlabel(self._get_param_label(param))
            ax.set_ylabel('Frequency')
            ax.set_title(f'{param.upper()} Distribution')
            ax.grid(True, alpha=0.3)
        elif n_plots == 2:
            for i, param in enumerate(available_params):
                ax = self.fig.add_subplot(1, 2, i+1)
                data = param_data[param]
                color = ['blue', 'red', 'green', 'orange', 'purple'][i]
                ax.hist(data, bins=30, alpha=0.7, color=color, edgecolor='black')
                ax.set_xlabel(self._get_param_label(param))
                ax.set_ylabel('Frequency')
                ax.set_title(f'{param.upper()} Distribution')
                ax.grid(True, alpha=0.3)
        else:
            # Multiple subplots for more parameters
            rows = 2 if n_plots > 2 else 1
            cols = min(3, n_plots) if n_plots > 2 else n_plots
            
            for i, param in enumerate(available_params[:6]):  # Limit to 6 plots
                ax = self.fig.add_subplot(rows, cols, i+1)
                data = param_data[param]
                color = ['blue', 'red', 'green', 'orange', 'purple', 'brown'][i]
                ax.hist(data, bins=25, alpha=0.7, color=color, edgecolor='black')
                ax.set_xlabel(self._get_param_label(param))
                ax.set_ylabel('Frequency')
                ax.set_title(f'{param.upper()}')
                ax.grid(True, alpha=0.3)

        self.fig.tight_layout()
        
    def _get_param_label(self, param):
        """Get appropriate label for parameter."""
        labels = {
            'depth': 'Depth (m)',
            'chl': 'Chlorophyll (mg/m³)',
            'cdom': 'CDOM (1/m)',
            'nap': 'NAP (mg/L)',
            'error': 'Inversion Error'
        }
        return labels.get(param, param)

    def clear_results(self):
        """Clear the current results display."""
        self.current_result = None

        # Clear summary
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, "No results available.")
        self.summary_text.config(state=tk.DISABLED)

        # Clear plot
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, "No results to display",
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title("Results")
        self.canvas.draw()
