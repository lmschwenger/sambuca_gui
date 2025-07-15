import os
import re
from setuptools import setup, find_packages

# Read version from __init__.py file to avoid import issues
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "sambuca", "gui", "__init__.py")
    with open(version_file, "r", encoding="utf-8") as f:
        content = f.read()
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError("Unable to find version string.")

__version__ = get_version()

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "GUI application for sambuca_core - Semi-analytical bio-optical modeling"

setup(
    name="sambuca.gui",
    version=__version__,
    author="Lasse M. Schwenger",
    author_email="lasse.m.schwenger@gmail.com",
    description="Graphical User Interface for sambuca_core bio-optical modeling",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/lmschwenger/sambuca_gui",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Topic :: Scientific/Engineering :: GIS",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="remote-sensing bio-optics water-quality satellite-imagery aquatic modeling",
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "pandas>=1.3.0",
        
        # Image processing
        "rasterio>=1.2.0",
        "pillow>=8.0.0",
        
        # Visualization
        "matplotlib>=3.4.0",
        "seaborn>=0.11.0",
        
        # GUI framework (choose one based on your preference)
        # "PyQt5>=5.15.0",  # Alternative GUI framework
        # "PyQt6>=6.0.0",   # Alternative GUI framework
        # "PySide6>=6.0.0", # Alternative GUI framework
        
        # Configuration and utilities
        "pathlib2>=2.3.0; python_version < '3.4'",
        "typing-extensions>=3.10.0; python_version < '3.8'",
    ],
    extras_require={
        # Sambuca core integration (optional but recommended)
        "sambuca": [
            "sambuca-core>=1.0.0",
        ],
        
        # Development dependencies
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.12.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
            "isort>=5.9.0",
            "pre-commit>=2.15.0",
        ],
        
        # Documentation
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=0.5.0",
            "sphinxcontrib-napoleon>=0.7",
        ],
        
        # Testing with real data
        "test": [
            "pytest-xdist>=2.3.0",
            "pytest-benchmark>=3.4.0",
        ],
        
        # Enhanced GUI features
        "enhanced": [
            "PyQt5>=5.15.0",
            "pyqtgraph>=0.12.0",
            "qtpy>=2.0.0",
        ],
        
        # All optional dependencies
        "all": [
            "sambuca-core>=1.0.0",
            "PyQt5>=5.15.0",
            "pyqtgraph>=0.12.0",
            "qtpy>=2.0.0",
        ],
    },
    
    # Entry points for command-line tools
    entry_points={
        "console_scripts": [
            "sambuca-gui=sambuca.gui.main:main",
            "sambuca-gui-cli=sambuca.gui.main:cli_main",
        ],
        "gui_scripts": [
            "sambuca-gui-app=sambuca.gui.main:gui_main",
        ],
    },
    
    # Package data
    package_data={
        "sambuca.gui": [
            "data/*.csv",
            "data/*.json",
            "icons/*.png",
            "icons/*.ico",
            "templates/*.json",
        ],
    },
    
    # Include additional files
    include_package_data=True,
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/lmschwenger/sambuca_gui/issues",
        "Source": "https://github.com/lmschwenger/sambuca_gui",
        "Documentation": "https://sambuca-gui.readthedocs.io/",
        "Sambuca Core": "https://github.com/lmschwenger/sambuca_core",
    },
    
    # Zip safety
    zip_safe=False,
)