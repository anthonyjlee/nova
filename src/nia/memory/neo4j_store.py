"""Neo4j memory store."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from neo4j import AsyncGraphDatabase, AsyncDriver
from .memory_types import Memory, Concept

logger = logging.getLogger(__name__)

class Neo4jMemoryStore:
    """Neo4j memory store."""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password"
    ):
        """Initialize Neo4j store."""
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    
    async def close(self):
        """Close Neo4j connection."""
        await self.driver.close()
    
    async def store_concept(
        self,
        name: str,
        type: str,
        description: str,
        related: Optional[List[str]] = None
    ) -> None:
        """Store concept in Neo4j."""
        try:
            async with self.driver.session() as session:
                # Create concept node
                await session.run(
                    """
                    MERGE (c:Concept {name: $name})
                    SET c.type = $type,
                        c.description = $description,
                        c.timestamp = datetime()
                    """,
                    name=name,
                    type=type,
                    description=description
                )
                
                # Create relationships to related concepts
                if related:
                    for rel in related:
                        await session.run(
                            """
                            MATCH (c1:Concept {name: $name1})
                            MERGE (c2:Concept {name: $name2})
                            MERGE (c1)-[:RELATED_TO]->(c2)
                            """,
                            name1=name,
                            name2=rel
                        )
                
        except Exception as e:
            logger.error(f"Error storing concept: {str(e)}")
    
    async def get_concept(self, name: str) -> Optional[Dict]:
        """Get concept by name."""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (c:Concept {name: $name})
                    OPTIONAL MATCH (c)-[:RELATED_TO]->(r:Concept)
                    RETURN c, collect(r.name) as related
                    """,
                    name=name
                )
                
                record = await result.single()
                if record:
                    concept = record["c"]
                    related = record["related"]
                    return {
                        "name": concept["name"],
                        "type": concept["type"],
                        "description": concept["description"],
                        "related": related
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting concept: {str(e)}")
            return None
    
    async def get_concepts_by_type(self, type: str) -> List[Dict]:
        """Get concepts by type."""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (c:Concept {type: $type})
                    OPTIONAL MATCH (c)-[:RELATED_TO]->(r:Concept)
                    RETURN c, collect(r.name) as related
                    """,
                    type=type
                )
                
                concepts = []
                async for record in result:
                    concept = record["c"]
                    related = record["related"]
                    concepts.append({
                        "name": concept["name"],
                        "type": concept["type"],
                        "description": concept["description"],
                        "related": related
                    })
                return concepts
                
        except Exception as e:
            logger.error(f"Error getting concepts by type: {str(e)}")
            return []
    
    async def get_related_concepts(self, name: str) -> List[Dict]:
        """Get concepts related to given concept."""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (c:Concept {name: $name})-[:RELATED_TO]->(r:Concept)
                    RETURN r
                    """,
                    name=name
                )
                
                concepts = []
                async for record in result:
                    concept = record["r"]
                    concepts.append({
                        "name": concept["name"],
                        "type": concept["type"],
                        "description": concept["description"]
                    })
                return concepts
                
        except Exception as e:
            logger.error(f"Error getting related concepts: {str(e)}")
            return []
    
    async def delete_concept(self, name: str) -> None:
        """Delete concept and its relationships."""
        try:
            async with self.driver.session() as session:
                await session.run(
                    """
                    MATCH (c:Concept {name: $name})
                    DETACH DELETE c
                    """,
                    name=name
                )
                
        except Exception as e:
            logger.error(f"Error deleting concept: {str(e)}")
    
    async def search_concepts(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """Search concepts by name or description."""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    CALL db.index.fulltext.queryNodes("concept_search", $query)
                    YIELD node, score
                    RETURN node, score
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    query=query,
                    limit=limit
                )
                
                concepts = []
                async for record in result:
                    concept = record["node"]
                    score = record["score"]
                    concepts.append({
                        "name": concept["name"],
                        "type": concept["type"],
                        "description": concept["description"],
                        "score": score
                    })
                return concepts
                
        except Exception as e:
            logger.error(f"Error searching concepts: {str(e)}")
            return []
