"""
Ollama AI Query Engine
=====================

Natural language to SQL/MongoDB query conversion using Ollama LLM.
Allows users to interact with the database without knowing programming.
"""

import json
import asyncio
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False
    print("Warning: httpx not available. Some AI query engine features will be limited.")

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    """Types of queries supported"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    AGGREGATE = "aggregate"
    UNKNOWN = "unknown"


@dataclass
class QueryIntent:
    """Represents the intent of a natural language query"""
    query_type: QueryType
    collection: Optional[str]
    conditions: Dict[str, Any]
    fields: List[str]
    data: Dict[str, Any]
    confidence: float
    raw_query: str


@dataclass
class AIQueryResult:
    """Result of AI query processing"""
    success: bool
    query_intent: Optional[QueryIntent]
    sql_query: Optional[str]
    mongo_query: Optional[Dict[str, Any]]
    explanation: str
    suggestions: List[str]
    error: Optional[str] = None


class OllamaClient:
    """Client for communicating with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma:2b"):
        self.base_url = base_url
        self.model = model
        if HTTPX_AVAILABLE and httpx is not None:
            self.client = httpx.AsyncClient(timeout=60.0)
        else:
            self.client = None
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response from Ollama"""
        if not self.client:
            return "Error: HTTP client not available. Please install httpx package."
            
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for more consistent responses
                    "top_p": 0.9,
                    "num_predict": 1000
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Failed to connect to Ollama: {str(e)}")
    
    async def check_availability(self) -> bool:
        """Check if Ollama is available"""
        if not self.client:
            return False
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()


class QueryAnalyzer:
    """Analyzes natural language queries to understand intent"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
        
        # System prompt for query analysis
        self.analysis_system_prompt = """
You are a database query analyzer. Your task is to analyze natural language queries and convert them to structured database operations.

Respond ONLY with valid JSON in this exact format:
{
    "query_type": "select|insert|update|delete|aggregate",
    "collection": "collection_name or null",
    "conditions": {"field": "value"},
    "fields": ["field1", "field2"],
    "data": {"field": "value"},
    "confidence": 0.95
}

Guidelines:
- query_type: Determine the operation type
- collection: Extract the table/collection name
- conditions: Extract WHERE/filter conditions
- fields: Extract SELECT fields or UPDATE fields
- data: Extract INSERT/UPDATE data
- confidence: Your confidence level (0.0-1.0)

Do not include any explanation, only the JSON response.
"""
    
    def _extract_keywords(self, query: str) -> Dict[str, List[str]]:
        """Extract keywords from query"""
        query_lower = query.lower()
        
        # Action keywords
        action_keywords = {
            "select": ["show", "get", "find", "list", "display", "retrieve", "fetch"],
            "insert": ["add", "create", "insert", "new", "save"],
            "update": ["update", "change", "modify", "edit", "set"],
            "delete": ["delete", "remove", "drop"]
        }
        
        # Collection indicators
        collection_keywords = ["from", "in", "table", "collection", "users", "products", "orders"]
        
        # Condition keywords
        condition_keywords = ["where", "with", "having", "equals", "is", "contains"]
        
        found_keywords = {
            "actions": [],
            "collections": [],
            "conditions": []
        }
        
        for action, synonyms in action_keywords.items():
            for synonym in synonyms:
                if synonym in query_lower:
                    found_keywords["actions"].append(action)
        
        for keyword in collection_keywords:
            if keyword in query_lower:
                found_keywords["collections"].append(keyword)
        
        for keyword in condition_keywords:
            if keyword in query_lower:
                found_keywords["conditions"].append(keyword)
        
        return found_keywords
    
    async def analyze_query(self, query: str, available_collections: Optional[List[str]] = None) -> QueryIntent:
        """Analyze natural language query and determine intent"""
        # First try keyword-based analysis for simple cases
        keywords = self._extract_keywords(query)
        
        # Build context for AI
        context = f"""
Available collections: {available_collections or []}
User query: "{query}"

Analyze this query and determine the database operation needed.
"""
        
        try:
            # Get AI analysis
            ai_response = await self.ollama.generate(
                context,
                self.analysis_system_prompt
            )
            
            # Parse JSON response
            try:
                analysis = json.loads(ai_response.strip())
                
                query_type = QueryType(analysis.get("query_type", "unknown"))
                
                return QueryIntent(
                    query_type=query_type,
                    collection=analysis.get("collection"),
                    conditions=analysis.get("conditions", {}),
                    fields=analysis.get("fields", []),
                    data=analysis.get("data", {}),
                    confidence=analysis.get("confidence", 0.5),
                    raw_query=query
                )
            
            except json.JSONDecodeError:
                # Fallback to keyword analysis
                return self._fallback_analysis(query, keywords)
        
        except Exception:
            # Fallback to keyword analysis
            return self._fallback_analysis(query, keywords)
    
    def _fallback_analysis(self, query: str, keywords: Dict[str, List[str]]) -> QueryIntent:
        """Fallback keyword-based analysis"""
        query_lower = query.lower()
        
        # Determine query type
        query_type = QueryType.UNKNOWN
        if any(action in keywords["actions"] for action in ["select"]) or any(word in query_lower for word in ["show", "get", "find"]):
            query_type = QueryType.SELECT
        elif any(action in keywords["actions"] for action in ["insert"]) or any(word in query_lower for word in ["add", "create"]):
            query_type = QueryType.INSERT
        elif any(action in keywords["actions"] for action in ["update"]) or any(word in query_lower for word in ["update", "change"]):
            query_type = QueryType.UPDATE
        elif any(action in keywords["actions"] for action in ["delete"]) or any(word in query_lower for word in ["delete", "remove"]):
            query_type = QueryType.DELETE
        
        # Extract collection name (simple heuristic)
        collection = None
        common_collections = ["users", "products", "orders", "customers", "items"]
        for coll in common_collections:
            if coll in query_lower:
                collection = coll
                break
        
        return QueryIntent(
            query_type=query_type,
            collection=collection,
            conditions={},
            fields=[],
            data={},
            confidence=0.3,  # Low confidence for fallback
            raw_query=query
        )


class SQLGenerator:
    """Generates SQL queries from query intents"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
        
        self.sql_system_prompt = """
You are a SQL query generator. Convert the given query intent to a valid SQL query.

Respond ONLY with the SQL query, nothing else. No explanations, no markdown formatting.

Examples:
Intent: Get all users where age > 25
Response: SELECT * FROM users WHERE age > 25

Intent: Add new user with name John and email john@example.com
Response: INSERT INTO users (name, email) VALUES ('John', 'john@example.com')
"""
    
    async def generate_sql(self, intent: QueryIntent, schema_info: Optional[Dict[str, List[str]]] = None) -> str:
        """Generate SQL query from intent"""
        # Build context
        context = f"""
Query Intent:
- Type: {intent.query_type.value}
- Collection: {intent.collection}
- Conditions: {intent.conditions}
- Fields: {intent.fields}
- Data: {intent.data}
- Original query: "{intent.raw_query}"

Available schema: {schema_info or {}}

Generate the appropriate SQL query.
"""
        
        try:
            sql_query = await self.ollama.generate(context, self.sql_system_prompt)
            return sql_query.strip()
        except Exception as e:
            # Fallback to template-based generation
            return self._generate_sql_template(intent)
    
    def _generate_sql_template(self, intent: QueryIntent) -> str:
        """Generate SQL using templates as fallback"""
        if intent.query_type == QueryType.SELECT:
            fields = ", ".join(intent.fields) if intent.fields else "*"
            sql = f"SELECT {fields} FROM {intent.collection or 'table'}"
            
            if intent.conditions:
                conditions = []
                for field, value in intent.conditions.items():
                    if isinstance(value, str):
                        conditions.append(f"{field} = '{value}'")
                    else:
                        conditions.append(f"{field} = {value}")
                sql += f" WHERE {' AND '.join(conditions)}"
            
            return sql
        
        elif intent.query_type == QueryType.INSERT:
            if intent.data:
                fields = ", ".join(intent.data.keys())
                values = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in intent.data.values()])
                return f"INSERT INTO {intent.collection or 'table'} ({fields}) VALUES ({values})"
        
        elif intent.query_type == QueryType.UPDATE:
            if intent.data:
                set_clauses = []
                for field, value in intent.data.items():
                    if isinstance(value, str):
                        set_clauses.append(f"{field} = '{value}'")
                    else:
                        set_clauses.append(f"{field} = {value}")
                
                sql = f"UPDATE {intent.collection or 'table'} SET {', '.join(set_clauses)}"
                
                if intent.conditions:
                    conditions = []
                    for field, value in intent.conditions.items():
                        if isinstance(value, str):
                            conditions.append(f"{field} = '{value}'")
                        else:
                            conditions.append(f"{field} = {value}")
                    sql += f" WHERE {' AND '.join(conditions)}"
                
                return sql
        
        elif intent.query_type == QueryType.DELETE:
            sql = f"DELETE FROM {intent.collection or 'table'}"
            
            if intent.conditions:
                conditions = []
                for field, value in intent.conditions.items():
                    if isinstance(value, str):
                        conditions.append(f"{field} = '{value}'")
                    else:
                        conditions.append(f"{field} = {value}")
                sql += f" WHERE {' AND '.join(conditions)}"
            
            return sql
        
        return f"-- Could not generate SQL for query type: {intent.query_type.value}"


class MongoQueryGenerator:
    """Generates MongoDB queries from query intents"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    async def generate_mongo_query(self, intent: QueryIntent) -> Dict[str, Any]:
        """Generate MongoDB query from intent"""
        query = {}
        
        if intent.query_type == QueryType.SELECT:
            query = {
                "operation": "find",
                "collection": intent.collection,
                "filter": intent.conditions,
                "projection": {field: 1 for field in intent.fields} if intent.fields else {}
            }
        
        elif intent.query_type == QueryType.INSERT:
            query = {
                "operation": "insertOne",
                "collection": intent.collection,
                "document": intent.data
            }
        
        elif intent.query_type == QueryType.UPDATE:
            query = {
                "operation": "updateMany",
                "collection": intent.collection,
                "filter": intent.conditions,
                "update": {"$set": intent.data}
            }
        
        elif intent.query_type == QueryType.DELETE:
            query = {
                "operation": "deleteMany",
                "collection": intent.collection,
                "filter": intent.conditions
            }
        
        return query


class AIQueryEngine:
    """Main AI query engine that coordinates all components"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "gemma:2b"):
        self.ollama = OllamaClient(ollama_url, model)
        self.analyzer = QueryAnalyzer(self.ollama)
        self.sql_generator = SQLGenerator(self.ollama)
        self.mongo_generator = MongoQueryGenerator(self.ollama)
        
        # Cache for schema information
        self.schema_cache: Dict[str, Dict[str, List[str]]] = {}
    
    async def process_query(self, natural_query: str, tenant_id: str, database_id: str,
                          available_collections: Optional[List[str]] = None) -> AIQueryResult:
        """Process a natural language query"""
        try:
            # Check if Ollama is available
            if not await self.ollama.check_availability():
                return AIQueryResult(
                    success=False,
                    query_intent=None,
                    sql_query=None,
                    mongo_query=None,
                    explanation="AI service (Ollama) is not available. Please ensure Ollama is running.",
                    suggestions=[
                        "Start Ollama service: 'ollama serve'",
                        "Install Ollama from https://ollama.ai",
                        "Use traditional SQL/MongoDB queries instead"
                    ],
                    error="Ollama service unavailable"
                )
            
            # Analyze query intent
            intent = await self.analyzer.analyze_query(natural_query, available_collections)
            
            # Generate SQL query
            schema_info = self.schema_cache.get(f"{tenant_id}:{database_id}", {})
            sql_query = await self.sql_generator.generate_sql(intent, schema_info)
            
            # Generate MongoDB query
            mongo_query = await self.mongo_generator.generate_mongo_query(intent)
            
            # Build explanation
            explanation = self._build_explanation(intent, sql_query, mongo_query)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(intent)
            
            return AIQueryResult(
                success=True,
                query_intent=intent,
                sql_query=sql_query,
                mongo_query=mongo_query,
                explanation=explanation,
                suggestions=suggestions
            )
        
        except Exception as e:
            return AIQueryResult(
                success=False,
                query_intent=None,
                sql_query=None,
                mongo_query=None,
                explanation=f"Failed to process query: {str(e)}",
                suggestions=[
                    "Try rephrasing your query",
                    "Be more specific about what you want to do",
                    "Use traditional SQL/MongoDB syntax instead"
                ],
                error=str(e)
            )
    
    def _build_explanation(self, intent: QueryIntent, sql_query: str, mongo_query: Dict[str, Any]) -> str:
        """Build explanation of what the query does"""
        explanations = {
            QueryType.SELECT: f"This will retrieve {', '.join(intent.fields) if intent.fields else 'all fields'} from {intent.collection}",
            QueryType.INSERT: f"This will add a new record to {intent.collection}",
            QueryType.UPDATE: f"This will update records in {intent.collection}",
            QueryType.DELETE: f"This will remove records from {intent.collection}",
            QueryType.AGGREGATE: f"This will perform aggregation on {intent.collection}"
        }
        
        base_explanation = explanations.get(intent.query_type, "This will perform a database operation")
        
        if intent.conditions:
            condition_text = ", ".join([f"{k} = {v}" for k, v in intent.conditions.items()])
            base_explanation += f" where {condition_text}"
        
        return f"{base_explanation}. Confidence: {intent.confidence:.0%}"
    
    def _generate_suggestions(self, intent: QueryIntent) -> List[str]:
        """Generate helpful suggestions"""
        suggestions = []
        
        if intent.confidence < 0.7:
            suggestions.append("Consider being more specific in your query")
        
        if not intent.collection:
            suggestions.append("Specify which table/collection you want to work with")
        
        if intent.query_type == QueryType.UNKNOWN:
            suggestions.extend([
                "Try starting with: 'Show all...', 'Add new...', 'Update...', or 'Delete...'",
                "Be clear about what action you want to perform"
            ])
        
        suggestions.append("You can also use traditional SQL or MongoDB syntax")
        
        return suggestions
    
    def update_schema_cache(self, tenant_id: str, database_id: str, schema: Dict[str, List[str]]):
        """Update schema information for better query generation"""
        self.schema_cache[f"{tenant_id}:{database_id}"] = schema
    
    async def close(self):
        """Close connections"""
        await self.ollama.close()


def create_ai_query_engine(ollama_url: str = "http://localhost:11434", 
                          model: str = "gemma:2b") -> AIQueryEngine:
    """Create and configure AI query engine"""
    return AIQueryEngine(ollama_url, model)
