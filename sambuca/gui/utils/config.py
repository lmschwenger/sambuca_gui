"""
Configuration Management for Sambuca GUI

Handles configuration settings, defaults, and user preferences.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import tkinter as tk
from tkinter import messagebox

class ConfigManager:
    """Manages configuration settings for the Sambuca GUI."""
    
    DEFAULT_CONFIG = {
        'ui': {
            'theme': 'clam',
            'window_size': [1000, 700],
            'window_position': None,  # [x, y] or None for center
            'font_size': 9,
            'auto_save_config': True
        },
        'processing': {
            'default_sensor': 'sentinel2',
            'default_method': 'lut',
            'default_grid_size': 20,
            'default_processes': 4,
            'auto_build_lut': False,
            'show_progress_details': True
        },
        'paths': {
            'last_image_dir': None,
            'last_output_dir': None,
            'last_siop_dir': None,
            'recent_images': [],
            'max_recent_files': 10
        },
        'parameters': {
            'depth_range': [0.1, 25.0],
            'chl_range': [0.01, 20.0],
            'cdom_range': [0.0001, 2.0],
            'nap_range': [0.001, 5.0],
            'substrate_fraction': 1.0
        },
        'advanced': {
            'enable_debug_logging': False,
            'check_updates_on_startup': True,
            'backup_results': True,
            'compression_level': 6
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file. If None, uses default location.
        """
        if config_file is None:
            config_dir = self._get_config_directory()
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_file = config_dir / "sambuca_gui_config.json"
        else:
            self.config_file = Path(config_file)
            
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
        
    def _get_config_directory(self) -> Path:
        """Get the appropriate config directory for the current OS."""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', Path.home())) / "SambucaGUI"
        else:  # Unix-like
            config_dir = Path.home() / ".config" / "sambuca_gui"
        return config_dir
        
    def load_config(self) -> bool:
        """Load configuration from file.
        
        Returns:
            True if config was loaded successfully, False otherwise.
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                # Merge with defaults to ensure all keys exist
                self.config = self._merge_configs(self.DEFAULT_CONFIG, loaded_config)
                return True
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            
        return False
        
    def save_config(self) -> bool:
        """Save current configuration to file.
        
        Returns:
            True if config was saved successfully, False otherwise.
        """
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
            return False
            
    def _merge_configs(self, base: Dict, overlay: Dict) -> Dict:
        """Recursively merge two configuration dictionaries."""
        result = base.copy()
        
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get a configuration value using a dot-separated path.
        
        Args:
            key_path: Dot-separated path (e.g., 'ui.theme')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key_path: str, value: Any) -> None:
        """Set a configuration value using a dot-separated path.
        
        Args:
            key_path: Dot-separated path (e.g., 'ui.theme')
            value: Value to set
        """
        keys = key_path.split('.')
        config_ref = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
            
        # Set the value
        config_ref[keys[-1]] = value
        
        # Auto-save if enabled
        if self.get('ui.auto_save_config', True):
            self.save_config()
            
    def add_recent_image(self, image_path: str) -> None:
        """Add an image to the recent files list."""
        recent = self.get('paths.recent_images', [])
        
        # Remove if already in list
        if image_path in recent:
            recent.remove(image_path)
            
        # Add to front
        recent.insert(0, image_path)
        
        # Limit list size
        max_recent = self.get('paths.max_recent_files', 10)
        recent = recent[:max_recent]
        
        self.set('paths.recent_images', recent)
        
    def get_recent_images(self) -> list:
        """Get list of recent image files that still exist."""
        recent = self.get('paths.recent_images', [])
        # Filter out files that no longer exist
        existing = [path for path in recent if Path(path).exists()]
        
        # Update the list if any files were removed
        if len(existing) != len(recent):
            self.set('paths.recent_images', existing)
            
        return existing
        
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config()
        
    def export_config(self, export_path: str) -> bool:
        """Export configuration to a file.
        
        Args:
            export_path: Path to export to
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
            
    def import_config(self, import_path: str) -> bool:
        """Import configuration from a file.
        
        Args:
            import_path: Path to import from
            
        Returns:
            True if import successful, False otherwise
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                
            # Merge with defaults
            self.config = self._merge_configs(self.DEFAULT_CONFIG, imported_config)
            self.save_config()
            return True
        except Exception as e:
            print(f"Error importing config: {e}")
            return False

    def create_settings_dialog(self, parent) -> None:
        """Create a settings dialog window."""
        SettingsDialog(parent, self)


class SettingsDialog:
    """Settings configuration dialog."""
    
    def __init__(self, parent, config_manager: ConfigManager):
        self.parent = parent
        self.config_manager = config_manager
        self.window = None
        self.create_dialog()
        
    def create_dialog(self):
        """Create the settings dialog."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Sambuca GUI Settings")
        self.window.geometry("500x600")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Center the dialog
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"500x600+{x}+{y}")
        
        # Create notebook for different categories
        from tkinter import ttk
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create frames for different setting categories
        self.create_ui_settings(notebook)
        self.create_processing_settings(notebook)
        self.create_path_settings(notebook)
        
        # Buttons frame
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="OK", command=self.save_and_close).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_defaults).pack(side=tk.LEFT)
        
    def create_ui_settings(self, notebook):
        """Create UI settings tab."""
        from tkinter import ttk
        
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Interface")
        
        # Theme selection
        ttk.Label(frame, text="Theme:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.theme_var = tk.StringVar(value=self.config_manager.get('ui.theme'))
        theme_combo = ttk.Combobox(frame, textvariable=self.theme_var, 
                                  values=['clam', 'alt', 'default', 'classic'])
        theme_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Font size
        ttk.Label(frame, text="Font Size:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.font_size_var = tk.IntVar(value=self.config_manager.get('ui.font_size'))
        font_spin = ttk.Spinbox(frame, from_=8, to=16, textvariable=self.font_size_var)
        font_spin.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Auto-save config
        self.auto_save_var = tk.BooleanVar(value=self.config_manager.get('ui.auto_save_config'))
        ttk.Checkbutton(frame, text="Auto-save configuration", 
                       variable=self.auto_save_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        frame.columnconfigure(1, weight=1)
        
    def create_processing_settings(self, notebook):
        """Create processing settings tab."""
        from tkinter import ttk
        
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Processing")
        
        # Default sensor
        ttk.Label(frame, text="Default Sensor:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.sensor_var = tk.StringVar(value=self.config_manager.get('processing.default_sensor'))
        sensor_combo = ttk.Combobox(frame, textvariable=self.sensor_var, 
                                   values=['sentinel2', 'landsat8'])
        sensor_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Default method
        ttk.Label(frame, text="Default Method:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.method_var = tk.StringVar(value=self.config_manager.get('processing.default_method'))
        method_combo = ttk.Combobox(frame, textvariable=self.method_var, 
                                   values=['lut', 'optimization'])
        method_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Grid size
        ttk.Label(frame, text="Default Grid Size:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.grid_size_var = tk.IntVar(value=self.config_manager.get('processing.default_grid_size'))
        grid_spin = ttk.Spinbox(frame, from_=10, to=100, textvariable=self.grid_size_var)
        grid_spin.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Show progress details
        self.progress_details_var = tk.BooleanVar(value=self.config_manager.get('processing.show_progress_details'))
        ttk.Checkbutton(frame, text="Show detailed progress", 
                       variable=self.progress_details_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        frame.columnconfigure(1, weight=1)
        
    def create_path_settings(self, notebook):
        """Create path settings tab."""
        from tkinter import ttk
        
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Paths")
        
        # Recent files limit
        ttk.Label(frame, text="Max Recent Files:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.max_recent_var = tk.IntVar(value=self.config_manager.get('paths.max_recent_files'))
        recent_spin = ttk.Spinbox(frame, from_=5, to=20, textvariable=self.max_recent_var)
        recent_spin.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Clear recent files button
        ttk.Button(frame, text="Clear Recent Files", 
                  command=self.clear_recent_files).grid(row=1, column=0, columnspan=2, pady=10)
        
        frame.columnconfigure(1, weight=1)
        
    def clear_recent_files(self):
        """Clear the recent files list."""
        self.config_manager.set('paths.recent_images', [])
        messagebox.showinfo("Settings", "Recent files list cleared.")
        
    def reset_defaults(self):
        """Reset all settings to defaults."""
        result = messagebox.askyesno("Reset Settings", 
                                   "Reset all settings to default values?")
        if result:
            self.config_manager.reset_to_defaults()
            self.window.destroy()
            messagebox.showinfo("Settings", "Settings reset to defaults. Restart the application to see changes.")
            
    def save_and_close(self):
        """Save settings and close dialog."""
        # Save UI settings
        self.config_manager.set('ui.theme', self.theme_var.get())
        self.config_manager.set('ui.font_size', self.font_size_var.get())
        self.config_manager.set('ui.auto_save_config', self.auto_save_var.get())
        
        # Save processing settings
        self.config_manager.set('processing.default_sensor', self.sensor_var.get())
        self.config_manager.set('processing.default_method', self.method_var.get())
        self.config_manager.set('processing.default_grid_size', self.grid_size_var.get())
        self.config_manager.set('processing.show_progress_details', self.progress_details_var.get())
        
        # Save path settings
        self.config_manager.set('paths.max_recent_files', self.max_recent_var.get())
        
        self.config_manager.save_config()
        self.window.destroy()
        messagebox.showinfo("Settings", "Settings saved successfully.")
