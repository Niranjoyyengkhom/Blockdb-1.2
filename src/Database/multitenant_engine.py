"""
Multi-Tenant Architecture Engine
===============================

Comprehensive multi-tenant system with isolated databases, users, and ABAC policies per tenant.
Each tenant operates in complete isolation with their own data encryption and access controls.
"""

import uuid
import json
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

from .mongodb_engine import MongoStyleDBEngine

# Import with fallback for Security module
try:
    from ..Security.dynamic_abac import create_enhanced_abac_engine  # type: ignore
except (ImportError, ValueError):
    # Fallback when Security module is not available
    def create_enhanced_abac_engine(*args, **kwargs):  # type: ignore
        """Fallback ABAC engine when Security module unavailable"""
        return None

from .archive_engine import create_archive_engine
from .sql_engine import SQLEngine
from .compliance_engine import create_audit_trail


@dataclass
class TenantConfig:
    """Configuration for a tenant"""
    tenant_id: str
    name: str
    description: str
    admin_email: str
    created_at: datetime
    encryption_key: str
    data_path: str
    max_databases: int = 10
    max_users: int = 100
    storage_limit_gb: int = 100
    is_active: bool = True
    settings: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


@dataclass
class TenantDatabase:
    """Database instance within a tenant"""
    db_id: str
    tenant_id: str
    name: str
    description: str
    created_at: datetime
    created_by: str
    data_path: str
    encryption_key: str
    is_active: bool = True
    settings: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


@dataclass
class TenantUser:
    """User within a tenant"""
    user_id: str
    tenant_id: str
    username: str
    email: str
    mnemonic_hash: str
    roles: List[str]
    permissions: List[str]
    databases: List[str]  # Database IDs user has access to
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    settings: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.last_login, str):
            self.last_login = datetime.fromisoformat(self.last_login)
        if isinstance(self.locked_until, str):
            self.locked_until = datetime.fromisoformat(self.locked_until)


class EncryptionManager:
    """Handles encryption/decryption for tenant data"""
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key"""
        return base64.urlsafe_b64encode(Fernet.generate_key()).decode()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
        """Derive encryption key from password"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return base64.urlsafe_b64encode(key).decode(), salt
    
    @staticmethod
    def encrypt_data(data: str, key: str) -> str:
        """Encrypt data with given key"""
        try:
            key_bytes = base64.urlsafe_b64decode(key.encode())
            f = Fernet(key_bytes)
            encrypted = f.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")
    
    @staticmethod
    def decrypt_data(encrypted_data: str, key: str) -> str:
        """Decrypt data with given key"""
        try:
            key_bytes = base64.urlsafe_b64decode(key.encode())
            f = Fernet(key_bytes)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = f.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")


class MnemonicManager:
    """Handles mnemonic-based authentication"""
    
    # BIP39 word list (simplified version for demo)
    WORD_LIST = [
        "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract",
        "absurd", "abuse", "access", "accident", "account", "accuse", "achieve", "acid",
        "acoustic", "acquire", "across", "act", "action", "actor", "actress", "actual",
        "adapt", "add", "addict", "address", "adjust", "admit", "adult", "advance",
        "advice", "aerobic", "affair", "afford", "afraid", "again", "age", "agent",
        "agree", "ahead", "aim", "air", "airport", "aisle", "alarm", "album",
        "alcohol", "alert", "alien", "all", "alley", "allow", "almost", "alone",
        "alpha", "already", "also", "alter", "always", "amateur", "amazing", "among",
        "amount", "amused", "analyst", "anchor", "ancient", "anger", "angle", "angry",
        "animal", "ankle", "announce", "annual", "another", "answer", "antenna", "antique",
        "anxiety", "any", "apart", "apology", "appear", "apple", "approve", "april",
        "arch", "arctic", "area", "arena", "argue", "arm", "armed", "armor",
        "army", "around", "arrange", "arrest", "arrive", "arrow", "art", "artefact",
        "artist", "artwork", "ask", "aspect", "assault", "asset", "assist", "assume",
        "asthma", "athlete", "atom", "attack", "attend", "attitude", "attract", "auction",
        "audit", "august", "aunt", "author", "auto", "autumn", "average", "avocado",
        "avoid", "awake", "aware", "away", "awesome", "awful", "awkward", "axis"
    ]
    
    @classmethod
    def generate_mnemonic(cls, strength: int = 128) -> str:
        """Generate a new mnemonic phrase"""
        # Simplified implementation
        entropy_bytes = secrets.randbits(strength) // 8
        words_count = strength // 32 * 3
        
        selected_words = []
        for _ in range(words_count):
            word_index = secrets.randbelow(len(cls.WORD_LIST))
            selected_words.append(cls.WORD_LIST[word_index])
        
        return " ".join(selected_words)
    
    @classmethod
    def validate_mnemonic(cls, mnemonic: str) -> bool:
        """Validate mnemonic phrase"""
        words = mnemonic.strip().split()
        if len(words) not in [12, 15, 18, 21, 24]:
            return False
        
        for word in words:
            if word.lower() not in cls.WORD_LIST:
                return False
        
        return True
    
    @classmethod
    def mnemonic_to_hash(cls, mnemonic: str) -> str:
        """Convert mnemonic to secure hash"""
        if not cls.validate_mnemonic(mnemonic):
            raise ValueError("Invalid mnemonic phrase")
        
        # Use PBKDF2 for secure hashing
        salt = b"blockchain_db_mnemonic_salt"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        hash_bytes = kdf.derive(mnemonic.encode())
        return base64.urlsafe_b64encode(hash_bytes).decode()


class SecurityMonitor:
    """Monitors and blocks unauthorized access attempts"""
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.blocked_ips_file = self.storage_path / "blocked_ips.json"
        self.access_log_file = self.storage_path / "access_log.json"
        
        self.blocked_ips = self._load_blocked_ips()
        self.max_failed_attempts = 5
        self.block_duration_minutes = 60
    
    def _load_blocked_ips(self) -> Dict[str, datetime]:
        """Load blocked IPs from storage"""
        if not self.blocked_ips_file.exists():
            return {}
        
        try:
            with open(self.blocked_ips_file, 'r') as f:
                data = json.load(f)
                # Convert ISO strings back to datetime
                return {
                    ip: datetime.fromisoformat(blocked_until)
                    for ip, blocked_until in data.items()
                }
        except Exception:
            return {}
    
    def _save_blocked_ips(self):
        """Save blocked IPs to storage"""
        # Convert datetime to ISO strings for JSON
        data = {
            ip: blocked_until.isoformat()
            for ip, blocked_until in self.blocked_ips.items()
        }
        
        with open(self.blocked_ips_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def log_access_attempt(self, ip: str, user_id: str, success: bool, details: Dict[str, Any]):
        """Log an access attempt"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ip": ip,
            "user_id": user_id,
            "success": success,
            "details": details
        }
        
        # Append to log file
        logs = []
        if self.access_log_file.exists():
            try:
                with open(self.access_log_file, 'r') as f:
                    logs = json.load(f)
            except Exception:
                logs = []
        
        logs.append(log_entry)
        
        # Keep only last 10000 entries
        if len(logs) > 10000:
            logs = logs[-10000:]
        
        with open(self.access_log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked"""
        if ip not in self.blocked_ips:
            return False
        
        blocked_until = self.blocked_ips[ip]
        if datetime.now(timezone.utc) > blocked_until:
            # Block period expired, remove from blocked list
            del self.blocked_ips[ip]
            self._save_blocked_ips()
            return False
        
        return True
    
    def record_failed_attempt(self, ip: str, user_id: str, reason: str):
        """Record a failed access attempt and potentially block IP"""
        self.log_access_attempt(ip, user_id, False, {"reason": reason})
        
        # Count recent failed attempts from this IP
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=30)  # Look at last 30 minutes
        
        failed_count = 0
        if self.access_log_file.exists():
            try:
                with open(self.access_log_file, 'r') as f:
                    logs = json.load(f)
                
                for log in logs:
                    log_time = datetime.fromisoformat(log["timestamp"])
                    if (log["ip"] == ip and 
                        not log["success"] and 
                        log_time > cutoff):
                        failed_count += 1
            except Exception:
                pass
        
        if failed_count >= self.max_failed_attempts:
            # Block this IP
            blocked_until = now + timedelta(minutes=self.block_duration_minutes)
            self.blocked_ips[ip] = blocked_until
            self._save_blocked_ips()
            
            return True  # IP was blocked
        
        return False  # IP not blocked yet
    
    def record_successful_attempt(self, ip: str, user_id: str):
        """Record a successful access attempt"""
        self.log_access_attempt(ip, user_id, True, {})


class MultiTenantEngine:
    """Core multi-tenant database engine"""
    
    def __init__(self, base_path: str = "./tenants"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Storage paths
        self.tenants_path = self.base_path / "tenants"
        self.security_path = self.base_path / "security"
        
        self.tenants_path.mkdir(exist_ok=True)
        self.security_path.mkdir(exist_ok=True)
        
        # Initialize security monitor
        self.security_monitor = SecurityMonitor(str(self.security_path))
        
        # Initialize encryption
        self.encryption_manager = EncryptionManager()
        
        # Initialize mnemonic manager
        self.mnemonic_manager = MnemonicManager()
        
        # Cache for active tenant engines
        self.tenant_engines: Dict[str, Dict[str, Any]] = {}
        
        # Load existing tenants
        self._load_tenants()
    
    def _load_tenants(self):
        """Load all existing tenants"""
        for tenant_dir in self.tenants_path.iterdir():
            if tenant_dir.is_dir():
                try:
                    self._load_tenant_engines(tenant_dir.name)
                except Exception as e:
                    print(f"Warning: Failed to load tenant {tenant_dir.name}: {e}")
    
    def _load_tenant_engines(self, tenant_id: str):
        """Load engines for a specific tenant"""
        tenant_path = self.tenants_path / tenant_id
        
        # Load tenant config
        config_file = tenant_path / "config.json"
        if not config_file.exists():
            return
        
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        tenant_config = TenantConfig(**config_data)
        
        if not tenant_config.is_active:
            return
        
        # Initialize engines for this tenant
        self.tenant_engines[tenant_id] = {
            "config": tenant_config,
            "databases": {},
            "users": {},
            "abac_engines": {},
        }
        
        # Load databases
        databases_dir = tenant_path / "databases"
        if databases_dir.exists():
            for db_dir in databases_dir.iterdir():
                if db_dir.is_dir():
                    try:
                        self._load_database_engines(tenant_id, db_dir.name)
                    except Exception as e:
                        print(f"Warning: Failed to load database {db_dir.name} for tenant {tenant_id}: {e}")
        
        # Load users
        users_file = tenant_path / "users.json"
        if users_file.exists():
            with open(users_file, 'r') as f:
                users_data = json.load(f)
            
            for user_data in users_data:
                user = TenantUser(**user_data)
                self.tenant_engines[tenant_id]["users"][user.user_id] = user
    
    def _load_database_engines(self, tenant_id: str, db_id: str):
        """Load engines for a specific database"""
        db_path = self.tenants_path / tenant_id / "databases" / db_id
        
        # Load database config
        config_file = db_path / "config.json"
        if not config_file.exists():
            return
        
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        db_config = TenantDatabase(**config_data)
        
        if not db_config.is_active:
            return
        
        # Initialize database engines
        db_engine = MongoStyleDBEngine(str(db_path / "data"))
        abac_engine = create_enhanced_abac_engine(db_engine)
        sql_engine = SQLEngine(db_engine)
        archive_engine = create_archive_engine(db_engine)
        audit_trail = create_audit_trail(db_engine)
        
        self.tenant_engines[tenant_id]["databases"][db_id] = {
            "config": db_config,
            "db_engine": db_engine,
            "abac_engine": abac_engine,
            "sql_engine": sql_engine,
            "archive_engine": archive_engine,
            "audit_trail": audit_trail,
        }
    
    def create_tenant(self, name: str, description: str, admin_email: str, admin_mnemonic: str) -> str:
        """Create a new tenant"""
        tenant_id = str(uuid.uuid4())
        
        # Validate mnemonic
        if not self.mnemonic_manager.validate_mnemonic(admin_mnemonic):
            raise ValueError("Invalid mnemonic phrase")
        
        # Create tenant directory structure
        tenant_path = self.tenants_path / tenant_id
        tenant_path.mkdir(parents=True, exist_ok=True)
        
        (tenant_path / "databases").mkdir(exist_ok=True)
        
        # Generate encryption key
        encryption_key = self.encryption_manager.generate_key()
        
        # Create tenant config
        tenant_config = TenantConfig(
            tenant_id=tenant_id,
            name=name,
            description=description,
            admin_email=admin_email,
            created_at=datetime.now(timezone.utc),
            encryption_key=encryption_key,
            data_path=str(tenant_path)
        )
        
        # Save tenant config
        with open(tenant_path / "config.json", 'w') as f:
            config_dict = asdict(tenant_config)
            config_dict["created_at"] = config_dict["created_at"].isoformat()
            json.dump(config_dict, f, indent=2)
        
        # Create admin user
        admin_user_id = str(uuid.uuid4())
        admin_user = TenantUser(
            user_id=admin_user_id,
            tenant_id=tenant_id,
            username="admin",
            email=admin_email,
            mnemonic_hash=self.mnemonic_manager.mnemonic_to_hash(admin_mnemonic),
            roles=["admin", "user"],
            permissions=["*"],  # All permissions
            databases=[],  # Will be populated as databases are created
            created_at=datetime.now(timezone.utc)
        )
        
        # Save users
        users_data = [asdict(admin_user)]
        users_data[0]["created_at"] = users_data[0]["created_at"].isoformat()
        
        with open(tenant_path / "users.json", 'w') as f:
            json.dump(users_data, f, indent=2)
        
        # Initialize tenant engines
        self.tenant_engines[tenant_id] = {
            "config": tenant_config,
            "databases": {},
            "users": {admin_user_id: admin_user},
            "abac_engines": {},
        }
        
        return tenant_id
    
    def create_database(self, tenant_id: str, name: str, description: str, created_by: str) -> str:
        """Create a new database within a tenant"""
        if tenant_id not in self.tenant_engines:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        tenant_config = self.tenant_engines[tenant_id]["config"]
        
        # Check limits
        current_db_count = len(self.tenant_engines[tenant_id]["databases"])
        if current_db_count >= tenant_config.max_databases:
            raise ValueError(f"Maximum databases limit ({tenant_config.max_databases}) reached")
        
        db_id = str(uuid.uuid4())
        
        # Create database directory
        db_path = self.tenants_path / tenant_id / "databases" / db_id
        db_path.mkdir(parents=True, exist_ok=True)
        
        (db_path / "data").mkdir(exist_ok=True)
        
        # Generate database-specific encryption key
        encryption_key = self.encryption_manager.generate_key()
        
        # Create database config
        db_config = TenantDatabase(
            db_id=db_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            data_path=str(db_path / "data"),
            encryption_key=encryption_key
        )
        
        # Save database config
        with open(db_path / "config.json", 'w') as f:
            config_dict = asdict(db_config)
            config_dict["created_at"] = config_dict["created_at"].isoformat()
            json.dump(config_dict, f, indent=2)
        
        # Initialize database engines
        self._load_database_engines(tenant_id, db_id)
        
        return db_id
    
    def create_user(self, tenant_id: str, username: str, email: str, mnemonic: str, 
                   roles: List[str], permissions: List[str], databases: List[str]) -> str:
        """Create a new user within a tenant"""
        if tenant_id not in self.tenant_engines:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        tenant_config = self.tenant_engines[tenant_id]["config"]
        
        # Check limits
        current_user_count = len(self.tenant_engines[tenant_id]["users"])
        if current_user_count >= tenant_config.max_users:
            raise ValueError(f"Maximum users limit ({tenant_config.max_users}) reached")
        
        # Validate mnemonic
        if not self.mnemonic_manager.validate_mnemonic(mnemonic):
            raise ValueError("Invalid mnemonic phrase")
        
        # Check if username/email already exists
        for user in self.tenant_engines[tenant_id]["users"].values():
            if user.username == username or user.email == email:
                raise ValueError("Username or email already exists")
        
        user_id = str(uuid.uuid4())
        
        # Create user
        user = TenantUser(
            user_id=user_id,
            tenant_id=tenant_id,
            username=username,
            email=email,
            mnemonic_hash=self.mnemonic_manager.mnemonic_to_hash(mnemonic),
            roles=roles,
            permissions=permissions,
            databases=databases,
            created_at=datetime.now(timezone.utc)
        )
        
        # Add to memory
        self.tenant_engines[tenant_id]["users"][user_id] = user
        
        # Save to file
        self._save_tenant_users(tenant_id)
        
        return user_id
    
    def _save_tenant_users(self, tenant_id: str):
        """Save tenant users to file"""
        users = list(self.tenant_engines[tenant_id]["users"].values())
        users_data = []
        
        for user in users:
            user_dict = asdict(user)
            user_dict["created_at"] = user_dict["created_at"].isoformat()
            if user_dict["last_login"]:
                user_dict["last_login"] = user_dict["last_login"].isoformat()
            if user_dict["locked_until"]:
                user_dict["locked_until"] = user_dict["locked_until"].isoformat()
            users_data.append(user_dict)
        
        users_file = self.tenants_path / tenant_id / "users.json"
        with open(users_file, 'w') as f:
            json.dump(users_data, f, indent=2)
    
    def authenticate_user(self, tenant_id: str, username: str, mnemonic: str, ip: str) -> Optional[TenantUser]:
        """Authenticate a user with mnemonic"""
        # Check if IP is blocked
        if self.security_monitor.is_ip_blocked(ip):
            raise Exception("IP address is temporarily blocked due to suspicious activity")
        
        if tenant_id not in self.tenant_engines:
            self.security_monitor.record_failed_attempt(ip, username, "Invalid tenant")
            return None
        
        # Find user
        user = None
        for u in self.tenant_engines[tenant_id]["users"].values():
            if u.username == username:
                user = u
                break
        
        if not user:
            self.security_monitor.record_failed_attempt(ip, username, "User not found")
            return None
        
        # Check if user is locked
        if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
            self.security_monitor.record_failed_attempt(ip, username, "User account locked")
            return None
        
        # Check if user is active
        if not user.is_active:
            self.security_monitor.record_failed_attempt(ip, username, "User account disabled")
            return None
        
        # Validate mnemonic
        try:
            provided_hash = self.mnemonic_manager.mnemonic_to_hash(mnemonic)
            if provided_hash != user.mnemonic_hash:
                # Record failed attempt
                user.failed_attempts += 1
                
                # Lock user if too many failures
                if user.failed_attempts >= 5:
                    user.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
                
                self._save_tenant_users(tenant_id)
                self.security_monitor.record_failed_attempt(ip, username, "Invalid mnemonic")
                return None
            
        except Exception:
            self.security_monitor.record_failed_attempt(ip, username, "Mnemonic validation error")
            return None
        
        # Successful authentication
        user.failed_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)
        
        self._save_tenant_users(tenant_id)
        self.security_monitor.record_successful_attempt(ip, username)
        
        return user
    
    def get_tenant_databases(self, tenant_id: str) -> List[TenantDatabase]:
        """Get all databases for a tenant"""
        if tenant_id not in self.tenant_engines:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        databases = []
        for db_data in self.tenant_engines[tenant_id]["databases"].values():
            databases.append(db_data["config"])
        
        return databases
    
    def get_database_engine(self, tenant_id: str, db_id: str) -> Dict[str, Any]:
        """Get database engines for a specific database"""
        if tenant_id not in self.tenant_engines:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        if db_id not in self.tenant_engines[tenant_id]["databases"]:
            raise ValueError(f"Database {db_id} not found in tenant {tenant_id}")
        
        return self.tenant_engines[tenant_id]["databases"][db_id]
    
    def get_tenant_users(self, tenant_id: str) -> List[TenantUser]:
        """Get all users for a tenant"""
        if tenant_id not in self.tenant_engines:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        return list(self.tenant_engines[tenant_id]["users"].values())
    
    def list_tenants(self) -> List[TenantConfig]:
        """List all tenants"""
        return [engines["config"] for engines in self.tenant_engines.values()]


def create_multitenant_engine(base_path: str = "./tenants") -> MultiTenantEngine:
    """Create and configure multi-tenant engine"""
    return MultiTenantEngine(base_path)
