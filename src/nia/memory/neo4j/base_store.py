"""Base Neo4j store implementation."""

from typing import Dict, List, Optional, Any, cast
from typing_extensions import LiteralString
from datetime import datetime
import logging
from neo4j import AsyncGraphDatabase, AsyncDriver, Query
from neo4j.exceptions import Neo4jError

logger = logging.getLogger(__name__)

class Neo4jBaseStore:
    """Base class for Neo4j storage operations."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", password: str = "password"):
        """Initialize Neo4j connection."""
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[AsyncDriver] = None
        
    async def connect(self):
        """Connect to Neo4j database."""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            # Test connection
            await self.driver.verify_connectivity()
            # Test query to ensure we can execute queries
            async with self.driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run("RETURN 1")
                    await result.data()
            logger.info("Connected to Neo4j and verified query execution")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise
            
    async def close(self):
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
            self.driver = None
            logger.info("Closed Neo4j connection")
            
    async def execute(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute Cypher query."""
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        try:
            async with self.driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(cast(LiteralString, query), parameters=params or {})
                    records = await result.data()
                    return records
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}\nQuery: {query}\nParams: {params}")
            raise
            
    async def create_node(self, label: str, properties: Dict[str, Any]) -> str:
        """Create a new node."""
        query = f"""
        CREATE (n:{label} $properties)
        RETURN n
        """
        try:
            await self.execute(query, {"properties": properties})
            return properties.get("id", "")
        except Exception as e:
            logger.error(f"Node creation failed: {str(e)}")
            raise
            
    async def create_relationship(self, from_id: str, to_id: str, 
                                rel_type: str, properties: Optional[Dict] = None):
        """Create a relationship between nodes."""
        query = f"""
        MATCH (a), (b)
        WHERE a.id = $from_id AND b.id = $to_id
        CREATE (a)-[r:{rel_type} $properties]->(b)
        RETURN r
        """
        try:
            await self.execute(query, {
                "from_id": from_id,
                "to_id": to_id,
                "properties": properties or {}
            })
        except Exception as e:
            logger.error(f"Relationship creation failed: {str(e)}")
            raise
            
    async def get_node(self, node_id: str) -> Optional[Dict]:
        """Get node by ID."""
        query = """
        MATCH (n {id: $node_id})
        RETURN n
        """
        try:
            results = await self.execute(query, {"node_id": node_id})
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Node retrieval failed: {str(e)}")
            raise
            
    async def update_node(self, node_id: str, properties: Dict[str, Any]):
        """Update node properties."""
        query = """
        MATCH (n {id: $node_id})
        SET n += $properties
        RETURN n
        """
        try:
            await self.execute(query, {
                "node_id": node_id,
                "properties": properties
            })
        except Exception as e:
            logger.error(f"Node update failed: {str(e)}")
            raise
            
    async def delete_node(self, node_id: str):
        """Delete node by ID."""
        query = """
        MATCH (n {id: $node_id})
        DETACH DELETE n
        """
        try:
            await self.execute(query, {"node_id": node_id})
        except Exception as e:
            logger.error(f"Node deletion failed: {str(e)}")
            raise
            
    async def get_neighbors(self, node_id: str, rel_type: Optional[str] = None,
                          direction: str = "both") -> List[Dict]:
        """Get node neighbors."""
        if direction == "out":
            pattern = f"-[r{':' + rel_type if rel_type else ''}]->"
        elif direction == "in":
            pattern = f"<-[r{':' + rel_type if rel_type else ''}]-"
        else:  # both
            pattern = f"-[r{':' + rel_type if rel_type else ''}]-"
            
        query = f"""
        MATCH (n {{id: $node_id}}){pattern}(m)
        RETURN m
        """
        try:
            return await self.execute(query, {"node_id": node_id})
        except Exception as e:
            logger.error(f"Neighbor retrieval failed: {str(e)}")
            raise
            
    async def search_nodes(self, label: Optional[str] = None,
                          properties: Optional[Dict] = None) -> List[Dict]:
        """Search nodes by label and properties."""
        where_clause = ""
        if properties:
            conditions = [f"n.{k} = ${k}" for k in properties.keys()]
            where_clause = f"WHERE {' AND '.join(conditions)}"
            
        query = f"""
        MATCH (n{':' + label if label else ''})
        {where_clause}
        RETURN n
        """
        try:
            return await self.execute(query, properties or {})
        except Exception as e:
            logger.error(f"Node search failed: {str(e)}")
            raise
