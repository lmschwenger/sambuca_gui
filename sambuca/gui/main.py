#!/usr/bin/env python3
"""
Sambuca Core GUI Launcher

Main entry point for the Sambuca Core GUI application.
Supports both GUI and command-line interfaces.
"""

import sys
import argparse
from pathlib import Path

# Add the sambuca_gui directory to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))


def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append('tkinter (usually bundled with Python)')
    
    try:
        import numpy
    except ImportError:
        missing_deps.append('numpy')
        
    try:
        import matplotlib
    except ImportError:
        missing_deps.append('matplotlib')
    
    # Check optional dependencies
    optional_missing = []
    try:
        import sambuca.core
    except ImportError:
        optional_missing.append('sambuca-core (for actual processing)')
        
    try:
        import rasterio
    except ImportError:
        optional_missing.append('rasterio (for image loading)')
    
    return missing_deps, optional_missing


def gui_main():
    """Launch the GUI application."""
    try:
        from .app import main
        main()
    except ImportError as e:
        print(f"Error importing GUI modules: {e}")
        print("Make sure you're running this from the correct directory")
        print("and that all dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting GUI: {e}")
        sys.exit(1)


def cli_main(args):
    """Run command-line interface."""
    print("Sambuca GUI CLI mode")
    print(f"Image: {args.image}")
    print(f"Output: {args.output}")
    print(f"Method: {args.method}")
    
    # Basic CLI processing implementation
    try:
        from .controllers.workflow_controller import WorkflowController
        
        controller = WorkflowController()
        
        params = {
            'image_path': args.image,
            'output_dir': args.output,
            'method': args.method,
            'sensor': args.sensor,
            'siop_dir': args.siop_dir
        }
        
        def progress_callback(progress):
            print(f"Progress: {progress:.1f}%")
            
        def completion_callback(success, message):
            if success:
                print(f"✓ {message}")
            else:
                print(f"✗ {message}")
                sys.exit(1)
        
        print("Starting processing...")
        controller.process_image(params, progress_callback, completion_callback)
        
        # Wait for completion (in real implementation, this would be more sophisticated)
        import time
        time.sleep(1)
        print("Processing completed (check output directory)")
        
    except ImportError as e:
        print(f"Error: {e}")
        print("sambuca_core is required for CLI processing")
        sys.exit(1)
    except Exception as e:
        print(f"Processing error: {e}")
        sys.exit(1)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description='Sambuca Core GUI - Bio-optical modeling interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                          # Launch GUI
  %(prog)s --check-deps             # Check dependencies
  %(prog)s --cli -i image.tif -o results/  # CLI mode
        '''
    )
    
    parser.add_argument('--version', action='version', 
                       version='%(prog)s 1.2.0')
    parser.add_argument('--check-deps', action='store_true',
                       help='Check dependencies and exit')
    parser.add_argument('--cli', action='store_true',
                       help='Run in command-line mode')
    
    # CLI-specific arguments
    parser.add_argument('-i', '--image', type=str,
                       help='Input image file (required for CLI mode)')
    parser.add_argument('-o', '--output', type=str,
                       help='Output directory (required for CLI mode)')
    parser.add_argument('-m', '--method', choices=['lut', 'optimization'],
                       default='lut', help='Processing method')
    parser.add_argument('-s', '--sensor', choices=['sentinel2', 'landsat8'],
                       default='sentinel2', help='Sensor type')
    parser.add_argument('--siop-dir', type=str,
                       help='SIOP data directory (optional)')
    
    args = parser.parse_args()
    
    # Check dependencies if requested
    if args.check_deps:
        print("Checking dependencies...")
        missing, optional_missing = check_dependencies()
        
        if missing:
            print("\n❌ Missing required dependencies:")
            for dep in missing:
                print(f"  - {dep}")
        else:
            print("\n✅ All required dependencies found")
            
        if optional_missing:
            print("\n⚠️  Missing optional dependencies:")
            for dep in optional_missing:
                print(f"  - {dep}")
                
        if missing:
            print("\nPlease install missing dependencies before running the GUI.")
            sys.exit(1)
        else:
            print("\nAll dependencies are satisfied.")
            sys.exit(0)
    
    # CLI mode
    if args.cli:
        if not args.image or not args.output:
            print("Error: --image and --output are required for CLI mode")
            parser.print_help()
            sys.exit(1)
            
        cli_main(args)
    else:
        # GUI mode (default)
        missing, optional_missing = check_dependencies()
        if missing:
            print("Error: Missing required dependencies:")
            for dep in missing:
                print(f"  - {dep}")
            print("\nRun with --check-deps for more details.")
            sys.exit(1)
            
        gui_main()


if __name__ == "__main__":
    main()
