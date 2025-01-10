"""Base Neo4j store implementation."""

import logging
from typing import Optional, Tuple, Dict, Any
from neo4j import AsyncGraphDatabase, AsyncDriver
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

_drivers: Dict[str, AsyncDriver] = {}

async def get_neo4j_driver(uri: str = "bolt://localhost:7687", auth: Tuple[str, str] = ("neo4j", "password")) -> AsyncDriver:
    """Get or create Neo4j driver."""
    global _drivers
    key = f"{uri}:{auth[0]}"
    if key not in _drivers:
        try:
            driver = AsyncGraphDatabase.driver(
                uri,
                auth=auth,
                max_connection_lifetime=3600
            )
            await driver.verify_connectivity()
            _drivers[key] = driver
        except Exception as e:
            logger.error(f"Failed to create Neo4j driver: {str(e)}")
            raise
    return _drivers[key]

async def reset_neo4j_driver(uri: str = "bolt://localhost:7687", auth: Tuple[str, str] = ("neo4j", "password")):
    """Reset Neo4j driver connection."""
    global _drivers
    key = f"{uri}:{auth[0]}"
    if key in _drivers:
        try:
            driver = _drivers[key]
            await driver.close()
            del _drivers[key]
        except Exception as e:
            logger.error(f"Error closing Neo4j driver: {str(e)}")
            _drivers.pop(key, None)

class Neo4jBaseStore:
    """Base class for Neo4j stores."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", auth: Tuple[str, str] = ("neo4j", "password"), **kwargs):
        """Initialize store."""
        self.uri = uri
        self.auth = auth
        self.driver = None
        self.kwargs = kwargs
        
    async def connect(self):
        """Connect to Neo4j."""
        try:
            if not self.driver:
                logger.info("Creating new Neo4j driver")
                self.driver = AsyncGraphDatabase.driver(
                    self.uri,
                    auth=self.auth,
                    max_connection_lifetime=3600
                )
                logger.info("Verifying Neo4j connectivity")
                await self.driver.verify_connectivity()
                logger.info("Successfully connected to Neo4j")
                
                # Create database if it doesn't exist
                try:
                    logger.info("Creating database if it doesn't exist")
                    async with self.driver.session(database="system") as session:
                        await session.run("CREATE DATABASE neo4j IF NOT EXISTS")
                        logger.info("Database created or already exists")
                except Exception as db_error:
                    logger.warning(f"Error creating database: {str(db_error)}")
                    # Continue even if database creation fails (might already exist)
                    pass
                    
                # Create constraints and indexes
                try:
                    logger.info("Creating constraints and indexes")
                    async with self.driver.session() as session:
                        # Create constraints
                        await session.run("""
                        CREATE CONSTRAINT agent_id IF NOT EXISTS
                        FOR (a:Agent) REQUIRE a.id IS UNIQUE
                        """)
                        await session.run("""
                        CREATE CONSTRAINT concept_name IF NOT EXISTS
                        FOR (c:Concept) REQUIRE c.name IS UNIQUE
                        """)
                        # Create indexes
                        await session.run("""
                        CREATE INDEX agent_type IF NOT EXISTS
                        FOR (a:Agent) ON (a.type)
                        """)
                        await session.run("""
                        CREATE INDEX concept_type IF NOT EXISTS
                        FOR (c:Concept) ON (c.type)
                        """)
                        logger.info("Constraints and indexes created")
                except Exception as schema_error:
                    logger.warning(f"Error creating schema: {str(schema_error)}")
                    # Continue even if schema creation fails
                    pass
            else:
                logger.info("Using existing Neo4j driver")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise
        
    async def close(self):
        """Close Neo4j connection."""
        if self.driver:
            try:
                await self.driver.close()
            except Exception as e:
                logger.error(f"Error closing Neo4j driver: {str(e)}")
            finally:
                self.driver = None
            
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def run_query(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        """Run Neo4j query.
        
        Args:
            query: Cypher query string
            parameters: Optional query parameters
            
        Returns:
            Query result records
        """
        if not self.driver:
            await self.connect()
            
        try:
            # Create session with database and access mode
            async with self.driver.session(
                database=self.kwargs.get("database", "neo4j"),
                default_access_mode=self.kwargs.get("access_mode", "WRITE")
            ) as session:
                # Run query and consume results immediately
                result = await session.run(query, parameters or {})
                try:
                    records = await result.data()
                finally:
                    # Ensure result is consumed
                    await result.consume()
                return records
        except Exception as e:
            logger.error(f"Error running query: {str(e)}")
            # Try to reconnect on failure
            try:
                await self.close()
                await self.connect()
            except Exception as reconnect_error:
                logger.error(f"Error reconnecting: {str(reconnect_error)}")
            raise
