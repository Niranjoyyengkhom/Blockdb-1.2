"""
IEDB File-Based Database Storage System
======================================
Manages encrypted databases as .block⛓️ folders and tables as .chain🔗 files
"""

import os
import json
import uuid
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from cryptography.fernet import Fernet
import threading

class FileStorageManager:
    """File-based storage system for tenant databases and tables"""
    
    def __init__(self, base_path: str = "Tenants_DB"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self.lock = threading.Lock()
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for data protection"""
        key_file = Path("encryption") / "storage.key"
        key_file.parent.mkdir(exist_ok=True)
        
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            return key
    
    def _encrypt_data(self, data: Any) -> bytes:
        """Encrypt data before storage"""
        serialized = json.dumps(data, default=str).encode()
        return self.fernet.encrypt(serialized)
    
    def _decrypt_data(self, encrypted_data: bytes) -> Any:
        """Decrypt data after retrieval"""
        decrypted = self.fernet.decrypt(encrypted_data)
        return json.loads(decrypted.decode())
    
    def _create_database_schema(self, tenant_id: str, database_name: str, description: str = "") -> Dict:
        """Create database schema file"""
        schema_data = {
            "database_name": database_name,
            "tenant_id": tenant_id,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
            "tables": [],
            "constraints": {
                "foreign_keys": [],
                "check_constraints": [],
                "unique_constraints": []
            },
            "indexes": [],
            "triggers": [],
            "views": [],
            "procedures": [],
            "functions": [],
            "metadata": {
                "character_set": "utf8mb4",
                "collation": "utf8mb4_unicode_ci",
                "engine": "IEDB_FileStorage",
                "encryption": "enabled"
            }
        }
        return schema_data
    
    def _create_table_schema(self, tenant_id: str, database_name: str, table_name: str, 
                           description: str, columns: List[Dict]) -> Dict:
        """Create table schema file"""
        schema_data = {
            "table_name": table_name,
            "database_name": database_name,
            "tenant_id": tenant_id,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
            "columns": columns,
            "primary_key": [col["name"] for col in columns if col.get("primary_key", False)],
            "foreign_keys": [col for col in columns if "foreign_key" in col],
            "indexes": [col["name"] for col in columns if col.get("index", False)],
            "unique_constraints": [col["name"] for col in columns if col.get("unique", False)],
            "not_null_constraints": [col["name"] for col in columns if not col.get("nullable", True)],
            "check_constraints": [col for col in columns if "check" in col],
            "default_values": {col["name"]: col["default"] for col in columns if "default" in col},
            "data_types": {col["name"]: col["type"] for col in columns},
            "column_comments": {col["name"]: col.get("comment", "") for col in columns if "comment" in col},
            "table_options": {
                "engine": "IEDB_FileStorage",
                "character_set": "utf8mb4",
                "collation": "utf8mb4_unicode_ci",
                "encryption": "enabled",
                "auto_increment": 1 if any(col.get("auto_increment") for col in columns) else None
            },
            "statistics": {
                "row_count": 0,
                "avg_row_length": 0,
                "data_length": 0,
                "index_length": 0,
                "data_free": 0
            }
        }
        return schema_data
    
    def _save_schema_file(self, schema_path: Path, schema_data: Dict):
        """Save encrypted schema file"""
        with open(schema_path, 'wb') as f:
            f.write(self._encrypt_data(schema_data))
    
    def _load_schema_file(self, schema_path: Path) -> Dict:
        """Load encrypted schema file"""
        if not schema_path.exists():
            return {}
        with open(schema_path, 'rb') as f:
            encrypted_data = f.read()
        return self._decrypt_data(encrypted_data)
    
    def _get_tenant_path(self, tenant_id: str) -> Path:
        """Get tenant directory path"""
        return self.base_path / f"tenant_{tenant_id}"
    
    def _get_database_path(self, tenant_id: str, database_name: str) -> Path:
        """Get database directory path with .block⛓️ extension"""
        return self._get_tenant_path(tenant_id) / f"{database_name}.block⛓️"
    
    def _get_database_schema_path(self, tenant_id: str, database_name: str) -> Path:
        """Get database schema file path"""
        return self._get_database_path(tenant_id, database_name) / f"{database_name}.sch"
    
    def _get_table_path(self, tenant_id: str, database_name: str, table_name: str) -> Path:
        """Get table file path with .chain🔗 extension"""
        return self._get_database_path(tenant_id, database_name) / f"{table_name}.chain🔗"
    
    def _get_table_schema_path(self, tenant_id: str, database_name: str, table_name: str) -> Path:
        """Get table schema file path"""
        return self._get_database_path(tenant_id, database_name) / f"{table_name}.sch"
    
    def create_database(self, tenant_id: str, database_name: str, description: str = "", config: Optional[Dict] = None) -> Dict:
        """Create a new database (folder) for tenant with schema file"""
        with self.lock:
            try:
                tenant_path = self._get_tenant_path(tenant_id)
                tenant_path.mkdir(exist_ok=True)
                
                database_path = self._get_database_path(tenant_id, database_name)
                
                if database_path.exists():
                    return {
                        "success": False,
                        "error": f"Database '{database_name}' already exists",
                        "path": str(database_path)
                    }
                
                # Create database directory
                database_path.mkdir(parents=True)
                
                # Create database metadata
                metadata = {
                    "id": str(uuid.uuid4()),
                    "name": database_name,
                    "tenant_id": tenant_id,
                    "type": "database",
                    "description": description,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "config": config or {},
                    "tables": [],
                    "encryption": "AES-256",
                    "storage_type": "file_based",
                    "version": "1.0",
                    "extension": ".block⛓️",
                    "blockchain_hash": hashlib.sha256(f"{tenant_id}{database_name}{time.time()}".encode()).hexdigest()[:16]
                }
                
                # Save metadata file
                metadata_file = database_path / "metadata.json"
                with open(metadata_file, 'wb') as f:
                    f.write(self._encrypt_data(metadata))
                
                # Create database schema file
                schema_data = self._create_database_schema(tenant_id, database_name, description)
                schema_path = self._get_database_schema_path(tenant_id, database_name)
                self._save_schema_file(schema_path, schema_data)
                
                # Create database info file
                db_info = {
                    "schema_version": "1.0",
                    "tables": [],
                    "total_records": 0,
                    "last_modified": datetime.now(timezone.utc).isoformat(),
                    "indexes": [],
                    "constraints": []
                }
                
                info_file = database_path / "database_info.json"
                with open(info_file, 'wb') as f:
                    f.write(self._encrypt_data(db_info))
                
                return {
                    "success": True,
                    "database_name": database_name,
                    "folder_path": str(database_path),
                    "schema_file": str(schema_path),
                    "extension": ".block⛓️",
                    "metadata": metadata,
                    "schema": schema_data,
                    "message": "Database and schema created successfully"
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to create database: {str(e)}"
                }
    
    def list_databases(self, tenant_id: str) -> Dict:
        """List all databases for a tenant"""
        try:
            tenant_path = self._get_tenant_path(tenant_id)
            
            if not tenant_path.exists():
                return {
                    "success": True,
                    "databases": [],
                    "tenant_id": tenant_id
                }
            
            databases = []
            for db_path in tenant_path.iterdir():
                if db_path.is_dir():
                    metadata_file = db_path / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'rb') as f:
                                metadata = self._decrypt_data(f.read())
                            databases.append({
                                "name": metadata["name"],
                                "created_at": metadata["created_at"],
                                "table_count": len(metadata.get("tables", [])),
                                "path": str(db_path)
                            })
                        except Exception as e:
                            # Skip corrupted metadata files
                            continue
            
            return {
                "success": True,
                "databases": databases,
                "tenant_id": tenant_id,
                "count": len(databases)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list databases: {str(e)}"
            }
    
    def create_table(self, tenant_id: str, database_name: str, table_name: str, 
                   description: str, columns: List[Dict]) -> Dict:
        """Create a new table (file) in database with schema file"""
        with self.lock:
            try:
                database_path = self._get_database_path(tenant_id, database_name)
                
                if not database_path.exists():
                    return {
                        "success": False,
                        "error": f"Database '{database_name}' does not exist"
                    }
                
                table_path = self._get_table_path(tenant_id, database_name, table_name)
                
                if table_path.exists():
                    return {
                        "success": False,
                        "error": f"Table '{table_name}' already exists"
                    }
                
                # Create table metadata
                table_metadata = {
                    "table_name": table_name,
                    "database_name": database_name,
                    "tenant_id": tenant_id,
                    "type": "table",
                    "description": description,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "columns": columns,
                    "extension": ".chain🔗",
                    "version": "1.0",
                    "blockchain_hash": hashlib.sha256(f"{tenant_id}{database_name}{table_name}{time.time()}".encode()).hexdigest()[:16]
                }
                
                # Create table data structure
                table_data = {
                    "metadata": table_metadata,
                    "records": [],
                    "stats": {
                        "total_records": 0,
                        "last_insert": None,
                        "last_update": None
                    }
                }
                
                # Save table file
                with open(table_path, 'wb') as f:
                    f.write(self._encrypt_data(table_data))
                
                # Create table schema file
                schema_data = self._create_table_schema(tenant_id, database_name, table_name, description, columns)
                schema_path = self._get_table_schema_path(tenant_id, database_name, table_name)
                self._save_schema_file(schema_path, schema_data)
                
                # Update database metadata to include new table
                self._update_database_metadata(tenant_id, database_name, table_name, "add")
                
                # Update database schema to include new table
                self._update_database_schema(tenant_id, database_name, table_name, columns)
                
                return {
                    "success": True,
                    "table_name": table_name,
                    "file_path": str(table_path),
                    "schema_file": str(schema_path),
                    "extension": ".chain🔗",
                    "columns": columns,
                    "metadata": table_metadata,
                    "schema": schema_data,
                    "message": "Table and schema created successfully"
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to create table: {str(e)}"
                }
    
    def list_tables(self, tenant_id: str, database_name: str) -> Dict:
        """List all tables in a database"""
        try:
            database_path = self._get_database_path(tenant_id, database_name)
            
            if not database_path.exists():
                return {
                    "success": False,
                    "error": f"Database '{database_name}' does not exist"
                }
            
            tables = []
            for table_file in database_path.glob("*.table"):
                try:
                    with open(table_file, 'rb') as f:
                        table_data = self._decrypt_data(f.read())
                    
                    tables.append({
                        "name": table_data["name"],
                        "created_at": table_data["created_at"],
                        "row_count": table_data["row_count"],
                        "schema": table_data["schema"],
                        "path": str(table_file)
                    })
                except Exception:
                    # Skip corrupted table files
                    continue
            
            return {
                "success": True,
                "tables": tables,
                "database": database_name,
                "tenant_id": tenant_id,
                "count": len(tables)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list tables: {str(e)}"
            }
    
    def insert_data(self, tenant_id: str, database_name: str, table_name: str, data: Dict) -> Dict:
        """Insert data into table"""
        with self.lock:
            try:
                table_path = self._get_table_path(tenant_id, database_name, table_name)
                
                if not table_path.exists():
                    return {
                        "success": False,
                        "error": f"Table '{table_name}' does not exist"
                    }
                
                # Load table data
                with open(table_path, 'rb') as f:
                    table_data = self._decrypt_data(f.read())
                
                # Add timestamp and row ID
                row_id = len(table_data["rows"]) + 1
                data["_id"] = row_id
                data["_created_at"] = datetime.now(timezone.utc).isoformat()
                
                # Add row to table
                table_data["rows"].append(data)
                table_data["row_count"] = len(table_data["rows"])
                table_data["last_modified"] = datetime.now(timezone.utc).isoformat()
                
                # Save updated table
                with open(table_path, 'wb') as f:
                    f.write(self._encrypt_data(table_data))
                
                return {
                    "success": True,
                    "row_id": row_id,
                    "data": data,
                    "message": "Data inserted successfully"
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to insert data: {str(e)}"
                }
    
    def query_data(self, tenant_id: str, database_name: str, table_name: str, conditions: Optional[Dict] = None) -> Dict:
        """Query data from table"""
        try:
            table_path = self._get_table_path(tenant_id, database_name, table_name)
            
            if not table_path.exists():
                return {
                    "success": False,
                    "error": f"Table '{table_name}' does not exist"
                }
            
            # Load table data
            with open(table_path, 'rb') as f:
                table_data = self._decrypt_data(f.read())
            
            rows = table_data["rows"]
            
            # Apply conditions if provided
            if conditions:
                filtered_rows = []
                for row in rows:
                    match = True
                    for key, value in conditions.items():
                        if key not in row or row[key] != value:
                            match = False
                            break
                    if match:
                        filtered_rows.append(row)
                rows = filtered_rows
            
            return {
                "success": True,
                "data": rows,
                "count": len(rows),
                "table": table_name,
                "database": database_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to query data: {str(e)}"
            }
    
    def _update_database_metadata(self, tenant_id: str, database_name: str, table_name: str, action: str):
        """Update database metadata when tables are added/removed"""
        try:
            database_path = self._get_database_path(tenant_id, database_name)
            metadata_file = database_path / "metadata.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'rb') as f:
                    metadata = self._decrypt_data(f.read())
                
                if action == "add" and table_name not in metadata["tables"]:
                    metadata["tables"].append(table_name)
                elif action == "remove" and table_name in metadata["tables"]:
                    metadata["tables"].remove(table_name)
                
                metadata["last_modified"] = datetime.now(timezone.utc).isoformat()
                
                with open(metadata_file, 'wb') as f:
                    f.write(self._encrypt_data(metadata))
        except Exception:
            # Non-critical operation, don't fail the main operation
            pass
    
    def _update_database_schema(self, tenant_id: str, database_name: str, table_name: str, columns: List[Dict]):
        """Update database schema file when tables are added"""
        try:
            schema_path = self._get_database_schema_path(tenant_id, database_name)
            
            if schema_path.exists():
                schema_data = self._load_schema_file(schema_path)
                
                # Add table to database schema
                table_info = {
                    "table_name": table_name,
                    "columns": columns,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "primary_key": [col["name"] for col in columns if col.get("primary_key", False)],
                    "foreign_keys": [col for col in columns if "foreign_key" in col],
                    "indexes": [col["name"] for col in columns if col.get("index", False)]
                }
                
                # Remove existing table info if it exists
                schema_data["tables"] = [t for t in schema_data["tables"] if t["table_name"] != table_name]
                
                # Add new table info
                schema_data["tables"].append(table_info)
                schema_data["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                # Save updated schema
                self._save_schema_file(schema_path, schema_data)
        except Exception:
            # Non-critical operation, don't fail the main operation
            pass
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            stats = {
                "base_path": str(self.base_path),
                "tenants": 0,
                "databases": 0,
                "tables": 0,
                "total_size_bytes": 0
            }
            
            if not self.base_path.exists():
                return stats
            
            for tenant_path in self.base_path.iterdir():
                if tenant_path.is_dir():
                    stats["tenants"] += 1
                    
                    for db_path in tenant_path.iterdir():
                        if db_path.is_dir():
                            stats["databases"] += 1
                            
                            for table_file in db_path.glob("*.table"):
                                stats["tables"] += 1
                                stats["total_size_bytes"] += table_file.stat().st_size
            
            stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
            return stats
            
        except Exception as e:
            return {"error": f"Failed to get storage stats: {str(e)}"}
    
    def get_database_schema(self, tenant_id: str, database_name: str) -> Dict:
        """Get database schema information"""
        try:
            schema_path = self._get_database_schema_path(tenant_id, database_name)
            
            if not schema_path.exists():
                return {
                    "success": False,
                    "error": f"Database schema file not found for '{database_name}'"
                }
            
            schema_data = self._load_schema_file(schema_path)
            
            return {
                "success": True,
                "database_name": database_name,
                "tenant_id": tenant_id,
                "schema_file": str(schema_path),
                "schema": schema_data
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get database schema: {str(e)}"
            }
    
    def get_table_schema(self, tenant_id: str, database_name: str, table_name: str) -> Dict:
        """Get table schema information"""
        try:
            schema_path = self._get_table_schema_path(tenant_id, database_name, table_name)
            
            if not schema_path.exists():
                return {
                    "success": False,
                    "error": f"Table schema file not found for '{table_name}'"
                }
            
            schema_data = self._load_schema_file(schema_path)
            
            return {
                "success": True,
                "table_name": table_name,
                "database_name": database_name,
                "tenant_id": tenant_id,
                "schema_file": str(schema_path),
                "schema": schema_data
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get table schema: {str(e)}"
            }
    
    def list_schema_files(self, tenant_id: str, database_name: str) -> Dict:
        """List all schema files in a database"""
        try:
            database_path = self._get_database_path(tenant_id, database_name)
            
            if not database_path.exists():
                return {
                    "success": False,
                    "error": f"Database '{database_name}' does not exist"
                }
            
            schema_files = []
            
            # Find all .sch files
            for schema_file in database_path.glob("*.sch"):
                schema_name = schema_file.stem
                schema_type = "database" if schema_name == database_name else "table"
                
                try:
                    schema_data = self._load_schema_file(schema_file)
                    file_info = {
                        "name": schema_name,
                        "type": schema_type,
                        "file_path": str(schema_file),
                        "created_at": schema_data.get("created_at"),
                        "version": schema_data.get("version"),
                        "size": schema_file.stat().st_size
                    }
                    
                    if schema_type == "table":
                        file_info["columns"] = len(schema_data.get("columns", []))
                    else:
                        file_info["tables"] = len(schema_data.get("tables", []))
                    
                    schema_files.append(file_info)
                except Exception:
                    # Skip corrupted schema files
                    continue
            
            return {
                "success": True,
                "database_name": database_name,
                "tenant_id": tenant_id,
                "schema_files": schema_files,
                "count": len(schema_files)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list schema files: {str(e)}"
            }

# Global storage instance
storage = FileStorageManager()
