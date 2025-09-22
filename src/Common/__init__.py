"""
IEDB Common Module
==================
Shared utilities and common functionality used across all IEDB modules.
"""

__version__ = "2.0.0"
__author__ = "IEDB Development Team"
__description__ = "Common utilities and shared functionality for IEDB"

# Import shared utilities when they exist
try:
    from .utils import (
        generate_unique_id,
        format_timestamp,
        validate_json,
        sanitize_string,
        calculate_hash
    )
    utils_available = True
except ImportError:
    utils_available = False

try:
    from .exceptions import (
        IEDBException,
        DatabaseException,
        SecurityException,
        ValidationException
    )
    exceptions_available = True
except ImportError:
    exceptions_available = False

try:
    from .constants import (
        DEFAULT_TIMEOUT,
        MAX_RETRIES,
        SUPPORTED_DATABASES,
        FILE_EXTENSIONS
    )
    constants_available = True
except ImportError:
    constants_available = False

__all__ = []

if utils_available:
    __all__.extend([
        "generate_unique_id",
        "format_timestamp", 
        "validate_json",
        "sanitize_string",
        "calculate_hash"
    ])

if exceptions_available:
    __all__.extend([
        "IEDBException",
        "DatabaseException",
        "SecurityException", 
        "ValidationException"
    ])

if constants_available:
    __all__.extend([
        "DEFAULT_TIMEOUT",
        "MAX_RETRIES",
        "SUPPORTED_DATABASES",
        "FILE_EXTENSIONS"
    ])
