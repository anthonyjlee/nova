"""
Neo4j store implementation.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from neo4j import AsyncGraphDatabase, AsyncDriver

logger = logging.getLogger(__name__)

def serialize_datetime(obj: Any) -> Any:
    """Serialize datetime objects to ISO format strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj

class Neo4jMemoryStore:
    """Neo4j-based memory store."""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password"
    ):
        """Initialize Neo4j connection."""
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    
    async def store_concept(
        self,
        name: str,
        type: str,
        description: str
    ) -> None:
        """Store concept in graph."""
        try:
            # First try to find existing concept
            query = """
                MATCH (c:Concept {id: $concept_name})
                RETURN c
                """
            
            async with self.driver.session() as session:
                result = await session.run(
                    query,
                    concept_name=name
                )
                record = await result.single()
                
                if record:
                    # Update existing concept if type or description changed
                    update_query = """
                        MATCH (c:Concept {id: $concept_name})
                        SET c.type = $concept_type,
                            c.description = $concept_desc,
                            c.updated_at = datetime()
                        """
                    await session.run(
                        update_query,
                        concept_name=name,
                        concept_type=type,
                        concept_desc=description
                    )
                else:
                    # Create new concept
                    create_query = """
                        CREATE (c:Concept {
                            id: $concept_name,
                            type: $concept_type,
                            description: $concept_desc,
                            created_at: datetime()
                        })
                        """
                    await session.run(
                        create_query,
                        concept_name=name,
                        concept_type=type,
                        concept_desc=description
                    )
                
        except Exception as e:
            logger.warning(f"Error creating/updating concept {name}: {str(e)}")
            raise
    
    async def store_concept_relationship(
        self,
        concept_name: str,
        related_name: str,
        relationship_type: str = "RELATED_TO"
    ) -> None:
        """Store relationship between concepts."""
        try:
            # First ensure both concepts exist
            await self.store_concept(concept_name, "concept", "Automatically created concept")
            await self.store_concept(related_name, "concept", "Automatically created concept")
            
            # Then create relationship if it doesn't exist
            query = f"""
                    MATCH (c:Concept {{id: $concept_name}})
                    MATCH (r:Concept {{id: $related_name}})
                    MERGE (c)-[rel:{relationship_type}]->(r)
                    ON CREATE SET rel.created_at = datetime()
                    ON MATCH SET rel.updated_at = datetime()
                    """
            
            async with self.driver.session() as session:
                await session.run(
                    query,
                    concept_name=concept_name,
                    related_name=related_name
                )
                
        except Exception as e:
            logger.warning(
                f"Error creating relationship {concept_name}->{related_name}: {str(e)}"
            )
            raise
    
    async def store_memory(
        self,
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> None:
        """Store memory in graph."""
        try:
            # Serialize datetime objects
            content = serialize_datetime(content)
            metadata = serialize_datetime(metadata) if metadata else {}
            
            # Create memory node with unique ID
            query = """
                CREATE (m:Memory {
                    id: randomUUID(),
                    type: $memory_type,
                    content: $content,
                    metadata: $metadata,
                    created_at: datetime()
                })
                """
            
            async with self.driver.session() as session:
                await session.run(
                    query,
                    memory_type=memory_type,
                    content=str(content),
                    metadata=str(metadata)
                )
                
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            raise
    
    async def get_system_info(self, name: str) -> Optional[Dict]:
        """Get information about an AI system."""
        try:
            query = """
            MATCH (s:AISystem {name: $name})
            OPTIONAL MATCH (s)-[:HAS_CAPABILITY]->(c:Capability)
            WITH s, collect(c) as capabilities
            RETURN {
                id: s.id,
                name: s.name,
                type: s.type,
                created_at: toString(s.created_at),
                capabilities: [cap in capabilities | {
                    id: cap.id,
                    type: cap.type,
                    description: cap.description,
                    confidence: cap.confidence
                }]
            } as system
            """
            
            async with self.driver.session() as session:
                result = await session.run(query, name=name)
                record = await result.single()
                return record["system"] if record else None
                
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            raise
    
    async def get_system_relationships(self, name: str) -> List[Dict]:
        """Get relationships for an AI system."""
        try:
            query = """
            MATCH (s:AISystem {name: $name})
            OPTIONAL MATCH (s)-[r]->(other)
            RETURN {
                relationship_type: type(r),
                target_type: labels(other)[0],
                target_name: other.name,
                target_id: other.id,
                properties: {
                    transition_date: CASE 
                        WHEN r.transition_date IS NOT NULL 
                        THEN toString(r.transition_date) 
                        ELSE null 
                    END,
                    confidence: r.confidence,
                    context: r.context
                }
            } as relationship
            """
            
            async with self.driver.session() as session:
                result = await session.run(query, name=name)
                records = await result.fetch()
                return [r["relationship"] for r in records]
                
        except Exception as e:
            logger.error(f"Error getting system relationships: {str(e)}")
            raise
    
    async def get_capabilities(self) -> List[Dict]:
        """Get all capabilities in the system."""
        try:
            query = """
            MATCH (c:Capability)
            RETURN {
                id: c.id,
                type: c.type,
                description: c.description,
                confidence: c.confidence
            } as capability
            """
            
            async with self.driver.session() as session:
                result = await session.run(query)
                records = await result.fetch()
                return [r["capability"] for r in records]
                
        except Exception as e:
            logger.error(f"Error getting capabilities: {str(e)}")
            raise

    async def count_concepts(self) -> int:
        """Get total number of concepts."""
        try:
            query = "MATCH (c:Concept) RETURN count(c) as count"
            async with self.driver.session() as session:
                result = await session.run(query)
                record = await result.single()
                return record["count"] if record else 0
        except Exception as e:
            logger.error(f"Error counting concepts: {str(e)}")
            return 0
    
    async def cleanup(self) -> None:
        """Clean up graph store."""
        try:
            # Delete all nodes and relationships
            query = """
            MATCH (n)
            DETACH DELETE n
            """
            async with self.driver.session() as session:
                await session.run(query)
                logger.info("Cleaned up all nodes and relationships")
            
        except Exception as e:
            logger.error(f"Error cleaning up graph store: {str(e)}")
            raise
    
    def close(self) -> None:
        """Close Neo4j connection."""
        try:
            self.driver.close()
            logger.info("Closed Neo4j connection")
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {str(e)}")
            raise
