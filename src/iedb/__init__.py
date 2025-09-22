"""
IEDB - Intelligent Enterprise Database
Copyright (C) 2025 Niranjoy Yengkhom <niranjoyy@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

__version__ = "2.0.0"
__author__ = "Niranjoy Yengkhom <niranjoyy@gmail.com>"
__license__ = "GPLv3+"

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("iedb")
except PackageNotFoundError:
    # Package is not installed
    pass

# Import main components for easy access
from iedb.core import Database, BlockchainDB
from iedb.api import create_app, APIManager
from iedb.security import SecurityManager, JWTAuth
from iedb.encryption import EncryptionManager

__all__ = [
    'Database',
    'BlockchainDB',
    'create_app',
    'APIManager',
    'SecurityManager',
    'JWTAuth',
    'EncryptionManager',
]