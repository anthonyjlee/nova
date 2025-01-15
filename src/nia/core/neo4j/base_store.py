"""Base Neo4j store implementation."""

from typing import Dict, Any, List, Optional, Union
from neo4j import AsyncGraphDatabase, AsyncDriver
import logging
import asyncio
import json
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from contextlib import asynccontextmanager

class Neo4jBaseStore:
    """Base store for Neo4j operations."""
    
    _driver_instance: Optional[AsyncDriver] = None
    _driver_lock = None
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password", max_retry_time: int = 30, retry_interval: int = 1):
        """Initialize Neo4j store."""
        self.uri = uri
        self.user = user
        self.password = password
        self.max_retry_time = max_retry_time
        self.retry_interval = retry_interval
        
        # Initialize lock if needed
        if Neo4jBaseStore._driver_lock is None:
            Neo4jBaseStore._driver_lock = asyncio.Lock()
        
    @property
    async def driver(self) -> AsyncDriver:
        """Get or create singleton driver instance with connection pooling."""
        if Neo4jBaseStore._driver_instance is None:
            async with Neo4jBaseStore._driver_lock:
                if Neo4jBaseStore._driver_instance is None:
                    retry_count = 0
                    start_time = asyncio.get_event_loop().time()
                    
                    while True:
                        try:
                            logger.info(f"Creating new Neo4j driver for {self.uri}")
                            driver = AsyncGraphDatabase.driver(
                                self.uri,
                                auth=(self.user, self.password),
                                max_connection_lifetime=300  # 5 minutes max connection lifetime
                            )
                            
                            # Verify connection
                            await driver.verify_connectivity()
                            Neo4jBaseStore._driver_instance = driver
                            logger.info("Successfully created Neo4j driver")
                            break
                            
                        except Exception as e:
                            retry_count += 1
                            elapsed_time = asyncio.get_event_loop().time() - start_time
                            
                            if elapsed_time >= self.max_retry_time:
                                logger.error(f"Failed to create Neo4j driver after {retry_count} attempts: {str(e)}")
                                raise
                                
                            logger.warning(f"Driver creation attempt {retry_count} failed: {str(e)}. Retrying...")
                            await asyncio.sleep(self.retry_interval)
                            
        return Neo4jBaseStore._driver_instance

    async def connect(self):
        """Initialize Neo4j connection."""
        try:
            # Get/create driver instance
            await self.driver
            logger.info("Neo4j connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j connection: {str(e)}")
            raise
                
    async def close(self):
        """Close Neo4j connection."""
        if Neo4jBaseStore._driver_instance:
            await Neo4jBaseStore._driver_instance.close()
            Neo4jBaseStore._driver_instance = None
            
    @asynccontextmanager
    async def transaction(self):
        """Context manager for Neo4j transactions."""
        driver = await self.driver
        async with driver.session() as session:
            async with session.begin_transaction() as tx:
                try:
                    yield tx
                    await tx.commit()
                except Exception as e:
                    await tx.rollback()
                    raise

    async def run_query(self, query: str, parameters: Optional[Dict[str, Any]] = None, _depth: int = 0) -> List[Dict[str, Any]]:
        """Run a Cypher query with parameters and circuit breaker."""
        # Circuit breaker
        if _depth > 2:  # Maximum recursion depth
            logger.error("Maximum recursion depth exceeded in Neo4j query")
            raise RuntimeError("Maximum recursion depth exceeded")
            
        try:
            driver = await self.driver
            logger.debug(f"Executing query: {query}")
            logger.debug(f"With parameters: {parameters}")
            
            async with driver.session() as session:
                result = await session.run(query, parameters or {})
                records = await result.data()
                
                logger.debug(f"Query returned {len(records)} records")
                return records
                
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise
            
    async def run_transaction(self, queries: List[Dict[str, Any]], _depth: int = 0) -> List[List[Dict[str, Any]]]:
        """Run multiple queries in a transaction with circuit breaker."""
        # Circuit breaker
        if _depth > 2:  # Maximum recursion depth
            logger.error("Maximum recursion depth exceeded in Neo4j transaction")
            raise RuntimeError("Maximum recursion depth exceeded")
            
        try:
            logger.debug(f"Starting transaction with {len(queries)} queries")
            
            async with self.transaction() as tx:
                results = []
                for query_dict in queries:
                    query = query_dict["query"]
                    parameters = query_dict.get("parameters", {})
                    
                    logger.debug(f"Executing query in transaction: {query}")
                    logger.debug(f"With parameters: {parameters}")
                    
                    result = await tx.run(query, parameters)
                    records = await result.data()
                    results.append(records)
                
                logger.debug("Transaction completed successfully")
                return results
                    
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            logger.error(f"Queries: {queries}")
            raise

class Neo4jMemoryStore(Neo4jBaseStore):
    """Neo4j store for memory operations."""
    
    async def store_memory(self, memory_data: Dict[str, Any], is_sync: bool = False) -> str:
        """Store memory data in Neo4j with minimal data."""
        try:
            # Extract essential fields
            memory_id = memory_data.get("id", str(datetime.now().timestamp()))
            
            # Create minimal content
            content = memory_data.get("content", {})
            if isinstance(content, dict):
                minimal_content = {
                    k: v for k, v in content.items()
                    if k in ["thread_id", "task_id", "message_id", "status"]
                }
            else:
                minimal_content = str(content)
            
            # Prepare minimal parameters
            params = {
                "id": memory_id,
                "type": memory_data.get("type", "episodic"),
                "content": json.dumps(minimal_content),  # Serialize minimal content
                "timestamp": memory_data.get("timestamp", datetime.now().isoformat())
            }
            
            # Log operation
            if not is_sync:
                logger.info(f"Storing memory {memory_id} with minimal data")
            
            # Create or update memory node
            query = """
            MERGE (m:Memory {id: $id})
            SET m.type = $type,
                m.content = $content,
                m.timestamp = $timestamp
            RETURN m
            """
            
            await self.run_query(query, params)
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {str(e)}")
            raise
            
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get memory data from Neo4j."""
        try:
            result = await self.run_query(
                """
                MATCH (m:Memory {id: $id})
                RETURN m
                """,
                {"id": memory_id}
            )
            
            if result and result[0]:
                memory_data = result[0]["m"]
                return {
                    "id": memory_id,
                    "type": memory_data.get("type", "episodic"),
                    "content": json.loads(memory_data.get("content", "{}")),
                    "timestamp": memory_data.get("timestamp")
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get memory: {str(e)}")
            return None
