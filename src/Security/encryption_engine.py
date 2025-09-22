"""
Advanced Encryption System
==========================

Comprehensive encryption system for protecting all sensitive data in the multi-tenant database.
Implements field-level encryption, tenant isolation, and secure key management.
"""

import os
import json
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
from pathlib import Path


@dataclass
class EncryptionKey:
    """Encryption key with metadata"""
    key_id: str
    tenant_id: str
    key_type: str  # "master", "database", "field"
    algorithm: str
    key_data: str
    created_at: str
    is_active: bool = True
    rotation_count: int = 0


class FieldEncryption:
    """Field-level encryption for sensitive data"""
    
    # Fields that should always be encrypted
    SENSITIVE_FIELDS = {
        "password", "secret", "private_key", "ssn", "credit_card", 
        "bank_account", "personal_data", "confidential", "sensitive",
        "pii", "phi", "financial", "salary", "income", "medical"
    }
    
    def __init__(self, encryption_key: str):
        self.key = base64.urlsafe_b64decode(encryption_key.encode())
        self.fernet = Fernet(base64.urlsafe_b64encode(self.key))
    
    def should_encrypt_field(self, field_name: str, value: Any) -> bool:
        """Determine if a field should be encrypted"""
        if not isinstance(value, (str, int, float)):
            return False
        
        field_lower = field_name.lower()
        
        # Check for sensitive field names
        for sensitive in self.SENSITIVE_FIELDS:
            if sensitive in field_lower:
                return True
        
        # Check for patterns in string values
        if isinstance(value, str):
            value_lower = value.lower()
            # Email patterns
            if "@" in value and "." in value:
                return True
            
            # Phone patterns
            if any(char.isdigit() for char in value) and len(value.replace("-", "").replace(" ", "")) >= 10:
                return True
            
            # Credit card patterns
            if value.replace("-", "").replace(" ", "").isdigit() and len(value.replace("-", "").replace(" ", "")) >= 13:
                return True
        
        return False
    
    def encrypt_value(self, value: Any) -> str:
        """Encrypt a single value"""
        if value is None:
            return None
        
        # Convert to string for encryption
        value_str = json.dumps(value) if not isinstance(value, str) else value
        
        # Encrypt
        encrypted_bytes = self.fernet.encrypt(value_str.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
    
    def decrypt_value(self, encrypted_value: str) -> Any:
        """Decrypt a single value"""
        if encrypted_value is None:
            return None
        
        try:
            # Decode and decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            value_str = decrypted_bytes.decode()
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                return value_str
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")
    
    def encrypt_document(self, document: Dict[str, Any], encryption_rules: Dict[str, bool] = None) -> Dict[str, Any]:
        """Encrypt fields in a document"""
        if not isinstance(document, dict):
            return document
        
        encrypted_doc = document.copy()
        
        for field_name, value in document.items():
            # Skip system fields
            if field_name.startswith("_"):
                continue
            
            should_encrypt = False
            
            # Check explicit rules first
            if encryption_rules and field_name in encryption_rules:
                should_encrypt = encryption_rules[field_name]
            else:
                # Use automatic detection
                should_encrypt = self.should_encrypt_field(field_name, value)
            
            if should_encrypt:
                # Mark field as encrypted and encrypt value
                encrypted_doc[field_name] = {
                    "__encrypted": True,
                    "__value": self.encrypt_value(value),
                    "__type": type(value).__name__
                }
            elif isinstance(value, dict):
                # Recursively encrypt nested documents
                encrypted_doc[field_name] = self.encrypt_document(value, encryption_rules)
            elif isinstance(value, list):
                # Encrypt list items if needed
                encrypted_list = []
                for item in value:
                    if isinstance(item, dict):
                        encrypted_list.append(self.encrypt_document(item, encryption_rules))
                    else:
                        encrypted_list.append(item)
                encrypted_doc[field_name] = encrypted_list
        
        return encrypted_doc
    
    def decrypt_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt fields in a document"""
        if not isinstance(document, dict):
            return document
        
        decrypted_doc = document.copy()
        
        for field_name, value in document.items():
            if isinstance(value, dict):
                if value.get("__encrypted"):
                    # Decrypt encrypted field
                    decrypted_doc[field_name] = self.decrypt_value(value["__value"])
                else:
                    # Recursively decrypt nested documents
                    decrypted_doc[field_name] = self.decrypt_document(value)
            elif isinstance(value, list):
                # Decrypt list items if needed
                decrypted_list = []
                for item in value:
                    if isinstance(item, dict):
                        decrypted_list.append(self.decrypt_document(item))
                    else:
                        decrypted_list.append(item)
                decrypted_doc[field_name] = decrypted_list
        
        return decrypted_doc


class KeyManager:
    """Manages encryption keys for tenants and databases"""
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.keys_file = self.storage_path / "encryption_keys.json"
        
        # Master key for encrypting other keys
        self.master_key = self._get_or_create_master_key()
        
        # Load existing keys
        self.keys: Dict[str, EncryptionKey] = self._load_keys()
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create the master encryption key"""
        master_key_file = self.storage_path / "master.key"
        
        if master_key_file.exists():
            with open(master_key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new master key
            master_key = Fernet.generate_key()
            
            # Save master key
            with open(master_key_file, 'wb') as f:
                f.write(master_key)
            
            # Set restrictive permissions
            os.chmod(master_key_file, 0o600)
            
            return master_key
    
    def _load_keys(self) -> Dict[str, EncryptionKey]:
        """Load encryption keys from storage"""
        if not self.keys_file.exists():
            return {}
        
        try:
            # Decrypt keys file with master key
            with open(self.keys_file, 'rb') as f:
                encrypted_data = f.read()
            
            fernet = Fernet(self.master_key)
            decrypted_data = fernet.decrypt(encrypted_data)
            keys_data = json.loads(decrypted_data.decode())
            
            keys = {}
            for key_id, key_dict in keys_data.items():
                keys[key_id] = EncryptionKey(**key_dict)
            
            return keys
        except Exception:
            return {}
    
    def _save_keys(self):
        """Save encryption keys to storage"""
        # Convert keys to dict
        keys_data = {}
        for key_id, key in self.keys.items():
            keys_data[key_id] = {
                "key_id": key.key_id,
                "tenant_id": key.tenant_id,
                "key_type": key.key_type,
                "algorithm": key.algorithm,
                "key_data": key.key_data,
                "created_at": key.created_at,
                "is_active": key.is_active,
                "rotation_count": key.rotation_count
            }
        
        # Encrypt with master key
        fernet = Fernet(self.master_key)
        json_data = json.dumps(keys_data).encode()
        encrypted_data = fernet.encrypt(json_data)
        
        # Save encrypted keys
        with open(self.keys_file, 'wb') as f:
            f.write(encrypted_data)
    
    def generate_tenant_key(self, tenant_id: str) -> str:
        """Generate a new encryption key for a tenant"""
        key_id = str(uuid.uuid4())
        key_data = base64.urlsafe_b64encode(Fernet.generate_key()).decode()
        
        encryption_key = EncryptionKey(
            key_id=key_id,
            tenant_id=tenant_id,
            key_type="master",
            algorithm="Fernet",
            key_data=key_data,
            created_at=str(uuid.uuid4())
        )
        
        self.keys[key_id] = encryption_key
        self._save_keys()
        
        return key_id
    
    def generate_database_key(self, tenant_id: str, database_id: str) -> str:
        """Generate a new encryption key for a database"""
        key_id = str(uuid.uuid4())
        key_data = base64.urlsafe_b64encode(Fernet.generate_key()).decode()
        
        encryption_key = EncryptionKey(
            key_id=key_id,
            tenant_id=tenant_id,
            key_type="database",
            algorithm="Fernet",
            key_data=key_data,
            created_at=str(uuid.uuid4())
        )
        
        self.keys[key_id] = encryption_key
        self._save_keys()
        
        return key_id
    
    def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Get an encryption key by ID"""
        return self.keys.get(key_id)
    
    def get_tenant_keys(self, tenant_id: str) -> List[EncryptionKey]:
        """Get all keys for a tenant"""
        return [key for key in self.keys.values() if key.tenant_id == tenant_id and key.is_active]
    
    def rotate_key(self, key_id: str) -> str:
        """Rotate an encryption key"""
        old_key = self.keys.get(key_id)
        if not old_key:
            raise ValueError(f"Key {key_id} not found")
        
        # Deactivate old key
        old_key.is_active = False
        
        # Create new key
        new_key_id = str(uuid.uuid4())
        new_key_data = base64.urlsafe_b64encode(Fernet.generate_key()).decode()
        
        new_key = EncryptionKey(
            key_id=new_key_id,
            tenant_id=old_key.tenant_id,
            key_type=old_key.key_type,
            algorithm=old_key.algorithm,
            key_data=new_key_data,
            created_at=str(uuid.uuid4()),
            rotation_count=old_key.rotation_count + 1
        )
        
        self.keys[new_key_id] = new_key
        self._save_keys()
        
        return new_key_id


class EncryptedStorageWrapper:
    """Wrapper for database engines to provide transparent encryption"""
    
    def __init__(self, db_engine, encryption_key: str, encryption_rules: Dict[str, Dict[str, bool]] = None):
        self.db_engine = db_engine
        self.field_encryption = FieldEncryption(encryption_key)
        self.encryption_rules = encryption_rules or {}
    
    def _get_collection_rules(self, collection_name: str) -> Dict[str, bool]:
        """Get encryption rules for a specific collection"""
        return self.encryption_rules.get(collection_name, {})
    
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """Insert document with encryption"""
        rules = self._get_collection_rules(collection_name)
        encrypted_doc = self.field_encryption.encrypt_document(document, rules)
        return self.db_engine.insert_one(collection_name, encrypted_doc)
    
    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Insert multiple documents with encryption"""
        rules = self._get_collection_rules(collection_name)
        encrypted_docs = []
        for doc in documents:
            encrypted_docs.append(self.field_encryption.encrypt_document(doc, rules))
        return self.db_engine.insert_many(collection_name, encrypted_docs)
    
    def find_one(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> Dict[str, Any]:
        """Find document with decryption"""
        # Note: Filtering on encrypted fields requires special handling
        result = self.db_engine.find_one(collection_name, filter_dict)
        
        if result and result.get('success') and result.get('document'):
            decrypted_doc = self.field_encryption.decrypt_document(result['document'])
            result['document'] = decrypted_doc
        
        return result
    
    def find(self, collection_name: str, filter_dict: Dict[str, Any] = None, 
             limit: int = None, skip: int = None, sort: List[tuple] = None) -> Dict[str, Any]:
        """Find documents with decryption"""
        result = self.db_engine.find(collection_name, filter_dict, limit, skip, sort)
        
        if result and result.get('success') and result.get('documents'):
            decrypted_docs = []
            for doc in result['documents']:
                decrypted_docs.append(self.field_encryption.decrypt_document(doc))
            result['documents'] = decrypted_docs
        
        return result
    
    def update_many(self, collection_name: str, filter_dict: Dict[str, Any], 
                   update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Update documents with encryption"""
        rules = self._get_collection_rules(collection_name)
        
        # Encrypt update operations
        encrypted_update = {}
        for op, fields in update_dict.items():
            if isinstance(fields, dict):
                encrypted_fields = {}
                for field, value in fields.items():
                    if op == "$set":
                        # Encrypt new values
                        if rules.get(field, self.field_encryption.should_encrypt_field(field, value)):
                            encrypted_fields[field] = {
                                "__encrypted": True,
                                "__value": self.field_encryption.encrypt_value(value),
                                "__type": type(value).__name__
                            }
                        else:
                            encrypted_fields[field] = value
                    else:
                        encrypted_fields[field] = value
                encrypted_update[op] = encrypted_fields
            else:
                encrypted_update[op] = fields
        
        return self.db_engine.update_many(collection_name, filter_dict, encrypted_update)
    
    def delete_many(self, collection_name: str, filter_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Delete documents (no encryption needed)"""
        return self.db_engine.delete_many(collection_name, filter_dict)
    
    def aggregate(self, collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate with decryption of results"""
        result = self.db_engine.aggregate(collection_name, pipeline)
        
        if isinstance(result, list):
            decrypted_results = []
            for doc in result:
                if isinstance(doc, dict):
                    decrypted_results.append(self.field_encryption.decrypt_document(doc))
                else:
                    decrypted_results.append(doc)
            return decrypted_results
        
        return result
    
    # Pass through other methods
    def __getattr__(self, name):
        return getattr(self.db_engine, name)


class TransparentEncryptionManager:
    """Manages transparent encryption for the entire system"""
    
    def __init__(self, storage_path: str):
        self.key_manager = KeyManager(storage_path)
        self.encryption_rules: Dict[str, Dict[str, Dict[str, bool]]] = {}
    
    def set_collection_encryption_rules(self, tenant_id: str, database_id: str, 
                                      collection_name: str, rules: Dict[str, bool]):
        """Set encryption rules for a specific collection"""
        if tenant_id not in self.encryption_rules:
            self.encryption_rules[tenant_id] = {}
        if database_id not in self.encryption_rules[tenant_id]:
            self.encryption_rules[tenant_id][database_id] = {}
        
        self.encryption_rules[tenant_id][database_id][collection_name] = rules
    
    def get_encrypted_engine(self, db_engine, tenant_id: str, database_id: str, key_id: str):
        """Get an encrypted wrapper for a database engine"""
        key = self.key_manager.get_key(key_id)
        if not key:
            raise ValueError(f"Encryption key {key_id} not found")
        
        # Get encryption rules for this database
        database_rules = {}
        if (tenant_id in self.encryption_rules and 
            database_id in self.encryption_rules[tenant_id]):
            database_rules = self.encryption_rules[tenant_id][database_id]
        
        return EncryptedStorageWrapper(db_engine, key.key_data, database_rules)
    
    def generate_tenant_encryption_key(self, tenant_id: str) -> str:
        """Generate encryption key for a new tenant"""
        return self.key_manager.generate_tenant_key(tenant_id)
    
    def generate_database_encryption_key(self, tenant_id: str, database_id: str) -> str:
        """Generate encryption key for a new database"""
        return self.key_manager.generate_database_key(tenant_id, database_id)


def create_encryption_manager(storage_path: str = "./encryption") -> TransparentEncryptionManager:
    """Create and configure encryption manager"""
    return TransparentEncryptionManager(storage_path)
