"""
Authentication Models and Schemas for IEDB JWT Authentication
===========================================================

Pydantic models for authentication requests, responses, and user management.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Re-export UserRole from jwt_auth_engine
from .jwt_auth_engine import UserRole, TokenType


class AuthRequest(BaseModel):
    """Base authentication request"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, max_length=128, description="Password")


class LoginRequest(AuthRequest):
    """Login request model"""
    remember_me: bool = Field(default=False, description="Remember login for extended period")


class RegisterRequest(AuthRequest):
    """User registration request"""
    email: EmailStr = Field(..., description="Valid email address")
    roles: List[UserRole] = Field(default=[UserRole.USER], description="User roles")
    tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenant setup")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional user metadata")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str = Field(..., description="Valid refresh token")


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(..., description="Email address for password reset")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdateRequest(BaseModel):
    """User update request"""
    email: Optional[EmailStr] = Field(None, description="New email address")
    roles: Optional[List[UserRole]] = Field(None, description="Updated roles")
    is_active: Optional[bool] = Field(None, description="Account active status")
    is_verified: Optional[bool] = Field(None, description="Account verification status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# Response Models
class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    scope: Optional[str] = Field(None, description="Token scope")


class UserResponse(BaseModel):
    """User information response"""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    roles: List[str] = Field(..., description="User roles")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    is_active: bool = Field(..., description="Account active status")
    is_verified: bool = Field(..., description="Account verification status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AuthResponse(BaseModel):
    """Authentication response"""
    user: UserResponse
    token: TokenResponse
    message: str = Field(default="Authentication successful")


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True
    data: Optional[Dict[str, Any]] = None


class AuthStatsResponse(BaseModel):
    """Authentication statistics response"""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    locked_users: int = Field(..., description="Number of locked users")
    active_tokens: int = Field(..., description="Number of active tokens")
    revoked_tokens: int = Field(..., description="Number of revoked tokens")


class UserListResponse(BaseModel):
    """User list response"""
    users: List[UserResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class APIKeyRequest(BaseModel):
    """API key creation request"""
    name: str = Field(..., min_length=1, max_length=100, description="API key name")
    scopes: List[str] = Field(default=[], description="API key scopes")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Expiration in days")


class APIKeyResponse(BaseModel):
    """API key response"""
    key_id: str = Field(..., description="API key identifier")
    name: str = Field(..., description="API key name")
    api_key: str = Field(..., description="API key token")
    scopes: List[str] = Field(..., description="API key scopes")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class RoleAssignmentRequest(BaseModel):
    """Role assignment request"""
    user_id: str = Field(..., description="User ID")
    roles: List[UserRole] = Field(..., description="Roles to assign")


class TenantAccessRequest(BaseModel):
    """Tenant access request"""
    user_id: str = Field(..., description="User ID")
    tenant_id: str = Field(..., description="Tenant ID")
    roles: List[UserRole] = Field(default=[UserRole.USER], description="Roles for the tenant")


# Query Parameters
class UserQueryParams(BaseModel):
    """User query parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search term for username or email")
    role: Optional[UserRole] = Field(None, description="Filter by role")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")


class TokenQueryParams(BaseModel):
    """Token query parameters"""
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    token_type: Optional[TokenType] = Field(None, description="Filter by token type")
    is_expired: Optional[bool] = Field(None, description="Filter by expiration status")


# Error Models
class AuthError(BaseModel):
    """Authentication error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ValidationError(BaseModel):
    """Validation error response"""
    field: str = Field(..., description="Field name with error")
    message: str = Field(..., description="Validation error message")
    value: Optional[Any] = Field(None, description="Invalid value")


# Security Models
class SecurityEvent(BaseModel):
    """Security event model"""
    event_type: str = Field(..., description="Type of security event")
    user_id: Optional[str] = Field(None, description="User ID involved")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional event details")


class LoginAttempt(BaseModel):
    """Login attempt model"""
    username: str = Field(..., description="Username attempted")
    success: bool = Field(..., description="Whether login was successful")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Attempt timestamp")
    failure_reason: Optional[str] = Field(None, description="Reason for failure if unsuccessful")


# Admin Models
class SystemInfoResponse(BaseModel):
    """System information response"""
    version: str = Field(..., description="System version")
    uptime: str = Field(..., description="System uptime")
    auth_stats: AuthStatsResponse = Field(..., description="Authentication statistics")
    security_settings: Dict[str, Any] = Field(..., description="Security configuration")


class BulkUserOperation(BaseModel):
    """Bulk user operation request"""
    operation: str = Field(..., description="Operation type (activate, deactivate, delete)")
    user_ids: List[str] = Field(..., description="List of user IDs")
    reason: Optional[str] = Field(None, description="Reason for bulk operation")


class AuditLogEntry(BaseModel):
    """Audit log entry"""
    log_id: str = Field(..., description="Unique log entry ID")
    user_id: Optional[str] = Field(None, description="User ID who performed action")
    action: str = Field(..., description="Action performed")
    resource: str = Field(..., description="Resource affected")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Action timestamp")
    ip_address: Optional[str] = Field(None, description="IP address")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional action details")


class AuditLogResponse(BaseModel):
    """Audit log response"""
    logs: List[AuditLogEntry]
    total: int
    page: int
    page_size: int
