"""
IEDB Security Module
==================
Security components for IEDB including authentication, encryption, and ABAC policies.
"""

# Import core security components
from .auth import (
    EnhancedAuthManager, 
    AuthSession, 
    UserCredentials,
    AuthMethod,
    SessionStatus,
    SecurityEvent,
    MnemonicAuthenticator
)
from .encryption_engine import (
    EncryptionKey,
    FieldEncryption, 
    KeyManager,
    EncryptedStorageWrapper,
    TransparentEncryptionManager
)
from .abac_engine import (
    ABACEngine, 
    PolicyEffect, 
    PolicyDecision,
    PolicyStore,
    AccessRequest,
    Policy,
    Rule,
    Condition,
    Attribute,
    AttributeType,
    ComparisonOperator,
    LogicalOperator,
    PolicyBuilder,
    RuleBuilder
)
from .dynamic_abac import create_enhanced_abac_engine

__all__ = [
    # Authentication
    "EnhancedAuthManager",
    "AuthSession",
    "UserCredentials", 
    "AuthMethod",
    "SessionStatus",
    "SecurityEvent",
    "MnemonicAuthenticator",
    
    # Encryption
    "EncryptionKey",
    "FieldEncryption",
    "KeyManager", 
    "EncryptedStorageWrapper",
    "TransparentEncryptionManager",
    
    # ABAC (Attribute-Based Access Control)
    "ABACEngine",
    "PolicyEffect",
    "PolicyDecision",
    "PolicyStore",
    "AccessRequest", 
    "Policy",
    "Rule",
    "Condition",
    "Attribute",
    "AttributeType",
    "ComparisonOperator",
    "LogicalOperator",
    "PolicyBuilder",
    "RuleBuilder",
    "create_enhanced_abac_engine"
]
