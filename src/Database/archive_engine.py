"""
Blockchain-Style Archiving System
=================================

Archive system that implements blockchain-style data retention where DELETE operations
move data to archive collections with complete audit trail and data integrity.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import uuid
from pathlib import Path


class ArchiveOperation(Enum):
    """Types of archive operations"""
    DELETE = "delete"           # Move to archive on delete
    EXPIRE = "expire"          # Move to archive on expiration
    MANUAL = "manual"          # Manual archival
    COMPLIANCE = "compliance"   # Compliance-driven archival
    RESTORE = "restore"        # Restore from archive


class ArchiveStatus(Enum):
    """Status of archived data"""
    ACTIVE = "active"           # Active in main collection
    ARCHIVED = "archived"       # Moved to archive
    PURGED = "purged"          # Permanently deleted (rare)
    RESTORED = "restored"       # Restored from archive


@dataclass
class ArchiveMetadata:
    """Metadata for archived documents"""
    original_id: str
    original_collection: str
    archive_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: ArchiveOperation = ArchiveOperation.DELETE
    status: ArchiveStatus = ArchiveStatus.ARCHIVED
    archived_at: datetime = field(default_factory=datetime.now)
    archived_by: str = "system"
    reason: str = "Document deleted"
    original_hash: str = ""
    archive_hash: str = ""
    restoration_count: int = 0
    last_restored_at: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    compliance_holds: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "original_id": self.original_id,
            "original_collection": self.original_collection,
            "archive_id": self.archive_id,
            "operation": self.operation.value,
            "status": self.status.value,
            "archived_at": self.archived_at.isoformat(),
            "archived_by": self.archived_by,
            "reason": self.reason,
            "original_hash": self.original_hash,
            "archive_hash": self.archive_hash,
            "restoration_count": self.restoration_count,
            "last_restored_at": self.last_restored_at.isoformat() if self.last_restored_at else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "compliance_holds": self.compliance_holds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArchiveMetadata':
        """Create from dictionary"""
        metadata = cls(
            original_id=data["original_id"],
            original_collection=data["original_collection"],
            archive_id=data.get("archive_id", str(uuid.uuid4())),
            operation=ArchiveOperation(data.get("operation", "delete")),
            status=ArchiveStatus(data.get("status", "archived")),
            archived_by=data.get("archived_by", "system"),
            reason=data.get("reason", "Document deleted"),
            original_hash=data.get("original_hash", ""),
            archive_hash=data.get("archive_hash", ""),
            restoration_count=data.get("restoration_count", 0),
            compliance_holds=data.get("compliance_holds", [])
        )
        
        if data.get("archived_at"):
            metadata.archived_at = datetime.fromisoformat(data["archived_at"])
        if data.get("last_restored_at"):
            metadata.last_restored_at = datetime.fromisoformat(data["last_restored_at"])
        if data.get("expiry_date"):
            metadata.expiry_date = datetime.fromisoformat(data["expiry_date"])
        
        return metadata


@dataclass
class ArchivePolicy:
    """Policy for data archival"""
    collection: str
    retention_days: int = 365 * 7  # 7 years default
    auto_archive: bool = True
    archive_on_delete: bool = True
    allow_purge: bool = False
    purge_after_days: Optional[int] = None
    compliance_requirements: List[str] = field(default_factory=list)
    encryption_required: bool = False
    compression_enabled: bool = True
    
    def should_archive(self, document: Dict[str, Any], operation: ArchiveOperation) -> bool:
        """Check if document should be archived"""
        if operation == ArchiveOperation.DELETE and not self.archive_on_delete:
            return False
        
        if operation == ArchiveOperation.EXPIRE and not self.auto_archive:
            return False
        
        return True
    
    def should_purge(self, metadata: ArchiveMetadata) -> bool:
        """Check if archived document should be purged"""
        if not self.allow_purge or not self.purge_after_days:
            return False
        
        if metadata.compliance_holds:
            return False  # Cannot purge if compliance holds exist
        
        age = (datetime.now() - metadata.archived_at).days
        return age > self.purge_after_days


class ArchiveEngine:
    """Engine for managing blockchain-style data archival"""
    
    def __init__(self, db_engine):
        self.db_engine = db_engine
        self.policies: Dict[str, ArchivePolicy] = {}
        self.archive_prefix = "archive_"
        self.metadata_collection = "archive_metadata"
        self.audit_collection = "archive_audit"
        
        # Ensure metadata collections exist
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize archive-related collections"""
        # Create indexes for better performance
        self.db_engine.create_index(self.metadata_collection, [("original_id", 1)])
        self.db_engine.create_index(self.metadata_collection, [("original_collection", 1)])
        self.db_engine.create_index(self.metadata_collection, [("archive_id", 1)])
        self.db_engine.create_index(self.metadata_collection, [("archived_at", 1)])
        self.db_engine.create_index(self.metadata_collection, [("status", 1)])
        
        self.db_engine.create_index(self.audit_collection, [("timestamp", 1)])
        self.db_engine.create_index(self.audit_collection, [("operation", 1)])
    
    def set_archive_policy(self, collection: str, policy: ArchivePolicy):
        """Set archival policy for a collection"""
        self.policies[collection] = policy
    
    def get_archive_policy(self, collection: str) -> ArchivePolicy:
        """Get archival policy for a collection"""
        return self.policies.get(collection, ArchivePolicy(collection=collection))
    
    def archive_document(self, collection: str, document: Dict[str, Any], 
                        operation: ArchiveOperation, user_id: str = "system", 
                        reason: str = "") -> str:
        """Archive a document"""
        policy = self.get_archive_policy(collection)
        
        if not policy.should_archive(document, operation):
            raise ValueError(f"Document cannot be archived: policy does not allow {operation.value}")
        
        # Create archive metadata
        original_id = str(document.get("_id", document.get("id", str(uuid.uuid4()))))
        metadata = ArchiveMetadata(
            original_id=original_id,
            original_collection=collection,
            operation=operation,
            archived_by=user_id,
            reason=reason or f"Document {operation.value}d",
            original_hash=self._calculate_hash(document)
        )
        
        # Process document for archival
        archive_document = self._prepare_document_for_archive(document, metadata)
        metadata.archive_hash = self._calculate_hash(archive_document)
        
        # Store in archive collection
        archive_collection = self._get_archive_collection_name(collection)
        self.db_engine.insert_one(archive_collection, archive_document)
        
        # Store metadata
        self.db_engine.insert_one(self.metadata_collection, metadata.to_dict())
        
        # Log audit event
        self._log_audit_event(operation, collection, original_id, metadata.archive_id, user_id, reason)
        
        return metadata.archive_id
    
    def restore_document(self, archive_id: str, user_id: str = "system", 
                        reason: str = "") -> Tuple[str, Dict[str, Any]]:
        """Restore a document from archive"""
        # Find metadata
        metadata_doc = self.db_engine.find_one(self.metadata_collection, {"archive_id": archive_id})
        if not metadata_doc:
            raise ValueError(f"Archive not found: {archive_id}")
        
        metadata = ArchiveMetadata.from_dict(metadata_doc)
        
        if metadata.status != ArchiveStatus.ARCHIVED:
            raise ValueError(f"Cannot restore: document status is {metadata.status.value}")
        
        # Find archived document
        archive_collection = self._get_archive_collection_name(metadata.original_collection)
        archive_doc = self.db_engine.find_one(archive_collection, {"_archive_metadata.archive_id": archive_id})
        
        if not archive_doc:
            raise ValueError(f"Archived document not found: {archive_id}")
        
        # Verify integrity
        if not self._verify_document_integrity(archive_doc, metadata):
            raise ValueError("Archive integrity check failed")
        
        # Prepare document for restoration
        restored_doc = self._prepare_document_for_restoration(archive_doc)
        
        # Insert into original collection
        result = self.db_engine.insert_one(metadata.original_collection, restored_doc)
        
        # Update metadata
        metadata.status = ArchiveStatus.RESTORED
        metadata.restoration_count += 1
        metadata.last_restored_at = datetime.now()
        
        self.db_engine.update_one(
            self.metadata_collection, 
            {"archive_id": archive_id}, 
            {"$set": metadata.to_dict()}
        )
        
        # Log audit event
        self._log_audit_event(
            ArchiveOperation.RESTORE, 
            metadata.original_collection, 
            metadata.original_id, 
            archive_id, 
            user_id, 
            reason or "Document restored"
        )
        
        return str(result), restored_doc
    
    def delete_with_archive(self, collection: str, filter_dict: Dict[str, Any], 
                          user_id: str = "system", reason: str = "") -> List[str]:
        """Delete documents and archive them"""
        # Find documents to delete
        documents = self.db_engine.find(collection, filter_dict)
        archive_ids = []
        
        for doc in documents:
            # Archive the document
            archive_id = self.archive_document(
                collection, doc, ArchiveOperation.DELETE, user_id, reason
            )
            archive_ids.append(archive_id)
        
        # Delete from original collection
        self.db_engine.delete_many(collection, filter_dict)
        
        return archive_ids
    
    def search_archives(self, collection: Optional[str] = None, 
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       status: Optional[ArchiveStatus] = None,
                       operation: Optional[ArchiveOperation] = None) -> List[Dict[str, Any]]:
        """Search archived documents"""
        filter_dict = {}
        
        if collection:
            filter_dict["original_collection"] = collection
        
        if start_date:
            filter_dict["archived_at"] = {"$gte": start_date.isoformat()}
        
        if end_date:
            if "archived_at" not in filter_dict:
                filter_dict["archived_at"] = {}
            filter_dict["archived_at"]["$lte"] = end_date.isoformat()
        
        if status:
            filter_dict["status"] = status.value
        
        if operation:
            filter_dict["operation"] = operation.value
        
        return self.db_engine.find(self.metadata_collection, filter_dict)
    
    def get_archive_statistics(self, collection: Optional[str] = None) -> Dict[str, Any]:
        """Get archive statistics"""
        try:
            # Build filter
            filter_dict = {}
            if collection:
                filter_dict["original_collection"] = collection
            
            # Get all archive metadata
            all_archives = list(self.db_engine.find(self.metadata_collection, filter_dict))
            
            # Basic statistics
            total_archived = len(all_archives)
            
            # Count by status
            status_counts = {}
            for archive in all_archives:
                status = archive.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by operation
            operation_counts = {}
            for archive in all_archives:
                operation = archive.get("operation", "unknown")
                operation_counts[operation] = operation_counts.get(operation, 0) + 1
            
            # Find oldest and newest
            oldest_archive = None
            newest_archive = None
            
            if all_archives:
                archives_with_dates = [a for a in all_archives if a.get("archived_at")]
                if archives_with_dates:
                    oldest_archive = min(archives_with_dates, key=lambda x: x["archived_at"])["archived_at"]
                    newest_archive = max(archives_with_dates, key=lambda x: x["archived_at"])["archived_at"]
            
            return {
                "total_archived": total_archived,
                "by_status": status_counts,
                "by_operation": operation_counts,
                "oldest_archive": oldest_archive,
                "newest_archive": newest_archive
            }
            
        except Exception as e:
            # Return safe defaults if there's any error
            return {
                "total_archived": 0,
                "by_status": {},
                "by_operation": {},
                "oldest_archive": None,
                "newest_archive": None,
                "error": str(e)
            }
    
    def cleanup_expired_archives(self) -> Dict[str, int]:
        """Clean up expired archived documents"""
        results = {"checked": 0, "purged": 0, "errors": 0}
        
        # Find all archived documents
        archives = self.db_engine.find(self.metadata_collection, {"status": "archived"})
        
        for archive_doc in archives:
            results["checked"] += 1
            
            try:
                metadata = ArchiveMetadata.from_dict(archive_doc)
                policy = self.get_archive_policy(metadata.original_collection)
                
                if policy.should_purge(metadata):
                    # Purge the document
                    self._purge_archive(metadata)
                    results["purged"] += 1
                    
            except Exception:
                results["errors"] += 1
        
        return results
    
    def _get_archive_collection_name(self, collection: str) -> str:
        """Get archive collection name"""
        return f"{self.archive_prefix}{collection}"
    
    def _prepare_document_for_archive(self, document: Dict[str, Any], 
                                    metadata: ArchiveMetadata) -> Dict[str, Any]:
        """Prepare document for archival"""
        archive_doc = document.copy()
        
        # Add archive metadata to document
        archive_doc["_archive_metadata"] = {
            "archive_id": metadata.archive_id,
            "original_id": metadata.original_id,
            "original_collection": metadata.original_collection,
            "archived_at": metadata.archived_at.isoformat(),
            "archived_by": metadata.archived_by,
            "reason": metadata.reason,
            "operation": metadata.operation.value
        }
        
        # Ensure document has an _id for archive collection
        if "_id" not in archive_doc:
            archive_doc["_id"] = metadata.archive_id
        else:
            archive_doc["_original_id"] = archive_doc["_id"]
            archive_doc["_id"] = metadata.archive_id
        
        return archive_doc
    
    def _prepare_document_for_restoration(self, archive_document: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare archived document for restoration"""
        restored_doc = archive_document.copy()
        
        # Remove archive metadata
        if "_archive_metadata" in restored_doc:
            del restored_doc["_archive_metadata"]
        
        # Restore original _id if it was changed
        if "_original_id" in restored_doc:
            restored_doc["_id"] = restored_doc["_original_id"]
            del restored_doc["_original_id"]
        elif "_id" in restored_doc:
            # Generate new ID for restoration
            del restored_doc["_id"]
        
        return restored_doc
    
    def _calculate_hash(self, document: Dict[str, Any]) -> str:
        """Calculate hash of document for integrity checking"""
        # Remove volatile fields
        doc_copy = document.copy()
        volatile_fields = ["_id", "_archive_metadata", "last_modified", "updated_at"]
        for field in volatile_fields:
            doc_copy.pop(field, None)
        
        # Create deterministic hash
        doc_str = json.dumps(doc_copy, sort_keys=True, default=str)
        return hashlib.sha256(doc_str.encode()).hexdigest()
    
    def _verify_document_integrity(self, archive_document: Dict[str, Any], 
                                 metadata: ArchiveMetadata) -> bool:
        """Verify document integrity"""
        current_hash = self._calculate_hash(archive_document)
        return current_hash == metadata.archive_hash
    
    def _purge_archive(self, metadata: ArchiveMetadata):
        """Permanently purge archived document"""
        archive_collection = self._get_archive_collection_name(metadata.original_collection)
        
        # Delete from archive collection
        self.db_engine.delete_one(archive_collection, {"_archive_metadata.archive_id": metadata.archive_id})
        
        # Update metadata status
        self.db_engine.update_one(
            self.metadata_collection,
            {"archive_id": metadata.archive_id},
            {"$set": {"status": ArchiveStatus.PURGED.value, "purged_at": datetime.now().isoformat()}}
        )
        
        # Log audit event
        self._log_audit_event(
            ArchiveOperation.DELETE,
            metadata.original_collection,
            metadata.original_id,
            metadata.archive_id,
            "system",
            "Archive purged due to policy"
        )
    
    def _log_audit_event(self, operation: ArchiveOperation, collection: str, 
                        original_id: str, archive_id: str, user_id: str, reason: str):
        """Log archive audit event"""
        audit_event = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation.value,
            "collection": collection,
            "original_id": original_id,
            "archive_id": archive_id,
            "user_id": user_id,
            "reason": reason,
            "event_id": str(uuid.uuid4())
        }
        
        self.db_engine.insert_one(self.audit_collection, audit_event)


# Factory function for creating archive engine with default policies
def create_archive_engine(db_engine) -> ArchiveEngine:
    """Create archive engine with sensible default policies"""
    engine = ArchiveEngine(db_engine)
    
    # Default policies for common collections
    default_policies = {
        "users": ArchivePolicy(
            collection="users",
            retention_days=365 * 7,  # 7 years
            archive_on_delete=True,
            allow_purge=False,
            compliance_requirements=["gdpr", "sox"]
        ),
        "transactions": ArchivePolicy(
            collection="transactions",
            retention_days=365 * 10,  # 10 years
            archive_on_delete=True,
            allow_purge=False,
            compliance_requirements=["sox", "pci"]
        ),
        "audit_logs": ArchivePolicy(
            collection="audit_logs",
            retention_days=90,
            archive_on_delete=True,
            allow_purge=True,
            purge_after_days=365 * 3  # 3 years
        ),
        "temp_data": ArchivePolicy(
            collection="temp_data",
            retention_days=30,
            archive_on_delete=False,
            allow_purge=True,
            purge_after_days=90
        )
    }
    
    for collection, policy in default_policies.items():
        engine.set_archive_policy(collection, policy)
    
    return engine
