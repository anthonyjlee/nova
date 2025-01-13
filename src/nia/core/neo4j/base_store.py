"""Base Neo4j store implementation."""

from typing import Dict, Any, List, Optional, Union
from neo4j import AsyncGraphDatabase, AsyncDriver
import logging
import asyncio
import json
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Global driver instance
_neo4j_driver: Optional[AsyncDriver] = None

def get_neo4j_driver() -> Optional[AsyncDriver]:
    """Get the global Neo4j driver instance."""
    global _neo4j_driver
    return _neo4j_driver

async def reset_neo4j_driver():
    """Reset the global Neo4j driver instance."""
    global _neo4j_driver
    if _neo4j_driver:
        await _neo4j_driver.close()
        _neo4j_driver = None

class Neo4jBaseStore:
    """Base store for Neo4j operations."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password", max_retry_time: int = 30, retry_interval: int = 1):
        """Initialize Neo4j store."""
        self.uri = uri
        self.user = user
        self.password = password
        self.max_retry_time = max_retry_time
        self.retry_interval = retry_interval
        self.driver: Optional[AsyncDriver] = None
        
    async def connect(self):
        """Connect to Neo4j with retry logic."""
        global _neo4j_driver
        retry_count = 0
        start_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                logger.info(f"Attempting to connect to Neo4j at {self.uri}")
                
                # Use global driver if available
                if _neo4j_driver:
                    self.driver = _neo4j_driver
                    await self.driver.verify_connectivity()
                    logger.info("Using existing Neo4j connection")
                    return
                
                # Create new driver
                self.driver = AsyncGraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password)
                )
                
                # Verify connection
                await self.driver.verify_connectivity()
                logger.info("Successfully connected to Neo4j")
                
                # Store as global driver
                _neo4j_driver = self.driver
                return
                
            except Exception as e:
                retry_count += 1
                elapsed_time = asyncio.get_event_loop().time() - start_time
                
                if elapsed_time >= self.max_retry_time:
                    logger.error(f"Failed to connect to Neo4j after {retry_count} attempts over {elapsed_time:.1f}s: {str(e)}")
                    raise
                    
                logger.warning(f"Connection attempt {retry_count} failed: {str(e)}. Retrying in {self.retry_interval}s...")
                await asyncio.sleep(self.retry_interval)
                
    async def close(self):
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
            self.driver = None
            
    async def run_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Run a Cypher query with parameters."""
        if not self.driver:
            logger.error("No Neo4j connection. Call connect() first.")
            raise RuntimeError("No Neo4j connection")
            
        try:
            logger.debug(f"Executing query: {query}")
            logger.debug(f"With parameters: {parameters}")
            
            async with self.driver.session() as session:
                result = await session.run(query, parameters or {})
                records = await result.data()
                
                logger.debug(f"Query returned {len(records)} records")
                return records
                
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise
            
    async def run_transaction(self, queries: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Run multiple queries in a transaction."""
        if not self.driver:
            logger.error("No Neo4j connection. Call connect() first.")
            raise RuntimeError("No Neo4j connection")
            
        try:
            logger.debug(f"Starting transaction with {len(queries)} queries")
            
            async with self.driver.session() as session:
                async with session.begin_transaction() as tx:
                    results = []
                    for query_dict in queries:
                        query = query_dict["query"]
                        parameters = query_dict.get("parameters", {})
                        
                        logger.debug(f"Executing query in transaction: {query}")
                        logger.debug(f"With parameters: {parameters}")
                        
                        result = await tx.run(query, parameters)
                        records = await result.data()
                        results.append(records)
                        
                    await tx.commit()
                    logger.debug("Transaction committed successfully")
                    return results
                    
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            logger.error(f"Queries: {queries}")
            raise

class Neo4jMemoryStore(Neo4jBaseStore):
    """Neo4j store for memory operations."""
    
    async def store_memory(self, memory_data: Dict[str, Any]) -> str:
        """Store memory data in Neo4j."""
        try:
            # Generate memory ID if not provided
            memory_id = memory_data.get("id", str(datetime.now().timestamp()))
            
            # Log incoming memory data
            logger.info("Storing memory with data:")
            logger.info(f"Memory ID: {memory_id}")
            logger.info(f"Raw memory data: {json.dumps(memory_data, indent=2)}")
            
            # Prepare parameters
            params = {
                "id": memory_id,
                "type": memory_data.get("type", "episodic"),
                "content": json.dumps(memory_data.get("content", {})),  # Serialize content for Neo4j
                "timestamp": memory_data.get("timestamp", datetime.now().isoformat()),
                "importance": memory_data.get("importance", 0.5)
            }
            
            # Log prepared parameters
            logger.info("Prepared Neo4j parameters:")
            logger.info(json.dumps(params, indent=2))
            
            # Create memory node
            query = """
            CREATE (m:Memory {
                id: $id,
                type: $type,
                content: $content,
                timestamp: $timestamp,
                importance: $importance
            })
            RETURN m
            """
            
            logger.info("Executing Neo4j query:")
            logger.info(query)
            
            result = await self.run_query(query, params)
            
            # Log result
            logger.info("Neo4j store result:")
            logger.info(json.dumps(result, indent=2))
            
            return memory_id
        except Exception as e:
            logger.error(f"Failed to store memory: {str(e)}")
            raise
