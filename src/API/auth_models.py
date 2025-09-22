"""
Authentication Models and Schemas for IEDB JWT Authentication API
================================================================

Pydantic models for authentication requests, responses, and ABAC policy management.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Re-export enums from jwt_auth_engine
try:
    from .jwt_auth_engine import UserRole, TokenType, ResourceType, ActionType
except ImportError:
    from jwt_auth_engine import UserRole, TokenType, ResourceType, ActionType


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
    attributes: Optional[Dict[str, Dict[str, Any]]] = Field(default_factory=dict, description="ABAC attributes")
    
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


class AccessCheckRequest(BaseModel):
    """Access check request for ABAC"""
    resource_type: ResourceType = Field(..., description="Type of resource being accessed")
    action: ActionType = Field(..., description="Action being performed")
    resource_attributes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Resource attributes")


class PolicyRuleRequest(BaseModel):
    """ABAC policy rule creation/update request"""
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="Rule description")
    resource_type: ResourceType = Field(..., description="Resource type")
    action: ActionType = Field(..., description="Action type")
    subject_attributes: List[Dict[str, Any]] = Field(default_factory=list, description="Subject attribute conditions")
    resource_attributes: List[Dict[str, Any]] = Field(default_factory=list, description="Resource attribute conditions")
    environment_attributes: List[Dict[str, Any]] = Field(default_factory=list, description="Environment attribute conditions")
    conditions: List[str] = Field(default_factory=list, description="Custom Python conditions")
    effect: str = Field(default="ALLOW", description="Policy effect (ALLOW/DENY)")
    priority: int = Field(default=0, description="Rule priority")


class UserUpdateRequest(BaseModel):
    """User update request"""
    email: Optional[EmailStr] = Field(None, description="New email address")
    roles: Optional[List[UserRole]] = Field(None, description="Updated roles")
    is_active: Optional[bool] = Field(None, description="Account active status")
    is_verified: Optional[bool] = Field(None, description="Account verification status")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    attributes: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="ABAC attributes")


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
    attributes: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="ABAC attributes")


class AuthResponse(BaseModel):
    """Authentication response"""
    user: UserResponse
    token: TokenResponse
    message: str = Field(default="Authentication successful")


class AccessCheckResponse(BaseModel):
    """Access check response"""
    decision: str = Field(..., description="Access decision (ALLOW/DENY)")
    applied_policies: List[str] = Field(default_factory=list, description="Applied policy rule IDs")
    context: Dict[str, Any] = Field(default_factory=dict, description="Access context")
    error: Optional[str] = Field(None, description="Error message if any")


class PolicyRuleResponse(BaseModel):
    """ABAC policy rule response"""
    rule_id: str = Field(..., description="Rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    resource_type: str = Field(..., description="Resource type")
    action: str = Field(..., description="Action type")
    subject_attributes: List[Dict[str, Any]] = Field(default_factory=list, description="Subject attributes")
    resource_attributes: List[Dict[str, Any]] = Field(default_factory=list, description="Resource attributes")
    environment_attributes: List[Dict[str, Any]] = Field(default_factory=list, description="Environment attributes")
    conditions: List[str] = Field(default_factory=list, description="Custom conditions")
    effect: str = Field(..., description="Policy effect")
    priority: int = Field(..., description="Rule priority")


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
    abac_policies: int = Field(..., description="Number of ABAC policies")


class UserListResponse(BaseModel):
    """User list response"""
    users: List[UserResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class PolicyListResponse(BaseModel):
    """Policy list response"""
    policies: List[PolicyRuleResponse]
    total: int


# Query Parameters
class UserQueryParams(BaseModel):
    """User query parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search term for username or email")
    role: Optional[UserRole] = Field(None, description="Filter by role")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")


# ABAC Specific Models
class AttributeDefinition(BaseModel):
    """Attribute definition for ABAC"""
    name: str = Field(..., description="Attribute name")
    value: Any = Field(..., description="Attribute value")
    attribute_type: str = Field(default="string", description="Attribute type")


class ContextRequest(BaseModel):
    """Context request for ABAC evaluation"""
    subject_attributes: Dict[str, AttributeDefinition] = Field(default_factory=dict, description="Subject attributes")
    resource_attributes: Dict[str, AttributeDefinition] = Field(default_factory=dict, description="Resource attributes")
    environment_attributes: Dict[str, AttributeDefinition] = Field(default_factory=dict, description="Environment attributes")
    action: ActionType = Field(..., description="Action being performed")
    resource_type: ResourceType = Field(..., description="Resource type")


class PolicyTestRequest(BaseModel):
    """Policy test request"""
    policy_rule: PolicyRuleRequest = Field(..., description="Policy rule to test")
    test_context: ContextRequest = Field(..., description="Test context")


class PolicyTestResponse(BaseModel):
    """Policy test response"""
    policy_applies: bool = Field(..., description="Whether policy applies to context")
    condition_results: Dict[str, bool] = Field(default_factory=dict, description="Individual condition results")
    final_decision: str = Field(..., description="Final policy decision")
    error: Optional[str] = Field(None, description="Error message if any")


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


# Advanced Models
class SessionInfo(BaseModel):
    """Session information"""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    is_active: bool = Field(..., description="Session active status")


class AuditLogEntry(BaseModel):
    """Audit log entry"""
    log_id: str = Field(..., description="Unique log entry ID")
    user_id: Optional[str] = Field(None, description="User ID who performed action")
    action: str = Field(..., description="Action performed")
    resource: str = Field(..., description="Resource affected")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Action timestamp")
    ip_address: Optional[str] = Field(None, description="IP address")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional action details")
    abac_decision: Optional[str] = Field(None, description="ABAC access decision")
    applied_policies: List[str] = Field(default_factory=list, description="Applied ABAC policies")


class SystemInfoResponse(BaseModel):
    """System information response"""
    version: str = Field(..., description="System version")
    uptime: str = Field(..., description="System uptime")
    auth_stats: AuthStatsResponse = Field(..., description="Authentication statistics")
    security_settings: Dict[str, Any] = Field(..., description="Security configuration")
    abac_status: Dict[str, Any] = Field(..., description="ABAC engine status")


# Bulk Operations
class BulkUserOperation(BaseModel):
    """Bulk user operation request"""
    operation: str = Field(..., description="Operation type (activate, deactivate, delete)")
    user_ids: List[str] = Field(..., description="List of user IDs")
    reason: Optional[str] = Field(None, description="Reason for bulk operation")


class BulkPolicyOperation(BaseModel):
    """Bulk policy operation request"""
    operation: str = Field(..., description="Operation type (enable, disable, delete)")
    policy_ids: List[str] = Field(..., description="List of policy IDs")
    reason: Optional[str] = Field(None, description="Reason for bulk operation")


# Integration Models
class TenantResourceAccess(BaseModel):
    """Tenant resource access configuration"""
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: str = Field(..., description="User identifier")
    resource_type: ResourceType = Field(..., description="Resource type")
    allowed_actions: List[ActionType] = Field(..., description="Allowed actions")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional attributes")
    expires_at: Optional[datetime] = Field(None, description="Access expiration")


class DatabaseAccessRequest(BaseModel):
    """Database access request with ABAC context"""
    tenant_id: str = Field(..., description="Tenant ID")
    database_name: str = Field(..., description="Database name")
    action: ActionType = Field(..., description="Requested action")
    additional_context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class TableAccessRequest(BaseModel):
    """Table access request with ABAC context"""
    tenant_id: str = Field(..., description="Tenant ID")
    database_name: str = Field(..., description="Database name")
    table_name: str = Field(..., description="Table name")
    action: ActionType = Field(..., description="Requested action")
    additional_context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
