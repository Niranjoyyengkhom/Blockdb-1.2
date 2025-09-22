"""
AI NLP Interface for IEDB
=========================
Natural Language Processing interface for database interactions.
"""

import os
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone

logger = logging.getLogger("IEDB.AI.NLPInterface")

class AINLPInterface:
    """
    Natural Language Processing interface for intuitive database interactions
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.command_patterns = self._initialize_command_patterns()
        self.conversation_history = []
        self.context_memory = {}
        
    def _initialize_command_patterns(self) -> Dict[str, List[Dict]]:
        """Initialize NLP command patterns for database operations"""
        return {
            "select": [
                {
                    "pattern": r"(?:show|get|find|list|select|retrieve)\s+(.+?)(?:\s+from\s+(\w+))?",
                    "confidence": 0.8,
                    "operation": "SELECT",
                    "description": "Data retrieval operations"
                },
                {
                    "pattern": r"what\s+(?:is|are)\s+(?:in|on)\s+(\w+)",
                    "confidence": 0.7,
                    "operation": "SELECT",
                    "description": "Question-based data queries"
                }
            ],
            "insert": [
                {
                    "pattern": r"(?:add|insert|create|save)\s+(.+?)(?:\s+(?:to|in|into)\s+(\w+))?",
                    "confidence": 0.8,
                    "operation": "INSERT",
                    "description": "Data insertion operations"
                }
            ],
            "update": [
                {
                    "pattern": r"(?:update|modify|change|edit)\s+(.+?)(?:\s+(?:in|on)\s+(\w+))?",
                    "confidence": 0.8,
                    "operation": "UPDATE",
                    "description": "Data modification operations"
                }
            ],
            "delete": [
                {
                    "pattern": r"(?:delete|remove|drop)\s+(.+?)(?:\s+from\s+(\w+))?",
                    "confidence": 0.8,
                    "operation": "DELETE",
                    "description": "Data deletion operations"
                }
            ],
            "schema": [
                {
                    "pattern": r"(?:describe|show\s+structure|show\s+schema|table\s+info)\s+(\w+)",
                    "confidence": 0.9,
                    "operation": "DESCRIBE",
                    "description": "Schema information queries"
                },
                {
                    "pattern": r"(?:show|list)\s+(?:tables|databases)",
                    "confidence": 0.9,
                    "operation": "SHOW",
                    "description": "Database structure queries"
                }
            ],
            "system": [
                {
                    "pattern": r"(?:status|health|info|stats|system)",
                    "confidence": 0.8,
                    "operation": "STATUS",
                    "description": "System information queries"
                }
            ]
        }
    
    def process_natural_language(self, text: str, tenant_id: str, 
                               context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process natural language input and convert to database operations
        
        Args:
            text: Natural language input
            tenant_id: Tenant identifier
            context: Additional context information
            
        Returns:
            Dict containing processed command information
        """
        try:
            logger.info(f"Processing NL input for tenant {tenant_id}: {text}")
            
            # Clean and normalize input
            normalized_text = self._normalize_text(text)
            
            # Extract intent and entities
            intent_analysis = self._analyze_intent(normalized_text)
            entities = self._extract_entities(normalized_text, context)
            
            # Generate database operation
            operation = self._generate_operation(intent_analysis, entities, context)
            
            # Store in conversation history
            conversation_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tenant_id": tenant_id,
                "input": text,
                "normalized": normalized_text,
                "intent": intent_analysis,
                "entities": entities,
                "operation": operation,
                "context": context or {}
            }
            self.conversation_history.append(conversation_entry)
            
            # Update context memory
            self._update_context_memory(tenant_id, conversation_entry)
            
            return {
                "success": True,
                "original_text": text,
                "normalized_text": normalized_text,
                "intent": intent_analysis,
                "entities": entities,
                "suggested_operation": operation,
                "confidence": intent_analysis.get("confidence", 0.5),
                "explanation": self._generate_explanation(intent_analysis, entities),
                "alternatives": self._suggest_alternatives(normalized_text),
                "context_used": bool(context)
            }
            
        except Exception as e:
            logger.error(f"NLP processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "original_text": text,
                "suggestions": self._generate_error_suggestions(text)
            }
    
    def _normalize_text(self, text: str) -> str:
        """Normalize input text for better processing"""
        # Convert to lowercase
        normalized = text.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Handle common contractions and variations
        replacements = {
            "show me": "show",
            "give me": "get",
            "find me": "find",
            "tell me": "show",
            "what is": "show",
            "what are": "show",
            "how many": "count",
            "list all": "list"
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def _analyze_intent(self, text: str) -> Dict[str, Any]:
        """Analyze the intent of the normalized text"""
        best_match = None
        best_confidence = 0.0
        
        for operation_type, patterns in self.command_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                confidence = pattern_info["confidence"]
                
                match = re.search(pattern, text, re.IGNORECASE)
                if match and confidence > best_confidence:
                    best_match = {
                        "operation_type": operation_type,
                        "operation": pattern_info["operation"],
                        "confidence": confidence,
                        "match_groups": match.groups(),
                        "description": pattern_info["description"]
                    }
                    best_confidence = confidence
        
        if best_match:
            return best_match
        else:
            return {
                "operation_type": "unknown",
                "operation": "UNKNOWN",
                "confidence": 0.1,
                "match_groups": (),
                "description": "Could not determine intent"
            }
    
    def _extract_entities(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        """Extract entities from the text"""
        entities = {
            "tables": [],
            "columns": [],
            "values": [],
            "conditions": [],
            "numbers": [],
            "dates": []
        }
        
        # Extract potential table names (simple word patterns)
        table_pattern = r'\b(?:table|from|into|in)\s+(\w+)'
        table_matches = re.findall(table_pattern, text, re.IGNORECASE)
        entities["tables"].extend(table_matches)
        
        # Extract potential column names
        column_pattern = r'\b(?:column|field)\s+(\w+)'
        column_matches = re.findall(column_pattern, text, re.IGNORECASE)
        entities["columns"].extend(column_matches)
        
        # Extract numbers
        number_pattern = r'\b(\d+(?:\.\d+)?)\b'
        number_matches = re.findall(number_pattern, text)
        entities["numbers"].extend([float(n) if '.' in n else int(n) for n in number_matches])
        
        # Extract quoted values
        value_pattern = r"'([^']+)'|\"([^\"]+)\""
        value_matches = re.findall(value_pattern, text)
        for match in value_matches:
            entities["values"].extend([v for v in match if v])
        
        # Extract WHERE-like conditions
        condition_pattern = r'\bwhere\s+(.+?)(?:\s+(?:order|group|limit)|$)'
        condition_matches = re.findall(condition_pattern, text, re.IGNORECASE)
        entities["conditions"].extend(condition_matches)
        
        # Use context to enhance entity extraction
        if context:
            if "current_table" in context:
                entities["tables"].append(context["current_table"])
            if "available_tables" in context:
                # Check if any mentioned words match available tables
                available_tables = context["available_tables"]
                words = text.split()
                for word in words:
                    if word in available_tables:
                        entities["tables"].append(word)
        
        return entities
    
    def _generate_operation(self, intent: Dict, entities: Dict, context: Optional[Dict]) -> Dict[str, Any]:
        """Generate database operation based on intent and entities"""
        operation_type = intent.get("operation", "UNKNOWN")
        
        operation = {
            "type": operation_type,
            "confidence": intent.get("confidence", 0.5),
            "parameters": {}
        }
        
        if operation_type == "SELECT":
            operation["parameters"] = {
                "action": "SELECT",
                "tables": entities.get("tables", []),
                "columns": entities.get("columns", []) or ["*"],
                "conditions": entities.get("conditions", []),
                "suggested_sql": self._generate_select_sql(entities)
            }
        
        elif operation_type == "INSERT":
            operation["parameters"] = {
                "action": "INSERT",
                "tables": entities.get("tables", []),
                "values": entities.get("values", []),
                "suggested_sql": self._generate_insert_sql(entities)
            }
        
        elif operation_type == "UPDATE":
            operation["parameters"] = {
                "action": "UPDATE",
                "tables": entities.get("tables", []),
                "values": entities.get("values", []),
                "conditions": entities.get("conditions", []),
                "suggested_sql": self._generate_update_sql(entities)
            }
        
        elif operation_type == "DELETE":
            operation["parameters"] = {
                "action": "DELETE",
                "tables": entities.get("tables", []),
                "conditions": entities.get("conditions", []),
                "suggested_sql": self._generate_delete_sql(entities)
            }
        
        elif operation_type == "DESCRIBE":
            operation["parameters"] = {
                "action": "DESCRIBE",
                "tables": entities.get("tables", []),
                "suggested_sql": f"DESCRIBE {entities.get('tables', ['table_name'])[0] if entities.get('tables') else 'table_name'}"
            }
        
        elif operation_type == "SHOW":
            operation["parameters"] = {
                "action": "SHOW",
                "suggested_sql": "SHOW TABLES" if "tables" in intent.get("match_groups", []) else "SHOW DATABASES"
            }
        
        elif operation_type == "STATUS":
            operation["parameters"] = {
                "action": "STATUS",
                "endpoint": "/health",
                "description": "Check system status and health"
            }
        
        return operation
    
    def _generate_select_sql(self, entities: Dict) -> str:
        """Generate SELECT SQL from entities"""
        columns = entities.get("columns", ["*"])
        tables = entities.get("tables", ["table_name"])
        conditions = entities.get("conditions", [])
        
        sql = f"SELECT {', '.join(columns) if columns != ['*'] else '*'}"
        sql += f" FROM {tables[0] if tables else 'table_name'}"
        
        if conditions:
            sql += f" WHERE {conditions[0]}"
        
        return sql
    
    def _generate_insert_sql(self, entities: Dict) -> str:
        """Generate INSERT SQL from entities"""
        tables = entities.get("tables", ["table_name"])
        values = entities.get("values", ["value1", "value2"])
        
        values_str = ', '.join(f"'{v}'" for v in values)
        return f"INSERT INTO {tables[0] if tables else 'table_name'} VALUES ({values_str})"
    
    def _generate_update_sql(self, entities: Dict) -> str:
        """Generate UPDATE SQL from entities"""
        tables = entities.get("tables", ["table_name"])
        conditions = entities.get("conditions", ["id = 1"])
        
        return f"UPDATE {tables[0] if tables else 'table_name'} SET column = 'value' WHERE {conditions[0] if conditions else 'id = 1'}"
    
    def _generate_delete_sql(self, entities: Dict) -> str:
        """Generate DELETE SQL from entities"""
        tables = entities.get("tables", ["table_name"])
        conditions = entities.get("conditions", ["id = 1"])
        
        return f"DELETE FROM {tables[0] if tables else 'table_name'} WHERE {conditions[0] if conditions else 'id = 1'}"
    
    def _generate_explanation(self, intent: Dict, entities: Dict) -> str:
        """Generate human-readable explanation of the operation"""
        operation = intent.get("operation", "UNKNOWN")
        confidence = intent.get("confidence", 0.5)
        
        explanations = {
            "SELECT": f"This appears to be a data retrieval request (confidence: {confidence:.1%})",
            "INSERT": f"This appears to be a data insertion request (confidence: {confidence:.1%})",
            "UPDATE": f"This appears to be a data modification request (confidence: {confidence:.1%})",
            "DELETE": f"This appears to be a data deletion request (confidence: {confidence:.1%})",
            "DESCRIBE": f"This appears to be a schema information request (confidence: {confidence:.1%})",
            "SHOW": f"This appears to be a database structure query (confidence: {confidence:.1%})",
            "STATUS": f"This appears to be a system status request (confidence: {confidence:.1%})"
        }
        
        base_explanation = explanations.get(operation, f"Could not clearly determine the operation type (confidence: {confidence:.1%})")
        
        # Add entity information
        if entities.get("tables"):
            base_explanation += f". Target table(s): {', '.join(entities['tables'])}"
        
        return base_explanation
    
    def _suggest_alternatives(self, text: str) -> List[str]:
        """Suggest alternative phrasings or operations"""
        suggestions = []
        
        # Common alternative phrasings
        if "show" in text:
            suggestions.append("Try 'list' or 'get' instead of 'show'")
        if "find" in text:
            suggestions.append("Try 'select' or 'get' instead of 'find'")
        
        # Always include helpful examples
        suggestions.extend([
            "Example: 'show all users from user_table'",
            "Example: 'get data where status = active'",
            "Example: 'describe table structure'",
            "Example: 'system status'"
        ])
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _generate_error_suggestions(self, text: str) -> List[str]:
        """Generate suggestions when processing fails"""
        return [
            "Try using simpler language",
            "Be more specific about the table or database",
            "Use keywords like 'show', 'get', 'list', 'find'",
            "Check the spelling of table and column names",
            "Try breaking complex requests into smaller parts"
        ]
    
    def _update_context_memory(self, tenant_id: str, conversation_entry: Dict):
        """Update context memory for better future processing"""
        if tenant_id not in self.context_memory:
            self.context_memory[tenant_id] = {
                "recent_tables": [],
                "recent_operations": [],
                "preferences": {}
            }
        
        memory = self.context_memory[tenant_id]
        
        # Update recent tables
        tables = conversation_entry["entities"].get("tables", [])
        for table in tables:
            if table not in memory["recent_tables"]:
                memory["recent_tables"].append(table)
                # Keep only last 5 tables
                memory["recent_tables"] = memory["recent_tables"][-5:]
        
        # Update recent operations
        operation = conversation_entry["operation"].get("type")
        if operation:
            memory["recent_operations"].append(operation)
            memory["recent_operations"] = memory["recent_operations"][-10:]
    
    def get_conversation_history(self, tenant_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get conversation history"""
        history = self.conversation_history
        
        if tenant_id:
            history = [c for c in history if c.get("tenant_id") == tenant_id]
        
        return history[-limit:] if limit else history
    
    def get_context_memory(self, tenant_id: str) -> Dict[str, Any]:
        """Get context memory for a tenant"""
        return self.context_memory.get(tenant_id, {})
    
    def suggest_query_improvements(self, query: str) -> List[Dict[str, str]]:
        """Suggest improvements for a query"""
        improvements = []
        
        # Check for common issues
        if len(query.split()) < 3:
            improvements.append({
                "issue": "Too short",
                "suggestion": "Try to be more descriptive about what you want"
            })
        
        if not any(keyword in query.lower() for keyword in ["show", "get", "find", "list", "select"]):
            improvements.append({
                "issue": "Missing action verb",
                "suggestion": "Start with words like 'show', 'get', 'find', or 'list'"
            })
        
        if "table" not in query.lower() and "from" not in query.lower():
            improvements.append({
                "issue": "No table specified",
                "suggestion": "Specify which table you want to work with"
            })
        
        return improvements
