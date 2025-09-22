# IEDB Release and Distribution Guide

This document provides instructions for releasing and distributing the IEDB library in various formats.

## Available Distribution Formats

The IEDB library can be distributed in the following formats:

1. **PyPI Package**: For installation via `pip` or `uv`
2. **Debian Package (.deb)**: For installation on Debian-based Linux distributions
3. **Windows Executable (.exe)**: For Windows users
4. **GitHub Release**: All packages can be published as GitHub releases

## Release Scripts

The following scripts are available to help with the release process:

### 1. `release.sh`

This is the master script that runs the entire release process. It will:

- Validate the package
- Upload to GitHub
- Create a .deb package
- Create a Windows executable
- Publish to PyPI (optional)
- Upload packages to GitHub Release (optional)

Usage:
```bash
./release.sh
```

### 2. `github_upload.sh`

This script handles uploading the code to GitHub and creating a release.

Usage:
```bash
./github_upload.sh
```

Features:
- Initializes a Git repository if needed
- Commits and pushes changes to GitHub
- Creates a GitHub release with the specified tag and release notes

### 3. `create_deb_package.sh`

This script creates a Debian package (.deb) for installation on Linux systems.

Usage:
```bash
./create_deb_package.sh
```

Features:
- Builds a proper Debian package structure
- Includes all necessary dependencies
- Creates a command-line tool for the IEDB library
- Provides post-installation setup

### 4. `create_windows_exe.sh`

This script creates a Windows executable (.exe) using PyInstaller.

Usage:
```bash
./create_windows_exe.sh
```

Features:
- Creates a graphical Windows application
- Bundles all dependencies
- Provides a user-friendly interface for database management
- Includes API server and encryption functionality

### 5. `upload_pypi.sh`

This script handles uploading the package to PyPI for distribution via pip.

Usage:
```bash
./upload_pypi.sh
```

Features:
- Optionally uploads to TestPyPI first for testing
- Uploads the package to PyPI
- Provides instructions for installation

## Release Workflow

The recommended release workflow is:

1. Update version numbers in `pyproject.toml` and `src/iedb/__init__.py`
2. Run `./validate_package.sh` to ensure everything is correct
3. Run `./release.sh` to execute the full release process
4. Follow the prompts to complete the release

## Installation Instructions

After releasing, users can install IEDB in the following ways:

### From PyPI

```bash
# Using UV
uv install iedb

# Using pip
pip install iedb
```

### From Debian Package

```bash
sudo dpkg -i iedb_1.0.0.deb
sudo apt-get install -f  # To resolve any dependencies
```

### From Windows Package

1. Download `iedb_windows.zip`
2. Extract the ZIP file
3. Run `IEDB_Manager.exe`

## Requirements for Building Packages

- **For .deb packages**: Debian-based system with `dpkg-deb` and `fakeroot`
- **For Windows EXE**: Python with PyInstaller and optionally Wine for cross-compilation
- **For GitHub uploads**: GitHub CLI (`gh`) installed and authenticated

## Troubleshooting

If you encounter issues during the release process:

1. Check the error messages for specific problems
2. Ensure all dependencies are installed
3. Verify that the package structure is correct
4. Check that you have the necessary permissions for all operations