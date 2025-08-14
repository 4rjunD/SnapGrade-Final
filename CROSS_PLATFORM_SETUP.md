# Cross-Platform Setup Guide

This application now supports **Windows**, **macOS**, and **Linux** with automatic Poppler detection.

## Poppler Installation

### Windows
```bash
# Option 1: Download precompiled binaries
# 1. Download from: https://github.com/oschwartz10612/poppler-windows/releases/
# 2. Extract to C:\poppler
# 3. Add C:\poppler\bin to your system PATH

# Option 2: Using Conda (recommended for Python environments)
conda install -c conda-forge poppler

# Option 3: Using Chocolatey
choco install poppler
```

### macOS
```bash
# Option 1: Using Homebrew (recommended)
brew install poppler

# Option 2: Using Conda
conda install -c conda-forge poppler

# Option 3: Using MacPorts
sudo port install poppler
```

### Linux (Ubuntu/Debian)
```bash
# Option 1: Using apt
sudo apt-get install poppler-utils

# Option 2: Using Conda
conda install -c conda-forge poppler
```

## Manual Configuration

If Poppler is not automatically detected, you can manually specify the path:

1. Copy `poppler_config.py.template` to `poppler_config.py`
2. Edit the file and uncomment the `MANUAL_POPPLER_PATH` line
3. Set the path to your Poppler bin directory

Example configurations:
```python
# Windows
MANUAL_POPPLER_PATH = r"C:\poppler\bin"

# macOS (Homebrew)
MANUAL_POPPLER_PATH = "/opt/homebrew/bin"

# Linux
MANUAL_POPPLER_PATH = "/usr/bin"
```

## Testing Your Setup

Run the cross-platform test to verify everything is working:

```bash
python test_cross_platform.py
```

This will check:
- Operating system detection
- Poppler installation and path detection
- pdf2image library functionality
- Platform-specific error messages

## Troubleshooting

### Common Issues

1. **"Unable to get page count" error**
   - This means Poppler is not installed or not in your PATH
   - Follow the installation instructions for your platform above

2. **Import errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`

3. **Virtual environment issues**
   - The app automatically checks virtual environment paths
   - If using conda, make sure to activate your environment first

### Platform-Specific Notes

**Windows:**
- The app checks common installation locations automatically
- Virtual environment Library/bin paths are checked
- Both .exe and non-.exe binary names are supported

**macOS:**
- Both Intel and Apple Silicon Homebrew paths are checked
- MacPorts and other package managers are supported

**Linux:**
- Standard system paths are checked first
- Snap packages and custom installations are supported

## Development Notes

The cross-platform functionality is implemented in:
- `file_processor/document_processor.py` - Main cross-platform logic
- `poppler_config.py` - Manual configuration support
- `test_cross_platform.py` - Testing and verification

The app automatically:
1. Detects your operating system
2. Checks for Poppler in system PATH
3. Searches platform-specific common installation locations
4. Falls back to manual configuration if available
5. Provides platform-specific error messages and installation instructions
