"""
JWT Authentication Engine for IEDB API - Dynamic ABAC
====================================================

Comprehensive JWT-based authentication system with dynamic Attribute-Based Access Control (ABAC),
role-based access control, password hashing, token management, and security features.
"""

import jwt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Union, Set
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


class ResourceType(Enum):
    """Resource types for ABAC"""
    TENANT = "tenant"
    DATABASE = "database"
    TABLE = "table"
    SCHEMA = "schema"
    API_ENDPOINT = "api_endpoint"
    SYSTEM = "system"


class ActionType(Enum):
    """Action types for ABAC"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"
    MANAGE = "manage"


@dataclass
class Attribute:
    """Attribute for ABAC evaluation"""
    name: str
    value: Any
    attribute_type: str = "string"  # string, number, boolean, list, datetime
    
    def __post_init__(self):
        """Validate and convert attribute value"""
        if self.attribute_type == "datetime" and isinstance(self.value, str):
            try:
                self.value = datetime.fromisoformat(self.value)
            except ValueError:
                pass


@dataclass
class PolicyRule:
    """ABAC policy rule"""
    rule_id: str
    name: str
    description: str
    resource_type: ResourceType
    action: ActionType
    subject_attributes: List[Dict[str, Any]] = field(default_factory=list)
    resource_attributes: List[Dict[str, Any]] = field(default_factory=list)
    environment_attributes: List[Dict[str, Any]] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)  # Python expressions
    effect: str = "ALLOW"  # ALLOW or DENY
    priority: int = 0  # Higher priority rules take precedence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "resource_type": self.resource_type.value,
            "action": self.action.value,
            "subject_attributes": self.subject_attributes,
            "resource_attributes": self.resource_attributes,
            "environment_attributes": self.environment_attributes,
            "conditions": self.conditions,
            "effect": self.effect,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyRule":
        """Create from dictionary"""
        return cls(
            rule_id=data["rule_id"],
            name=data["name"],
            description=data["description"],
            resource_type=ResourceType(data["resource_type"]),
            action=ActionType(data["action"]),
            subject_attributes=data.get("subject_attributes", []),
            resource_attributes=data.get("resource_attributes", []),
            environment_attributes=data.get("environment_attributes", []),
            conditions=data.get("conditions", []),
            effect=data.get("effect", "ALLOW"),
            priority=data.get("priority", 0)
        )


@dataclass
class AccessContext:
    """Context for ABAC evaluation"""
    subject_attributes: Dict[str, Attribute]
    resource_attributes: Dict[str, Attribute]
    environment_attributes: Dict[str, Attribute]
    action: ActionType
    resource_type: ResourceType
    
    def get_attribute_value(self, attribute_name: str, context_type: str = "subject") -> Any:
        """Get attribute value from context"""
        if context_type == "subject":
            attr = self.subject_attributes.get(attribute_name)
        elif context_type == "resource":
            attr = self.resource_attributes.get(attribute_name)
        elif context_type == "environment":
            attr = self.environment_attributes.get(attribute_name)
        else:
            return None
        
        return attr.value if attr else None


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
    attributes: Dict[str, Attribute] = field(default_factory=dict)  # For ABAC
    
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
            "metadata": self.metadata,
            "attributes": {k: {"name": v.name, "value": v.value, "type": v.attribute_type} 
                         for k, v in self.attributes.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserCredentials":
        """Create from dictionary"""
        user = cls(
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
        
        # Load attributes
        if "attributes" in data:
            for k, v in data["attributes"].items():
                user.attributes[k] = Attribute(v["name"], v["value"], v["type"])
        
        return user


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


class DynamicABACEngine:
    """
    Dynamic Attribute-Based Access Control Engine
    """
    
    def __init__(self, storage_path: str = "auth_data"):
        """Initialize ABAC engine"""
        self.storage_path = storage_path
        self.policies_file = os.path.join(storage_path, "abac_policies.json")
        self.policies: Dict[str, PolicyRule] = {}
        
        # Initialize storage
        os.makedirs(storage_path, exist_ok=True)
        self._load_policies()
        
        # Built-in policies for common scenarios
        self._create_default_policies()
    
    def _load_policies(self):
        """Load policies from storage"""
        try:
            if os.path.exists(self.policies_file):
                with open(self.policies_file, 'r') as f:
                    policies_data = json.load(f)
                    self.policies = {
                        policy_id: PolicyRule.from_dict(data)
                        for policy_id, data in policies_data.items()
                    }
            logger.info(f"Loaded {len(self.policies)} ABAC policies")
        except Exception as e:
            logger.error(f"Error loading ABAC policies: {e}")
    
    def _save_policies(self):
        """Save policies to storage"""
        try:
            policies_data = {
                policy_id: policy.to_dict()
                for policy_id, policy in self.policies.items()
            }
            with open(self.policies_file, 'w') as f:
                json.dump(policies_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving ABAC policies: {e}")
    
    def _create_default_policies(self):
        """Create default ABAC policies"""
        default_policies = [
            # Super Admin - Full Access
            PolicyRule(
                rule_id="super_admin_full_access",
                name="Super Admin Full Access",
                description="Super admins have full access to all resources",
                resource_type=ResourceType.SYSTEM,
                action=ActionType.ADMIN,
                subject_attributes=[{"name": "role", "operator": "equals", "value": "super_admin"}],
                effect="ALLOW",
                priority=1000
            ),
            
            # Tenant Admin - Tenant Access
            PolicyRule(
                rule_id="tenant_admin_access",
                name="Tenant Admin Access",
                description="Tenant admins can manage their tenant resources",
                resource_type=ResourceType.TENANT,
                action=ActionType.MANAGE,
                subject_attributes=[{"name": "role", "operator": "equals", "value": "tenant_admin"}],
                resource_attributes=[{"name": "tenant_id", "operator": "equals", "value": "{subject.tenant_id}"}],
                effect="ALLOW",
                priority=900
            ),
            
            # Database Admin - Database Access
            PolicyRule(
                rule_id="db_admin_database_access",
                name="Database Admin Access",
                description="Database admins can manage databases in their tenant",
                resource_type=ResourceType.DATABASE,
                action=ActionType.MANAGE,
                subject_attributes=[{"name": "role", "operator": "equals", "value": "database_admin"}],
                resource_attributes=[{"name": "tenant_id", "operator": "equals", "value": "{subject.tenant_id}"}],
                effect="ALLOW",
                priority=800
            ),
            
            # User - Read/Write Access
            PolicyRule(
                rule_id="user_read_write_access",
                name="User Read Write Access",
                description="Users can read and write to tables in their tenant",
                resource_type=ResourceType.TABLE,
                action=ActionType.UPDATE,
                subject_attributes=[{"name": "role", "operator": "equals", "value": "user"}],
                resource_attributes=[{"name": "tenant_id", "operator": "equals", "value": "{subject.tenant_id}"}],
                effect="ALLOW",
                priority=700
            ),
            
            # Read Only - Read Access
            PolicyRule(
                rule_id="readonly_read_access",
                name="Read Only Access",
                description="Read-only users can only read from tables in their tenant",
                resource_type=ResourceType.TABLE,
                action=ActionType.READ,
                subject_attributes=[{"name": "role", "operator": "equals", "value": "read_only"}],
                resource_attributes=[{"name": "tenant_id", "operator": "equals", "value": "{subject.tenant_id}"}],
                effect="ALLOW",
                priority=600
            ),
            
            # Time-based Access Control
            PolicyRule(
                rule_id="business_hours_access",
                name="Business Hours Access",
                description="Sensitive operations only during business hours",
                resource_type=ResourceType.DATABASE,
                action=ActionType.DELETE,
                environment_attributes=[
                    {"name": "hour", "operator": ">=", "value": 9},
                    {"name": "hour", "operator": "<=", "value": 17},
                    {"name": "weekday", "operator": "<=", "value": 4}
                ],
                effect="ALLOW",
                priority=500
            )
        ]
        
        # Add default policies if they don't exist
        for policy in default_policies:
            if policy.rule_id not in self.policies:
                self.policies[policy.rule_id] = policy
        
        self._save_policies()
    
    def add_policy(self, policy: PolicyRule) -> bool:
        """Add or update ABAC policy"""
        try:
            self.policies[policy.rule_id] = policy
            self._save_policies()
            logger.info(f"Added ABAC policy: {policy.name}")
            return True
        except Exception as e:
            logger.error(f"Error adding ABAC policy: {e}")
            return False
    
    def remove_policy(self, rule_id: str) -> bool:
        """Remove ABAC policy"""
        try:
            if rule_id in self.policies:
                del self.policies[rule_id]
                self._save_policies()
                logger.info(f"Removed ABAC policy: {rule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing ABAC policy: {e}")
            return False
    
    def evaluate_access(self, context: AccessContext) -> Dict[str, Any]:
        """Evaluate access based on ABAC policies"""
        try:
            applicable_policies = []
            
            # Find applicable policies
            for policy in self.policies.values():
                if (policy.resource_type == context.resource_type and 
                    policy.action == context.action):
                    
                    if self._policy_applies(policy, context):
                        applicable_policies.append(policy)
            
            # Sort by priority (higher priority first)
            applicable_policies.sort(key=lambda p: p.priority, reverse=True)
            
            # Evaluate policies
            decision = "DENY"  # Default deny
            applied_policies = []
            
            for policy in applicable_policies:
                if self._evaluate_policy(policy, context):
                    applied_policies.append(policy.rule_id)
                    if policy.effect == "ALLOW":
                        decision = "ALLOW"
                        break
                    elif policy.effect == "DENY":
                        decision = "DENY"
                        break
            
            return {
                "decision": decision,
                "applied_policies": applied_policies,
                "context": {
                    "action": context.action.value,
                    "resource_type": context.resource_type.value,
                    "subject_id": context.get_attribute_value("user_id", "subject")
                }
            }
            
        except Exception as e:
            logger.error(f"Error evaluating ABAC access: {e}")
            return {"decision": "DENY", "error": str(e)}
    
    def _policy_applies(self, policy: PolicyRule, context: AccessContext) -> bool:
        """Check if policy applies to context"""
        try:
            # Check resource type and action
            if (policy.resource_type != context.resource_type or 
                policy.action != context.action):
                return False
            
            # Basic applicability check
            return True
            
        except Exception as e:
            logger.error(f"Error checking policy applicability: {e}")
            return False
    
    def _evaluate_policy(self, policy: PolicyRule, context: AccessContext) -> bool:
        """Evaluate if policy conditions are met"""
        try:
            # Evaluate subject attributes
            if not self._evaluate_attributes(policy.subject_attributes, context, "subject"):
                return False
            
            # Evaluate resource attributes
            if not self._evaluate_attributes(policy.resource_attributes, context, "resource"):
                return False
            
            # Evaluate environment attributes
            if not self._evaluate_attributes(policy.environment_attributes, context, "environment"):
                return False
            
            # Evaluate custom conditions
            if not self._evaluate_conditions(policy.conditions, context):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating policy: {e}")
            return False
    
    def _evaluate_attributes(self, attribute_conditions: List[Dict[str, Any]], 
                           context: AccessContext, context_type: str) -> bool:
        """Evaluate attribute conditions"""
        try:
            for condition in attribute_conditions:
                attr_name = condition["name"]
                operator = condition["operator"]
                expected_value = condition["value"]
                
                # Resolve dynamic values
                if isinstance(expected_value, str) and expected_value.startswith("{"):
                    expected_value = self._resolve_dynamic_value(expected_value, context)
                
                actual_value = context.get_attribute_value(attr_name, context_type)
                
                if not self._evaluate_condition(actual_value, operator, expected_value):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating attributes: {e}")
            return False
    
    def _evaluate_condition(self, actual: Any, operator: str, expected: Any) -> bool:
        """Evaluate single condition"""
        try:
            if operator == "equals":
                return actual == expected
            elif operator == "not_equals":
                return actual != expected
            elif operator == "in":
                return actual in expected if isinstance(expected, (list, set)) else False
            elif operator == "not_in":
                return actual not in expected if isinstance(expected, (list, set)) else True
            elif operator == ">=":
                return actual >= expected
            elif operator == "<=":
                return actual <= expected
            elif operator == ">":
                return actual > expected
            elif operator == "<":
                return actual < expected
            elif operator == "contains":
                return expected in actual if isinstance(actual, (str, list)) else False
            elif operator == "starts_with":
                return actual.startswith(expected) if isinstance(actual, str) else False
            elif operator == "ends_with":
                return actual.endswith(expected) if isinstance(actual, str) else False
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    def _resolve_dynamic_value(self, value: str, context: AccessContext) -> Any:
        """Resolve dynamic values like {subject.tenant_id}"""
        try:
            if value.startswith("{subject."):
                attr_name = value[9:-1]  # Remove {subject. and }
                return context.get_attribute_value(attr_name, "subject")
            elif value.startswith("{resource."):
                attr_name = value[10:-1]  # Remove {resource. and }
                return context.get_attribute_value(attr_name, "resource")
            elif value.startswith("{environment."):
                attr_name = value[13:-1]  # Remove {environment. and }
                return context.get_attribute_value(attr_name, "environment")
            else:
                return value
                
        except Exception as e:
            logger.error(f"Error resolving dynamic value: {e}")
            return value
    
    def _evaluate_conditions(self, conditions: List[str], context: AccessContext) -> bool:
        """Evaluate custom Python conditions"""
        try:
            for condition in conditions:
                # Simple evaluation - in production, use a safer expression evaluator
                # This is a basic implementation for demo purposes
                if not eval(condition, {"context": context}):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error evaluating conditions: {e}")
            return False
    
    def get_policies(self) -> List[PolicyRule]:
        """Get all policies"""
        return list(self.policies.values())
    
    def get_policy(self, rule_id: str) -> Optional[PolicyRule]:
        """Get specific policy"""
        return self.policies.get(rule_id)


class JWTAuthEngine:
    """
    JWT Authentication Engine with Dynamic ABAC
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
        
        # ABAC Engine
        self.abac_engine = DynamicABACEngine(storage_path)
        
        # Initialize storage
        self._init_storage()
        self._load_data()
        
        # HTTP Bearer for FastAPI
        self.security = HTTPBearer()
        
        logger.info("JWT Authentication Engine with Dynamic ABAC initialized")
    
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
                   metadata: Optional[Dict[str, Any]] = None,
                   attributes: Optional[Dict[str, Attribute]] = None) -> str:
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
            metadata=metadata or {},
            attributes=attributes or {}
        )
        
        # Add default attributes for ABAC
        user.attributes.update({
            "user_id": Attribute("user_id", user_id, "string"),
            "username": Attribute("username", username, "string"),
            "email": Attribute("email", email, "string"),
            "tenant_id": Attribute("tenant_id", tenant_id, "string") if tenant_id else None,
            "roles": Attribute("roles", [role.value for role in roles], "list"),
            "created_at": Attribute("created_at", user.created_at, "datetime")
        })
        
        # Remove None attributes
        user.attributes = {k: v for k, v in user.attributes.items() if v is not None}
        
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
    
    # ABAC Integration
    def check_access(self, token: str, resource_type: ResourceType, action: ActionType, 
                    resource_attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check access using Dynamic ABAC"""
        try:
            # Verify token
            token_payload = self.verify_token(token)
            user = self.get_user(token_payload.user_id)
            
            if not user:
                return {"decision": "DENY", "error": "User not found"}
            
            # Create access context
            subject_attrs = user.attributes.copy()
            
            # Add current role as an attribute for ABAC evaluation
            if user.roles:
                subject_attrs["role"] = Attribute("role", user.roles[0].value, "string")
            
            resource_attrs = {}
            if resource_attributes:
                for k, v in resource_attributes.items():
                    resource_attrs[k] = Attribute(k, v, "string")
            
            # Environment attributes
            now = datetime.now()
            env_attrs = {
                "current_time": Attribute("current_time", now, "datetime"),
                "hour": Attribute("hour", now.hour, "number"),
                "weekday": Attribute("weekday", now.weekday(), "number"),
                "timestamp": Attribute("timestamp", now.timestamp(), "number")
            }
            
            context = AccessContext(
                subject_attributes=subject_attrs,
                resource_attributes=resource_attrs,
                environment_attributes=env_attrs,
                action=action,
                resource_type=resource_type
            )
            
            # Evaluate access
            return self.abac_engine.evaluate_access(context)
            
        except Exception as e:
            logger.error(f"Error checking access: {e}")
            return {"decision": "DENY", "error": str(e)}
    
    def require_access(self, token: str, resource_type: ResourceType, action: ActionType,
                      resource_attributes: Optional[Dict[str, Any]] = None) -> UserCredentials:
        """Require access and return user if allowed"""
        access_result = self.check_access(token, resource_type, action, resource_attributes)
        
        if access_result["decision"] != "ALLOW":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: {access_result.get('error', 'Insufficient permissions')}"
            )
        
        token_payload = self.verify_token(token)
        user = self.get_user(token_payload.user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    
    def logout(self, token: str):
        """Logout user by revoking token"""
        self.revoked_tokens.add(token)
        if token in self.active_tokens:
            del self.active_tokens[token]
            self._save_tokens()
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        active_users = len([u for u in self.users.values() if u.is_active])
        locked_users = len([u for u in self.users.values() if u.locked_until and u.locked_until > datetime.now(timezone.utc)])
        
        return {
            "total_users": len(self.users),
            "active_users": active_users,
            "locked_users": locked_users,
            "active_tokens": len(self.active_tokens),
            "revoked_tokens": len(self.revoked_tokens),
            "abac_policies": len(self.abac_engine.policies)
        }


def create_jwt_auth_engine(secret_key: Optional[str] = None, storage_path: str = "auth_data") -> JWTAuthEngine:
    """Create JWT authentication engine with Dynamic ABAC"""
    return JWTAuthEngine(secret_key=secret_key, storage_path=storage_path)
