"""
Attribute-Based Access Control (ABAC) Engine
============================================

A comprehensive ABAC implementation for fine-grained access control
with support for policies, attributes, and dynamic decision making.
"""

from typing import Dict, List, Optional, Any, Set, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import re
from pathlib import Path


class PolicyEffect(Enum):
    """Policy decision effects"""
    ALLOW = "allow"
    DENY = "deny"


class AttributeType(Enum):
    """Supported attribute types"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    LIST = "list"
    OBJECT = "object"


class ComparisonOperator(Enum):
    """Comparison operators for attribute evaluation"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    EXISTS = "exists"


class LogicalOperator(Enum):
    """Logical operators for combining conditions"""
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class Attribute:
    """Represents an attribute in the ABAC system"""
    name: str
    type: AttributeType
    value: Any
    category: str = "custom"  # subject, resource, action, environment, custom
    
    def __post_init__(self):
        """Validate attribute value against type"""
        self._validate_value()
    
    def _validate_value(self):
        """Validate that value matches the declared type"""
        if self.type == AttributeType.STRING and not isinstance(self.value, str):
            raise ValueError(f"Attribute {self.name} expects string, got {type(self.value)}")
        elif self.type == AttributeType.NUMBER and not isinstance(self.value, (int, float)):
            raise ValueError(f"Attribute {self.name} expects number, got {type(self.value)}")
        elif self.type == AttributeType.BOOLEAN and not isinstance(self.value, bool):
            raise ValueError(f"Attribute {self.name} expects boolean, got {type(self.value)}")
        elif self.type == AttributeType.DATETIME and not isinstance(self.value, datetime):
            raise ValueError(f"Attribute {self.name} expects datetime, got {type(self.value)}")
        elif self.type == AttributeType.LIST and not isinstance(self.value, list):
            raise ValueError(f"Attribute {self.name} expects list, got {type(self.value)}")
        elif self.type == AttributeType.OBJECT and not isinstance(self.value, dict):
            raise ValueError(f"Attribute {self.name} expects object, got {type(self.value)}")


@dataclass
class Condition:
    """Represents a single condition in a policy rule"""
    attribute_name: str
    operator: ComparisonOperator
    value: Any
    attribute_type: Optional[AttributeType] = None
    
    def evaluate(self, attributes: Dict[str, Attribute]) -> bool:
        """Evaluate this condition against provided attributes"""
        if self.attribute_name not in attributes:
            if self.operator == ComparisonOperator.EXISTS:
                return False
            return False  # Missing attribute fails condition
        
        attr = attributes[self.attribute_name]
        attr_value = attr.value
        comparison_value = self.value
        
        # Handle EXISTS operator specially
        if self.operator == ComparisonOperator.EXISTS:
            return True
        
        try:
            # Perform comparison based on operator
            if self.operator == ComparisonOperator.EQUALS:
                return attr_value == comparison_value
            elif self.operator == ComparisonOperator.NOT_EQUALS:
                return attr_value != comparison_value
            elif self.operator == ComparisonOperator.GREATER_THAN:
                return attr_value > comparison_value
            elif self.operator == ComparisonOperator.GREATER_THAN_OR_EQUAL:
                return attr_value >= comparison_value
            elif self.operator == ComparisonOperator.LESS_THAN:
                return attr_value < comparison_value
            elif self.operator == ComparisonOperator.LESS_THAN_OR_EQUAL:
                return attr_value <= comparison_value
            elif self.operator == ComparisonOperator.IN:
                return attr_value in comparison_value
            elif self.operator == ComparisonOperator.NOT_IN:
                return attr_value not in comparison_value
            elif self.operator == ComparisonOperator.CONTAINS:
                if isinstance(attr_value, (str, list)):
                    return comparison_value in attr_value
                return False
            elif self.operator == ComparisonOperator.STARTS_WITH:
                if isinstance(attr_value, str):
                    return attr_value.startswith(comparison_value)
                return False
            elif self.operator == ComparisonOperator.ENDS_WITH:
                if isinstance(attr_value, str):
                    return attr_value.endswith(comparison_value)
                return False
            elif self.operator == ComparisonOperator.REGEX:
                if isinstance(attr_value, str) and isinstance(comparison_value, str):
                    return bool(re.match(comparison_value, attr_value))
                return False
            
        except (TypeError, ValueError):
            return False
        
        return False


@dataclass
class Rule:
    """Represents a rule with conditions and logical operators"""
    conditions: List[Union[Condition, 'Rule']]
    operator: LogicalOperator = LogicalOperator.AND
    
    def evaluate(self, attributes: Dict[str, Attribute]) -> bool:
        """Evaluate this rule against provided attributes"""
        if not self.conditions:
            return True
        
        results = []
        for condition in self.conditions:
            if isinstance(condition, Condition):
                results.append(condition.evaluate(attributes))
            elif isinstance(condition, Rule):
                results.append(condition.evaluate(attributes))
        
        if self.operator == LogicalOperator.AND:
            return all(results)
        elif self.operator == LogicalOperator.OR:
            return any(results)
        elif self.operator == LogicalOperator.NOT:
            # NOT should only have one condition
            return not results[0] if results else True
        
        return False


@dataclass
class Policy:
    """Represents an ABAC policy"""
    id: str
    name: str
    description: str
    effect: PolicyEffect
    rules: List[Rule]
    priority: int = 0
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    def evaluate(self, attributes: Dict[str, Attribute]) -> bool:
        """Evaluate all rules in this policy"""
        if not self.enabled:
            return False
        
        if not self.rules:
            return True
        
        # All rules must pass for policy to apply
        for rule in self.rules:
            if not rule.evaluate(attributes):
                return False
        
        return True


@dataclass
class AccessRequest:
    """Represents an access request to be evaluated"""
    subject_attributes: Dict[str, Attribute]
    resource_attributes: Dict[str, Attribute]
    action_attributes: Dict[str, Attribute]
    environment_attributes: Dict[str, Attribute] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def get_all_attributes(self) -> Dict[str, Attribute]:
        """Get all attributes combined"""
        all_attrs = {}
        all_attrs.update(self.subject_attributes)
        all_attrs.update(self.resource_attributes)
        all_attrs.update(self.action_attributes)
        all_attrs.update(self.environment_attributes)
        return all_attrs


@dataclass
class PolicyDecision:
    """Represents the result of a policy evaluation"""
    decision: PolicyEffect
    applied_policies: List[str]
    evaluation_time: datetime = field(default_factory=datetime.now)
    reason: str = ""
    obligations: List[str] = field(default_factory=list)
    advice: List[str] = field(default_factory=list)


class PolicyStore:
    """Storage and management for ABAC policies"""
    
    def __init__(self):
        self.policies: Dict[str, Policy] = {}
        self._policy_file: Optional[Path] = None
    
    def add_policy(self, policy: Policy) -> bool:
        """Add a new policy"""
        self.policies[policy.id] = policy
        return True
    
    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy by ID"""
        if policy_id in self.policies:
            del self.policies[policy_id]
            return True
        return False
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a policy by ID"""
        return self.policies.get(policy_id)
    
    def list_policies(self, enabled_only: bool = False) -> List[Policy]:
        """List all policies"""
        policies = list(self.policies.values())
        if enabled_only:
            policies = [p for p in policies if p.enabled]
        return sorted(policies, key=lambda p: p.priority, reverse=True)
    
    def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> bool:
        """Update a policy"""
        if policy_id not in self.policies:
            return False
        
        policy = self.policies[policy_id]
        for key, value in updates.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        
        policy.updated_at = datetime.now()
        return True
    
    def enable_policy(self, policy_id: str) -> bool:
        """Enable a policy"""
        return self.update_policy(policy_id, {"enabled": True})
    
    def disable_policy(self, policy_id: str) -> bool:
        """Disable a policy"""
        return self.update_policy(policy_id, {"enabled": False})
    
    def save_to_file(self, file_path: Path) -> bool:
        """Save policies to JSON file"""
        try:
            policy_data = []
            for policy in self.policies.values():
                policy_dict = {
                    "id": policy.id,
                    "name": policy.name,
                    "description": policy.description,
                    "effect": policy.effect.value,
                    "priority": policy.priority,
                    "enabled": policy.enabled,
                    "created_at": policy.created_at.isoformat(),
                    "updated_at": policy.updated_at.isoformat(),
                    "tags": policy.tags,
                    "rules": self._serialize_rules(policy.rules)
                }
                policy_data.append(policy_dict)
            
            with open(file_path, 'w') as f:
                json.dump(policy_data, f, indent=2)
            
            self._policy_file = file_path
            return True
        except Exception:
            return False
    
    def load_from_file(self, file_path: Path) -> bool:
        """Load policies from JSON file"""
        try:
            with open(file_path, 'r') as f:
                policy_data = json.load(f)
            
            self.policies.clear()
            for policy_dict in policy_data:
                policy = Policy(
                    id=policy_dict["id"],
                    name=policy_dict["name"],
                    description=policy_dict["description"],
                    effect=PolicyEffect(policy_dict["effect"]),
                    priority=policy_dict["priority"],
                    enabled=policy_dict["enabled"],
                    created_at=datetime.fromisoformat(policy_dict["created_at"]),
                    updated_at=datetime.fromisoformat(policy_dict["updated_at"]),
                    tags=policy_dict["tags"],
                    rules=self._deserialize_rules(policy_dict["rules"])
                )
                self.policies[policy.id] = policy
            
            self._policy_file = file_path
            return True
        except Exception:
            return False
    
    def _serialize_rules(self, rules: List[Rule]) -> List[Dict[str, Any]]:
        """Serialize rules to JSON-compatible format"""
        serialized = []
        for rule in rules:
            rule_dict = {
                "operator": rule.operator.value,
                "conditions": []
            }
            
            for condition in rule.conditions:
                if isinstance(condition, Condition):
                    cond_dict = {
                        "type": "condition",
                        "attribute_name": condition.attribute_name,
                        "operator": condition.operator.value,
                        "value": condition.value,
                        "attribute_type": condition.attribute_type.value if condition.attribute_type else None
                    }
                    rule_dict["conditions"].append(cond_dict)
                elif isinstance(condition, Rule):
                    # Recursive serialization for nested rules
                    nested_rules = self._serialize_rules([condition])
                    rule_dict["conditions"].append({
                        "type": "rule",
                        "rule": nested_rules[0]
                    })
            
            serialized.append(rule_dict)
        return serialized
    
    def _deserialize_rules(self, rules_data: List[Dict[str, Any]]) -> List[Rule]:
        """Deserialize rules from JSON format"""
        rules = []
        for rule_dict in rules_data:
            conditions = []
            
            for cond_data in rule_dict["conditions"]:
                if cond_data["type"] == "condition":
                    condition = Condition(
                        attribute_name=cond_data["attribute_name"],
                        operator=ComparisonOperator(cond_data["operator"]),
                        value=cond_data["value"],
                        attribute_type=AttributeType(cond_data["attribute_type"]) if cond_data["attribute_type"] else None
                    )
                    conditions.append(condition)
                elif cond_data["type"] == "rule":
                    # Recursive deserialization for nested rules
                    nested_rules = self._deserialize_rules([cond_data["rule"]])
                    conditions.append(nested_rules[0])
            
            rule = Rule(
                conditions=conditions,
                operator=LogicalOperator(rule_dict["operator"])
            )
            rules.append(rule)
        
        return rules


class ABACEngine:
    """Main ABAC Engine for policy evaluation and decision making"""
    
    def __init__(self, policy_store: Optional[PolicyStore] = None):
        self.policy_store = policy_store or PolicyStore()
        self.default_decision = PolicyEffect.DENY
        self.conflict_resolution = "deny_overrides"  # deny_overrides, permit_overrides, first_applicable
    
    def evaluate_request(self, request: AccessRequest) -> PolicyDecision:
        """Evaluate an access request against all applicable policies"""
        all_attributes = request.get_all_attributes()
        applicable_policies = []
        allow_policies = []
        deny_policies = []
        
        # Find all applicable policies
        for policy in self.policy_store.list_policies(enabled_only=True):
            if policy.evaluate(all_attributes):
                applicable_policies.append(policy.id)
                
                if policy.effect == PolicyEffect.ALLOW:
                    allow_policies.append(policy)
                else:
                    deny_policies.append(policy)
        
        # Apply conflict resolution strategy
        decision = self._resolve_conflicts(allow_policies, deny_policies)
        
        # Build decision result
        reason = self._build_decision_reason(decision, allow_policies, deny_policies)
        
        return PolicyDecision(
            decision=decision,
            applied_policies=applicable_policies,
            reason=reason
        )
    
    def _resolve_conflicts(self, allow_policies: List[Policy], deny_policies: List[Policy]) -> PolicyEffect:
        """Resolve conflicts between policies"""
        if self.conflict_resolution == "deny_overrides":
            # If any deny policy applies, deny access
            if deny_policies:
                return PolicyEffect.DENY
            elif allow_policies:
                return PolicyEffect.ALLOW
            else:
                return self.default_decision
        
        elif self.conflict_resolution == "permit_overrides":
            # If any allow policy applies, allow access
            if allow_policies:
                return PolicyEffect.ALLOW
            elif deny_policies:
                return PolicyEffect.DENY
            else:
                return self.default_decision
        
        elif self.conflict_resolution == "first_applicable":
            # Use the highest priority policy
            all_policies = allow_policies + deny_policies
            if all_policies:
                highest_priority = max(all_policies, key=lambda p: p.priority)
                return highest_priority.effect
            else:
                return self.default_decision
        
        return self.default_decision
    
    def _build_decision_reason(self, decision: PolicyEffect, allow_policies: List[Policy], deny_policies: List[Policy]) -> str:
        """Build a human-readable reason for the decision"""
        if decision == PolicyEffect.ALLOW:
            if allow_policies:
                policy_names = [p.name for p in allow_policies]
                return f"Access allowed by policies: {', '.join(policy_names)}"
            else:
                return "Access allowed by default"
        else:
            if deny_policies:
                policy_names = [p.name for p in deny_policies]
                return f"Access denied by policies: {', '.join(policy_names)}"
            else:
                return "Access denied by default"
    
    def set_conflict_resolution(self, strategy: str) -> bool:
        """Set the conflict resolution strategy"""
        valid_strategies = ["deny_overrides", "permit_overrides", "first_applicable"]
        if strategy in valid_strategies:
            self.conflict_resolution = strategy
            return True
        return False
    
    def set_default_decision(self, decision: PolicyEffect) -> None:
        """Set the default decision when no policies apply"""
        self.default_decision = decision
    
    def test_policy(self, policy_id: str, request: AccessRequest) -> Dict[str, Any]:
        """Test a specific policy against a request"""
        policy = self.policy_store.get_policy(policy_id)
        if not policy:
            return {"error": "Policy not found"}
        
        all_attributes = request.get_all_attributes()
        applies = policy.evaluate(all_attributes)
        
        return {
            "policy_id": policy_id,
            "policy_name": policy.name,
            "applies": applies,
            "effect": policy.effect.value if applies else None,
            "enabled": policy.enabled
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        policies = self.policy_store.list_policies()
        enabled_policies = [p for p in policies if p.enabled]
        allow_policies = [p for p in policies if p.effect == PolicyEffect.ALLOW]
        deny_policies = [p for p in policies if p.effect == PolicyEffect.DENY]
        
        return {
            "total_policies": len(policies),
            "enabled_policies": len(enabled_policies),
            "disabled_policies": len(policies) - len(enabled_policies),
            "allow_policies": len(allow_policies),
            "deny_policies": len(deny_policies),
            "conflict_resolution": self.conflict_resolution,
            "default_decision": self.default_decision.value
        }


# Utility functions for creating common attribute types
def create_subject_attribute(name: str, value: Any, attr_type: AttributeType) -> Attribute:
    """Create a subject attribute"""
    return Attribute(name=name, type=attr_type, value=value, category="subject")


def create_resource_attribute(name: str, value: Any, attr_type: AttributeType) -> Attribute:
    """Create a resource attribute"""
    return Attribute(name=name, type=attr_type, value=value, category="resource")


def create_action_attribute(name: str, value: Any, attr_type: AttributeType) -> Attribute:
    """Create an action attribute"""
    return Attribute(name=name, type=attr_type, value=value, category="action")


def create_environment_attribute(name: str, value: Any, attr_type: AttributeType) -> Attribute:
    """Create an environment attribute"""
    return Attribute(name=name, type=attr_type, value=value, category="environment")


# Policy builder utilities
class PolicyBuilder:
    """Helper class for building policies programmatically"""
    
    def __init__(self, policy_id: str, name: str):
        self.policy_id = policy_id
        self.name = name
        self.description = ""
        self.effect = PolicyEffect.DENY
        self.priority = 0
        self.rules: List[Rule] = []
        self.tags: List[str] = []
    
    def with_description(self, description: str) -> 'PolicyBuilder':
        self.description = description
        return self
    
    def with_effect(self, effect: PolicyEffect) -> 'PolicyBuilder':
        self.effect = effect
        return self
    
    def with_priority(self, priority: int) -> 'PolicyBuilder':
        self.priority = priority
        return self
    
    def with_tags(self, tags: List[str]) -> 'PolicyBuilder':
        self.tags = tags
        return self
    
    def add_rule(self, rule: Rule) -> 'PolicyBuilder':
        self.rules.append(rule)
        return self
    
    def build(self) -> Policy:
        return Policy(
            id=self.policy_id,
            name=self.name,
            description=self.description,
            effect=self.effect,
            rules=self.rules,
            priority=self.priority,
            tags=self.tags
        )


class RuleBuilder:
    """Helper class for building rules programmatically"""
    
    def __init__(self, operator: LogicalOperator = LogicalOperator.AND):
        self.operator = operator
        self.conditions: List[Union[Condition, Rule]] = []
    
    def add_condition(self, attribute_name: str, operator: ComparisonOperator, value: Any, attribute_type: Optional[AttributeType] = None) -> 'RuleBuilder':
        condition = Condition(
            attribute_name=attribute_name,
            operator=operator,
            value=value,
            attribute_type=attribute_type
        )
        self.conditions.append(condition)
        return self
    
    def add_rule(self, rule: Rule) -> 'RuleBuilder':
        self.conditions.append(rule)
        return self
    
    def build(self) -> Rule:
        return Rule(conditions=self.conditions, operator=self.operator)
