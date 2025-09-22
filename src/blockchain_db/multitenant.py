"""
Multitenant Management System
============================

Comprehensive multitenancy system with isolated databases, users, and ABAC policies.
Each tenant operates in complete isolation with their own data and security context.
"""

import uuid
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import json
import os

# Import engines from Database module
try:
    from ..Database.mongodb_engine import MongoStyleDBEngine
except ImportError:
    from .engine_stubs import MongoStyleDBEngine

try:
    from ..Database.sql_engine import SQLEngine
except ImportError:
    from .engine_stubs import SQLEngine

try:
    from ..Database.archive_engine import ArchiveEngine
except ImportError:
    from .engine_stubs import ArchiveEngine

# Import stub functionality for missing components
from .engine_stubs import (
    EnhancedABACEngine, AuditTrail, 
    create_enhanced_abac_engine, create_audit_trail, create_archive_engine
)


class TenantStatus(Enum):
    """Tenant status enumeration"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    PENDING = "pending"


class TenantPlan(Enum):
    """Tenant subscription plans"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class TenantConfig:
    """Tenant configuration and settings"""
    tenant_id: str
    name: str
    status: TenantStatus
    plan: TenantPlan
    created_at: datetime
    admin_email: str
    encryption_key: str
    data_path: str
    max_databases: int = 10
    max_users: int = 100
    max_storage_mb: int = 1000
    features: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "status": self.status.value,
            "plan": self.plan.value,
            "created_at": self.created_at.isoformat(),
            "admin_email": self.admin_email,
            "encryption_key": self.encryption_key,
            "data_path": self.data_path,
            "max_databases": self.max_databases,
            "max_users": self.max_users,
            "max_storage_mb": self.max_storage_mb,
            "features": list(self.features),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TenantConfig':
        """Create from dictionary"""
        return cls(
            tenant_id=data["tenant_id"],
            name=data["name"],
            status=TenantStatus(data["status"]),
            plan=TenantPlan(data["plan"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            admin_email=data["admin_email"],
            encryption_key=data["encryption_key"],
            data_path=data["data_path"],
            max_databases=data.get("max_databases", 10),
            max_users=data.get("max_users", 100),
            max_storage_mb=data.get("max_storage_mb", 1000),
            features=set(data.get("features", [])),
            metadata=data.get("metadata", {})
        )


@dataclass
class TenantDatabase:
    """Tenant database configuration"""
    db_id: str
    tenant_id: str
    name: str
    description: str
    created_at: datetime
    encryption_enabled: bool = True
    backup_enabled: bool = True
    archiving_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "db_id": self.db_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "encryption_enabled": self.encryption_enabled,
            "backup_enabled": self.backup_enabled,
            "archiving_enabled": self.archiving_enabled,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TenantDatabase':
        """Create from dictionary"""
        return cls(
            db_id=data["db_id"],
            tenant_id=data["tenant_id"],
            name=data["name"],
            description=data["description"],
            created_at=datetime.fromisoformat(data["created_at"]),
            encryption_enabled=data.get("encryption_enabled", True),
            backup_enabled=data.get("backup_enabled", True),
            archiving_enabled=data.get("archiving_enabled", True),
            metadata=data.get("metadata", {})
        )


@dataclass
class TenantEngines:
    """Tenant-specific database engines"""
    db_engine: Any = None
    abac_engine: Any = None
    sql_engine: Any = None
    archive_engine: Any = None
    audit_trail: Any = None


class MultitenantManager:
    """
    Comprehensive multitenant management system
    
    Manages multiple tenants with isolated databases, users, and security policies.
    Each tenant operates in complete isolation with their own data and configuration.
    """
    
    def __init__(self, base_path: str = "./tenants"):
        """Initialize multitenant manager"""
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # System-level storage
        self.system_db_path = self.base_path / "system"
        self.system_db_path.mkdir(exist_ok=True)
        
        # Initialize system database
        self.system_db = MongoStyleDBEngine(str(self.system_db_path))
        
        # Create system collections
        self._initialize_system_collections()
        
        # Tenant engines cache
        self.tenant_engines: Dict[str, TenantEngines] = {}
        
        # Load existing tenants
        self._load_tenants()
    
    def _initialize_system_collections(self):
        """Initialize system-level collections"""
        collections = [
            "tenants",
            "tenant_databases", 
            "tenant_users",
            "security_events",
            "system_audit"
        ]
        
        for collection in collections:
            try:
                self.system_db.create_collection(collection)
            except Exception:
                pass  # Collection might already exist
    
    def _load_tenants(self):
        """Load existing tenants on startup"""
        try:
            tenants_result = self.system_db.find("tenants", {})
            if tenants_result.get("success"):
                for tenant_doc in tenants_result.get("documents", []):
                    tenant_config = TenantConfig.from_dict(tenant_doc)
                    # Initialize tenant engines if active
                    if tenant_config.status == TenantStatus.ACTIVE:
                        self._initialize_tenant_engines(tenant_config.tenant_id)
        except Exception as e:
            print(f"Warning: Could not load existing tenants: {e}")
    
    def create_tenant(
        self, 
        name: str, 
        admin_email: str, 
        plan: TenantPlan = TenantPlan.FREE,
        features: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """Create a new tenant"""
        try:
            # Generate tenant ID and encryption key
            tenant_id = str(uuid.uuid4())
            encryption_key = secrets.token_hex(32)
            
            # Create tenant directory
            tenant_path = self.base_path / tenant_id
            tenant_path.mkdir(exist_ok=True)
            
            # Set plan-based limits
            plan_limits = {
                TenantPlan.FREE: {"max_databases": 1, "max_users": 5, "max_storage_mb": 100},
                TenantPlan.BASIC: {"max_databases": 5, "max_users": 25, "max_storage_mb": 1000},
                TenantPlan.PREMIUM: {"max_databases": 20, "max_users": 100, "max_storage_mb": 10000},
                TenantPlan.ENTERPRISE: {"max_databases": -1, "max_users": -1, "max_storage_mb": -1}
            }
            
            limits = plan_limits.get(plan, plan_limits[TenantPlan.FREE])
            
            # Create tenant configuration
            tenant_config = TenantConfig(
                tenant_id=tenant_id,
                name=name,
                status=TenantStatus.ACTIVE,
                plan=plan,
                created_at=datetime.now(timezone.utc),
                admin_email=admin_email,
                encryption_key=encryption_key,
                data_path=str(tenant_path),
                max_databases=limits["max_databases"],
                max_users=limits["max_users"],
                max_storage_mb=limits["max_storage_mb"],
                features=features or set()
            )
            
            # Store tenant configuration
            result = self.system_db.insert_one("tenants", tenant_config.to_dict())
            if not result.get("success"):
                return {"success": False, "error": "Failed to store tenant configuration"}
            
            # Initialize tenant engines
            self._initialize_tenant_engines(tenant_id)
            
            # Create default database for tenant
            default_db = self.create_tenant_database(
                tenant_id=tenant_id,
                name="default",
                description="Default database for tenant"
            )
            
            return {
                "success": True,
                "tenant_id": tenant_id,
                "encryption_key": encryption_key,
                "default_database": default_db
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _initialize_tenant_engines(self, tenant_id: str) -> bool:
        """Initialize database engines for a tenant"""
        try:
            tenant_config = self.get_tenant_config(tenant_id)
            if not tenant_config:
                return False
            
            # Create tenant-specific data path
            tenant_data_path = Path(tenant_config.data_path) / "data"
            tenant_data_path.mkdir(exist_ok=True)
            
            # Initialize engines
            db_engine = MongoStyleDBEngine(str(tenant_data_path))
            abac_engine = create_enhanced_abac_engine(db_engine)
            sql_engine = SQLEngine(db_engine)
            archive_engine = create_archive_engine(db_engine)
            audit_trail = create_audit_trail(db_engine)
            
            # Store engines
            self.tenant_engines[tenant_id] = TenantEngines(
                db_engine=db_engine,
                abac_engine=abac_engine,
                sql_engine=sql_engine,
                archive_engine=archive_engine,
                audit_trail=audit_trail
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to initialize engines for tenant {tenant_id}: {e}")
            return False
    
    def get_tenant_config(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get tenant configuration"""
        try:
            result = self.system_db.find_one("tenants", {"tenant_id": tenant_id})
            if result.get("success") and result.get("document"):
                return TenantConfig.from_dict(result["document"])
            return None
        except Exception:
            return None
    
    def get_tenant_engines(self, tenant_id: str) -> Optional[TenantEngines]:
        """Get tenant-specific engines"""
        if tenant_id not in self.tenant_engines:
            if not self._initialize_tenant_engines(tenant_id):
                return None
        return self.tenant_engines.get(tenant_id)
    
    def create_tenant_database(
        self, 
        tenant_id: str, 
        name: str, 
        description: str = ""
    ) -> Dict[str, Any]:
        """Create a new database for a tenant"""
        try:
            # Check tenant exists and is active
            tenant_config = self.get_tenant_config(tenant_id)
            if not tenant_config or tenant_config.status != TenantStatus.ACTIVE:
                return {"success": False, "error": "Tenant not found or inactive"}
            
            # Check database limits
            existing_dbs = self.list_tenant_databases(tenant_id)
            if (tenant_config.max_databases > 0 and 
                len(existing_dbs.get("databases", [])) >= tenant_config.max_databases):
                return {"success": False, "error": "Database limit exceeded for tenant"}
            
            # Create database configuration
            db_config = TenantDatabase(
                db_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name=name,
                description=description,
                created_at=datetime.now(timezone.utc)
            )
            
            # Store database configuration
            result = self.system_db.insert_one("tenant_databases", db_config.to_dict())
            if not result.get("success"):
                return {"success": False, "error": "Failed to store database configuration"}
            
            return {
                "success": True,
                "database_id": db_config.db_id,
                "database_config": db_config.to_dict()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_tenant_databases(self, tenant_id: str) -> Dict[str, Any]:
        """List databases for a tenant"""
        try:
            result = self.system_db.find("tenant_databases", {"tenant_id": tenant_id})
            if result.get("success"):
                databases = [TenantDatabase.from_dict(doc).to_dict() 
                           for doc in result.get("documents", [])]
                return {"success": True, "databases": databases}
            return {"success": False, "error": "Failed to retrieve databases"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_tenants(self) -> Dict[str, Any]:
        """List all tenants"""
        try:
            result = self.system_db.find("tenants", {})
            if result.get("success"):
                tenants = [TenantConfig.from_dict(doc).to_dict() 
                          for doc in result.get("documents", [])]
                return {"success": True, "tenants": tenants}
            return {"success": False, "error": "Failed to retrieve tenants"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def suspend_tenant(self, tenant_id: str, reason: str = "") -> Dict[str, Any]:
        """Suspend a tenant"""
        try:
            # Update tenant status
            result = self.system_db.update_one(
                "tenants",
                {"tenant_id": tenant_id},
                {"$set": {"status": TenantStatus.SUSPENDED.value, "suspended_reason": reason}}
            )
            
            # Remove from active engines
            if tenant_id in self.tenant_engines:
                del self.tenant_engines[tenant_id]
            
            return {"success": result.get("success", False)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Delete a tenant (with data archiving)"""
        try:
            tenant_config = self.get_tenant_config(tenant_id)
            if not tenant_config:
                return {"success": False, "error": "Tenant not found"}
            
            # Archive tenant data before deletion
            archive_path = self.base_path / "archived" / tenant_id
            archive_path.mkdir(parents=True, exist_ok=True)
            
            # Move tenant data to archive
            import shutil
            if Path(tenant_config.data_path).exists():
                shutil.move(tenant_config.data_path, str(archive_path / "data"))
            
            # Remove from system database
            self.system_db.delete_one("tenants", {"tenant_id": tenant_id})
            self.system_db.delete_many("tenant_databases", {"tenant_id": tenant_id})
            self.system_db.delete_many("tenant_users", {"tenant_id": tenant_id})
            
            # Remove from active engines
            if tenant_id in self.tenant_engines:
                del self.tenant_engines[tenant_id]
            
            return {"success": True, "archived_to": str(archive_path)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


def create_multitenant_manager(base_path: str = "./tenants") -> MultitenantManager:
    """Create and initialize multitenant manager"""
    return MultitenantManager(base_path)
