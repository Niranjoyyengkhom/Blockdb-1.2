"""
Enhanced Authentication System
=============================

Comprehensive authentication with mnemonic-based auth, JWT tokens, 
session management, and security blocking for unauthorized access.
"""

import hashlib
import secrets
import uuid
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import re
import ipaddress

try:
    from mnemonic import Mnemonic
    MNEMONIC_AVAILABLE = True
except ImportError:
    MNEMONIC_AVAILABLE = False
    print("Warning: Mnemonic package not available. Mnemonic auth will be disabled.")


class AuthMethod(Enum):
    """Authentication methods"""
    PASSWORD = "password"
    MNEMONIC = "mnemonic"
    JWT_TOKEN = "jwt_token"
    API_KEY = "api_key"
    MULTI_FACTOR = "multi_factor"


class SessionStatus(Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


class SecurityEventType(Enum):
    """Security event types"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ACCOUNT_LOCKED = "account_locked"
    PERMISSION_DENIED = "permission_denied"
    TOKEN_EXPIRED = "token_expired"
    INVALID_MNEMONIC = "invalid_mnemonic"


@dataclass
class UserCredentials:
    """User credentials structure"""
    user_id: str
    tenant_id: str
    username: str
    email: str
    password_hash: Optional[str] = None
    mnemonic_hash: Optional[str] = None
    salt: str = field(default_factory=lambda: secrets.token_hex(16))
    auth_methods: Set[AuthMethod] = field(default_factory=set)
    is_active: bool = True
    is_locked: bool = False
    failed_attempts: int = 0
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "mnemonic_hash": self.mnemonic_hash,
            "salt": self.salt,
            "auth_methods": [method.value for method in self.auth_methods],
            "is_active": self.is_active,
            "is_locked": self.is_locked,
            "failed_attempts": self.failed_attempts,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserCredentials':
        """Create from dictionary"""
        return cls(
            user_id=data["user_id"],
            tenant_id=data["tenant_id"],
            username=data["username"],
            email=data["email"],
            password_hash=data.get("password_hash"),
            mnemonic_hash=data.get("mnemonic_hash"),
            salt=data.get("salt", secrets.token_hex(16)),
            auth_methods={AuthMethod(method) for method in data.get("auth_methods", [])},
            is_active=data.get("is_active", True),
            is_locked=data.get("is_locked", False),
            failed_attempts=data.get("failed_attempts", 0),
            last_login=datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class AuthSession:
    """Authentication session"""
    session_id: str
    user_id: str
    tenant_id: str
    status: SessionStatus
    auth_method: AuthMethod
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    permissions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if session is valid"""
        now = datetime.now(timezone.utc)
        return (
            self.status == SessionStatus.ACTIVE and
            self.expires_at > now and
            (now - self.last_activity).seconds < 3600  # 1 hour inactivity limit
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "status": self.status.value,
            "auth_method": self.auth_method.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "permissions": list(self.permissions),
            "metadata": self.metadata
        }


@dataclass
class SecurityEvent:
    """Security event for audit trail"""
    event_id: str
    event_type: SecurityEventType
    user_id: Optional[str]
    tenant_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any]
    severity: str = "medium"  # low, medium, high, critical
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "severity": self.severity
        }


class MnemonicAuthenticator:
    """Mnemonic-based authentication system"""
    
    def __init__(self, language: str = "english"):
        """Initialize mnemonic authenticator"""
        self.available = MNEMONIC_AVAILABLE
        if self.available:
            self.mnemonic = Mnemonic(language)
        else:
            self.mnemonic = None
    
    def generate_mnemonic(self, strength: int = 128) -> Optional[str]:
        """Generate a new mnemonic phrase"""
        if not self.available:
            return None
        
        return self.mnemonic.generate(strength=strength)
    
    def mnemonic_to_seed(self, mnemonic_phrase: str, passphrase: str = "") -> Optional[bytes]:
        """Convert mnemonic to seed bytes"""
        if not self.available:
            return None
        
        return self.mnemonic.to_seed(mnemonic_phrase, passphrase)
    
    def validate_mnemonic(self, mnemonic_phrase: str) -> bool:
        """Validate mnemonic phrase"""
        if not self.available:
            return False
        
        return self.mnemonic.check(mnemonic_phrase)
    
    def hash_mnemonic(self, mnemonic_phrase: str, salt: str) -> str:
        """Hash mnemonic phrase for storage"""
        if not self.available:
            raise ValueError("Mnemonic authentication not available")
        
        # Convert mnemonic to seed
        seed = self.mnemonic_to_seed(mnemonic_phrase)
        
        # Hash with salt
        combined = salt.encode() + seed
        return hashlib.sha256(combined).hexdigest()


class EnhancedAuthManager:
    """
    Enhanced authentication manager with multiple auth methods,
    session management, and security monitoring
    """
    
    def __init__(self, system_db, jwt_secret: Optional[str] = None):
        """Initialize authentication manager"""
        self.system_db = system_db
        self.jwt_secret = jwt_secret or secrets.token_urlsafe(32)
        self.mnemonic_auth = MnemonicAuthenticator()
        
        # Security settings
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.session_duration = timedelta(hours=24)
        self.jwt_expiry = timedelta(hours=1)
        
        # Active sessions
        self.active_sessions: Dict[str, AuthSession] = {}
        
        # Rate limiting
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.max_requests_per_minute = 10
        
        # Blocked IPs
        self.blocked_ips: Set[str] = set()
        
        # Initialize collections
        self._initialize_auth_collections()
    
    def _initialize_auth_collections(self):
        """Initialize authentication collections"""
        collections = [
            "user_credentials",
            "auth_sessions", 
            "security_events",
            "api_keys",
            "blocked_ips"
        ]
        
        for collection in collections:
            try:
                self.system_db.create_collection(collection)
            except Exception:
                pass  # Collection might already exist
    
    def _check_rate_limit(self, ip_address: str) -> bool:
        """Check if IP is rate limited"""
        now = datetime.now(timezone.utc)
        
        if ip_address not in self.rate_limits:
            self.rate_limits[ip_address] = []
        
        # Clean old requests
        cutoff = now - timedelta(minutes=1)
        self.rate_limits[ip_address] = [
            req_time for req_time in self.rate_limits[ip_address] 
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.rate_limits[ip_address]) >= self.max_requests_per_minute:
            return False
        
        # Add current request
        self.rate_limits[ip_address].append(now)
        return True
    
    def _log_security_event(
        self, 
        event_type: SecurityEventType, 
        ip_address: str,
        user_agent: str = "",
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "medium"
    ):
        """Log security event"""
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(timezone.utc),
            details=details or {},
            severity=severity
        )
        
        try:
            self.system_db.insert_one("security_events", event.to_dict())
        except Exception as e:
            print(f"Failed to log security event: {e}")
    
    def create_user(
        self, 
        tenant_id: str,
        username: str,
        email: str,
        password: Optional[str] = None,
        mnemonic_phrase: Optional[str] = None,
        auth_methods: Optional[Set[AuthMethod]] = None
    ) -> Dict[str, Any]:
        """Create new user with credentials"""
        try:
            # Validate inputs
            if not auth_methods:
                auth_methods = {AuthMethod.PASSWORD}
            
            if AuthMethod.PASSWORD in auth_methods and not password:
                return {"success": False, "error": "Password required for password authentication"}
            
            if AuthMethod.MNEMONIC in auth_methods and not mnemonic_phrase:
                if self.mnemonic_auth.available:
                    # Generate mnemonic if not provided
                    generated_mnemonic = self.mnemonic_auth.generate_mnemonic()
                    if generated_mnemonic:
                        mnemonic_phrase = generated_mnemonic
                    else:
                        return {"success": False, "error": "Failed to generate mnemonic"}
                else:
                    return {"success": False, "error": "Mnemonic authentication not available"}
            
            # Check if user already exists
            existing = self.system_db.find_one(
                "user_credentials", 
                {"$or": [{"username": username}, {"email": email}, {"tenant_id": tenant_id}]}
            )
            
            if existing.get("success") and existing.get("document"):
                return {"success": False, "error": "User already exists"}
            
            # Create user credentials
            user_id = str(uuid.uuid4())
            salt = secrets.token_hex(16)
            
            credentials = UserCredentials(
                user_id=user_id,
                tenant_id=tenant_id,
                username=username,
                email=email,
                salt=salt,
                auth_methods=auth_methods
            )
            
            # Hash password if provided
            if password and AuthMethod.PASSWORD in auth_methods:
                password_bytes = password.encode('utf-8')
                salt_bytes = salt.encode('utf-8')
                credentials.password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
            
            # Hash mnemonic if provided
            if mnemonic_phrase and AuthMethod.MNEMONIC in auth_methods:
                if not self.mnemonic_auth.validate_mnemonic(mnemonic_phrase):
                    return {"success": False, "error": "Invalid mnemonic phrase"}
                credentials.mnemonic_hash = self.mnemonic_auth.hash_mnemonic(mnemonic_phrase, salt)
            
            # Store credentials
            result = self.system_db.insert_one("user_credentials", credentials.to_dict())
            
            if result.get("success"):
                response = {
                    "success": True,
                    "user_id": user_id,
                    "auth_methods": [method.value for method in auth_methods]
                }
                
                # Include generated mnemonic if applicable
                if mnemonic_phrase and AuthMethod.MNEMONIC in auth_methods:
                    response["mnemonic_phrase"] = mnemonic_phrase
                
                return response
            else:
                return {"success": False, "error": "Failed to create user"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def authenticate(
        self,
        tenant_id: str,
        username: str,
        credential: str,
        auth_method: AuthMethod,
        ip_address: str,
        user_agent: str = ""
    ) -> Dict[str, Any]:
        """Authenticate user with various methods"""
        try:
            # Check rate limiting
            if not self._check_rate_limit(ip_address):
                self._log_security_event(
                    SecurityEventType.SUSPICIOUS_ACTIVITY,
                    ip_address,
                    user_agent,
                    details={"reason": "Rate limit exceeded"}
                )
                return {"success": False, "error": "Rate limit exceeded"}
            
            # Check if IP is blocked
            if ip_address in self.blocked_ips:
                self._log_security_event(
                    SecurityEventType.UNAUTHORIZED_ACCESS,
                    ip_address,
                    user_agent,
                    details={"reason": "Blocked IP"}
                )
                return {"success": False, "error": "Access denied"}
            
            # Get user credentials
            user_result = self.system_db.find_one(
                "user_credentials",
                {"tenant_id": tenant_id, "username": username}
            )
            
            if not user_result.get("success") or not user_result.get("document"):
                self._log_security_event(
                    SecurityEventType.LOGIN_FAILED,
                    ip_address,
                    user_agent,
                    details={"reason": "User not found", "username": username}
                )
                return {"success": False, "error": "Invalid credentials"}
            
            user_creds = UserCredentials.from_dict(user_result["document"])
            
            # Check if user is active and not locked
            if not user_creds.is_active or user_creds.is_locked:
                self._log_security_event(
                    SecurityEventType.LOGIN_FAILED,
                    ip_address,
                    user_agent,
                    user_id=user_creds.user_id,
                    tenant_id=tenant_id,
                    details={"reason": "Account inactive or locked"}
                )
                return {"success": False, "error": "Account is inactive or locked"}
            
            # Check if auth method is supported
            if auth_method not in user_creds.auth_methods:
                return {"success": False, "error": "Authentication method not supported"}
            
            # Verify credentials based on method
            auth_success = False
            
            if auth_method == AuthMethod.PASSWORD:
                if user_creds.password_hash:
                    auth_success = bcrypt.checkpw(
                        credential.encode('utf-8'),
                        user_creds.password_hash.encode('utf-8')
                    )
            
            elif auth_method == AuthMethod.MNEMONIC:
                if user_creds.mnemonic_hash and self.mnemonic_auth.available:
                    try:
                        computed_hash = self.mnemonic_auth.hash_mnemonic(credential, user_creds.salt)
                        auth_success = computed_hash == user_creds.mnemonic_hash
                    except Exception:
                        auth_success = False
            
            if auth_success:
                # Update login info
                user_creds.last_login = datetime.now(timezone.utc)
                user_creds.failed_attempts = 0
                
                self.system_db.update_one(
                    "user_credentials",
                    {"user_id": user_creds.user_id},
                    {"$set": {
                        "last_login": user_creds.last_login.isoformat(),
                        "failed_attempts": 0
                    }}
                )
                
                # Create session
                session = self._create_session(
                    user_creds.user_id,
                    tenant_id,
                    auth_method,
                    ip_address,
                    user_agent
                )
                
                # Generate JWT token
                jwt_token = self._generate_jwt_token(user_creds.user_id, tenant_id)
                
                self._log_security_event(
                    SecurityEventType.LOGIN_SUCCESS,
                    ip_address,
                    user_agent,
                    user_id=user_creds.user_id,
                    tenant_id=tenant_id
                )
                
                return {
                    "success": True,
                    "user_id": user_creds.user_id,
                    "session_id": session.session_id,
                    "jwt_token": jwt_token,
                    "expires_at": session.expires_at.isoformat()
                }
            else:
                # Handle failed attempt
                user_creds.failed_attempts += 1
                
                # Lock account if too many failures
                if user_creds.failed_attempts >= self.max_failed_attempts:
                    user_creds.is_locked = True
                    self._log_security_event(
                        SecurityEventType.ACCOUNT_LOCKED,
                        ip_address,
                        user_agent,
                        user_id=user_creds.user_id,
                        tenant_id=tenant_id,
                        severity="high"
                    )
                
                self.system_db.update_one(
                    "user_credentials",
                    {"user_id": user_creds.user_id},
                    {"$set": {
                        "failed_attempts": user_creds.failed_attempts,
                        "is_locked": user_creds.is_locked
                    }}
                )
                
                self._log_security_event(
                    SecurityEventType.LOGIN_FAILED,
                    ip_address,
                    user_agent,
                    user_id=user_creds.user_id,
                    tenant_id=tenant_id,
                    details={"attempts": user_creds.failed_attempts}
                )
                
                return {"success": False, "error": "Invalid credentials"}
        
        except Exception as e:
            self._log_security_event(
                SecurityEventType.LOGIN_FAILED,
                ip_address,
                user_agent,
                details={"error": str(e)},
                severity="high"
            )
            return {"success": False, "error": str(e)}
    
    def _create_session(
        self,
        user_id: str,
        tenant_id: str,
        auth_method: AuthMethod,
        ip_address: str,
        user_agent: str
    ) -> AuthSession:
        """Create authentication session"""
        now = datetime.now(timezone.utc)
        session = AuthSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            status=SessionStatus.ACTIVE,
            auth_method=auth_method,
            created_at=now,
            expires_at=now + self.session_duration,
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store session
        self.active_sessions[session.session_id] = session
        self.system_db.insert_one("auth_sessions", session.to_dict())
        
        return session
    
    def _generate_jwt_token(self, user_id: str, tenant_id: str) -> str:
        """Generate JWT token"""
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "iat": now,
            "exp": now + self.jwt_expiry,
            "iss": "blockchain-db"
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def validate_session(self, session_id: str) -> Optional[AuthSession]:
        """Validate and return session if valid"""
        session = self.active_sessions.get(session_id)
        
        if session and session.is_valid():
            # Update last activity
            session.last_activity = datetime.now(timezone.utc)
            return session
        
        # Remove invalid session
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        return None
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = SessionStatus.REVOKED
            del self.active_sessions[session_id]
            
            # Update in database
            self.system_db.update_one(
                "auth_sessions",
                {"session_id": session_id},
                {"$set": {"status": SessionStatus.REVOKED.value}}
            )
            return True
        return False
    
    def block_ip(self, ip_address: str, reason: str = "") -> bool:
        """Block IP address"""
        self.blocked_ips.add(ip_address)
        
        # Store in database
        self.system_db.insert_one("blocked_ips", {
            "ip_address": ip_address,
            "reason": reason,
            "blocked_at": datetime.now(timezone.utc).isoformat()
        })
        
        return True
    
    def get_security_events(
        self, 
        tenant_id: str = None, 
        event_type: SecurityEventType = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get security events"""
        filter_dict = {}
        
        if tenant_id:
            filter_dict["tenant_id"] = tenant_id
        
        if event_type:
            filter_dict["event_type"] = event_type.value
        
        result = self.system_db.find("security_events", filter_dict, limit=limit)
        
        if result.get("success"):
            return result.get("documents", [])
        
        return []


def create_auth_manager(system_db, jwt_secret: str = None) -> EnhancedAuthManager:
    """Create enhanced authentication manager"""
    return EnhancedAuthManager(system_db, jwt_secret)
