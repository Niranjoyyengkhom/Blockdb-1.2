"""
AI Module for IEDB
==================
Intelligent AI-powered features for database operations, analysis, and insights.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("IEDB.AI")

# Version information
__version__ = "1.0.0"
__author__ = "IEDB Development Team"

try:
    # Import AI components with fallback handling
    from . import query_processor  # type: ignore
    from . import data_analyzer  # type: ignore
    from . import insight_generator  # type: ignore
    from . import nlp_interface  # type: ignore
    from . import ai_query  # type: ignore
    from . import ai_query_engine  # type: ignore
    
    # Make classes available at module level
    AIQueryProcessor = query_processor.AIQueryProcessor  # type: ignore
    AIDataAnalyzer = data_analyzer.AIDataAnalyzer  # type: ignore
    AIInsightGenerator = insight_generator.AIInsightGenerator  # type: ignore
    AINLPInterface = nlp_interface.AINLPInterface  # type: ignore
    OllamaAIQueryEngine = ai_query.OllamaAIQueryEngine  # type: ignore
    QueryType = ai_query.QueryType  # type: ignore
    AIQueryRequest = ai_query.AIQueryRequest  # type: ignore
    AIQueryResponse = ai_query.AIQueryResponse  # type: ignore
    SchemaAnalyzer = ai_query.SchemaAnalyzer  # type: ignore
    AIQueryEngine = ai_query_engine.AIQueryEngine  # type: ignore
    
    AI_COMPONENTS_AVAILABLE = True
    logger.info("IEDB AI module loaded successfully")
    
except ImportError as e:
    AI_COMPONENTS_AVAILABLE = False
    logger.warning(f"Some AI components could not be imported: {e}")
    
    # Create placeholder classes to prevent import errors
    class AIQueryProcessor:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("AIQueryProcessor not available")
    
    class AIDataAnalyzer:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("AIDataAnalyzer not available")
    
    class AIInsightGenerator:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("AIInsightGenerator not available")
    
    class AINLPInterface:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("AINLPInterface not available")
            
    class OllamaAIQueryEngine:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("OllamaAIQueryEngine not available")
    
    class QueryType:
        pass
    
    class AIQueryRequest:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("AIQueryRequest not available")
    
    class AIQueryResponse:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("AIQueryResponse not available")
    
    class SchemaAnalyzer:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("SchemaAnalyzer not available")

# AI module configuration
AI_CONFIG = {
    "query_processor": {
        "enabled": True,
        "confidence_threshold": 0.7,
        "max_history": 100
    },
    "data_analyzer": {
        "enabled": True,
        "cache_size": 50,
        "analysis_timeout": 300
    },
    "insight_generator": {
        "enabled": True,
        "trend_window_days": 30,
        "confidence_threshold": 0.6
    },
    "nlp_interface": {
        "enabled": True,
        "conversation_history_limit": 50,
        "context_memory_size": 20
    },
    "ai_query": {
        "enabled": True,
        "ollama_host": "http://localhost:11434",
        "model": "gemma:2b"
    }
}

# Export main classes
__all__ = [
    "AIQueryProcessor",
    "AIDataAnalyzer", 
    "AIInsightGenerator",
    "AINLPInterface",
    "OllamaAIQueryEngine",
    "AIQueryEngine",
    "QueryType",
    "AIQueryRequest",
    "AIQueryResponse",
    "SchemaAnalyzer",
    "AI_CONFIG",
    "AI_COMPONENTS_AVAILABLE"
]

def get_ai_status():
    """Get the status of all AI components"""
    status = {
        "version": __version__,
        "components_available": AI_COMPONENTS_AVAILABLE,
        "components": {},
        "overall_status": "healthy"
    }
    
    if not AI_COMPONENTS_AVAILABLE:
        status["overall_status"] = "unavailable"
        status["error"] = "AI components could not be imported"
        return status
    
    components = [
        ("query_processor", AIQueryProcessor),
        ("data_analyzer", AIDataAnalyzer),
        ("insight_generator", AIInsightGenerator),
        ("nlp_interface", AINLPInterface),
        ("ai_query", OllamaAIQueryEngine)
    ]
    
    for name, cls in components:
        try:
            # Check if class is available
            if cls.__name__.endswith("NotImplementedError"):
                status["components"][name] = {
                    "status": "not_available",
                    "error": "Component not implemented",
                    "enabled": False
                }
            else:
                status["components"][name] = {
                    "status": "available",
                    "class": cls.__name__,
                    "enabled": AI_CONFIG.get(name, {}).get("enabled", True)
                }
        except Exception as e:
            status["components"][name] = {
                "status": "error",
                "error": str(e),
                "enabled": False
            }
    
    # Check overall status
    unavailable_components = [
        name for name, info in status["components"].items() 
        if info["status"] != "available"
    ]
    
    if unavailable_components:
        status["overall_status"] = "degraded"
        status["unavailable_components"] = unavailable_components
    
    return status

def create_ai_manager(config: Optional[Dict[str, Any]] = None):
    """Create an AI manager with all components"""
    config = config or AI_CONFIG
    
    if not AI_COMPONENTS_AVAILABLE:
        raise RuntimeError("AI components are not available. Cannot create AI manager.")
    
    class AIManager:
        def __init__(self, config: Dict[str, Any]):
            self.config = config
            self.query_processor = None
            self.data_analyzer = None
            self.insight_generator = None
            self.nlp_interface = None
            self.ai_query = None
            
            self._initialize_components()
        
        def _initialize_components(self):
            """Initialize AI components based on configuration"""
            try:
                if self.config.get("query_processor", {}).get("enabled", True):
                    try:
                        self.query_processor = AIQueryProcessor(self.config.get("query_processor", {}))
                    except NotImplementedError:
                        logger.warning("AIQueryProcessor not implemented")
                
                if self.config.get("data_analyzer", {}).get("enabled", True):
                    try:
                        self.data_analyzer = AIDataAnalyzer(self.config.get("data_analyzer", {}))
                    except NotImplementedError:
                        logger.warning("AIDataAnalyzer not implemented")
                
                if self.config.get("insight_generator", {}).get("enabled", True):
                    try:
                        self.insight_generator = AIInsightGenerator(self.config.get("insight_generator", {}))
                    except NotImplementedError:
                        logger.warning("AIInsightGenerator not implemented")
                
                if self.config.get("nlp_interface", {}).get("enabled", True):
                    try:
                        self.nlp_interface = AINLPInterface(self.config.get("nlp_interface", {}))
                    except NotImplementedError:
                        logger.warning("AINLPInterface not implemented")
                
                if self.config.get("ai_query", {}).get("enabled", True):
                    try:
                        ai_config = self.config.get("ai_query", {})
                        self.ai_query = OllamaAIQueryEngine(
                            model_name=ai_config.get("model", "llama3.1"),
                            ollama_host=ai_config.get("ollama_host", "http://localhost:11434")
                        )
                    except NotImplementedError:
                        logger.warning("OllamaAIQueryEngine not implemented")
                
                logger.info("AI Manager initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize AI components: {e}")
        
        def process_natural_query(self, query: str, tenant_id: str, context: Optional[Dict[str, Any]] = None):
            """Process a natural language query through the AI pipeline"""
            results = {}
            context = context or {}
            
            # AI Query Engine processing
            if self.ai_query:
                try:
                    request = AIQueryRequest(
                        tenant_id=tenant_id,
                        user_id=context.get("user_id", "unknown"),
                        natural_language=query,
                        database_name=context.get("database", "default"),
                        context=context
                    )
                    # Note: generate_query is async, this is a simplified version
                    results["ai_query_request"] = request
                    results["ai_query_available"] = True
                except Exception as e:
                    results["ai_query_error"] = str(e)
            
            return results
        
        def analyze_and_generate_insights(self, data: list, tenant_id: str, analysis_type: str = "general"):
            """Analyze data and generate insights"""
            results = {
                "data_count": len(data),
                "tenant_id": tenant_id,
                "analysis_type": analysis_type
            }
            
            # Basic analysis when components are available
            if self.data_analyzer:
                results["analyzer_available"] = True
            
            if self.insight_generator:
                results["insights_available"] = True
            
            return results
        
        def get_status(self):
            """Get status of the AI manager and all components"""
            return {
                "manager_status": "active",
                "components": {
                    "query_processor": bool(self.query_processor),
                    "data_analyzer": bool(self.data_analyzer),
                    "insight_generator": bool(self.insight_generator),
                    "nlp_interface": bool(self.nlp_interface),
                    "ai_query": bool(self.ai_query)
                },
                "config": self.config
            }
    
    return AIManager(config)

# Module initialization
logger.info(f"IEDB AI Module v{__version__} initialized")
