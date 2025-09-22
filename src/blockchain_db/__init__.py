"""
IEDB (Intelligent Enterprise Database) - Core Module
File-based database with encryption and blockchain-themed storage
Organized with Security, Database, Common, and API modules
"""

__version__ = "2.0.0"
__author__ = "IEDB Team"
__description__ = "Intelligent Enterprise Database - Encrypted file-based storage with blockchain themes"

# Import main components from reorganized structure
try:
    from .multitenant import MultitenantManager, TenantConfig, TenantDatabase
    from .optimized_database import OptimizedBlockchainDB as OptimizedDatabase
    from .notification_system import NotificationSystem
except ImportError as e:
    MultitenantManager = None
    TenantConfig = None 
    TenantDatabase = None
    OptimizedDatabase = None
    NotificationSystem = None

__all__ = [
    "MultitenantManager",
    "TenantConfig",
    "TenantDatabase", 
    "OptimizedDatabase",
    "NotificationSystem"
]
