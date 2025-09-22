# IEDB UV Library Installation Guide

This guide provides instructions for installing and using the IEDB Python package with UV.

## What is UV?

UV is a modern Python package installer and resolver that is significantly faster than pip. It's written in Rust and provides a drop-in replacement for pip with better performance and more reliable dependency resolution.

## Installation

### 1. Install UV (if not already installed)

```bash
# Install UV using the official installer
curl -sSf https://astral.sh/uv/install.sh | bash

# Or if you use pip
pip install uv
```

### 2. Install IEDB Package

#### From Local Build

```bash
# Install the wheel file
uv pip install ./dist/iedb-2.0.0-py3-none-any.whl

# Or install in development mode
uv pip install -e .
```

#### From PyPI (Once Published)

```bash
# Install the latest version
uv pip install iedb

# Install a specific version
uv pip install iedb==2.0.0

# Install with extra features
uv pip install iedb[dev,ui]
```

## Usage

### Command Line Interface

The IEDB package provides a command-line interface for common operations:

```bash
# Start the IEDB server
iedb-cli server --host 0.0.0.0 --port 8000

# Initialize a new database
iedb-cli init --path ./my_database

# Create a backup
iedb-cli backup --source ./my_database --target ./backups

# Check version
iedb-cli version
```

### Python API

```python
from iedb import BlockchainDB

# Create a new database instance
db = BlockchainDB(storage_path="./my_database")

# Add data
db.insert("users", {"id": "user123", "name": "John Doe"})

# Query data
results = db.query("users", {"name": "John Doe"})
```

## Building the Package

To build the package yourself:

```bash
# Clone the repository
git clone https://github.com/Niranjoyyengkhom/Blockdb-1.2.git
cd Blockdb-1.2

# Run the build script
./build_package.sh

# This will create distribution files in the dist/ directory
```

## Advantages of Using UV

1. **Speed**: UV is 10-100x faster than pip for most operations
2. **Reliability**: Better dependency resolution avoids broken environments
3. **Compatibility**: Works as a drop-in replacement for pip
4. **Lock Files**: Better lock file support for reproducible environments
5. **Caching**: Improved caching of packages

## Support

If you encounter any issues with the IEDB UV library:

- Email: niranjoyy@gmail.com
- GitHub Issues: https://github.com/Niranjoyyengkhom/Blockdb-1.2/issues