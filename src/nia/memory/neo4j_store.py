"""
Neo4j-based memory store implementation using structured types.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from neo4j import GraphDatabase, Driver
from .memory_types import (
    Memory, AISystem, Capability, Evolution,
    Neo4jSchema, Neo4jQuery, Neo4jQuerySet,
    DEFAULT_SCHEMA, DEFAULT_CAPABILITIES,
    NOVA, NIA, ECHO, RelationshipTypes as RT
)
from .llm_interface import LLMInterface

logger = logging.getLogger(__name__)

class Neo4jMemoryStore:
    """Neo4j-based memory store with structured types."""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
        llm: Optional[LLMInterface] = None
    ):
        """Initialize Neo4j connection."""
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.llm = llm or LLMInterface()
        self.initialize_schema()
        self.initialize_core_nodes()
    
    def initialize_schema(self) -> None:
        """Initialize Neo4j schema."""
        with self.driver.session() as session:
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT memory_id IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
                "CREATE CONSTRAINT task_id IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE",
                "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE",
                "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT capability_id IF NOT EXISTS FOR (c:Capability) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT evolution_id IF NOT EXISTS FOR (e:Evolution) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT system_id IF NOT EXISTS FOR (s:AISystem) REQUIRE s.id IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.error(f"Error creating constraint: {str(e)}")
    
    def initialize_core_nodes(self) -> None:
        """Initialize core system nodes."""
        with self.driver.session() as session:
            # Create AI systems
            systems_query = f"""
            MERGE (nova:AISystem {{id: $nova.id}})
            SET nova += $nova
            
            MERGE (nia:AISystem {{id: $nia.id}})
            SET nia += $nia
            
            MERGE (echo:AISystem {{id: $echo.id}})
            SET echo += $echo
            
            WITH nova, nia, echo
            MERGE (echo)-[r1:{RT.PREDECESSOR_OF}]->(nia)
            MERGE (nia)-[r2:{RT.PREDECESSOR_OF}]->(nova)
            SET r1.transition_date = datetime($nia_date),
                r2.transition_date = datetime($nova_date)
            """
            
            session.run(
                systems_query,
                nova=vars(NOVA),
                nia=vars(NIA),
                echo=vars(ECHO),
                nia_date=NIA.created_at.isoformat(),
                nova_date=NOVA.created_at.isoformat()
            )
            
            # Create capabilities
            capabilities_query = f"""
            UNWIND $capabilities as cap
            MERGE (c:Capability {{id: cap.id}})
            SET c += cap
            
            WITH c
            MATCH (nia:AISystem {{name: 'Nia'}})
            WHERE c.id in $nia_capabilities
            MERGE (nia)-[h:{RT.HAS_CAPABILITY}]->(c)
            SET h.confidence = 1.0,
                h.context = 'predecessor'
            """
            
            session.run(
                capabilities_query,
                capabilities=[vars(cap) for cap in DEFAULT_CAPABILITIES],
                nia_capabilities=NIA.capabilities
            )
    
    async def store_memory(
        self,
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> str:
        """Store a memory with all related nodes."""
        memory_id = f"{memory_type}_{datetime.now().isoformat()}"
        
        # Convert content and metadata to strings
        content_str = json.dumps(content, default=str)
        metadata_str = json.dumps(metadata or {}, default=str)
        
        # Create memory query
        query = """
        CREATE (m:Memory {
            id: $memory_id,
            type: $memory_type,
            content: $content,
            metadata: $metadata,
            created_at: datetime()
        })
        WITH m
        
        MATCH (nova:AISystem {name: 'Nova'})
        CREATE (m)-[:CREATED_BY {
            created_at: datetime()
        }]->(nova)
        RETURN m.id as memory_id
        """
        
        with self.driver.session() as session:
            try:
                result = session.run(
                    query,
                    memory_id=memory_id,
                    memory_type=memory_type,
                    content=content_str,
                    metadata=metadata_str
                )
                
                record = result.single()
                if record is None:
                    raise ValueError("Failed to create memory node")
                
                # Create similarity relationships in a separate query
                similarity_query = """
                MATCH (m:Memory {id: $memory_id})
                MATCH (prev:Memory)
                WHERE prev.id <> m.id
                WITH m, prev,
                     reduce(s = 0.0,
                           w in split(toLower(m.content), ' ') |
                           s + case when toLower(prev.content) contains w then 1.0 else 0.0 end
                     ) / size(split(toLower(m.content), ' ')) as similarity
                WHERE similarity > 0.3
                CREATE (m)-[:SIMILAR_TO {
                    score: similarity,
                    created_at: datetime()
                }]->(prev)
                """
                
                try:
                    session.run(similarity_query, memory_id=memory_id)
                except Exception as e:
                    logger.warning(f"Error creating similarity relationships: {str(e)}")
                
                return record["memory_id"]
                
            except Exception as e:
                logger.error(f"Error storing memory: {str(e)}")
                return await self._store_memory_basic(
                    memory_type,
                    content,
                    metadata
                )
    
    async def _store_memory_basic(
        self,
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> str:
        """Basic memory storage without advanced features."""
        memory_id = f"{memory_type}_{datetime.now().isoformat()}"
        
        query = """
        CREATE (m:Memory {
            id: $memory_id,
            type: $memory_type,
            content: $content,
            metadata: $metadata,
            created_at: datetime()
        })
        WITH m
        MATCH (nova:AISystem {name: 'Nova'})
        CREATE (m)-[:CREATED_BY]->(nova)
        RETURN m.id as memory_id
        """
        
        with self.driver.session() as session:
            try:
                result = session.run(
                    query,
                    memory_id=memory_id,
                    memory_type=memory_type,
                    content=json.dumps(content, default=str),
                    metadata=json.dumps(metadata or {}, default=str)
                )
                
                record = result.single()
                if record is None:
                    raise ValueError("Failed to create memory node")
                
                return record["memory_id"]
                
            except Exception as e:
                logger.error(f"Error in basic memory storage: {str(e)}")
                raise
    
    async def get_capabilities(self) -> List[Dict]:
        """Get all capabilities in the system."""
        try:
            query = """
            MATCH (c:Capability)
            OPTIONAL MATCH (s:AISystem)-[r:HAS_CAPABILITY]->(c)
            WITH c, collect({
                name: s.name,
                type: s.type,
                confidence: coalesce(r.confidence, 0.0)
            }) as systems
            RETURN {
                id: c.id,
                type: c.type,
                description: c.description,
                confidence: c.confidence,
                systems: systems
            } as capability
            """
            
            result = await self.query_graph(query)
            return [r["capability"] for r in result]
            
        except Exception as e:
            logger.error(f"Error getting capabilities: {str(e)}")
            return []
    
    async def search_memories(
        self,
        content_pattern: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search memories in the graph."""
        try:
            conditions = []
            params = {"limit": limit}
            
            if content_pattern:
                conditions.append("m.content CONTAINS $content")
                params["content"] = content_pattern
            
            if memory_type:
                conditions.append("m.type = $type")
                params["type"] = memory_type
            
            where_clause = " AND ".join(conditions) if conditions else "true"
            
            query = f"""
            MATCH (m:Memory)
            WHERE {where_clause}
            WITH m
            ORDER BY m.created_at DESC
            LIMIT $limit
            OPTIONAL MATCH (m)-[r]->(n)
            WITH m, collect({{
                type: type(r),
                target_type: head(labels(n)),
                target_id: n.id,
                properties: properties(r)
            }}) as rels
            RETURN {{
                id: m.id,
                type: m.type,
                content: m.content,
                metadata: m.metadata,
                created_at: toString(m.created_at),
                relationships: rels
            }} as memory
            """
            
            result = await self.query_graph(query, params)
            return [r["memory"] for r in result]
            
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
    
    async def query_graph(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Error querying graph: {str(e)}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up database."""
        try:
            with self.driver.session() as session:
                # Step 1: Drop all constraints first
                try:
                    constraints = session.run("SHOW CONSTRAINTS")
                    for constraint in constraints:
                        name = constraint.get('name', '')
                        if name:
                            session.run(f"DROP CONSTRAINT {name}")
                except Exception as e:
                    logger.warning(f"Error dropping constraints: {str(e)}")
                
                # Step 2: Remove all relationships
                session.run("MATCH ()-[r]-() DELETE r")
                
                # Step 3: Remove all nodes
                session.run("MATCH (n) DELETE n")
                
                # Step 4: Verify cleanup
                result = session.run("MATCH (n) RETURN count(n) as count")
                count = result.single()["count"]
                if count > 0:
                    logger.warning(f"Found {count} remaining nodes after cleanup")
                    
                    # Try one more time with DETACH DELETE
                    session.run("MATCH (n) DETACH DELETE n")
                    
                    # Verify again
                    result = session.run("MATCH (n) RETURN count(n) as count")
                    count = result.single()["count"]
                    if count > 0:
                        raise Exception(f"Failed to clean up {count} nodes")
                
                logger.info("Successfully cleaned up all nodes")
                
                # Step 5: Re-initialize schema
                self.initialize_schema()
                
                # Step 6: Re-initialize core nodes
                self.initialize_core_nodes()
                
                # Step 7: Verify initialization
                result = session.run("""
                    MATCH (n)
                    WITH labels(n) as labels, count(n) as count
                    RETURN labels, count
                """)
                
                for record in result:
                    logger.info(f"Initialized {record['count']} nodes with labels {record['labels']}")
                
                logger.info("Re-initialized Neo4j database")
            
        except Exception as e:
            logger.error(f"Error cleaning up Neo4j database: {str(e)}")
            raise
    
    def close(self) -> None:
        """Close Neo4j connection."""
        try:
            self.driver.close()
            logger.info("Closed Neo4j connection")
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {str(e)}")
            raise
