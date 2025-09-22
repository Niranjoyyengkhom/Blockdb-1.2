"""
Dynamic ABAC Engine Extensions
=============================

Enhanced ABAC system with dynamic policy evaluation based on data content,
real-time context analysis, and fine-grained data-level access control.
"""

from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, time
import json
import re
from pathlib import Path
from enum import Enum

from .abac_engine import (
    ABACEngine, PolicyStore, AccessRequest, PolicyDecision, Policy, Rule, Condition,
    Attribute, AttributeType, ComparisonOperator, LogicalOperator, PolicyEffect
)


class DataAccessLevel(Enum):
    """Data access levels for fine-grained control"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    UPDATE = "update"
    DELETE = "delete"
    ARCHIVE = "archive"
    ADMIN = "admin"


class ContextType(Enum):
    """Types of dynamic context"""
    TIME_BASED = "time_based"
    LOCATION_BASED = "location_based"
    DATA_BASED = "data_based"
    USER_BASED = "user_based"
    ROLE_BASED = "role_based"
    DEPARTMENT_BASED = "department_based"
    PROJECT_BASED = "project_based"


@dataclass
class DataClassification:
    """Data classification for access control"""
    level: str  # public, internal, confidential, restricted, top_secret
    categories: List[str] = field(default_factory=list)  # pii, financial, medical, etc.
    owner: Optional[str] = None
    department: Optional[str] = None
    project: Optional[str] = None
    retention_period: Optional[int] = None  # days
    compliance_tags: List[str] = field(default_factory=list)  # gdpr, hipaa, sox, etc.


@dataclass
class DynamicContext:
    """Dynamic context for real-time policy evaluation"""
    context_type: ContextType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def is_valid(self) -> bool:
        """Check if context is still valid"""
        if self.expires_at:
            return datetime.now() < self.expires_at
        return True


@dataclass
class DataFilter:
    """Filter for data-level access control"""
    field: str
    operation: str  # mask, redact, filter, transform
    condition: Dict[str, Any]
    replacement: Optional[Any] = None


@dataclass
class PolicyTemplate:
    """Template for creating dynamic policies"""
    template_id: str
    name: str
    description: str
    effect: PolicyEffect
    conditions_template: Dict[str, Any]
    parameters: List[str] = field(default_factory=list)
    
    def instantiate(self, parameters: Dict[str, Any]) -> Policy:
        """Create policy instance from template"""
        # Replace template parameters with actual values
        conditions_json = json.dumps(self.conditions_template)
        for param, value in parameters.items():
            conditions_json = conditions_json.replace(f"{{{param}}}", str(value))
        
        instantiated_conditions = json.loads(conditions_json)
        
        return Policy(
            id=f"{self.template_id}_{hash(str(parameters))}",
            name=f"{self.name} - {parameters}",
            description=self.description,
            effect=self.effect,
            rules=[],  # Would be built from instantiated_conditions
            priority=100,  # Templates get high priority
            tags=[f"template:{self.template_id}"]
        )


class DynamicPolicyEngine:
    """Engine for dynamic policy creation and management"""
    
    def __init__(self):
        self.templates: Dict[str, PolicyTemplate] = {}
        self.context_providers: Dict[ContextType, Callable] = {}
        self.data_classifiers: List[Callable] = []
        self.policy_cache: Dict[str, Policy] = {}
        self.cache_ttl = 300  # 5 minutes
    
    def register_template(self, template: PolicyTemplate):
        """Register a policy template"""
        self.templates[template.template_id] = template
    
    def register_context_provider(self, context_type: ContextType, provider: Callable):
        """Register a dynamic context provider"""
        self.context_providers[context_type] = provider
    
    def register_data_classifier(self, classifier: Callable):
        """Register a data classification function"""
        self.data_classifiers.append(classifier)
    
    def create_dynamic_policy(self, template_id: str, parameters: Dict[str, Any]) -> Optional[Policy]:
        """Create dynamic policy from template"""
        if template_id not in self.templates:
            return None
        
        template = self.templates[template_id]
        return template.instantiate(parameters)
    
    def get_dynamic_context(self, context_type: ContextType, **kwargs) -> Optional[DynamicContext]:
        """Get dynamic context using registered providers"""
        if context_type not in self.context_providers:
            return None
        
        provider = self.context_providers[context_type]
        try:
            data = provider(**kwargs)
            return DynamicContext(context_type=context_type, data=data)
        except Exception:
            return None
    
    def classify_data(self, data: Dict[str, Any]) -> DataClassification:
        """Classify data using registered classifiers"""
        classification = DataClassification(level="internal")
        
        for classifier in self.data_classifiers:
            try:
                result = classifier(data)
                if isinstance(result, DataClassification):
                    # Merge classifications (take the most restrictive)
                    if self._is_more_restrictive(result.level, classification.level):
                        classification.level = result.level
                    classification.categories.extend(result.categories)
                    classification.compliance_tags.extend(result.compliance_tags)
            except Exception:
                continue
        
        return classification
    
    def _is_more_restrictive(self, level1: str, level2: str) -> bool:
        """Check if level1 is more restrictive than level2"""
        levels = ["public", "internal", "confidential", "restricted", "top_secret"]
        return levels.index(level1) > levels.index(level2)


class DataLevelABAC:
    """Data-level ABAC for fine-grained access control"""
    
    def __init__(self, db_engine, abac_engine: ABACEngine):
        self.db_engine = db_engine
        self.abac_engine = abac_engine
        self.data_filters: Dict[str, List[DataFilter]] = {}
        self.field_permissions: Dict[str, Dict[str, DataAccessLevel]] = {}
        
    def set_field_permission(self, collection: str, field: str, role: str, level: DataAccessLevel):
        """Set field-level permissions"""
        if collection not in self.field_permissions:
            self.field_permissions[collection] = {}
        self.field_permissions[collection][f"{role}:{field}"] = level
    
    def add_data_filter(self, collection: str, data_filter: DataFilter):
        """Add data filter for collection"""
        if collection not in self.data_filters:
            self.data_filters[collection] = []
        self.data_filters[collection].append(data_filter)
    
    def filter_documents(self, collection: str, documents: List[Dict[str, Any]], 
                        user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply data-level filtering to documents"""
        if not documents:
            return documents
        
        filtered_documents = []
        
        for doc in documents:
            filtered_doc = self._filter_single_document(collection, doc, user_context)
            if filtered_doc:
                filtered_documents.append(filtered_doc)
        
        return filtered_documents
    
    def _filter_single_document(self, collection: str, document: Dict[str, Any], 
                               user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter a single document based on policies"""
        user_roles = user_context.get("roles", [])
        filtered_doc = document.copy()
        
        # Apply field-level permissions
        for field in list(filtered_doc.keys()):
            can_access = False
            
            for role in user_roles:
                permission_key = f"{role}:{field}"
                if collection in self.field_permissions:
                    permission = self.field_permissions[collection].get(permission_key)
                    if permission and permission != DataAccessLevel.NONE:
                        can_access = True
                        break
            
            if not can_access:
                # Check if field should be masked or removed
                if self._should_mask_field(collection, field, user_context):
                    filtered_doc[field] = "***MASKED***"
                else:
                    del filtered_doc[field]
        
        # Apply data filters
        if collection in self.data_filters:
            for data_filter in self.data_filters[collection]:
                filtered_doc = self._apply_data_filter(filtered_doc, data_filter, user_context)
                if not filtered_doc:
                    return None
        
        return filtered_doc
    
    def _should_mask_field(self, collection: str, field: str, user_context: Dict[str, Any]) -> bool:
        """Determine if field should be masked instead of removed"""
        # Check for PII or sensitive data patterns
        sensitive_patterns = [
            r'.*ssn.*', r'.*social.*', r'.*passport.*', r'.*credit.*', r'.*card.*',
            r'.*password.*', r'.*secret.*', r'.*key.*', r'.*token.*'
        ]
        
        field_lower = field.lower()
        for pattern in sensitive_patterns:
            if re.match(pattern, field_lower):
                return True
        
        return False
    
    def _apply_data_filter(self, document: Dict[str, Any], data_filter: DataFilter, 
                          user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply a specific data filter"""
        if data_filter.field not in document:
            return document
        
        field_value = document[data_filter.field]
        
        # Evaluate filter condition
        if not self._evaluate_filter_condition(document, data_filter.condition, user_context):
            return document
        
        # Apply filter operation
        if data_filter.operation == "mask":
            document[data_filter.field] = self._mask_value(field_value)
        elif data_filter.operation == "redact":
            document[data_filter.field] = "[REDACTED]"
        elif data_filter.operation == "filter":
            return None  # Filter out entire document
        elif data_filter.operation == "transform":
            document[data_filter.field] = self._transform_value(field_value, data_filter.replacement)
        
        return document
    
    def _evaluate_filter_condition(self, document: Dict[str, Any], condition: Dict[str, Any], 
                                  user_context: Dict[str, Any]) -> bool:
        """Evaluate filter condition"""
        # Simplified condition evaluation
        for field, value in condition.items():
            if field in document:
                if document[field] != value:
                    return False
            elif field in user_context:
                if user_context[field] != value:
                    return False
        return True
    
    def _mask_value(self, value: Any) -> str:
        """Mask a value"""
        if isinstance(value, str):
            if len(value) <= 4:
                return "*" * len(value)
            else:
                return value[:2] + "*" * (len(value) - 4) + value[-2:]
        else:
            return "***"
    
    def _transform_value(self, value: Any, replacement: Any) -> Any:
        """Transform a value"""
        if replacement is not None:
            return replacement
        return value


class ComplianceEngine:
    """Engine for ensuring regulatory compliance"""
    
    def __init__(self):
        self.compliance_rules: Dict[str, List[Callable]] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.retention_policies: Dict[str, int] = {}  # collection -> days
        
    def register_compliance_rule(self, regulation: str, rule: Callable):
        """Register a compliance rule"""
        if regulation not in self.compliance_rules:
            self.compliance_rules[regulation] = []
        self.compliance_rules[regulation].append(rule)
    
    def set_retention_policy(self, collection: str, days: int):
        """Set data retention policy"""
        self.retention_policies[collection] = days
    
    def check_compliance(self, operation: str, collection: str, data: Dict[str, Any], 
                        user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance for an operation"""
        violations = []
        warnings = []
        
        # Check all applicable compliance rules
        for regulation, rules in self.compliance_rules.items():
            for rule in rules:
                try:
                    result = rule(operation, collection, data, user_context)
                    if result.get("violation"):
                        violations.append({
                            "regulation": regulation,
                            "message": result.get("message", "Compliance violation")
                        })
                    elif result.get("warning"):
                        warnings.append({
                            "regulation": regulation,
                            "message": result.get("message", "Compliance warning")
                        })
                except Exception as e:
                    warnings.append({
                        "regulation": regulation,
                        "message": f"Compliance check failed: {str(e)}"
                    })
        
        # Log audit event
        self._log_audit_event(operation, collection, data, user_context, violations, warnings)
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings
        }
    
    def _log_audit_event(self, operation: str, collection: str, data: Dict[str, Any], 
                        user_context: Dict[str, Any], violations: List[Dict], warnings: List[Dict]):
        """Log audit event"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "collection": collection,
            "user": user_context.get("user_id", "unknown"),
            "roles": user_context.get("roles", []),
            "data_size": len(str(data)),
            "violations": len(violations),
            "warnings": len(warnings),
            "compliant": len(violations) == 0
        }
        
        self.audit_log.append(audit_entry)
        
        # Keep only last 10000 entries
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]
    
    def get_audit_report(self, start_date: Optional[datetime] = None, 
                        end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate audit report"""
        filtered_entries = self.audit_log
        
        if start_date or end_date:
            filtered_entries = []
            for entry in self.audit_log:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if start_date and entry_time < start_date:
                    continue
                if end_date and entry_time > end_date:
                    continue
                filtered_entries.append(entry)
        
        total_operations = len(filtered_entries)
        violations = sum(1 for e in filtered_entries if e["violations"] > 0)
        warnings = sum(1 for e in filtered_entries if e["warnings"] > 0)
        
        return {
            "period": {
                "start": start_date.isoformat() if start_date else "all",
                "end": end_date.isoformat() if end_date else "all"
            },
            "total_operations": total_operations,
            "violations": violations,
            "warnings": warnings,
            "compliance_rate": (total_operations - violations) / total_operations if total_operations > 0 else 1.0,
            "entries": filtered_entries
        }


class EnhancedABACEngine(ABACEngine):
    """Enhanced ABAC engine with dynamic policies and data-level control"""
    
    def __init__(self, policy_store: Optional[PolicyStore] = None):
        super().__init__(policy_store)
        self.dynamic_engine = DynamicPolicyEngine()
        self.data_abac = None  # Will be set when db_engine is available
        self.compliance_engine = ComplianceEngine()
        self.time_based_policies: Dict[str, Policy] = {}
        
        # Register default context providers
        self._register_default_context_providers()
        self._register_default_data_classifiers()
        self._register_default_compliance_rules()
    
    def set_db_engine(self, db_engine):
        """Set the database engine for data-level ABAC"""
        self.data_abac = DataLevelABAC(db_engine, self)
    
    def evaluate_request_with_data(self, request: AccessRequest, data: Optional[Dict[str, Any]] = None) -> PolicyDecision:
        """Evaluate request with dynamic data context"""
        # Get base decision
        base_decision = self.evaluate_request(request)
        
        # Check compliance
        if data:
            user_context = {
                "user_id": request.subject_attributes.get("user_id", {}).value,
                "roles": request.subject_attributes.get("roles", {}).value or []
            }
            
            compliance_result = self.compliance_engine.check_compliance(
                request.action_attributes.get("action_type", {}).value or "unknown",
                request.resource_attributes.get("resource_name", {}).value or "unknown",
                data,
                user_context
            )
            
            if not compliance_result["compliant"]:
                return PolicyDecision(
                    decision=PolicyEffect.DENY,
                    applied_policies=base_decision.applied_policies,
                    reason=f"Compliance violation: {', '.join([v['message'] for v in compliance_result['violations']])}"
                )
        
        # Add dynamic context evaluation
        dynamic_policies = self._get_applicable_dynamic_policies(request, data)
        
        # Combine decisions
        all_policies = base_decision.applied_policies + [p.id for p in dynamic_policies]
        
        # Re-evaluate with dynamic policies
        if dynamic_policies:
            for policy in dynamic_policies:
                if policy.evaluate(request.get_all_attributes()):
                    if policy.effect == PolicyEffect.DENY:
                        return PolicyDecision(
                            decision=PolicyEffect.DENY,
                            applied_policies=all_policies,
                            reason=f"Dynamic policy denied access: {policy.name}"
                        )
        
        return PolicyDecision(
            decision=base_decision.decision,
            applied_policies=all_policies,
            reason=base_decision.reason
        )
    
    def filter_data_for_user(self, collection: str, documents: List[Dict[str, Any]], 
                           user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter documents based on user's data access permissions"""
        if not self.data_abac:
            return documents
        
        return self.data_abac.filter_documents(collection, documents, user_context)
    
    def _get_applicable_dynamic_policies(self, request: AccessRequest, 
                                       data: Optional[Dict[str, Any]]) -> List[Policy]:
        """Get applicable dynamic policies"""
        dynamic_policies = []
        
        # Time-based policies
        current_time = datetime.now().time()
        for policy_id, policy in self.time_based_policies.items():
            # Check if policy applies at current time
            if self._is_time_policy_active(policy, current_time):
                dynamic_policies.append(policy)
        
        # Data-based policies
        if data:
            classification = self.dynamic_engine.classify_data(data)
            data_policies = self._get_data_classification_policies(classification)
            dynamic_policies.extend(data_policies)
        
        return dynamic_policies
    
    def _is_time_policy_active(self, policy: Policy, current_time: time) -> bool:
        """Check if time-based policy is currently active"""
        # Simplified time-based policy check
        # In practice, this would check policy tags or rules for time constraints
        return True
    
    def _get_data_classification_policies(self, classification: DataClassification) -> List[Policy]:
        """Get policies based on data classification"""
        policies = []
        
        # Create dynamic policies based on classification
        if classification.level == "confidential":
            policy = Policy(
                id=f"confidential_data_{datetime.now().timestamp()}",
                name="Confidential Data Access",
                description="Dynamic policy for confidential data",
                effect=PolicyEffect.DENY,
                rules=[],
                priority=200
            )
            policies.append(policy)
        
        return policies
    
    def _register_default_context_providers(self):
        """Register default context providers"""
        def time_context(**kwargs):
            now = datetime.now()
            return {
                "hour": now.hour,
                "day_of_week": now.weekday(),
                "is_business_hours": 9 <= now.hour <= 17 and now.weekday() < 5
            }
        
        def location_context(**kwargs):
            ip = kwargs.get("ip", "unknown")
            # Simplified location detection
            return {
                "ip": ip,
                "is_internal": ip.startswith("192.168.") or ip.startswith("10."),
                "country": "unknown"
            }
        
        self.dynamic_engine.register_context_provider(ContextType.TIME_BASED, time_context)
        self.dynamic_engine.register_context_provider(ContextType.LOCATION_BASED, location_context)
    
    def _register_default_data_classifiers(self):
        """Register default data classifiers"""
        def pii_classifier(data: Dict[str, Any]) -> DataClassification:
            classification = DataClassification(level="internal")
            
            # Check for PII patterns
            pii_patterns = {
                "ssn": r'\d{3}-?\d{2}-?\d{4}',
                "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                "phone": r'\d{3}-?\d{3}-?\d{4}',
                "credit_card": r'\d{4}-?\d{4}-?\d{4}-?\d{4}'
            }
            
            data_str = str(data).lower()
            
            for pii_type, pattern in pii_patterns.items():
                if re.search(pattern, data_str):
                    classification.categories.append(pii_type)
                    classification.level = "confidential"
                    classification.compliance_tags.append("gdpr")
            
            return classification
        
        self.dynamic_engine.register_data_classifier(pii_classifier)
    
    def _register_default_compliance_rules(self):
        """Register default compliance rules"""
        def gdpr_rule(operation: str, collection: str, data: Dict[str, Any], user_context: Dict[str, Any]):
            # Check for PII processing without consent
            if "email" in str(data).lower() or "personal" in collection.lower():
                if operation in ["insert", "update"] and not user_context.get("gdpr_consent"):
                    return {"violation": True, "message": "GDPR: PII processing requires explicit consent"}
            return {"violation": False}
        
        def retention_rule(operation: str, collection: str, data: Dict[str, Any], user_context: Dict[str, Any]):
            # Check data retention policies
            if collection in self.compliance_engine.retention_policies:
                retention_days = self.compliance_engine.retention_policies[collection]
                if "created_at" in data:
                    created_date = data["created_at"]
                    if isinstance(created_date, str):
                        created_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    
                    age = (datetime.now() - created_date).days
                    if age > retention_days:
                        return {"warning": True, "message": f"Data exceeds retention policy ({retention_days} days)"}
            return {"violation": False}
        
        self.compliance_engine.register_compliance_rule("gdpr", gdpr_rule)
        self.compliance_engine.register_compliance_rule("retention", retention_rule)


# Factory function for creating pre-configured ABAC engine
def create_enhanced_abac_engine(db_engine=None) -> EnhancedABACEngine:
    """Create a fully configured enhanced ABAC engine"""
    policy_store = PolicyStore()
    engine = EnhancedABACEngine(policy_store)
    
    if db_engine:
        engine.set_db_engine(db_engine)
    
    # Add default field permissions
    if engine.data_abac:
        # Example field permissions
        engine.data_abac.set_field_permission("users", "ssn", "admin", DataAccessLevel.READ)
        engine.data_abac.set_field_permission("users", "ssn", "user", DataAccessLevel.NONE)
        engine.data_abac.set_field_permission("users", "email", "admin", DataAccessLevel.READ)
        engine.data_abac.set_field_permission("users", "email", "user", DataAccessLevel.READ)
    
    # Set retention policies
    engine.compliance_engine.set_retention_policy("users", 2555)  # 7 years
    engine.compliance_engine.set_retention_policy("audit_logs", 90)  # 90 days
    
    return engine
