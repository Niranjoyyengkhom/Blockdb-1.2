"""
AI Query Processor for IEDB
============================
Processes natural language queries and converts them to database operations.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone

logger = logging.getLogger("IEDB.AI.QueryProcessor")

class AIQueryProcessor:
    """
    AI-powered query processor for natural language database queries
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.supported_operations = [
            "SELECT", "INSERT", "UPDATE", "DELETE", 
            "CREATE", "DROP", "DESCRIBE", "SHOW"
        ]
        self.query_history = []
        
    def process_natural_language_query(self, query: str, tenant_id: str, 
                                     database_name: Optional[str] = None,
                                     context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a natural language query and convert it to database operations
        
        Args:
            query: Natural language query
            tenant_id: Tenant identifier
            database_name: Target database name
            context: Additional context for query processing
            
        Returns:
            Dict containing processed query results
        """
        try:
            logger.info(f"Processing NL query for tenant {tenant_id}: {query}")
            
            # Store query in history
            query_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tenant_id": tenant_id,
                "database_name": database_name,
                "original_query": query,
                "context": context or {}
            }
            
            # Simple keyword-based processing (placeholder for advanced AI)
            processed_query = self._analyze_query_intent(query)
            
            # Generate response based on query type
            if processed_query["intent"] == "data_retrieval":
                result = self._process_data_query(query, tenant_id, database_name)
            elif processed_query["intent"] == "schema_info":
                result = self._process_schema_query(query, tenant_id, database_name)
            elif processed_query["intent"] == "system_info":
                result = self._process_system_query(query, tenant_id)
            else:
                result = self._generate_fallback_response(query)
            
            query_record["processed_query"] = processed_query
            query_record["result"] = result
            self.query_history.append(query_record)
            
            return {
                "success": True,
                "query": query,
                "intent": processed_query["intent"],
                "confidence": processed_query["confidence"],
                "result": result,
                "suggestions": self._generate_suggestions(query, processed_query),
                "execution_time": "Processing completed"
            }
            
        except Exception as e:
            logger.error(f"AI query processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "suggestions": ["Try rephrasing your query", "Check your database connection"]
            }
    
    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze the intent of a natural language query"""
        query_lower = query.lower()
        
        # Data retrieval keywords
        if any(word in query_lower for word in ["show", "get", "find", "list", "select", "what"]):
            if any(word in query_lower for word in ["table", "column", "schema", "structure"]):
                return {"intent": "schema_info", "confidence": 0.8}
            else:
                return {"intent": "data_retrieval", "confidence": 0.9}
        
        # System information keywords
        elif any(word in query_lower for word in ["status", "health", "stats", "system"]):
            return {"intent": "system_info", "confidence": 0.85}
        
        # Data modification keywords
        elif any(word in query_lower for word in ["add", "insert", "create", "update", "modify"]):
            return {"intent": "data_modification", "confidence": 0.7}
        
        # Deletion keywords
        elif any(word in query_lower for word in ["delete", "remove", "drop"]):
            return {"intent": "data_deletion", "confidence": 0.8}
        
        else:
            return {"intent": "unknown", "confidence": 0.3}
    
    def _process_data_query(self, query: str, tenant_id: str, database_name: Optional[str]) -> Dict[str, Any]:
        """Process data retrieval queries"""
        return {
            "type": "data_query",
            "suggested_sql": "SELECT * FROM table_name WHERE condition",
            "explanation": f"To retrieve data based on your query: '{query}'",
            "next_steps": [
                "Specify the table name",
                "Add any filtering conditions",
                "Choose columns to display"
            ]
        }
    
    def _process_schema_query(self, query: str, tenant_id: str, database_name: Optional[str]) -> Dict[str, Any]:
        """Process schema information queries"""
        return {
            "type": "schema_query",
            "suggested_action": "DESCRIBE table_name",
            "explanation": f"To get schema information: '{query}'",
            "next_steps": [
                "Check available databases",
                "List tables in database",
                "View table structure"
            ]
        }
    
    def _process_system_query(self, query: str, tenant_id: str) -> Dict[str, Any]:
        """Process system information queries"""
        return {
            "type": "system_query",
            "suggested_endpoint": "/health or /stats",
            "explanation": f"To get system information: '{query}'",
            "next_steps": [
                "Check system health",
                "View database statistics",
                "Monitor performance"
            ]
        }
    
    def _generate_fallback_response(self, query: str) -> Dict[str, Any]:
        """Generate fallback response for unknown queries"""
        return {
            "type": "fallback",
            "message": "I'm not sure how to process this query yet.",
            "explanation": f"Query '{query}' needs clarification",
            "suggestions": [
                "Try using keywords like 'show', 'get', 'list'",
                "Be more specific about what you want to find",
                "Check the available databases and tables first"
            ]
        }
    
    def _generate_suggestions(self, query: str, processed_query: Dict) -> List[str]:
        """Generate helpful suggestions based on the query"""
        suggestions = []
        
        if processed_query["confidence"] < 0.7:
            suggestions.append("Try being more specific with your request")
        
        suggestions.extend([
            "Use 'show databases' to see available databases",
            "Use 'show tables' to see available tables",
            "Check the API documentation for more examples"
        ])
        
        return suggestions
    
    def get_query_history(self, tenant_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get query history for analysis"""
        history = self.query_history
        
        if tenant_id:
            history = [q for q in history if q.get("tenant_id") == tenant_id]
        
        return history[-limit:] if limit else history
    
    def get_popular_queries(self, tenant_id: Optional[str] = None) -> List[Dict]:
        """Get most popular query patterns"""
        # Placeholder for analytics
        return [
            {"pattern": "show tables", "count": 15, "success_rate": 0.95},
            {"pattern": "get data from *", "count": 12, "success_rate": 0.87},
            {"pattern": "database status", "count": 8, "success_rate": 1.0}
        ]
