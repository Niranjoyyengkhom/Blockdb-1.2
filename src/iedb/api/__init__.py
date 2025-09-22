"""
IEDB API module - FastAPI implementation
"""
from typing import Dict, List, Any, Optional, Union
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


class APIManager:
    """API Manager for IEDB."""
    
    def __init__(self, db_instance=None):
        """Initialize the API manager.
        
        Args:
            db_instance: Optional database instance
        """
        self.app = None
        self.db = db_instance
        self.security_enabled = False
        self.auth_handler = None
    
    def setup_security(self, auth_handler):
        """Set up security for the API.
        
        Args:
            auth_handler: Authentication handler
        """
        self.security_enabled = True
        self.auth_handler = auth_handler
    
    def create_api(self, title: str = "IEDB API", version: str = "1.0.0") -> FastAPI:
        """Create a FastAPI instance.
        
        Args:
            title: API title
            version: API version
        
        Returns:
            FastAPI instance
        """
        app = FastAPI(
            title=title,
            description="IEDB - Intelligent Enterprise Database API",
            version=version,
            docs_url="/docs",
            redoc_url="/redoc",
        )
        
        self.app = app
        self._setup_routes()
        
        return app
    
    def _setup_routes(self):
        """Set up API routes."""
        app = self.app
        
        @app.get("/")
        async def root():
            return {"message": "IEDB API", "version": "2.0.0"}
        
        @app.get("/health")
        async def health_check():
            return {"status": "healthy"}
        
        # Add collection endpoints if database is available
        if self.db:
            # Define request models
            class CollectionCreate(BaseModel):
                name: str
            
            class DocumentCreate(BaseModel):
                data: Dict[str, Any]
            
            class DocumentUpdate(BaseModel):
                data: Dict[str, Any]
            
            class QueryModel(BaseModel):
                query: Dict[str, Any]
            
            # Define authentication dependency if security is enabled
            auth_dependency = []
            if self.security_enabled and self.auth_handler:
                auth_dependency = [Depends(self.auth_handler.get_current_user)]
            
            @app.post("/collections", status_code=status.HTTP_201_CREATED)
            async def create_collection(collection: CollectionCreate, *args, **kwargs):
                if len(auth_dependency) > 0:
                    # Use the first dependency result
                    user = kwargs.get("user")
                    if not user:
                        raise HTTPException(status_code=401, detail="Not authenticated")
                
                result = self.db.create_collection(collection.name)
                if not result:
                    raise HTTPException(status_code=400, detail="Collection already exists")
                return {"message": f"Collection {collection.name} created"}
            
            @app.post("/collections/{collection_name}/documents", status_code=status.HTTP_201_CREATED)
            async def insert_document(collection_name: str, document: DocumentCreate, *args, **kwargs):
                if len(auth_dependency) > 0:
                    # Check authentication
                    user = kwargs.get("user")
                    if not user:
                        raise HTTPException(status_code=401, detail="Not authenticated")
                
                doc_id = self.db.insert(collection_name, document.data)
                return {"id": doc_id, "message": "Document inserted"}
            
            @app.get("/collections/{collection_name}/documents")
            async def get_documents(collection_name: str, *args, **kwargs):
                if len(auth_dependency) > 0:
                    # Check authentication
                    user = kwargs.get("user")
                    if not user:
                        raise HTTPException(status_code=401, detail="Not authenticated")
                
                documents = self.db.find(collection_name)
                return {"documents": documents, "count": len(documents)}
            
            @app.post("/collections/{collection_name}/query")
            async def query_documents(collection_name: str, query: QueryModel, *args, **kwargs):
                if len(auth_dependency) > 0:
                    # Check authentication
                    user = kwargs.get("user")
                    if not user:
                        raise HTTPException(status_code=401, detail="Not authenticated")
                
                documents = self.db.find(collection_name, query.query)
                return {"documents": documents, "count": len(documents)}
            
            @app.put("/collections/{collection_name}/documents/{doc_id}")
            async def update_document(
                collection_name: str, doc_id: str, document: DocumentUpdate, *args, **kwargs
            ):
                if len(auth_dependency) > 0:
                    # Check authentication
                    user = kwargs.get("user")
                    if not user:
                        raise HTTPException(status_code=401, detail="Not authenticated")
                
                result = self.db.update(collection_name, doc_id, document.data)
                if not result:
                    raise HTTPException(status_code=404, detail="Document not found")
                return {"message": "Document updated"}
            
            @app.delete("/collections/{collection_name}/documents/{doc_id}")
            async def delete_document(collection_name: str, doc_id: str, *args, **kwargs):
                if len(auth_dependency) > 0:
                    # Check authentication
                    user = kwargs.get("user")
                    if not user:
                        raise HTTPException(status_code=401, detail="Not authenticated")
                
                result = self.db.delete(collection_name, doc_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Document not found")
                return {"message": "Document deleted"}


def create_app(db_instance=None, enable_security=False, auth_handler=None, 
               title: str = "IEDB API", version: str = "2.0.0") -> FastAPI:
    """Create a FastAPI instance with IEDB API.
    
    Args:
        db_instance: Database instance
        enable_security: Enable security features
        auth_handler: Authentication handler
        title: API title
        version: API version
    
    Returns:
        FastAPI instance
    """
    api_manager = APIManager(db_instance)
    
    if enable_security and auth_handler:
        api_manager.setup_security(auth_handler)
    
    return api_manager.create_api(title, version)