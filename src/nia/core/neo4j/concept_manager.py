"""
Neo4j concept manager implementation.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

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

class ConceptManager:
    """Manager for concept operations in Neo4j."""
    
    def __init__(self, store):
        """Initialize concept manager."""
        self.store = store
    
    async def store_concept(
        self,
        name: str,
        type: str,
        description: str,
        related: Optional[List[str]] = None
    ) -> None:
        """Store concept in graph."""
        try:
            # Store concept
            await self.store.store_concept(
                name=name,
                type=type,
                description=description
            )
            
            # Store relationships
            if related:
                for related_name in related:
                    try:
                        await self.store.store_concept_relationship(
                            name,
                            related_name
                        )
                    except Exception as e:
                        logger.warning(
                            f"Error creating relationship {name}->{related_name}: {str(e)}"
                        )
                        # Continue even if relationship creation fails
            
        except Exception as e:
            logger.error(f"Error storing concept {name}: {str(e)}")
            raise
    
    async def get_concept(self, name: str) -> Optional[Dict]:
        """Get concept by name."""
        try:
            query = """
            MATCH (c:Concept {id: $name})
            OPTIONAL MATCH (c)-[r:RELATED_TO]->(other:Concept)
            WITH c, collect({
                name: other.id,
                type: other.type,
                description: other.description,
                relationship_type: type(r),
                created_at: toString(r.created_at)
            }) as related
            RETURN {
                name: c.id,
                type: c.type,
                description: c.description,
                related: related
            } as concept
            """
            
            async with self.store.driver.session() as session:
                result = await session.run(query, name=name)
                record = await result.single()
                return record["concept"] if record else None
                
        except Exception as e:
            logger.error(f"Error getting concept {name}: {str(e)}")
            raise
    
    async def get_related_concepts(
        self,
        name: str,
        relationship_type: Optional[str] = None,
        max_depth: int = 2
    ) -> List[Dict]:
        """Get concepts related to given concept."""
        try:
            # Build relationship pattern based on type
            rel_pattern = f"[r:{relationship_type}]" if relationship_type else "[r]"
            
            query = f"""
            MATCH (c:Concept {{id: $name}})
            CALL apoc.path.subgraphNodes(c, {{
                relationshipFilter: "{rel_pattern}",
                maxLevel: $max_depth
            }})
            YIELD node
            WITH node as related
            WHERE related.id <> $name
            RETURN {{
                name: related.id,
                type: related.type,
                description: related.description
            }} as concept
            """
            
            async with self.store.driver.session() as session:
                result = await session.run(
                    query,
                    name=name,
                    max_depth=max_depth
                )
                records = await result.fetch()
                return [r["concept"] for r in records]
                
        except Exception as e:
            logger.error(f"Error getting related concepts for {name}: {str(e)}")
            raise
    
    async def search_concepts(
        self,
        pattern: str,
        limit: int = 10
    ) -> List[Dict]:
        """Search concepts by pattern."""
        try:
            query = """
            CALL db.index.fulltext.queryNodes("concept_search", $pattern)
            YIELD node, score
            WITH node as concept, score
            RETURN {
                name: concept.id,
                type: concept.type,
                description: concept.description,
                score: score
            } as result
            ORDER BY score DESC
            LIMIT $limit
            """
            
            async with self.store.driver.session() as session:
                result = await session.run(
                    query,
                    pattern=pattern,
                    limit=limit
                )
                records = await result.fetch()
                return [r["result"] for r in records]
                
        except Exception as e:
            logger.error(f"Error searching concepts: {str(e)}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up concepts."""
        try:
            query = "MATCH (c:Concept) DETACH DELETE c"
            async with self.store.driver.session() as session:
                await session.run(query)
                logger.info("Cleaned up concept nodes and relationships")
                
        except Exception as e:
            logger.error(f"Error cleaning up concepts: {str(e)}")
            raise
