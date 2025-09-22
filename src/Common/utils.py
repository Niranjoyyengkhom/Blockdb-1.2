"""
IEDB Common Utilities
====================
Shared utility functions used across IEDB modules.
"""

import uuid
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def generate_unique_id() -> str:
    """Generate a unique identifier."""
    return str(uuid.uuid4())


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format a datetime as ISO string with timezone."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.isoformat()


def validate_json(data: str) -> bool:
    """Validate if a string is valid JSON."""
    try:
        json.loads(data)
        return True
    except (ValueError, TypeError):
        return False


def sanitize_string(text: str) -> str:
    """Sanitize string input by removing potentially harmful characters."""
    if not isinstance(text, str):
        return str(text)
    
    # Remove control characters and normalize whitespace
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def calculate_hash(data: Any) -> str:
    """Calculate SHA-256 hash of data."""
    if isinstance(data, dict):
        data_str = json.dumps(data, sort_keys=True)
    elif isinstance(data, (list, tuple)):
        data_str = json.dumps(list(data), sort_keys=True)
    else:
        data_str = str(data)
    
    return hashlib.sha256(data_str.encode()).hexdigest()


def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary with nested key support."""
    try:
        keys = key.split('.')
        value = dictionary
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError, AttributeError):
        return default


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to maximum length with optional suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def is_valid_email(email: str) -> bool:
    """Basic email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
