"""Base Neo4j store with core database operations."""

import logging
import asyncio
import random
from typing import Any, Callable, Optional
from datetime import datetime
from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, SessionExpired

logger = logging.getLogger(__name__)

class Neo4jBaseStore:
    """Base class for Neo4j store operations."""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password",
        max_retry_time: int = 30,
        retry_interval: int = 1
    ):
        """Initialize Neo4j store with connection settings."""
        self.uri = uri
        self.user = user
        self.password = password
        self.max_retry_time = max_retry_time
        self.retry_interval = retry_interval
        self.driver = self._create_driver()

    def _create_driver(self) -> AsyncDriver:
        """Create a new Neo4j driver with current settings."""
        return AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=60
        )

    async def _check_connection(self) -> bool:
        """Check if the Neo4j connection is healthy."""
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1")
                await result.single()
                return True
        except Exception as e:
            logger.warning(f"Connection check failed: {str(e)}")
            return False

    async def _recreate_driver(self):
        """Recreate the Neo4j driver with current settings."""
        try:
            if self.driver:
                await self.driver.close()
        except Exception as e:
            logger.warning(f"Error closing existing driver: {str(e)}")
            
        self.driver = self._create_driver()

    async def _execute_with_retry(self, operation: Callable[[], Any]) -> Any:
        """Execute Neo4j operation with retry logic."""
        start_time = datetime.now()
        last_error = None
        attempt = 0
        
        while (datetime.now() - start_time).total_seconds() < self.max_retry_time:
            try:
                # Check driver health
                if not self.driver or not await self._check_connection():
                    logger.warning("Neo4j driver unhealthy, recreating...")
                    await self._recreate_driver()
                
                attempt += 1
                try:
                    result = await operation()
                    if attempt > 1:
                        logger.info(f"Operation succeeded after {attempt} attempts")
                    return result
                except (ServiceUnavailable, SessionExpired) as e:
                    last_error = e
                    logger.warning(f"Neo4j operation failed (attempt {attempt}): {str(e)}")
                    
                    # Exponential backoff with jitter
                    delay = min(self.retry_interval * (2 ** (attempt - 1)), 10)  # Cap at 10 seconds
                    jitter = random.uniform(0, 0.1 * delay)  # 10% jitter
                    await asyncio.sleep(delay + jitter)
                    
                    # Force driver recreation on connection errors
                    await self._recreate_driver()
                    continue
                    
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error during retry: {str(e)}")
                break
                
        error_msg = f"Operation failed after {attempt} attempts over {self.max_retry_time}s: {str(last_error)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    async def verify_database(self) -> dict[str, bool]:
        """Verify database connection, plugins, and required indexes."""
        status = {
            "connection": False,
            "concept_index": False,
            "fulltext_index": False,
            "apoc": False,
            "gds": False
        }
        
        try:
            async with self.driver.session() as session:
                # Check connection
                result = await session.run("RETURN 1")
                await result.single()
                status["connection"] = True
                logger.info("Database connection verified")
                
                # Check plugins
                result = await session.run("SHOW PROCEDURES")
                procedures = [record["name"] async for record in result]
                
                # Check APOC
                if any(p.startswith("apoc.") for p in procedures):
                    status["apoc"] = True
                    logger.info("APOC plugin verified")
                else:
                    logger.warning("APOC plugin not found")
                
                # Check Graph Data Science
                if any(p.startswith("gds.") for p in procedures):
                    status["gds"] = True
                    logger.info("Graph Data Science plugin verified")
                else:
                    logger.warning("Graph Data Science plugin not found")
                
                # Check indexes
                result = await session.run("SHOW INDEXES")
                async for record in result:
                    index_name = record.get("name", "")
                    index_state = record.get("state", "")
                    
                    if "concept_name_idx" in index_name:
                        status["concept_index"] = index_state == "ONLINE"
                    elif "concept_search" in index_name:
                        status["fulltext_index"] = index_state == "ONLINE"
                
                if not status["concept_index"] or not status["fulltext_index"]:
                    logger.warning("Missing or offline indexes. Creating/Rebuilding...")
                    
                    # Drop and recreate indexes
                    if not status["concept_index"]:
                        await session.run("DROP INDEX concept_name_idx IF EXISTS")
                        await session.run("CREATE INDEX concept_name_idx IF NOT EXISTS FOR (c:Concept) ON (c.name)")
                    
                    # Handle full-text index
                    if not status["fulltext_index"]:
                        try:
                            await session.run("CALL db.index.fulltext.drop('concept_search')")
                        except Exception:
                            pass  # Index might not exist
                        
                        try:
                            await session.run(
                                """
                                CALL db.index.fulltext.create(
                                    'concept_search',
                                    ['Concept'],
                                    ['name', 'description']
                                )
                                """
                            )
                        except Exception as e:
                            if "already exists" not in str(e):
                                raise
                    
                    # Wait for indexes to come online
                    logger.info("Waiting for indexes to come online...")
                    while True:
                        result = await session.run("SHOW INDEXES")
                        indexes = [record async for record in result]
                        all_online = all(
                            record["state"] == "ONLINE" 
                            for record in indexes 
                            if "concept_name_idx" in record["name"] or "concept_search" in record["name"]
                        )
                        if all_online:
                            status["concept_index"] = status["fulltext_index"] = True
                            logger.info("All indexes are online")
                            break
                        await asyncio.sleep(1)
                else:
                    logger.info("All required indexes verified")
                
                # Log verification results
                logger.info("Database verification results:")
                for component, verified in status.items():
                    logger.info(f"  {component}: {'✓' if verified else '✗'}")
                
        except Exception as e:
            logger.error(f"Database verification failed: {str(e)}")
            if not status["connection"]:
                logger.error("Could not connect to Neo4j. Please check:")
                logger.error("1. Neo4j is running (docker-compose up)")
                logger.error("2. Credentials are correct (neo4j/password)")
                logger.error("3. Port 7687 is accessible")
            elif not (status["apoc"] and status["gds"]):
                logger.error("Required plugins not found. Please check:")
                logger.error("1. APOC and GDS plugins are in ./plugins/")
                logger.error("2. Plugin settings in docker-compose.yml")
                logger.error("3. Neo4j container logs for plugin loading errors")
        
        return status

    async def close(self):
        """Close Neo4j connection."""
        await self.driver.close()
