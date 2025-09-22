"""
IEDB API Module
==============
API endpoints and web services for IEDB.
Provides FastAPI-based REST API for all IEDB functionality.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("IEDB.API")

# Version information
__version__ = "2.0.0"
__author__ = "IEDB Development Team"

# API Configuration
API_CONFIG = {
    "title": "IEDB API",
    "description": "Intelligent Enterprise Database API",
    "version": __version__,
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "openapi_url": "/openapi.json",
    "cors": {
        "allow_origins": ["*"],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"]
    },
    "middleware": {
        "gzip": True,
        "cors": True,
        "trusted_host": True
    }
}

# API Tags for functional grouping
API_TAGS = [
    {
        "name": "System & Health",
        "description": "System status, health checks, and monitoring endpoints",
    },
    {
        "name": "Authentication",
        "description": "User authentication, login, logout, and session management",
    },
    {
        "name": "Tenant Management",
        "description": "Create, manage, and list tenants in the multi-tenant system",
    },
    {
        "name": "Database Operations",
        "description": "Database creation, table management, and primary/foreign key operations",
    },
    {
        "name": "Database Query System",
        "description": "Advanced SQL and MongoDB-style query execution with optimization",
    },
    {
        "name": "AI Query System",
        "description": "Natural language query processing, AI settings, and query history",
    },
    {
        "name": "AI Settings & Models",
        "description": "AI model management, selection, installation, and configuration",
    },
    {
        "name": "User Management",
        "description": "User creation, management, profiles, and authentication",
    },
    {
        "name": "File & Media Management",
        "description": "File upload, download, storage, and media handling",
    },
    {
        "name": "Security & ABAC",
        "description": "Security policies, ABAC rules, and access control management",
    },
    {
        "name": "Analytics & Insights", 
        "description": "Data analytics, insights generation, and reporting",
    },
    {
        "name": "Documentation",
        "description": "API documentation, help, and reference materials",
    }
]

try:
    # Try to import the main API components
    from .iedb_api import (
        app as iedb_app,
        verify_token
    )
    
    API_COMPONENTS_AVAILABLE = True
    logger.info("IEDB API components loaded successfully")
    
except ImportError as e:
    API_COMPONENTS_AVAILABLE = False
    logger.warning(f"Could not import API components: {e}")
    
    # Create placeholder
    iedb_app = None
    
    def verify_token(*args, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("API components not available")

try:
    # Try to import demo components
    from .demo_grouped_api import app as demo_app
    DEMO_AVAILABLE = True
    logger.info("Demo API available")
except ImportError as e:
    DEMO_AVAILABLE = False
    logger.warning(f"Demo API not available: {e}")
    demo_app = None

# Export main components
__all__ = [
    "iedb_app",
    "demo_app", 
    "verify_token",
    "API_CONFIG",
    "API_TAGS",
    "API_COMPONENTS_AVAILABLE",
    "DEMO_AVAILABLE"
]

def get_api_status():
    """Get the status of API components"""
    return {
        "version": __version__,
        "main_api_available": API_COMPONENTS_AVAILABLE,
        "demo_api_available": DEMO_AVAILABLE,
        "components": {
            "iedb_api": bool(iedb_app),
            "demo_api": bool(demo_app)
        },
        "config": API_CONFIG,
        "tags_count": len(API_TAGS)
    }

def create_api_server(config: Optional[Dict[str, Any]] = None, use_demo: bool = False):
    """Create API server instance"""
    config = config or API_CONFIG
    
    if use_demo and DEMO_AVAILABLE:
        logger.info("Using demo API server")
        return demo_app
    elif API_COMPONENTS_AVAILABLE:
        logger.info("Using main IEDB API server")
        return iedb_app
    else:
        raise RuntimeError("No API components available")

def get_available_apis():
    """Get list of available API applications"""
    apis = []
    
    if API_COMPONENTS_AVAILABLE:
        apis.append({
            "name": "iedb_api",
            "description": "Main IEDB API server",
            "app": iedb_app,
            "type": "production"
        })
    
    if DEMO_AVAILABLE:
        apis.append({
            "name": "demo_api", 
            "description": "Demo API with grouped functionality",
            "app": demo_app,
            "type": "demo"
        })
    
    return apis

def get_api_endpoints(app_name: str = "iedb_api"):
    """Get API endpoints for specified app"""
    if app_name == "iedb_api" and API_COMPONENTS_AVAILABLE:
        return {
            "app": iedb_app,
            "docs": "/docs",
            "redoc": "/redoc", 
            "openapi": "/openapi.json",
            "available": True
        }
    elif app_name == "demo_api" and DEMO_AVAILABLE:
        return {
            "app": demo_app,
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json", 
            "available": True
        }
    else:
        return {
            "app": None,
            "available": False,
            "error": f"API '{app_name}' not available"
        }

# Module initialization
logger.info(f"IEDB API Module v{__version__} initialized")
logger.info(f"Main API available: {API_COMPONENTS_AVAILABLE}")
logger.info(f"Demo API available: {DEMO_AVAILABLE}")