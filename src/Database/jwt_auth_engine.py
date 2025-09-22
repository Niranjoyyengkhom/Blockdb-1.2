"""
JWT Authentication Engine for IEDB
==================================

Comprehensive JWT-based authentication system with role-based access control,
password hashing, token management, and security features.
"""

import jwt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger("IEDB.JWTAuth")


class UserRole(Enum):
    """User roles for RBAC"""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    DATABASE_ADMIN = "database_admin"
    USER = "user"
    READ_ONLY = "read_only"
    API_KEY = "api_key"


class TokenType(Enum):
    """JWT token types"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    RESET_PASSWORD = "reset_password"


@dataclass
class UserCredentials:
    """User credentials and profile"""
    user_id: str
    username: str
    email: str
    password_hash: str
    roles: List[UserRole]
    tenant_id: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "roles": [role.value for role in self.roles],
            "tenant_id": self.tenant_id,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "failed_attempts": self.failed_attempts,
            "locked_until": self.locked_until.isoformat() if self.locked_until else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserCredentials":
        """Create from dictionary"""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            email=data["email"],
            password_hash=data["password_hash"],
            roles=[UserRole(role) for role in data["roles"]],
            tenant_id=data.get("tenant_id"),
            is_active=data.get("is_active", True),
            is_verified=data.get("is_verified", False),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_login=datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None,
            failed_attempts=data.get("failed_attempts", 0),
            locked_until=datetime.fromisoformat(data["locked_until"]) if data.get("locked_until") else None,
            metadata=data.get("metadata", {})
        )


@dataclass
class JWTToken:
    """JWT token information"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 3600  # seconds
    scope: Optional[str] = None


@dataclass
class TokenPayload:
    """JWT token payload"""
    user_id: str
    username: str
    email: str
    roles: List[str]
    tenant_id: Optional[str] = None
    token_type: str = "access"
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=1))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JWT payload dictionary"""
        return {
            "sub": self.user_id,
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "tenant_id": self.tenant_id,
            "token_type": self.token_type,
            "iat": int(self.issued_at.timestamp()),
            "exp": int(self.expires_at.timestamp()),
            "jti": secrets.token_urlsafe(16)  # JWT ID for tracking
        }


class JWTAuthEngine:
    """
    JWT Authentication Engine with comprehensive security features
    """
    
    def __init__(self, 
                 secret_key: Optional[str] = None,
                 algorithm: str = "HS256",
                 access_token_expire_minutes: int = 60,
                 refresh_token_expire_days: int = 30,
                 storage_path: str = "auth_data"):
        """Initialize JWT authentication engine"""
        
        # JWT Configuration
        self.secret_key = secret_key or self._generate_secret_key()
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Storage
        self.storage_path = storage_path
        self.users_file = os.path.join(storage_path, "users.json")
        self.tokens_file = os.path.join(storage_path, "active_tokens.json")
        
        # In-memory caches
        self.users: Dict[str, UserCredentials] = {}
        self.active_tokens: Dict[str, Dict[str, Any]] = {}
        self.revoked_tokens: set = set()
        
        # Security settings
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        
        # Initialize storage
        self._init_storage()
        self._load_data()
        
        # HTTP Bearer for FastAPI
        self.security = HTTPBearer()
        
        logger.info("JWT Authentication Engine initialized")
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        return secrets.token_urlsafe(64)
    
    def _init_storage(self):
        """Initialize storage directories and files"""
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Initialize users file
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
        
        # Initialize tokens file
        if not os.path.exists(self.tokens_file):
            with open(self.tokens_file, 'w') as f:
                json.dump({}, f)
    
    def _load_data(self):
        """Load users and tokens from storage"""
        try:
            # Load users
            with open(self.users_file, 'r') as f:
                users_data = json.load(f)
                self.users = {
                    user_id: UserCredentials.from_dict(data)
                    for user_id, data in users_data.items()
                }
            
            # Load active tokens
            with open(self.tokens_file, 'r') as f:
                self.active_tokens = json.load(f)
            
            logger.info(f"Loaded {len(self.users)} users and {len(self.active_tokens)} active tokens")
            
        except Exception as e:
            logger.error(f"Error loading auth data: {e}")
    
    def _save_users(self):
        """Save users to storage"""
        try:
            users_data = {
                user_id: user.to_dict()
                for user_id, user in self.users.items()
            }
            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def _save_tokens(self):
        """Save active tokens to storage"""
        try:
            with open(self.tokens_file, 'w') as f:
                json.dump(self.active_tokens, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tokens: {e}")
    
    # Password Management
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    # User Management
    def create_user(self, 
                   username: str,
                   email: str,
                   password: str,
                   roles: List[UserRole],
                   tenant_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new user"""
        
        # Check if user already exists
        for user in self.users.values():
            if user.username == username or user.email == email:
                raise ValueError("User with this username or email already exists")
        
        # Generate user ID
        user_id = f"user_{secrets.token_urlsafe(16)}"
        
        # Create user credentials
        user = UserCredentials(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            roles=roles,
            tenant_id=tenant_id,
            metadata=metadata or {}
        )
        
        # Store user
        self.users[user_id] = user
        self._save_users()
        
        logger.info(f"Created user: {username} with roles: {[r.value for r in roles]}")
        return user_id
    
    def get_user(self, user_id: str) -> Optional[UserCredentials]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[UserCredentials]:
        """Get user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def get_user_by_email(self, email: str) -> Optional[UserCredentials]:
        """Get user by email"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def update_user(self, user_id: str, **updates) -> bool:
        """Update user information"""
        if user_id not in self.users:
            return False
        
        user = self.users[user_id]
        
        # Update allowed fields
        if 'email' in updates:
            user.email = updates['email']
        if 'roles' in updates:
            user.roles = updates['roles']
        if 'is_active' in updates:
            user.is_active = updates['is_active']
        if 'is_verified' in updates:
            user.is_verified = updates['is_verified']
        if 'metadata' in updates:
            user.metadata.update(updates['metadata'])
        
        self._save_users()
        return True
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        if user_id in self.users:
            del self.users[user_id]
            self._save_users()
            
            # Revoke all user tokens
            self.revoke_user_tokens(user_id)
            return True
        return False
    
    # Authentication
    def authenticate_user(self, username: str, password: str) -> Optional[UserCredentials]:
        """Authenticate user with username and password"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        # Check if account is locked
        if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked until {user.locked_until}"
            )
        
        # Check if account is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_attempts += 1
            
            # Lock account if too many failed attempts
            if user.failed_attempts >= self.max_failed_attempts:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=self.lockout_duration_minutes)
                logger.warning(f"Account locked for user: {username}")
            
            self._save_users()
            return None
        
        # Reset failed attempts on successful login
        user.failed_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)
        self._save_users()
        
        return user
    
    # Token Management
    def create_access_token(self, user: UserCredentials, expires_delta: Optional[timedelta] = None) -> str:
        """Create access token"""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = TokenPayload(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            roles=[role.value for role in user.roles],
            tenant_id=user.tenant_id,
            token_type=TokenType.ACCESS.value,
            expires_at=expire
        )
        
        token = jwt.encode(payload.to_dict(), self.secret_key, algorithm=self.algorithm)
        
        # Store active token
        self.active_tokens[token] = {
            "user_id": user.user_id,
            "token_type": TokenType.ACCESS.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expire.isoformat()
        }
        self._save_tokens()
        
        return token
    
    def create_refresh_token(self, user: UserCredentials) -> str:
        """Create refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        
        payload = TokenPayload(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            roles=[role.value for role in user.roles],
            tenant_id=user.tenant_id,
            token_type=TokenType.REFRESH.value,
            expires_at=expire
        )
        
        token = jwt.encode(payload.to_dict(), self.secret_key, algorithm=self.algorithm)
        
        # Store active token
        self.active_tokens[token] = {
            "user_id": user.user_id,
            "token_type": TokenType.REFRESH.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expire.isoformat()
        }
        self._save_tokens()
        
        return token
    
    def login(self, username: str, password: str) -> JWTToken:
        """Complete login process"""
        user = self.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Create tokens
        access_token = self.create_access_token(user)
        refresh_token = self.create_refresh_token(user)
        
        return JWTToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60
        )
    
    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode token"""
        try:
            # Check if token is revoked
            if token in self.revoked_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is in active tokens
            if token not in self.active_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token not found in active tokens"
                )
            
            # Convert to TokenPayload
            token_payload = TokenPayload(
                user_id=payload["sub"],
                username=payload["username"],
                email=payload["email"],
                roles=payload["roles"],
                tenant_id=payload.get("tenant_id"),
                token_type=payload["token_type"],
                issued_at=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            )
            
            return token_payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def refresh_access_token(self, refresh_token: str) -> JWTToken:
        """Refresh access token using refresh token"""
        token_payload = self.verify_token(refresh_token)
        
        if token_payload.token_type != TokenType.REFRESH.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type for refresh"
            )
        
        user = self.get_user(token_payload.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = self.create_access_token(user)
        
        return JWTToken(
            access_token=access_token,
            expires_in=self.access_token_expire_minutes * 60
        )
    
    def revoke_token(self, token: str):
        """Revoke a specific token"""
        self.revoked_tokens.add(token)
        if token in self.active_tokens:
            del self.active_tokens[token]
            self._save_tokens()
    
    def revoke_user_tokens(self, user_id: str):
        """Revoke all tokens for a user"""
        tokens_to_remove = []
        for token, info in self.active_tokens.items():
            if info["user_id"] == user_id:
                self.revoked_tokens.add(token)
                tokens_to_remove.append(token)
        
        for token in tokens_to_remove:
            del self.active_tokens[token]
        
        self._save_tokens()
    
    def logout(self, token: str):
        """Logout user by revoking token"""
        self.revoke_token(token)
    
    # Role-Based Access Control
    def has_role(self, user: UserCredentials, required_role: UserRole) -> bool:
        """Check if user has required role"""
        return required_role in user.roles
    
    def has_any_role(self, user: UserCredentials, required_roles: List[UserRole]) -> bool:
        """Check if user has any of the required roles"""
        return any(role in user.roles for role in required_roles)
    
    def require_role(self, token: str, required_role: UserRole) -> UserCredentials:
        """Require specific role for access"""
        token_payload = self.verify_token(token)
        user = self.get_user(token_payload.user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not self.has_role(user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}"
            )
        
        return user
    
    def require_tenant_access(self, token: str, tenant_id: str) -> UserCredentials:
        """Require tenant access"""
        token_payload = self.verify_token(token)
        user = self.get_user(token_payload.user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Super admin has access to all tenants
        if UserRole.SUPER_ADMIN in user.roles:
            return user
        
        # Check if user belongs to the tenant
        if user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )
        
        return user
    
    # Utility Methods
    def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> UserCredentials:
        """Get current user from authorization credentials"""
        token = credentials.credentials
        token_payload = self.verify_token(token)
        user = self.get_user(token_payload.user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens"""
        current_time = datetime.now(timezone.utc)
        expired_tokens = []
        
        for token, info in self.active_tokens.items():
            expires_at = datetime.fromisoformat(info["expires_at"])
            if current_time > expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.active_tokens[token]
        
        self._save_tokens()
        logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        active_users = len([u for u in self.users.values() if u.is_active])
        locked_users = len([u for u in self.users.values() if u.locked_until and u.locked_until > datetime.now(timezone.utc)])
        
        return {
            "total_users": len(self.users),
            "active_users": active_users,
            "locked_users": locked_users,
            "active_tokens": len(self.active_tokens),
            "revoked_tokens": len(self.revoked_tokens)
        }


def create_jwt_auth_engine(secret_key: Optional[str] = None, storage_path: str = "auth_data") -> JWTAuthEngine:
    """Create JWT authentication engine"""
    return JWTAuthEngine(secret_key=secret_key, storage_path=storage_path)


# FastAPI Dependencies
def create_auth_dependencies(auth_engine: JWTAuthEngine):
    """Create FastAPI dependencies for authentication"""
    
    async def get_current_user(credentials: HTTPAuthorizationCredentials = auth_engine.security):
        """FastAPI dependency to get current user"""
        return auth_engine.get_current_user(credentials)
    
    def require_role(required_role: UserRole):
        """FastAPI dependency factory for role requirements"""
        async def role_dependency(credentials: HTTPAuthorizationCredentials = auth_engine.security):
            token = credentials.credentials
            return auth_engine.require_role(token, required_role)
        return role_dependency
    
    def require_tenant_access(tenant_id: str):
        """FastAPI dependency factory for tenant access"""
        async def tenant_dependency(credentials: HTTPAuthorizationCredentials = auth_engine.security):
            token = credentials.credentials
            return auth_engine.require_tenant_access(token, tenant_id)
        return tenant_dependency
    
    return {
        "get_current_user": get_current_user,
        "require_role": require_role,
        "require_tenant_access": require_tenant_access
    }
