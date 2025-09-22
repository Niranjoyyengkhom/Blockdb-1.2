# IEDB Library Release Package Summary

This document provides an overview of all the files that make up the IEDB library release package.

## Package Structure

```
IEDB_Release/
├── pyproject.toml          # Package metadata and build configuration
├── setup.py                # Legacy setup script for backward compatibility
├── README_PYPI.md          # PyPI-specific readme 
├── RELEASE_README.md       # Release version readme
├── LIBRARY_DOCUMENTATION.md # Comprehensive documentation
├── src/
│   └── iedb/               # Main package directory
│       ├── __init__.py     # Package initialization with version
│       ├── py.typed        # Type hint marker file
│       ├── core/           # Core database functionality
│       │   └── __init__.py # Database and BlockchainDB implementation
│       ├── api/            # API integration
│       │   └── __init__.py # FastAPI integration
│       ├── security/       # Authentication
│       │   └── __init__.py # JWT authentication
│       └── encryption/     # Encryption utilities
│           └── __init__.py # File and data encryption
└── scripts/
    ├── build_uv.sh         # Build script for UV packaging
    ├── test_install_uv.sh  # Test package installation
    ├── upload_pypi.sh      # Upload to PyPI
    ├── upload_github.sh    # Upload to GitHub Packages
    ├── validate_package.sh # Validate package before publishing
    └── comprehensive_example.py # Example showing all features
```

## File Descriptions

### Configuration Files

- **pyproject.toml**: Modern Python packaging configuration with project metadata, dependencies, and build settings. Used by both pip and UV.
  
- **setup.py**: Legacy setup script included for backward compatibility with older Python tools.

- **README_PYPI.md**: PyPI-specific readme file shown on the PyPI page.

### Documentation

- **RELEASE_README.md**: Main readme file for the release version, providing an overview of the library.

- **LIBRARY_DOCUMENTATION.md**: Comprehensive documentation covering all library features, modules, and usage examples.

### Source Code

- **src/iedb/__init__.py**: Main package initialization file, defining version and public exports.

- **src/iedb/py.typed**: Marker file indicating that this package includes type annotations.

- **src/iedb/core/__init__.py**: Core database module with Database and BlockchainDB classes.

- **src/iedb/api/__init__.py**: API module with FastAPI integration for exposing database endpoints.

- **src/iedb/security/__init__.py**: Security module with JWT authentication and user management.

- **src/iedb/encryption/__init__.py**: Encryption module for securing data and files.

### Scripts

- **build_uv.sh**: Script to build the package using UV and create distributable files.

- **test_install_uv.sh**: Script to test installing the package from local distribution files.

- **upload_pypi.sh**: Script to upload the package to PyPI for public distribution.

- **upload_github.sh**: Script to upload the package to GitHub Packages.

- **validate_package.sh**: Script to validate the package before publishing.

- **comprehensive_example.py**: Comprehensive example demonstrating all library features.

## Dependencies

The IEDB library has these primary dependencies:

- **fastapi**: For REST API functionality
- **uvicorn**: ASGI server for running the API
- **pydantic**: For data validation and schema definition
- **cryptography**: For encryption functionality
- **python-jose**: For JWT token handling
- **passlib**: For password hashing and verification

## Build and Distribution

The package is built using modern Python packaging tools (either build + setuptools or UV). The resulting distribution includes both source distribution (.tar.gz) and wheel (.whl) formats.

## Installation

The package can be installed using either pip or UV:

```bash
# Using UV (recommended)
uv install iedb

# Using pip
pip install iedb
```