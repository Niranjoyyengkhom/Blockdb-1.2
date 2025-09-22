"""
BASIC Compliance and Audit System
================================

Comprehensive compliance system implementing Banking, Accounting, Securities, Insurance, 
and Core (BASIC) regulatory requirements with transaction logging, audit trails, 
data integrity checks, and automated compliance reporting.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import uuid
from pathlib import Path
import logging


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    SOX = "sox"              # Sarbanes-Oxley Act
    GDPR = "gdpr"            # General Data Protection Regulation
    HIPAA = "hipaa"          # Health Insurance Portability and Accountability Act
    PCI_DSS = "pci_dss"      # Payment Card Industry Data Security Standard
    BASEL_III = "basel_iii"  # Basel III banking regulations
    IFRS = "ifrs"            # International Financial Reporting Standards
    GAAP = "gaap"            # Generally Accepted Accounting Principles
    COSO = "coso"            # Committee of Sponsoring Organizations
    COBIT = "cobit"          # Control Objectives for Information Technologies


class AuditEventType(Enum):
    """Types of audit events"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ARCHIVE = "archive"
    RESTORE = "restore"
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    BACKUP = "backup"
    RESTORE_BACKUP = "restore_backup"
    CONFIG_CHANGE = "config_change"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_CHECK = "compliance_check"
    POLICY_VIOLATION = "policy_violation"


class RiskLevel(Enum):
    """Risk levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TransactionStatus(Enum):
    """Transaction processing status"""
    INITIATED = "initiated"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    ARCHIVED = "archived"


@dataclass
class AuditEvent:
    """Comprehensive audit event record"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: AuditEventType = AuditEventType.READ
    user_id: str = "system"
    session_id: Optional[str] = None
    ip_address: str = "unknown"
    user_agent: Optional[str] = None
    resource_type: str = ""
    resource_id: str = ""
    collection: Optional[str] = None
    operation: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    risk_level: RiskLevel = RiskLevel.LOW
    compliance_frameworks: List[ComplianceFramework] = field(default_factory=list)
    data_classification: str = "internal"
    retention_period: int = 2555  # 7 years in days
    hash_signature: str = ""
    parent_transaction_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Generate hash signature after initialization"""
        if not self.hash_signature:
            self.hash_signature = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate cryptographic hash for integrity verification"""
        data = {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "operation": self.operation,
            "details": self.details,
            "success": self.success
        }
        
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "collection": self.collection,
            "operation": self.operation,
            "details": self.details,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "risk_level": self.risk_level.value,
            "compliance_frameworks": [f.value for f in self.compliance_frameworks],
            "data_classification": self.data_classification,
            "retention_period": self.retention_period,
            "hash_signature": self.hash_signature,
            "parent_transaction_id": self.parent_transaction_id,
            "success": self.success,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create from dictionary"""
        event = cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            user_id=data.get("user_id", "system"),
            session_id=data.get("session_id"),
            ip_address=data.get("ip_address", "unknown"),
            user_agent=data.get("user_agent"),
            resource_type=data.get("resource_type", ""),
            resource_id=data.get("resource_id", ""),
            collection=data.get("collection"),
            operation=data.get("operation", ""),
            details=data.get("details", {}),
            before_state=data.get("before_state"),
            after_state=data.get("after_state"),
            data_classification=data.get("data_classification", "internal"),
            retention_period=data.get("retention_period", 2555),
            hash_signature=data.get("hash_signature", ""),
            parent_transaction_id=data.get("parent_transaction_id"),
            success=data.get("success", True),
            error_message=data.get("error_message")
        )
        
        # Set enums
        if data.get("timestamp"):
            event.timestamp = datetime.fromisoformat(data["timestamp"])
        if data.get("event_type"):
            event.event_type = AuditEventType(data["event_type"])
        if data.get("risk_level"):
            event.risk_level = RiskLevel(data["risk_level"])
        if data.get("compliance_frameworks"):
            event.compliance_frameworks = [ComplianceFramework(f) for f in data["compliance_frameworks"]]
        
        return event


@dataclass
class Transaction:
    """Database transaction record for ACID compliance"""
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: TransactionStatus = TransactionStatus.INITIATED
    user_id: str = "system"
    operations: List[Dict[str, Any]] = field(default_factory=list)
    rollback_data: List[Dict[str, Any]] = field(default_factory=list)
    isolation_level: str = "READ_COMMITTED"
    timeout_seconds: int = 300
    locks_acquired: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "transaction_id": self.transaction_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "user_id": self.user_id,
            "operations": self.operations,
            "rollback_data": self.rollback_data,
            "isolation_level": self.isolation_level,
            "timeout_seconds": self.timeout_seconds,
            "locks_acquired": list(self.locks_acquired)
        }


@dataclass
class ComplianceReport:
    """Compliance audit report"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = field(default_factory=datetime.now)
    framework: ComplianceFramework = ComplianceFramework.SOX
    period_start: datetime = field(default_factory=lambda: datetime.now() - timedelta(days=30))
    period_end: datetime = field(default_factory=datetime.now)
    total_events: int = 0
    violations: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    compliance_score: float = 0.0
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    data_integrity_checks: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "framework": self.framework.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_events": self.total_events,
            "violations": self.violations,
            "recommendations": self.recommendations,
            "compliance_score": self.compliance_score,
            "risk_assessment": self.risk_assessment,
            "data_integrity_checks": self.data_integrity_checks
        }


class AuditTrail:
    """Comprehensive audit trail system"""
    
    def __init__(self, db_engine):
        self.db_engine = db_engine
        self.audit_collection = "audit_trail"
        self.transaction_collection = "transactions"
        self.compliance_collection = "compliance_reports"
        self.logger = logging.getLogger(__name__)
        
        # Initialize collections
        self._initialize_audit_collections()
    
    def _initialize_audit_collections(self):
        """Initialize audit-related collections and indexes"""
        # Create indexes for performance
        self.db_engine.create_index(self.audit_collection, [("timestamp", -1)])
        self.db_engine.create_index(self.audit_collection, [("user_id", 1)])
        self.db_engine.create_index(self.audit_collection, [("event_type", 1)])
        self.db_engine.create_index(self.audit_collection, [("resource_type", 1)])
        self.db_engine.create_index(self.audit_collection, [("collection", 1)])
        self.db_engine.create_index(self.audit_collection, [("risk_level", 1)])
        self.db_engine.create_index(self.audit_collection, [("compliance_frameworks", 1)])
        self.db_engine.create_index(self.audit_collection, [("hash_signature", 1)])
        
        self.db_engine.create_index(self.transaction_collection, [("transaction_id", 1)])
        self.db_engine.create_index(self.transaction_collection, [("started_at", -1)])
        self.db_engine.create_index(self.transaction_collection, [("status", 1)])
        self.db_engine.create_index(self.transaction_collection, [("user_id", 1)])
    
    def log_event(self, event: AuditEvent) -> str:
        """Log an audit event"""
        try:
            # Store the event
            self.db_engine.insert_one(self.audit_collection, event.to_dict())
            
            # Check for compliance violations
            self._check_real_time_compliance(event)
            
            return event.event_id
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
            raise
    
    def log_database_operation(self, operation: str, collection: str, user_id: str,
                             before_state: Optional[Dict[str, Any]] = None,
                             after_state: Optional[Dict[str, Any]] = None,
                             session_context: Optional[Dict[str, Any]] = None) -> str:
        """Log a database operation with full audit details"""
        
        # Determine event type
        event_type_map = {
            "insert": AuditEventType.CREATE,
            "find": AuditEventType.READ,
            "update": AuditEventType.UPDATE,
            "delete": AuditEventType.DELETE,
            "archive": AuditEventType.ARCHIVE,
            "restore": AuditEventType.RESTORE
        }
        event_type = event_type_map.get(operation.lower(), AuditEventType.READ)
        
        # Determine risk level
        risk_level = self._assess_risk_level(operation, collection, before_state, after_state)
        
        # Determine applicable compliance frameworks
        frameworks = self._determine_compliance_frameworks(collection, before_state, after_state)
        
        # Create audit event
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            session_id=session_context.get("session_id") if session_context else None,
            ip_address=session_context.get("ip_address", "unknown") if session_context else "unknown",
            user_agent=session_context.get("user_agent") if session_context else None,
            resource_type="collection",
            resource_id=collection,
            collection=collection,
            operation=operation,
            details=session_context or {},
            before_state=before_state,
            after_state=after_state,
            risk_level=risk_level,
            compliance_frameworks=frameworks,
            data_classification=self._classify_data(collection, before_state, after_state)
        )
        
        return self.log_event(event)
    
    def start_transaction(self, user_id: str, isolation_level: str = "READ_COMMITTED") -> str:
        """Start a new transaction"""
        transaction = Transaction(
            user_id=user_id,
            isolation_level=isolation_level
        )
        
        # Store transaction
        self.db_engine.insert_one(self.transaction_collection, transaction.to_dict())
        
        # Log transaction start
        self.log_event(AuditEvent(
            event_type=AuditEventType.CREATE,
            user_id=user_id,
            resource_type="transaction",
            resource_id=transaction.transaction_id,
            operation="start_transaction",
            details={"isolation_level": isolation_level}
        ))
        
        return transaction.transaction_id
    
    def complete_transaction(self, transaction_id: str, status: TransactionStatus) -> bool:
        """Complete a transaction"""
        try:
            # Update transaction status
            self.db_engine.update_one(
                self.transaction_collection,
                {"transaction_id": transaction_id},
                {
                    "$set": {
                        "status": status.value,
                        "completed_at": datetime.now().isoformat()
                    }
                }
            )
            
            # Get transaction details
            transaction_doc = self.db_engine.find_one(
                self.transaction_collection, 
                {"transaction_id": transaction_id}
            )
            
            if transaction_doc:
                # Log transaction completion
                self.log_event(AuditEvent(
                    event_type=AuditEventType.UPDATE,
                    user_id=transaction_doc.get("user_id", "system"),
                    resource_type="transaction",
                    resource_id=transaction_id,
                    operation="complete_transaction",
                    details={"status": status.value, "operations_count": len(transaction_doc.get("operations", []))}
                ))
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to complete transaction {transaction_id}: {e}")
            return False
    
    def verify_audit_integrity(self, start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Verify integrity of audit trail"""
        filter_dict = {}
        
        if start_date:
            filter_dict["timestamp"] = {"$gte": start_date.isoformat()}
        if end_date:
            if "timestamp" not in filter_dict:
                filter_dict["timestamp"] = {}
            filter_dict["timestamp"]["$lte"] = end_date.isoformat()
        
        events_result = self.db_engine.find(self.audit_collection, filter_dict)
        
        # Handle different return types from db_engine.find
        if isinstance(events_result, dict) and "documents" in events_result:
            events = events_result["documents"]
        elif isinstance(events_result, list):
            events = events_result
        else:
            events = []
        
        total_events = 0
        integrity_violations = []
        
        for event_doc in events:
            total_events += 1
            
            # Handle case where event_doc might be a string (JSON) or dict
            if isinstance(event_doc, str):
                try:
                    import json
                    event_doc = json.loads(event_doc)
                except (json.JSONDecodeError, TypeError):
                    continue
            
            if not isinstance(event_doc, dict):
                continue
            
            # Recreate event to verify hash
            try:
                event = AuditEvent.from_dict(event_doc)
                expected_hash = event._generate_hash()
                
                if event.hash_signature != expected_hash:
                    integrity_violations.append({
                        "event_id": event.event_id,
                        "timestamp": event.timestamp.isoformat(),
                        "expected_hash": expected_hash,
                        "actual_hash": event.hash_signature,
                        "user_id": event.user_id
                    })
            except Exception as e:
                # Skip events that can't be processed
                continue
        
        return {
            "total_events_checked": total_events,
            "integrity_violations": len(integrity_violations),
            "violations_details": integrity_violations,
            "integrity_score": (total_events - len(integrity_violations)) / total_events if total_events > 0 else 1.0
        }
    
    def generate_compliance_report(self, framework: ComplianceFramework,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> ComplianceReport:
        """Generate comprehensive compliance report"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # Get relevant audit events
        filter_dict = {
            "timestamp": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            },
            "compliance_frameworks": framework.value
        }
        
        events = list(self.db_engine.find(self.audit_collection, filter_dict))
        
        # Analyze events for compliance
        violations = self._analyze_compliance_violations(framework, events)
        recommendations = self._generate_compliance_recommendations(framework, violations)
        compliance_score = self._calculate_compliance_score(events, violations)
        risk_assessment = self._assess_compliance_risks(events, violations)
        data_integrity = self.verify_audit_integrity(start_date, end_date)
        
        report = ComplianceReport(
            framework=framework,
            period_start=start_date,
            period_end=end_date,
            total_events=len(events),
            violations=violations,
            recommendations=recommendations,
            compliance_score=compliance_score,
            risk_assessment=risk_assessment,
            data_integrity_checks=data_integrity
        )
        
        # Store the report
        self.db_engine.insert_one(self.compliance_collection, report.to_dict())
        
        return report
    
    def _assess_risk_level(self, operation: str, collection: str,
                          before_state: Optional[Dict[str, Any]],
                          after_state: Optional[Dict[str, Any]]) -> RiskLevel:
        """Assess risk level of an operation"""
        
        # High-risk operations
        if operation.lower() in ["delete", "drop", "truncate"]:
            return RiskLevel.HIGH
        
        # High-risk collections
        if collection.lower() in ["users", "accounts", "transactions", "payments"]:
            if operation.lower() in ["update", "create"]:
                return RiskLevel.MEDIUM
        
        # Check for sensitive data changes
        if before_state and after_state:
            sensitive_fields = ["password", "ssn", "credit_card", "account_number", "salary"]
            for field in sensitive_fields:
                if field in str(before_state).lower() or field in str(after_state).lower():
                    return RiskLevel.HIGH
        
        return RiskLevel.LOW
    
    def _determine_compliance_frameworks(self, collection: str,
                                       before_state: Optional[Dict[str, Any]],
                                       after_state: Optional[Dict[str, Any]]) -> List[ComplianceFramework]:
        """Determine applicable compliance frameworks"""
        frameworks = []
        
        # Financial data
        if any(keyword in collection.lower() for keyword in ["account", "transaction", "payment", "financial"]):
            frameworks.extend([ComplianceFramework.SOX, ComplianceFramework.GAAP])
        
        # Personal data
        if any(keyword in collection.lower() for keyword in ["user", "customer", "personal", "employee"]):
            frameworks.append(ComplianceFramework.GDPR)
        
        # Health data
        if any(keyword in collection.lower() for keyword in ["health", "medical", "patient"]):
            frameworks.append(ComplianceFramework.HIPAA)
        
        # Payment data
        data_str = str(before_state) + str(after_state)
        if any(keyword in data_str.lower() for keyword in ["credit_card", "card_number", "payment"]):
            frameworks.append(ComplianceFramework.PCI_DSS)
        
        # Default to SOX for audit purposes
        if not frameworks:
            frameworks.append(ComplianceFramework.SOX)
        
        return frameworks
    
    def _classify_data(self, collection: str,
                      before_state: Optional[Dict[str, Any]],
                      after_state: Optional[Dict[str, Any]]) -> str:
        """Classify data sensitivity level"""
        
        data_str = str(before_state) + str(after_state) + collection
        data_lower = data_str.lower()
        
        # Top secret
        if any(keyword in data_lower for keyword in ["salary", "ssn", "tax_id", "bank_account"]):
            return "top_secret"
        
        # Confidential
        if any(keyword in data_lower for keyword in ["password", "credit_card", "medical", "personal"]):
            return "confidential"
        
        # Restricted
        if any(keyword in data_lower for keyword in ["financial", "transaction", "account"]):
            return "restricted"
        
        # Internal
        if any(keyword in data_lower for keyword in ["user", "customer", "employee"]):
            return "internal"
        
        return "public"
    
    def _check_real_time_compliance(self, event: AuditEvent):
        """Check for real-time compliance violations"""
        # Check for suspicious patterns
        recent_events = self._get_recent_events_by_user(event.user_id, timedelta(minutes=5))
        
        if len(recent_events) > 100:  # Too many operations in short time
            self.log_event(AuditEvent(
                event_type=AuditEventType.SECURITY_EVENT,
                user_id=event.user_id,
                resource_type="security",
                resource_id="rate_limit",
                operation="excessive_operations",
                details={"event_count": len(recent_events), "trigger_event": event.event_id},
                risk_level=RiskLevel.HIGH
            ))
    
    def _get_recent_events_by_user(self, user_id: str, time_window: timedelta) -> List[Dict[str, Any]]:
        """Get recent events by user within time window"""
        since = datetime.now() - time_window
        return list(self.db_engine.find(self.audit_collection, {
            "user_id": user_id,
            "timestamp": {"$gte": since.isoformat()}
        }))
    
    def _analyze_compliance_violations(self, framework: ComplianceFramework,
                                     events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze events for compliance violations"""
        violations = []
        
        if framework == ComplianceFramework.SOX:
            violations.extend(self._check_sox_violations(events))
        elif framework == ComplianceFramework.GDPR:
            violations.extend(self._check_gdpr_violations(events))
        elif framework == ComplianceFramework.PCI_DSS:
            violations.extend(self._check_pci_violations(events))
        
        return violations
    
    def _check_sox_violations(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for SOX compliance violations"""
        violations = []
        
        # Check for unauthorized financial data access
        for event in events:
            if (event.get("collection", "").lower() in ["transactions", "accounts", "financial"] and
                event.get("event_type") in ["update", "delete"] and
                event.get("risk_level") == "high"):
                
                violations.append({
                    "type": "unauthorized_financial_modification",
                    "event_id": event.get("event_id"),
                    "description": "High-risk modification to financial data",
                    "severity": "high",
                    "recommendation": "Review authorization and implement additional controls"
                })
        
        return violations
    
    def _check_gdpr_violations(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for GDPR compliance violations"""
        violations = []
        
        # Check for personal data processing without consent logging
        for event in events:
            if (event.get("data_classification") in ["confidential", "restricted"] and
                "consent" not in str(event.get("details", {})).lower()):
                
                violations.append({
                    "type": "personal_data_processing_without_consent",
                    "event_id": event.get("event_id"),
                    "description": "Processing of personal data without documented consent",
                    "severity": "medium",
                    "recommendation": "Ensure consent is documented for all personal data processing"
                })
        
        return violations
    
    def _check_pci_violations(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for PCI DSS compliance violations"""
        violations = []
        
        # Check for credit card data access
        for event in events:
            event_str = str(event).lower()
            if any(keyword in event_str for keyword in ["credit_card", "card_number", "cvv", "payment"]):
                violations.append({
                    "type": "payment_card_data_access",
                    "event_id": event.get("event_id"),
                    "description": "Access to payment card data detected",
                    "severity": "high",
                    "recommendation": "Ensure PCI DSS controls are in place for card data"
                })
        
        return violations
    
    def _generate_compliance_recommendations(self, framework: ComplianceFramework,
                                           violations: List[Dict[str, Any]]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        if violations:
            recommendations.append("Address identified compliance violations immediately")
            recommendations.append("Review and update access controls")
            recommendations.append("Implement additional monitoring for high-risk operations")
        
        if framework == ComplianceFramework.SOX:
            recommendations.extend([
                "Ensure segregation of duties for financial operations",
                "Implement change management controls",
                "Regular review of user access to financial systems"
            ])
        elif framework == ComplianceFramework.GDPR:
            recommendations.extend([
                "Document consent for all personal data processing",
                "Implement data minimization principles",
                "Ensure data subject rights are respected"
            ])
        
        return recommendations
    
    def _calculate_compliance_score(self, events: List[Dict[str, Any]],
                                  violations: List[Dict[str, Any]]) -> float:
        """Calculate compliance score (0-100)"""
        if not events:
            return 100.0
        
        total_events = len(events)
        violation_count = len(violations)
        
        # Weight violations by severity
        weighted_violations = 0
        for violation in violations:
            severity = violation.get("severity", "low")
            if severity == "critical":
                weighted_violations += 4
            elif severity == "high":
                weighted_violations += 3
            elif severity == "medium":
                weighted_violations += 2
            else:
                weighted_violations += 1
        
        # Calculate score
        max_possible_score = total_events * 4  # Assuming all could be critical
        actual_violations = min(weighted_violations, max_possible_score)
        
        score = ((max_possible_score - actual_violations) / max_possible_score) * 100
        return round(score, 2)
    
    def _assess_compliance_risks(self, events: List[Dict[str, Any]],
                               violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess compliance risks"""
        risk_levels = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for event in events:
            risk_level = event.get("risk_level", "low")
            risk_levels[risk_level] += 1
        
        total_events = len(events)
        
        return {
            "risk_distribution": risk_levels,
            "high_risk_percentage": (risk_levels["high"] + risk_levels["critical"]) / total_events * 100 if total_events > 0 else 0,
            "violation_rate": len(violations) / total_events * 100 if total_events > 0 else 0,
            "recommendations_count": len(violations),
            "overall_risk": "high" if risk_levels["high"] + risk_levels["critical"] > total_events * 0.1 else "medium" if risk_levels["medium"] > total_events * 0.2 else "low"
        }


# Factory function for creating audit trail system
def create_audit_trail(db_engine) -> AuditTrail:
    """Create comprehensive audit trail system"""
    return AuditTrail(db_engine)
