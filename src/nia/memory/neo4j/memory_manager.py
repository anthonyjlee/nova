"""
Neo4j memory node and relationship management.
"""

import logging
import json
from datetime import datetime
from neo4j import Session
from typing import Dict, List, Any, Optional
from ..memory_types import RelationshipTypes as RT

logger = logging.getLogger(__name__)

class Neo4jMemoryManager:
    """Manages memory nodes and relationships in Neo4j."""
    
    def __init__(self, session: Session):
        """Initialize memory manager."""
        self.session = session
    
    def create_memory(
        self,
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> str:
        """Create a memory node with basic relationships."""
        try:
            memory_id = f"{memory_type}_{datetime.now().isoformat()}"
            
            # Convert content and metadata to strings
            content_str = json.dumps(content, default=str)
            metadata_str = json.dumps(metadata or {}, default=str)
            
            # Create memory node and link to Nova
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
            
            result = self.session.run(
                query,
                memory_id=memory_id,
                memory_type=memory_type,
                content=content_str,
                metadata=metadata_str
            )
            
            record = result.single()
            if record is None:
                raise ValueError("Failed to create memory node")
            
            return record["memory_id"]
            
        except Exception as e:
            logger.error(f"Error creating memory: {str(e)}")
            raise
    
    def create_topic_relationships(
        self,
        memory_id: str,
        topics: List[str]
    ) -> None:
        """Create topic nodes and relationships."""
        try:
            for topic in topics:
                query = """
                MATCH (m:Memory {id: $memory_id})
                MERGE (t:Topic {id: $topic})
                CREATE (m)-[:HAS_TOPIC {
                    created_at: datetime()
                }]->(t)
                """
                
                self.session.run(
                    query,
                    memory_id=memory_id,
                    topic=topic
                )
        except Exception as e:
            logger.warning(f"Error creating topic relationships: {str(e)}")
    
    def search_memories(
        self,
        content_pattern: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories with their relationships."""
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
            
            // Get direct relationships
            OPTIONAL MATCH (m)-[r]->(n)
            WITH m, collect({{
                type: type(r),
                target_type: head(labels(n)),
                target_id: n.id,
                properties: properties(r)
            }}) as direct_rels
            
            // Get concepts
            OPTIONAL MATCH (m)-[:HAS_CONCEPT]->(c:Concept)
            WITH m, direct_rels, collect({{
                id: c.id,
                type: c.type,
                description: c.description
            }}) as concepts
            
            // Get topics
            OPTIONAL MATCH (m)-[:HAS_TOPIC]->(t:Topic)
            WITH m, direct_rels, concepts, collect(t.id) as topics
            
            RETURN {{
                id: m.id,
                type: m.type,
                content: m.content,
                metadata: m.metadata,
                created_at: toString(m.created_at),
                relationships: direct_rels,
                concepts: concepts,
                topics: topics
            }} as memory
            """
            
            result = self.session.run(query, params)
            return [dict(record["memory"]) for record in result]
            
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
    
    def cleanup_memories(self) -> None:
        """Remove all memory nodes and relationships."""
        try:
            self.session.run("MATCH (m:Memory) DETACH DELETE m")
            self.session.run("MATCH (t:Topic) DETACH DELETE t")
            logger.info("Cleaned up memory nodes and relationships")
        except Exception as e:
            logger.error(f"Error cleaning up memories: {str(e)}")
            raise
