"""Base Neo4j store implementation."""

import logging
from typing import Optional, Tuple, Dict, Any
from neo4j import AsyncGraphDatabase, AsyncDriver

logger = logging.getLogger(__name__)

_drivers: Dict[str, AsyncDriver] = {}

async def get_neo4j_driver(uri: str = "neo4j://0.0.0.0:7687", auth: Tuple[str, str] = ("neo4j", "password")) -> AsyncDriver:
    """Get or create Neo4j driver."""
    global _drivers
    key = f"{uri}:{auth[0]}"
    if key not in _drivers:
        _drivers[key] = AsyncGraphDatabase.driver(uri, auth=auth)
    return _drivers[key]

async def reset_neo4j_driver(uri: str = "neo4j://0.0.0.0:7687", auth: Tuple[str, str] = ("neo4j", "password")):
    """Reset Neo4j driver connection."""
    global _drivers
    key = f"{uri}:{auth[0]}"
    if key in _drivers:
        try:
            await _drivers[key].close()
        except Exception as e:
            logger.error(f"Error closing Neo4j driver: {str(e)}")
        finally:
            del _drivers[key]

class Neo4jBaseStore:
    """Base class for Neo4j stores."""
    
    def __init__(self, uri: str = "neo4j://0.0.0.0:7687", auth: Tuple[str, str] = ("neo4j", "password"), **kwargs):
        """Initialize store."""
        self.uri = uri
        self.auth = auth
        self.driver = None
        self.kwargs = kwargs
        
    async def connect(self):
        """Connect to Neo4j."""
        self.driver = await get_neo4j_driver(self.uri, self.auth)
        
    async def close(self):
        """Close Neo4j connection."""
        if self.driver:
            await reset_neo4j_driver(self.uri, self.auth)
            self.driver = None
            
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
