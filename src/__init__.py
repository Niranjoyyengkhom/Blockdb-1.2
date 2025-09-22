"""IEDB - Intelligent Enterprise Database

IEDB is an advanced file-based database system with encryption, AI features,
JWT authentication, and blockchain-inspired storage.

Copyright (C) 2025 Niranjoy Yengkhom <niranjoyy@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

__version__ = "2.0.0"
__author__ = "Niranjoy Yengkhom"
__email__ = "niranjoyy@gmail.com"
__license__ = "GPLv3"

# Import main components to make them available at the package level
try:
    from .API import app
    from .Database import database
    from .blockchain_db import BlockchainDB
    from .Security import security
except ImportError:
    # Handle the case where the package is imported in a context where
    # some modules are not available or during installation
    pass