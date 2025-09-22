"""
IEDB Database Module
==================
Database engines, storage components, and authentication for IEDB.
"""

# Import main database engines
from .multitenant_engine import MultiTenantEngine, TenantConfig, TenantDatabase, TenantUser
from .mongodb_engine import MongoStyleDBEngine
from .sql_engine import SQLEngine
from .btree_engine import BTreeEngine
from .btree_sql_engine import BTreeSQLEngine
from .archive_engine import create_archive_engine
from .compliance_engine import create_audit_trail
from .encryption_engine import TransparentEncryptionManager, create_encryption_manager
from .file_storage import FileStorageManager
from .file_storage_manager import FileStorageManager as FSManager

# Import authentication components
from .jwt_auth_engine import (
    JWTAuthEngine, 
    UserRole, 
    TokenType, 
    UserCredentials, 
    JWTToken, 
    TokenPayload,
    create_jwt_auth_engine,
    create_auth_dependencies
)
from .auth_models import (
    LoginRequest,
    RegisterRequest,
    TokenRefreshRequest,
    PasswordChangeRequest,
    UserUpdateRequest,
    TokenResponse,
    UserResponse,
    AuthResponse,
    MessageResponse,
    AuthStatsResponse
)
from .auth_api import AuthenticationAPI, create_auth_api

__all__ = [
    # Database engines
    "MultiTenantEngine",
    "TenantConfig", 
    "TenantDatabase",
    "TenantUser",
    "MongoStyleDBEngine",
    "SQLEngine",
    "BTreeEngine", 
    "BTreeSQLEngine",
    "create_archive_engine",
    "create_audit_trail",
    "TransparentEncryptionManager",
    "create_encryption_manager",
    "FileStorageManager",
    "FSManager",
    
    # Authentication engine
    "JWTAuthEngine",
    "UserRole",
    "TokenType",
    "UserCredentials",
    "JWTToken",
    "TokenPayload",
    "create_jwt_auth_engine",
    "create_auth_dependencies",
    
    # Authentication models
    "LoginRequest",
    "RegisterRequest", 
    "TokenRefreshRequest",
    "PasswordChangeRequest",
    "UserUpdateRequest",
    "TokenResponse",
    "UserResponse",
    "AuthResponse",
    "MessageResponse",
    "AuthStatsResponse",
    
    # Authentication API
    "AuthenticationAPI",
    "create_auth_api"
]
