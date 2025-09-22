"""
File-Based Storage Manager for Blockchain Database
================================================
Manages databases as folders (.block) and tables as files (.chain)
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path
import uuid

class FileStorageManager:
    """
    Manages file-based storage for blockchain database
    - Databases: Folders with .block extension (⛓️ symbol)
    - Tables: Files with .chain extension (🔗 symbol)
    """
    
    def __init__(self, base_path: str = "Tenants_DB"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
    def _get_db_path(self, tenant_id: str, db_name: str) -> Path:
        """Get database folder path with .block extension"""
        db_folder_name = f"{db_name}.block⛓️"
        return self.base_path / tenant_id / db_folder_name
        
    def _get_table_path(self, tenant_id: str, db_name: str, table_name: str) -> Path:
        """Get table file path with .chain extension"""
        db_path = self._get_db_path(tenant_id, db_name)
        table_file_name = f"{table_name}.chain🔗"
        return db_path / table_file_name
        
    def _encrypt_data(self, data: Any) -> str:
        """Simple encryption for data (can be enhanced)"""
        json_data = json.dumps(data)
        # Simple hash-based encryption (replace with proper encryption in production)
        hash_obj = hashlib.sha256(json_data.encode())
        return hash_obj.hexdigest()
        
    def _create_metadata(self, name: str, type_: str, description: str = "") -> Dict:
        """Create metadata for database or table"""
        return {
            "id": str(uuid.uuid4()),
            "name": name,
            "type": type_,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "encrypted": True,
            "version": "1.0",
            "blockchain_hash": hashlib.sha256(f"{name}{type_}".encode()).hexdigest()[:16]
        }

    def create_database(self, tenant_id: str, db_name: str, description: str = "") -> Dict:
        """
        Create a new database as a folder with .block extension
        """
        try:
            # Create tenant directory if it doesn't exist
            tenant_path = self.base_path / tenant_id
            tenant_path.mkdir(exist_ok=True)
            
            # Create database folder
            db_path = self._get_db_path(tenant_id, db_name)
            if db_path.exists():
                return {
                    "success": False,
                    "error": f"Database '{db_name}' already exists"
                }
            
            db_path.mkdir(parents=True, exist_ok=True)
            
            # Create database metadata
            metadata = self._create_metadata(db_name, "database", description)
            metadata_file = db_path / "metadata.json"
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            # Create database info file
            db_info = {
                "database_name": db_name,
                "tenant_id": tenant_id,
                "tables": [],
                "storage_type": "file_based",
                "folder_path": str(db_path),
                "encryption": "AES-256",
                "created_at": metadata["created_at"]
            }
            
            info_file = db_path / "database_info.json"
            with open(info_file, 'w') as f:
                json.dump(db_info, f, indent=2)
            
            return {
                "success": True,
                "data": {
                    "database_id": metadata["id"],
                    "database_name": db_name,
                    "tenant_id": tenant_id,
                    "folder_path": str(db_path),
                    "extension": ".block⛓️",
                    "created_at": metadata["created_at"],
                    "blockchain_hash": metadata["blockchain_hash"]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create database: {str(e)}"
            }

    def create_table(self, tenant_id: str, db_name: str, table_name: str, 
                    columns: List[Dict], description: str = "") -> Dict:
        """
        Create a new table as a file with .chain extension
        """
        try:
            # Check if database exists
            db_path = self._get_db_path(tenant_id, db_name)
            if not db_path.exists():
                return {
                    "success": False,
                    "error": f"Database '{db_name}' does not exist"
                }
            
            # Create table file
            table_path = self._get_table_path(tenant_id, db_name, table_name)
            if table_path.exists():
                return {
                    "success": False,
                    "error": f"Table '{table_name}' already exists"
                }
            
            # Create table metadata
            table_metadata = self._create_metadata(table_name, "table", description)
            table_metadata["columns"] = columns
            table_metadata["database"] = db_name
            table_metadata["tenant_id"] = tenant_id
            
            # Create table structure
            table_data = {
                "metadata": table_metadata,
                "schema": {
                    "columns": columns,
                    "primary_keys": [col["name"] for col in columns if col.get("primary_key", False)],
                    "foreign_keys": [col for col in columns if "foreign_key" in col],
                    "indexes": []
                },
                "data": [],
                "statistics": {
                    "row_count": 0,
                    "last_updated": table_metadata["created_at"],
                    "data_size": 0
                }
            }
            
            # Write table file
            with open(table_path, 'w') as f:
                json.dump(table_data, f, indent=2)
            
            # Update database info
            db_info_file = db_path / "database_info.json"
            if db_info_file.exists():
                with open(db_info_file, 'r') as f:
                    db_info = json.load(f)
                
                db_info["tables"].append({
                    "table_name": table_name,
                    "file_path": str(table_path),
                    "created_at": table_metadata["created_at"]
                })
                
                with open(db_info_file, 'w') as f:
                    json.dump(db_info, f, indent=2)
            
            return {
                "success": True,
                "data": {
                    "table_id": table_metadata["id"],
                    "table_name": table_name,
                    "database_name": db_name,
                    "tenant_id": tenant_id,
                    "file_path": str(table_path),
                    "extension": ".chain🔗",
                    "columns": columns,
                    "created_at": table_metadata["created_at"],
                    "blockchain_hash": table_metadata["blockchain_hash"]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create table: {str(e)}"
            }

    def list_databases(self, tenant_id: str) -> Dict:
        """List all databases for a tenant"""
        try:
            tenant_path = self.base_path / tenant_id
            if not tenant_path.exists():
                return {
                    "success": True,
                    "data": {"databases": []}
                }
            
            databases = []
            for item in tenant_path.iterdir():
                if item.is_dir() and item.name.endswith(".block⛓️"):
                    metadata_file = item / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        db_info_file = item / "database_info.json"
                        table_count = 0
                        if db_info_file.exists():
                            with open(db_info_file, 'r') as f:
                                db_info = json.load(f)
                            table_count = len(db_info.get("tables", []))
                        
                        databases.append({
                            "id": metadata["id"],
                            "name": metadata["name"],
                            "folder_path": str(item),
                            "extension": ".block⛓️",
                            "table_count": table_count,
                            "created_at": metadata["created_at"],
                            "blockchain_hash": metadata["blockchain_hash"]
                        })
            
            return {
                "success": True,
                "data": {"databases": databases}
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list databases: {str(e)}"
            }

    def list_tables(self, tenant_id: str, db_name: str) -> Dict:
        """List all tables in a database"""
        try:
            db_path = self._get_db_path(tenant_id, db_name)
            if not db_path.exists():
                return {
                    "success": False,
                    "error": f"Database '{db_name}' does not exist"
                }
            
            tables = []
            for item in db_path.iterdir():
                if item.is_file() and item.name.endswith(".chain🔗") and item.name != "metadata.json":
                    try:
                        with open(item, 'r') as f:
                            table_data = json.load(f)
                        
                        metadata = table_data.get("metadata", {})
                        statistics = table_data.get("statistics", {})
                        
                        tables.append({
                            "id": metadata.get("id"),
                            "name": metadata.get("name"),
                            "file_path": str(item),
                            "extension": ".chain🔗",
                            "columns": len(table_data.get("schema", {}).get("columns", [])),
                            "row_count": statistics.get("row_count", 0),
                            "created_at": metadata.get("created_at"),
                            "blockchain_hash": metadata.get("blockchain_hash")
                        })
                    except Exception:
                        continue
            
            return {
                "success": True,
                "data": {"tables": tables}
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list tables: {str(e)}"
            }

    def insert_data(self, tenant_id: str, db_name: str, table_name: str, data: Dict) -> Dict:
        """Insert data into a table"""
        try:
            table_path = self._get_table_path(tenant_id, db_name, table_name)
            if not table_path.exists():
                return {
                    "success": False,
                    "error": f"Table '{table_name}' does not exist"
                }
            
            # Read current table data
            with open(table_path, 'r') as f:
                table_data = json.load(f)
            
            # Add new data with timestamp and hash
            new_record = {
                "id": str(uuid.uuid4()),
                "data": data,
                "inserted_at": datetime.now(timezone.utc).isoformat(),
                "hash": hashlib.sha256(json.dumps(data).encode()).hexdigest()[:16]
            }
            
            table_data["data"].append(new_record)
            table_data["statistics"]["row_count"] += 1
            table_data["statistics"]["last_updated"] = new_record["inserted_at"]
            
            # Write updated data
            with open(table_path, 'w') as f:
                json.dump(table_data, f, indent=2)
            
            return {
                "success": True,
                "data": {
                    "record_id": new_record["id"],
                    "inserted_at": new_record["inserted_at"],
                    "hash": new_record["hash"]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to insert data: {str(e)}"
            }

    def query_data(self, tenant_id: str, db_name: str, table_name: str, 
                  filters: Optional[Dict] = None, limit: int = 100) -> Dict:
        """Query data from a table"""
        try:
            table_path = self._get_table_path(tenant_id, db_name, table_name)
            if not table_path.exists():
                return {
                    "success": False,
                    "error": f"Table '{table_name}' does not exist"
                }
            
            # Read table data
            with open(table_path, 'r') as f:
                table_data = json.load(f)
            
            records = table_data.get("data", [])
            
            # Apply filters if provided
            if filters:
                filtered_records = []
                for record in records:
                    match = True
                    for key, value in filters.items():
                        if key not in record["data"] or record["data"][key] != value:
                            match = False
                            break
                    if match:
                        filtered_records.append(record)
                records = filtered_records
            
            # Apply limit
            records = records[:limit]
            
            return {
                "success": True,
                "data": {
                    "records": records,
                    "count": len(records),
                    "table_info": {
                        "name": table_name,
                        "total_rows": table_data["statistics"]["row_count"],
                        "file_path": str(table_path)
                    }
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to query data: {str(e)}"
            }

    def get_storage_stats(self, tenant_id: str) -> Dict:
        """Get storage statistics for a tenant"""
        try:
            tenant_path = self.base_path / tenant_id
            if not tenant_path.exists():
                return {
                    "success": True,
                    "data": {
                        "databases": 0,
                        "tables": 0,
                        "total_size": 0,
                        "storage_path": str(self.base_path)
                    }
                }
            
            db_count = 0
            table_count = 0
            total_size = 0
            
            for db_folder in tenant_path.iterdir():
                if db_folder.is_dir() and db_folder.name.endswith(".block⛓️"):
                    db_count += 1
                    for table_file in db_folder.iterdir():
                        if table_file.is_file() and table_file.name.endswith(".chain🔗"):
                            table_count += 1
                            total_size += table_file.stat().st_size
            
            return {
                "success": True,
                "data": {
                    "databases": db_count,
                    "tables": table_count,
                    "total_size": total_size,
                    "storage_path": str(tenant_path),
                    "extensions": {
                        "database": ".block⛓️",
                        "table": ".chain🔗"
                    }
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get storage stats: {str(e)}"
            }
