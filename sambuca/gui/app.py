"""
Main GUI Application

Entry point for the Sambuca Core GUI application with enhanced configuration management.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path

from .views.main_window import MainWindow
from .utils.config import ConfigManager


class SambucaGuiApp:
    """Main GUI application class for Sambuca Core with configuration management."""

    def __init__(self):
        # Initialize configuration first
        self.config_manager = ConfigManager()
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Sambuca Core - Bathymetry Processing GUI v1.2.0")
        
        # Apply configuration settings
        self._apply_configuration()
        
        # Set up styling
        self._setup_styling()
        
        # Initialize main window
        self.main_window = MainWindow(self.root, self.config_manager)
        
        # Set up window event handlers
        self._setup_event_handlers()
        
    def _apply_configuration(self):
        """Apply configuration settings to the main window."""
        # Window size
        width, height = self.config_manager.get('ui.window_size', [1000, 700])
        
        # Window position
        position = self.config_manager.get('ui.window_position')
        if position:
            x, y = position
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        else:
            # Center window on screen
            self.root.geometry(f"{width}x{height}")
            self.root.update_idletasks()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            
        # Make window resizable
        self.root.minsize(800, 600)
        
    def _setup_styling(self):
        """Configure the GUI theme and styling."""
        style = ttk.Style()
        
        # Apply theme from configuration
        theme = self.config_manager.get('ui.theme', 'clam')
        available_themes = style.theme_names()
        
        if theme in available_themes:
            style.theme_use(theme)
        elif 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
            
        # Configure custom styles
        style.configure('Heading.TLabel', font=('TkDefaultFont', 12, 'bold'))
        style.configure('Accent.TButton', font=('TkDefaultFont', 9, 'bold'))
        
        # Font size configuration
        font_size = self.config_manager.get('ui.font_size', 9)
        default_font = ('TkDefaultFont', font_size)
        self.root.option_add('*Font', default_font)
        
    def _setup_event_handlers(self):
        """Set up window event handlers for saving state."""
        # Save window position and size on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Save window state when moved or resized
        self.root.bind('<Configure>', self._on_window_configure)
        
    def _on_window_configure(self, event):
        """Handle window configuration changes."""
        # Only save if the event is for the main window
        if event.widget == self.root:
            # Save window size
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            self.config_manager.set('ui.window_size', [width, height])
            
            # Save window position
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            if x >= 0 and y >= 0:  # Avoid negative positions
                self.config_manager.set('ui.window_position', [x, y])
                
    def _on_closing(self):
        """Handle application closing."""
        try:
            # Save final configuration
            self.config_manager.save_config()
            
            # Check if there are any ongoing processes
            if hasattr(self.main_window, 'workflow_panel'):
                workflow_panel = self.main_window.workflow_panel
                if (hasattr(workflow_panel, 'process_button') and 
                    workflow_panel.process_button['state'] == 'disabled'):
                    
                    result = messagebox.askyesno(
                        "Quit Application",
                        "Processing is currently running. Are you sure you want to quit?"
                    )
                    if not result:
                        return
                        
        except Exception as e:
            print(f"Error during shutdown: {e}")
            
        # Close the application
        self.root.quit()
        self.root.destroy()
        
    def show_about_dialog(self):
        """Show the about dialog."""
        about_text = '''
Sambuca Core GUI v1.2.0

A graphical user interface for semi-analytical bio-optical modeling
of aquatic reflectance spectra.

Based on sambuca_core package.

Author: Lasse M. Schwenger
License: MIT
        '''
        messagebox.showinfo("About Sambuca GUI", about_text.strip())
        
    def show_help_dialog(self):
        """Show the help dialog."""
        help_text = '''
Quick Start Guide:

1. Configure Parameters:
   - Set parameter ranges for LUT building
   - Select sensor and bands
   - Choose processing method

2. Select Files:
   - Choose input image file
   - Set output directory
   - Optionally select SIOP directory

3. Process:
   - Build LUT if using LUT method
   - Click "Process Image" to start

4. View Results:
   - Check the Results panel for outputs
   - View depth maps and error statistics
   
For detailed help, check the documentation.
        '''
        messagebox.showinfo("Help", help_text.strip())
        
    def check_sambuca_core(self):
        """Check sambuca_core availability and show status."""
        try:
            import sambuca.core
            from sambuca.core import __version__ as core_version
            messagebox.showinfo(
                "Sambuca Core Status", 
                f"sambuca_core is available\nVersion: {core_version}"
            )
        except ImportError:
            result = messagebox.askyesno(
                "Sambuca Core Not Found",
                "sambuca_core is not installed or not available.\n\n"
                "This package is required for actual processing.\n"
                "You can still use the GUI to configure parameters.\n\n"
                "Would you like to see installation instructions?"
            )
            if result:
                install_text = '''
To install sambuca_core:

1. Using pip:
   pip install sambuca-core

2. From source:
   git clone https://github.com/lmschwenger/sambuca_core.git
   cd sambuca_core
   pip install .

3. For development:
   pip install -e .
                '''
                messagebox.showinfo("Installation Instructions", install_text.strip())

    def run(self):
        """Start the GUI application."""
        try:
            # Check for updates if enabled
            if self.config_manager.get('advanced.check_updates_on_startup', True):
                self._check_for_updates()
                
            # Add menu bar
            self._create_menu_bar()
            
            # Start the main loop
            self.root.mainloop()
            
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Shutting down...")
            self._on_closing()
        except Exception as e:
            print(f"Unexpected error: {e}")
            messagebox.showerror("Unexpected Error", 
                               f"An unexpected error occurred:\n{str(e)}")
            
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings...", command=self._show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Check Dependencies", command=self._check_dependencies)
        tools_menu.add_command(label="Sambuca Core Status", command=self.check_sambuca_core)
        tools_menu.add_separator()
        tools_menu.add_command(label="Clear Configuration", command=self._reset_config)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Quick Start", command=self.show_help_dialog)
        help_menu.add_command(label="About", command=self.show_about_dialog)
        
    def _show_settings(self):
        """Show the settings dialog."""
        self.config_manager.create_settings_dialog(self.root)
        
    def _check_dependencies(self):
        """Check and display dependency status."""
        from .main import check_dependencies
        
        missing, optional_missing = check_dependencies()
        
        status_text = "Dependency Status:\n\n"
        
        if not missing:
            status_text += "✅ All required dependencies found\n\n"
        else:
            status_text += "❌ Missing required dependencies:\n"
            for dep in missing:
                status_text += f"  - {dep}\n"
            status_text += "\n"
            
        if optional_missing:
            status_text += "⚠️ Missing optional dependencies:\n"
            for dep in optional_missing:
                status_text += f"  - {dep}\n"
        else:
            status_text += "✅ All optional dependencies found"
            
        messagebox.showinfo("Dependencies", status_text)
        
    def _reset_config(self):
        """Reset configuration to defaults."""
        result = messagebox.askyesno(
            "Reset Configuration",
            "This will reset all settings to default values.\n\n"
            "Are you sure you want to continue?"
        )
        if result:
            self.config_manager.reset_to_defaults()
            messagebox.showinfo(
                "Configuration Reset",
                "Configuration has been reset to defaults.\n"
                "Please restart the application for changes to take effect."
            )
            
    def _check_for_updates(self):
        """Check for application updates (placeholder)."""
        # This would implement actual update checking in a real application
        pass


def main():
    """Main entry point for the GUI."""
    try:
        app = SambucaGuiApp()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        # Try to show error dialog if possible
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            messagebox.showerror("Startup Error",
                               f"Failed to start Sambuca GUI:\n{str(e)}")
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
