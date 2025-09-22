"""
AI Query Interface
==================

Ollama-based AI system for natural language to SQL/MongoDB query conversion.
Allows non-programmers to interact with databases using natural language.
"""

import json
import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import uuid
from dataclasses import dataclass
from enum import Enum
import requests
import time

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    ollama = None
    OLLAMA_AVAILABLE = False
    print("Warning: Ollama not available. AI query features will be limited.")


class QueryType(Enum):
    """Types of queries the AI can generate"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    AGGREGATE = "aggregate"
    CREATE = "create"
    DROP = "drop"


class QueryComplexity(Enum):
    """Query complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


@dataclass
class AIQueryRequest:
    """AI query request structure"""
    tenant_id: str
    user_id: str
    natural_language: str
    database_name: str
    preferred_type: str = "auto"  # sql, mongodb, auto
    context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


@dataclass
class AIQueryResponse:
    """AI query response structure"""
    success: bool
    query_type: Optional[QueryType] = None
    sql_query: Optional[str] = None
    mongodb_query: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    confidence: float = 0.0
    complexity: Optional[QueryComplexity] = None
    suggested_alternatives: Optional[List[str]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.suggested_alternatives is None:
            self.suggested_alternatives = []


class SchemaAnalyzer:
    """Analyzes database schema to provide context for AI queries"""
    
    def __init__(self, db_engine):
        """Initialize with database engine"""
        self.db_engine = db_engine
        self.schema_cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    def get_collections_info(self) -> Dict[str, Any]:
        """Get information about available collections"""
        try:
            collections = self.db_engine.list_collections()
            
            collections_info = {}
            for collection_name in collections:
                # Get sample documents to infer schema
                sample_result = self.db_engine.find(collection_name, {}, limit=5)
                if sample_result.get("success"):
                    documents = sample_result.get("documents", [])
                    if documents:
                        # Analyze field types and structure
                        fields = {}
                        for doc in documents:
                            for field, value in doc.items():
                                if field not in fields:
                                    fields[field] = {
                                        "type": type(value).__name__,
                                        "examples": [value],
                                        "nullable": False
                                    }
                                else:
                                    if value is None:
                                        fields[field]["nullable"] = True
                                    elif len(fields[field]["examples"]) < 3:
                                        fields[field]["examples"].append(value)
                        
                        collections_info[collection_name] = {
                            "document_count": len(documents),
                            "fields": fields,
                            "sample_documents": documents[:2]  # Include 2 sample docs
                        }
            
            return collections_info
        except Exception as e:
            print(f"Error getting collections info: {e}")
            return {}
    
    def get_schema_context(self) -> str:
        """Get schema context as string for AI prompt"""
        collections_info = self.get_collections_info()
        
        context_parts = ["Available Collections and Schema:\n"]
        
        for collection_name, info in collections_info.items():
            context_parts.append(f"\nCollection: {collection_name}")
            context_parts.append(f"Document count: {info.get('document_count', 0)}")
            context_parts.append("Fields:")
            
            for field_name, field_info in info.get("fields", {}).items():
                field_type = field_info.get("type", "unknown")
                nullable = " (nullable)" if field_info.get("nullable") else ""
                examples = field_info.get("examples", [])
                example_str = f" - examples: {examples[:2]}" if examples else ""
                context_parts.append(f"  - {field_name}: {field_type}{nullable}{example_str}")
        
        return "\n".join(context_parts)


class OllamaAIQueryEngine:
    """
    Ollama-based AI query engine for natural language to database queries
    """
    
    def __init__(self, model_name: str = "gemma:2b", ollama_host: str = "http://localhost:11434"):
        """Initialize Ollama AI query engine"""
        self.model_name = model_name
        self.ollama_host = ollama_host
        self.schema_analyzer = None
        self.conversation_history = {}
        
        # Check if Ollama is available
        self.available = self._check_ollama_availability()
        
        if not self.available:
            print("Warning: Ollama service not available. AI queries will use fallback.")
    
    def set_schema_analyzer(self, schema_analyzer: SchemaAnalyzer):
        """Set schema analyzer for context"""
        self.schema_analyzer = schema_analyzer
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama service is available"""
        try:
            if not OLLAMA_AVAILABLE:
                return False
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI query generation"""
        return """You are an expert database query assistant. Your job is to convert natural language requests into SQL queries or MongoDB operations.

Key guidelines:
1. Generate syntactically correct SQL or MongoDB queries
2. Use proper field names based on the provided schema
3. Include appropriate WHERE clauses for filtering
4. Use JOINs when data spans multiple collections
5. Always explain your reasoning
6. Suggest alternatives when applicable
7. Indicate confidence level (0.0 to 1.0)
8. Classify query complexity (simple, moderate, complex, expert)

Response format (JSON):
{
    "query_type": "select|insert|update|delete|aggregate",
    "sql_query": "SELECT * FROM...",
    "mongodb_query": {"find": {...}},
    "explanation": "I generated this query because...",
    "confidence": 0.85,
    "complexity": "moderate",
    "suggested_alternatives": ["Alternative query 1", "Alternative query 2"]
}

Remember:
- Use the exact field names from the schema
- Handle edge cases gracefully
- Provide clear explanations
- Suggest multiple approaches when possible"""
    
    def _build_prompt(self, request: AIQueryRequest, schema_context: str) -> str:
        """Build complete prompt for AI"""
        conversation = self.conversation_history.get(request.user_id, [])
        
        prompt_parts = [
            "Database Schema Context:",
            schema_context,
            "\nUser Request:",
            f"Database: {request.database_name}",
            f"Query: {request.natural_language}",
            f"Preferred type: {request.preferred_type}",
        ]
        
        # Add conversation history for context
        if conversation:
            prompt_parts.extend([
                "\nRecent conversation:",
                *conversation[-3:]  # Last 3 exchanges
            ])
        
        # Add any additional context
        if request.context:
            prompt_parts.extend([
                "\nAdditional context:",
                json.dumps(request.context, indent=2)
            ])
        
        prompt_parts.append("\nGenerate the appropriate database query:")
        
        return "\n".join(prompt_parts)
    
    async def generate_query(self, request: AIQueryRequest) -> AIQueryResponse:
        """Generate database query from natural language"""
        try:
            if not self.available:
                return self._fallback_query_generation(request)
            
            # Get schema context
            schema_context = ""
            if self.schema_analyzer:
                schema_context = self.schema_analyzer.get_schema_context()
            
            # Build prompt
            prompt = self._build_prompt(request, schema_context)
            
            # Generate query using Ollama
            try:
                if not OLLAMA_AVAILABLE or ollama is None:
                    raise Exception("Ollama is not available")
                    
                response = ollama.generate(
                    model=self.model_name,
                    prompt=prompt,
                    system=self._get_system_prompt()
                )
                
                # Parse response
                ai_response = self._parse_ai_response(response.get("response", ""))
                
                # Update conversation history
                self._update_conversation_history(request.user_id, request.natural_language, ai_response)
                
                return ai_response
                
            except Exception as e:
                print(f"Ollama generation error: {e}")
                return self._fallback_query_generation(request)
        
        except Exception as e:
            return AIQueryResponse(
                success=False,
                error=f"AI query generation failed: {str(e)}"
            )
    
    def _parse_ai_response(self, ai_text: str) -> AIQueryResponse:
        """Parse AI response text into structured response"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    return AIQueryResponse(
                        success=True,
                        query_type=QueryType(data.get("query_type", "select")),
                        sql_query=data.get("sql_query"),
                        mongodb_query=data.get("mongodb_query"),
                        explanation=data.get("explanation", ""),
                        confidence=float(data.get("confidence", 0.7)),
                        complexity=QueryComplexity(data.get("complexity", "moderate")),
                        suggested_alternatives=data.get("suggested_alternatives", [])
                    )
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # Fallback: try to extract SQL query from text
            sql_patterns = [
                r'(SELECT.*?(?=\n|$))',
                r'(INSERT.*?(?=\n|$))',
                r'(UPDATE.*?(?=\n|$))',
                r'(DELETE.*?(?=\n|$))'
            ]
            
            for pattern in sql_patterns:
                match = re.search(pattern, ai_text, re.IGNORECASE | re.DOTALL)
                if match:
                    return AIQueryResponse(
                        success=True,
                        query_type=QueryType.SELECT,
                        sql_query=match.group(1).strip(),
                        explanation=ai_text,
                        confidence=0.6,
                        complexity=QueryComplexity.MODERATE
                    )
            
            return AIQueryResponse(
                success=False,
                error="Could not parse AI response",
                explanation=ai_text
            )
            
        except Exception as e:
            return AIQueryResponse(
                success=False,
                error=f"Response parsing failed: {str(e)}"
            )
    
    def _fallback_query_generation(self, request: AIQueryRequest) -> AIQueryResponse:
        """Fallback query generation when Ollama is not available"""
        natural_lang = request.natural_language.lower()
        
        # Simple pattern matching for basic queries
        if any(word in natural_lang for word in ["show", "list", "get", "find", "select"]):
            # SELECT query
            if "all" in natural_lang or "everything" in natural_lang:
                sql_query = f"SELECT * FROM {request.database_name}"
            else:
                sql_query = f"SELECT * FROM {request.database_name} LIMIT 10"
            
            return AIQueryResponse(
                success=True,
                query_type=QueryType.SELECT,
                sql_query=sql_query,
                explanation="Generated basic SELECT query using pattern matching",
                confidence=0.4,
                complexity=QueryComplexity.SIMPLE
            )
        
        elif any(word in natural_lang for word in ["insert", "add", "create"]):
            return AIQueryResponse(
                success=True,
                query_type=QueryType.INSERT,
                explanation="Detected INSERT operation - please provide specific field values",
                confidence=0.3,
                complexity=QueryComplexity.SIMPLE,
                suggested_alternatives=[
                    "Please specify: INSERT INTO table (field1, field2) VALUES (value1, value2)"
                ]
            )
        
        else:
            return AIQueryResponse(
                success=False,
                error="Could not interpret query. Please be more specific or use simpler language.",
                suggested_alternatives=[
                    "Try: 'Show all records from users'",
                    "Try: 'Find users where age > 25'",
                    "Try: 'Insert new user with name John'"
                ]
            )
    
    def _update_conversation_history(self, user_id: str, query: str, response: AIQueryResponse):
        """Update conversation history for context"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        history = self.conversation_history[user_id]
        history.append(f"Q: {query}")
        
        if response.sql_query:
            history.append(f"A: {response.sql_query}")
        elif response.mongodb_query:
            history.append(f"A: {json.dumps(response.mongodb_query)}")
        
        # Keep only last 10 exchanges
        self.conversation_history[user_id] = history[-20:]
    
    def get_query_suggestions(self, partial_text: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Get query suggestions for autocomplete"""
        suggestions = []
        text_lower = partial_text.lower()
        
        # Common query starters
        if text_lower.startswith("show") or text_lower.startswith("list"):
            suggestions.extend([
                "show all users",
                "show users where age > 25",
                "list all products",
                "show recent orders"
            ])
        
        elif text_lower.startswith("find") or text_lower.startswith("get"):
            suggestions.extend([
                "find users by email",
                "get total count of orders",
                "find products in category electronics",
                "get average price of products"
            ])
        
        elif text_lower.startswith("add") or text_lower.startswith("insert"):
            suggestions.extend([
                "add new user with name and email",
                "insert product with price and category",
                "add order for user"
            ])
        
        elif text_lower.startswith("update"):
            suggestions.extend([
                "update user email where id = 123",
                "update product price where name = 'laptop'",
                "update order status to shipped"
            ])
        
        return suggestions[:5]  # Return top 5 suggestions


def create_ai_query_engine(model_name: str = "llama3.1", ollama_host: str = "http://localhost:11434") -> OllamaAIQueryEngine:
    """Create AI query engine"""
    return OllamaAIQueryEngine(model_name, ollama_host)
