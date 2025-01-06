"""Base vector store implementation."""

import logging
from typing import Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

logger = logging.getLogger(__name__)

_clients: Dict[str, QdrantClient] = {}

def get_vector_store(host: str = "localhost", port: int = 6333, **kwargs) -> QdrantClient:
    """Get or create Qdrant client."""
    global _clients
    key = f"{host}:{port}"
    if key not in _clients:
        _clients[key] = QdrantClient(host=host, port=port, **kwargs)
    return _clients[key]

async def reset_vector_store(host: str = "localhost", port: int = 6333):
    """Reset vector store connection."""
    global _clients
    key = f"{host}:{port}"
    if key in _clients:
        try:
            _clients[key].close()
        except Exception as e:
            logger.error(f"Error closing vector store: {str(e)}")
        finally:
            del _clients[key]

class VectorBaseStore:
    """Base class for vector stores."""
    
    def __init__(self, host: str = "localhost", port: int = 6333, **kwargs):
        """Initialize store."""
        self.host = host
        self.port = port
        self.kwargs = kwargs
        self.client = None
        
    def connect(self):
        """Connect to vector store."""
        self.client = get_vector_store(self.host, self.port, **self.kwargs)
        
    def close(self):
        """Close vector store connection."""
        if self.client:
            reset_vector_store(self.host, self.port)
            self.client = None
            
    async def __aenter__(self):
        """Async context manager entry."""
        self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.close()
