"""
IEDB Custom Exceptions
=====================
Custom exception classes for IEDB error handling.
"""

from typing import Optional, Dict, Any


class IEDBException(Exception):
    """Base exception class for all IEDB-related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "IEDB_ERROR"
        self.details = details or {}
    
    def __str__(self):
        return f"[{self.error_code}] {self.message}"
    
    def to_dict(self):
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class DatabaseException(IEDBException):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str, database: Optional[str] = None, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)
        self.database = database
        self.operation = operation


class SecurityException(IEDBException):
    """Exception raised for security-related errors."""
    
    def __init__(self, message: str, security_context: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SECURITY_ERROR", details)
        self.security_context = security_context


class ValidationException(IEDBException):
    """Exception raised for data validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field
        self.value = value


class AuthenticationException(SecurityException):
    """Exception raised for authentication failures."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHENTICATION", details)


class AuthorizationException(SecurityException):
    """Exception raised for authorization failures."""
    
    def __init__(self, message: str = "Authorization failed", resource: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHORIZATION", details)
        self.resource = resource


class EncryptionException(SecurityException):
    """Exception raised for encryption/decryption errors."""
    
    def __init__(self, message: str = "Encryption operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "ENCRYPTION", details)


class TenantException(DatabaseException):
    """Exception raised for tenant-related errors."""
    
    def __init__(self, message: str, tenant_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "multitenant", "TENANT_OPERATION", details)
        self.tenant_id = tenant_id


class ConfigurationException(IEDBException):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)
        self.config_key = config_key


class ConnectionException(DatabaseException):
    """Exception raised for database connection errors."""
    
    def __init__(self, message: str = "Database connection failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "unknown", "CONNECTION", details)
