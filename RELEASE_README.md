# IEDB (Integrated Encrypted Database) - Release Version

[![PyPI version](https://img.shields.io/badge/pypi-0.1.0-blue.svg)](https://pypi.org/project/iedb/)
[![UV Compatible](https://img.shields.io/badge/uv-compatible-brightgreen.svg)](https://github.com/astral-sh/uv)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A lightweight blockchain-based database with integrated encryption, authentication, and REST API capabilities.

## Release Overview

This is the official PyPI/UV compatible release of IEDB - a blockchain-enabled database system with built-in encryption, authentication, and API capabilities. This package provides a clean, well-organized interface to the core functionality.

## Features

- **Blockchain Database**: Store data with blockchain-level integrity verification
- **Encryption**: Built-in encryption for sensitive data and files
- **Authentication**: JWT-based user authentication and authorization
- **REST API**: FastAPI integration for quickly exposing your database
- **Modern Python**: Type hints, async support, and modern packaging
- **UV Compatible**: Optimized for installation with the UV package manager

## Installation

```bash
# Using UV (recommended)
uv install iedb

# Using pip
pip install iedb
```

## Basic Usage

```python
from iedb.core import BlockchainDB
from iedb.api import APIManager
from iedb.security import JWTAuth
import uvicorn

# Create a blockchain database
db = BlockchainDB('./mydata')

# Add some data
db.insert('users', {'id': '1', 'name': 'Alice'})
db.insert('users', {'id': '2', 'name': 'Bob'})

# Create an API to expose your database
api = APIManager(
    database=db,
    title="My DB API",
    description="Blockchain database API with JWT auth"
)

# Run the API server
if __name__ == "__main__":
    uvicorn.run(api.app, host="0.0.0.0", port=8000)
```

## Module Structure

The IEDB library is organized into these modules:

- **iedb.core**: Database and blockchain functionality
- **iedb.api**: FastAPI integration for REST API
- **iedb.security**: JWT authentication and user management
- **iedb.encryption**: Data and file encryption utilities

## Documentation

For full documentation, see:

- [Library Documentation](LIBRARY_DOCUMENTATION.md)
- [Comprehensive Example](comprehensive_example.py)

## Package Distribution

This package is available via:

- **PyPI**: `pip install iedb` or `uv install iedb`
- **GitHub Packages**: See the repository for details
- **Source**: Clone the repository and install with `uv install -e .`

## Running Tests

```bash
# Validate the package before using
./validate_package.sh

# Run the comprehensive example
./comprehensive_example.py
```

## License

IEDB is licensed under the GNU General Public License v3.0 (GPL-3.0).

Copyright (c) 2023-2024 niranjoyy@gmail.com

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.