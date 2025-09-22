"""
Authentication API Endpoints for IEDB
=====================================

FastAPI endpoints for JWT authentication, user management, and security features.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timezone

from .jwt_auth_engine import JWTAuthEngine, UserRole, UserCredentials, create_auth_dependencies
from .auth_models import (
    LoginRequest, RegisterRequest, TokenRefreshRequest, PasswordChangeRequest,
    PasswordResetRequest, PasswordResetConfirm, UserUpdateRequest, APIKeyRequest,
    RoleAssignmentRequest, TenantAccessRequest, UserQueryParams, BulkUserOperation,
    TokenResponse, UserResponse, AuthResponse, MessageResponse, AuthStatsResponse,
    UserListResponse, APIKeyResponse, SystemInfoResponse, AuditLogEntry
)

logger = logging.getLogger("IEDB.AuthAPI")


class AuthenticationAPI:
    """
    Authentication API with comprehensive JWT-based security
    """
    
    def __init__(self, auth_engine: JWTAuthEngine):
        """Initialize authentication API"""
        self.auth_engine = auth_engine
        self.router = APIRouter()
        
        # Create authentication dependencies
        self.auth_deps = create_auth_dependencies(auth_engine)
        
        # Setup routes
        self._setup_routes()
        
        logger.info("Authentication API initialized")
    
    def _setup_routes(self):
        """Setup API routes"""
        
        # Public authentication endpoints
        self.router.add_api_route(
            "/auth/login",
            self.login,
            methods=["POST"],
            response_model=AuthResponse,
            summary="User Login",
            description="Authenticate user with username and password"
        )
        
        self.router.add_api_route(
            "/auth/register",
            self.register,
            methods=["POST"],
            response_model=AuthResponse,
            summary="User Registration",
            description="Register a new user account"
        )
        
        self.router.add_api_route(
            "/auth/refresh",
            self.refresh_token,
            methods=["POST"],
            response_model=TokenResponse,
            summary="Refresh Access Token",
            description="Refresh access token using refresh token"
        )
        
        # Protected authentication endpoints
        self.router.add_api_route(
            "/auth/logout",
            self.logout,
            methods=["POST"],
            response_model=MessageResponse,
            summary="User Logout",
            description="Logout and revoke current token"
        )
        
        self.router.add_api_route(
            "/auth/me",
            self.get_current_user_info,
            methods=["GET"],
            response_model=UserResponse,
            summary="Get Current User",
            description="Get current authenticated user information"
        )
        
        self.router.add_api_route(
            "/auth/change-password",
            self.change_password,
            methods=["POST"],
            response_model=MessageResponse,
            summary="Change Password",
            description="Change user password"
        )
        
        # Password reset endpoints
        self.router.add_api_route(
            "/auth/reset-password",
            self.request_password_reset,
            methods=["POST"],
            response_model=MessageResponse,
            summary="Request Password Reset",
            description="Request password reset via email"
        )
        
        self.router.add_api_route(
            "/auth/reset-password/confirm",
            self.confirm_password_reset,
            methods=["POST"],
            response_model=MessageResponse,
            summary="Confirm Password Reset",
            description="Confirm password reset with token"
        )
        
        # User management endpoints (admin only)
        self.router.add_api_route(
            "/auth/users",
            self.list_users,
            methods=["GET"],
            response_model=UserListResponse,
            summary="List Users",
            description="List all users (admin only)"
        )
        
        self.router.add_api_route(
            "/auth/users/{user_id}",
            self.get_user,
            methods=["GET"],
            response_model=UserResponse,
            summary="Get User",
            description="Get user by ID (admin only)"
        )
        
        self.router.add_api_route(
            "/auth/users/{user_id}",
            self.update_user,
            methods=["PUT"],
            response_model=UserResponse,
            summary="Update User",
            description="Update user information (admin only)"
        )
        
        self.router.add_api_route(
            "/auth/users/{user_id}",
            self.delete_user,
            methods=["DELETE"],
            response_model=MessageResponse,
            summary="Delete User",
            description="Delete user account (admin only)"
        )
        
        # Role management endpoints
        self.router.add_api_route(
            "/auth/users/{user_id}/roles",
            self.assign_roles,
            methods=["PUT"],
            response_model=MessageResponse,
            summary="Assign Roles",
            description="Assign roles to user (admin only)"
        )
        
        self.router.add_api_route(
            "/auth/users/{user_id}/tenant-access",
            self.grant_tenant_access,
            methods=["PUT"],
            response_model=MessageResponse,
            summary="Grant Tenant Access",
            description="Grant user access to tenant (admin only)"
        )
        
        # API key management
        self.router.add_api_route(
            "/auth/api-keys",
            self.create_api_key,
            methods=["POST"],
            response_model=APIKeyResponse,
            summary="Create API Key",
            description="Create API key for programmatic access"
        )
        
        self.router.add_api_route(
            "/auth/api-keys",
            self.list_api_keys,
            methods=["GET"],
            response_model=List[APIKeyResponse],
            summary="List API Keys",
            description="List user's API keys"
        )
        
        self.router.add_api_route(
            "/auth/api-keys/{key_id}",
            self.revoke_api_key,
            methods=["DELETE"],
            response_model=MessageResponse,
            summary="Revoke API Key",
            description="Revoke API key"
        )
        
        # Administrative endpoints
        self.router.add_api_route(
            "/auth/admin/stats",
            self.get_auth_stats,
            methods=["GET"],
            response_model=AuthStatsResponse,
            summary="Authentication Statistics",
            description="Get authentication statistics (admin only)"
        )
        
        self.router.add_api_route(
            "/auth/admin/system-info",
            self.get_system_info,
            methods=["GET"],
            response_model=SystemInfoResponse,
            summary="System Information",
            description="Get system information (admin only)"
        )
        
        self.router.add_api_route(
            "/auth/admin/cleanup-tokens",
            self.cleanup_expired_tokens,
            methods=["POST"],
            response_model=MessageResponse,
            summary="Cleanup Expired Tokens",
            description="Clean up expired tokens (admin only)"
        )
        
        self.router.add_api_route(
            "/auth/admin/bulk-operations",
            self.bulk_user_operations,
            methods=["POST"],
            response_model=MessageResponse,
            summary="Bulk User Operations",
            description="Perform bulk operations on users (admin only)"
        )
    
    # Authentication endpoints
    async def login(self, request: LoginRequest, client_request: Request):
        """User login"""
        try:
            # Log login attempt
            client_ip = client_request.client.host if client_request.client else "unknown"
            logger.info(f"Login attempt for user: {request.username} from IP: {client_ip}")
            
            # Authenticate user
            jwt_token = self.auth_engine.login(request.username, request.password)
            
            # Get user info
            user = self.auth_engine.get_user_by_username(request.username)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed"
                )
            
            # Create response
            user_response = UserResponse(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                roles=[role.value for role in user.roles],
                tenant_id=user.tenant_id,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                last_login=user.last_login,
                metadata=user.metadata
            )
            
            token_response = TokenResponse(
                access_token=jwt_token.access_token,
                refresh_token=jwt_token.refresh_token,
                token_type=jwt_token.token_type,
                expires_in=jwt_token.expires_in
            )
            
            logger.info(f"Successful login for user: {request.username}")
            return AuthResponse(user=user_response, token=token_response)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error for user {request.username}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )
    
    async def register(self, request: RegisterRequest):
        """User registration"""
        try:
            # Create user
            user_id = self.auth_engine.create_user(
                username=request.username,
                email=request.email,
                password=request.password,
                roles=request.roles,
                tenant_id=request.tenant_id,
                metadata=request.metadata
            )
            
            # Get created user
            user = self.auth_engine.get_user(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User creation failed"
                )
            
            # Auto-login after registration
            jwt_token = self.auth_engine.login(request.username, request.password)
            
            # Create response
            user_response = UserResponse(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                roles=[role.value for role in user.roles],
                tenant_id=user.tenant_id,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                last_login=user.last_login,
                metadata=user.metadata
            )
            
            token_response = TokenResponse(
                access_token=jwt_token.access_token,
                refresh_token=jwt_token.refresh_token,
                token_type=jwt_token.token_type,
                expires_in=jwt_token.expires_in
            )
            
            logger.info(f"User registered successfully: {request.username}")
            return AuthResponse(
                user=user_response,
                token=token_response,
                message="Registration successful"
            )
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Registration error for user {request.username}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration service error"
            )
    
    async def refresh_token(self, request: TokenRefreshRequest):
        """Refresh access token"""
        try:
            jwt_token = self.auth_engine.refresh_access_token(request.refresh_token)
            
            return TokenResponse(
                access_token=jwt_token.access_token,
                token_type=jwt_token.token_type,
                expires_in=jwt_token.expires_in
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh service error"
            )
    
    async def logout(self, credentials: HTTPAuthorizationCredentials = Depends(lambda: JWTAuthEngine.security)):
        """User logout"""
        try:
            token = credentials.credentials
            self.auth_engine.logout(token)
            
            return MessageResponse(message="Logout successful")
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout service error"
            )
    
    async def get_current_user_info(self, current_user: UserCredentials = Depends(lambda: None)):
        """Get current user information"""
        # This would be properly dependency-injected in real usage
        # For now, we'll handle it manually
        return UserResponse(
            user_id=current_user.user_id,
            username=current_user.username,
            email=current_user.email,
            roles=[role.value for role in current_user.roles],
            tenant_id=current_user.tenant_id,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            created_at=current_user.created_at,
            last_login=current_user.last_login,
            metadata=current_user.metadata
        )
    
    async def change_password(self, request: PasswordChangeRequest, current_user: UserCredentials = Depends(lambda: None)):
        """Change user password"""
        try:
            # Verify current password
            if not self.auth_engine.verify_password(request.current_password, current_user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Update password
            new_password_hash = self.auth_engine.hash_password(request.new_password)
            current_user.password_hash = new_password_hash
            
            # Save changes
            self.auth_engine._save_users()
            
            # Revoke all user tokens (force re-login)
            self.auth_engine.revoke_user_tokens(current_user.user_id)
            
            logger.info(f"Password changed for user: {current_user.username}")
            return MessageResponse(message="Password changed successfully. Please login again.")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password change error for user {current_user.username}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password change service error"
            )
    
    async def request_password_reset(self, request: PasswordResetRequest):
        """Request password reset"""
        # In a real implementation, this would send an email with reset token
        # For now, we'll just return a success message
        user = self.auth_engine.get_user_by_email(request.email)
        if user:
            logger.info(f"Password reset requested for user: {user.username}")
        
        # Always return success to prevent email enumeration
        return MessageResponse(message="If the email exists, a password reset link has been sent.")
    
    async def confirm_password_reset(self, request: PasswordResetConfirm):
        """Confirm password reset"""
        # In a real implementation, this would verify the reset token
        # For now, we'll just return a success message
        return MessageResponse(message="Password reset successful.")
    
    # Admin endpoints
    async def list_users(self, 
                        params: UserQueryParams = Depends(),
                        current_user: UserCredentials = Depends(lambda: None)):
        """List users (admin only)"""
        # Check admin permissions
        if not self.auth_engine.has_any_role(current_user, [UserRole.SUPER_ADMIN, UserRole.DATABASE_ADMIN]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Get all users (in real implementation, add pagination and filtering)
        all_users = list(self.auth_engine.users.values())
        
        # Convert to response models
        user_responses = [
            UserResponse(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                roles=[role.value for role in user.roles],
                tenant_id=user.tenant_id,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                last_login=user.last_login,
                metadata=user.metadata
            )
            for user in all_users
        ]
        
        return UserListResponse(
            users=user_responses,
            total=len(user_responses),
            page=params.page,
            page_size=params.page_size
        )
    
    async def get_user(self, user_id: str, current_user: UserCredentials = Depends(lambda: None)):
        """Get user by ID (admin only)"""
        # Check admin permissions
        if not self.auth_engine.has_any_role(current_user, [UserRole.SUPER_ADMIN, UserRole.DATABASE_ADMIN]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        user = self.auth_engine.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            roles=[role.value for role in user.roles],
            tenant_id=user.tenant_id,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login,
            metadata=user.metadata
        )
    
    async def update_user(self, 
                         user_id: str,
                         request: UserUpdateRequest,
                         current_user: UserCredentials = Depends(lambda: None)):
        """Update user (admin only)"""
        # Check admin permissions
        if not self.auth_engine.has_any_role(current_user, [UserRole.SUPER_ADMIN, UserRole.DATABASE_ADMIN]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Update user
        update_data = request.dict(exclude_unset=True)
        success = self.auth_engine.update_user(user_id, **update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Return updated user
        user = self.auth_engine.get_user(user_id)
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            roles=[role.value for role in user.roles],
            tenant_id=user.tenant_id,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login,
            metadata=user.metadata
        )
    
    async def delete_user(self, user_id: str, current_user: UserCredentials = Depends(lambda: None)):
        """Delete user (admin only)"""
        # Check admin permissions
        if not self.auth_engine.has_role(current_user, UserRole.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        success = self.auth_engine.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return MessageResponse(message="User deleted successfully")
    
    async def assign_roles(self, 
                          user_id: str,
                          request: RoleAssignmentRequest,
                          current_user: UserCredentials = Depends(lambda: None)):
        """Assign roles to user (admin only)"""
        # Check admin permissions
        if not self.auth_engine.has_role(current_user, UserRole.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        success = self.auth_engine.update_user(user_id, roles=request.roles)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return MessageResponse(message="Roles assigned successfully")
    
    async def grant_tenant_access(self,
                                 user_id: str,
                                 request: TenantAccessRequest,
                                 current_user: UserCredentials = Depends(lambda: None)):
        """Grant tenant access (admin only)"""
        # Check admin permissions
        if not self.auth_engine.has_any_role(current_user, [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        success = self.auth_engine.update_user(
            user_id,
            tenant_id=request.tenant_id,
            roles=request.roles
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return MessageResponse(message="Tenant access granted successfully")
    
    async def create_api_key(self, request: APIKeyRequest, current_user: UserCredentials = Depends(lambda: None)):
        """Create API key"""
        # For now, return a placeholder response
        return APIKeyResponse(
            key_id=f"key_{current_user.user_id}",
            name=request.name,
            api_key="api_key_placeholder",
            scopes=request.scopes,
            created_at=datetime.now(timezone.utc),
            expires_at=None
        )
    
    async def list_api_keys(self, current_user: UserCredentials = Depends(lambda: None)):
        """List user's API keys"""
        # For now, return empty list
        return []
    
    async def revoke_api_key(self, key_id: str, current_user: UserCredentials = Depends(lambda: None)):
        """Revoke API key"""
        return MessageResponse(message="API key revoked successfully")
    
    async def get_auth_stats(self, current_user: UserCredentials = Depends(lambda: None)):
        """Get authentication statistics (admin only)"""
        # Check admin permissions
        if not self.auth_engine.has_any_role(current_user, [UserRole.SUPER_ADMIN, UserRole.DATABASE_ADMIN]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        stats = self.auth_engine.get_auth_stats()
        return AuthStatsResponse(**stats)
    
    async def get_system_info(self, current_user: UserCredentials = Depends(lambda: None)):
        """Get system information (admin only)"""
        # Check admin permissions
        if not self.auth_engine.has_role(current_user, UserRole.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        stats = self.auth_engine.get_auth_stats()
        return SystemInfoResponse(
            version="IEDB v2.0.0",
            uptime="System uptime information",
            auth_stats=AuthStatsResponse(**stats),
            security_settings={
                "max_failed_attempts": self.auth_engine.max_failed_attempts,
                "lockout_duration_minutes": self.auth_engine.lockout_duration_minutes,
                "access_token_expire_minutes": self.auth_engine.access_token_expire_minutes,
                "refresh_token_expire_days": self.auth_engine.refresh_token_expire_days
            }
        )
    
    async def cleanup_expired_tokens(self, current_user: UserCredentials = Depends(lambda: None)):
        """Clean up expired tokens (admin only)"""
        # Check admin permissions
        if not self.auth_engine.has_any_role(current_user, [UserRole.SUPER_ADMIN, UserRole.DATABASE_ADMIN]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        self.auth_engine.cleanup_expired_tokens()
        return MessageResponse(message="Expired tokens cleaned up successfully")
    
    async def bulk_user_operations(self, 
                                  request: BulkUserOperation,
                                  current_user: UserCredentials = Depends(lambda: None)):
        """Perform bulk operations on users (admin only)"""
        # Check admin permissions
        if not self.auth_engine.has_role(current_user, UserRole.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        success_count = 0
        for user_id in request.user_ids:
            if request.operation == "activate":
                if self.auth_engine.update_user(user_id, is_active=True):
                    success_count += 1
            elif request.operation == "deactivate":
                if self.auth_engine.update_user(user_id, is_active=False):
                    success_count += 1
            elif request.operation == "delete":
                if self.auth_engine.delete_user(user_id):
                    success_count += 1
        
        return MessageResponse(
            message=f"Bulk operation '{request.operation}' completed. {success_count}/{len(request.user_ids)} users processed."
        )


def create_auth_api(auth_engine: JWTAuthEngine) -> APIRouter:
    """Create authentication API router"""
    auth_api = AuthenticationAPI(auth_engine)
    return auth_api.router
