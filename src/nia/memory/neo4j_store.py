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
                logger.info(f"Storing concept: {name} ({type})")
                result = await session.run(
                    """
                    MERGE (c:Concept {name: $name})
                    WITH c, $type as type
                    CALL {
                        WITH c, type
                        CALL {
                            WITH c
                            REMOVE c:Entity:Topic:Capability:Evolution:AISystem:Emotion:Belief:Synthesis:Goal:Pattern
                        }
                        WITH c, type
                        CALL {
                            WITH c, type
                            // Set caption for visualization
                            SET c.caption = c.name
                            
                            // Set labels based on type patterns
                            FOREACH (x IN CASE 
                                WHEN type CONTAINS 'entity' OR type CONTAINS 'object' THEN [1] 
                                ELSE [] END | 
                                SET c:Entity)
                            FOREACH (x IN CASE 
                                WHEN type CONTAINS 'topic' OR type CONTAINS 'subject' OR type CONTAINS 'theme' THEN [1] 
                                ELSE [] END | 
                                SET c:Topic)
                            FOREACH (x IN CASE 
                                WHEN type CONTAINS 'capability' OR type CONTAINS 'ability' OR type CONTAINS 'skill' THEN [1] 
                                ELSE [] END | 
                                SET c:Capability)
                            FOREACH (x IN CASE 
                                WHEN type CONTAINS 'evolution' OR type CONTAINS 'development' OR type CONTAINS 'growth' THEN [1] 
                                ELSE [] END | 
                                SET c:Evolution)
                            FOREACH (x IN CASE 
                                WHEN type CONTAINS 'system' OR type CONTAINS 'ai' OR type CONTAINS 'agent' THEN [1] 
                                ELSE [] END | 
                                SET c:AISystem)
                            FOREACH (x IN CASE 
                                WHEN type CONTAINS 'emotion' OR type CONTAINS 'affect' OR type CONTAINS 'feeling' THEN [1] 
                                ELSE [] END | 
                                SET c:Emotion)
                            FOREACH (x IN CASE 
                                WHEN type CONTAINS 'belief' OR type CONTAINS 'knowledge' OR type CONTAINS 'understanding' THEN [1] 
                                ELSE [] END | 
                                SET c:Belief)
                            FOREACH (x IN CASE 
                                WHEN type CONTAINS 'synthesis' OR type CONTAINS 'integration' OR type CONTAINS 'coordination' THEN [1] 
                                ELSE [] END | 
                                SET c:Synthesis)
                            FOREACH (x IN CASE 
                                WHEN type CONTAINS 'goal' OR type CONTAINS 'desire' OR type CONTAINS 'motivation' THEN [1] 
                                ELSE [] END | 
                                SET c:Goal)
                            FOREACH (x IN CASE 
                                WHEN type CONTAINS 'pattern' OR type CONTAINS 'structure' OR type CONTAINS 'organization' THEN [1] 
                                ELSE [] END | 
                                SET c:Pattern)
                        }
                    }
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
                    # Create all relationships in a single query
                    logger.info(f"Creating relationships for concept {name} to: {related}")
                    await session.run(
                        """
                        MATCH (c1:Concept {name: $name})
                        UNWIND $related as rel_name
                        MERGE (c2:Concept {name: rel_name})
                        MERGE (c1)-[:RELATED_TO]->(c2)
                        """,
                        name=name,
                        related=related
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

    async def count_concepts_by_label(self) -> Dict[str, int]:
        """Count concepts by label type."""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    CALL {
                        MATCH (c:Entity) RETURN count(c) as entity_count
                        UNION ALL
                        MATCH (c:Topic) RETURN count(c) as topic_count
                        UNION ALL
                        MATCH (c:Capability) RETURN count(c) as capability_count
                        UNION ALL
                        MATCH (c:Evolution) RETURN count(c) as evolution_count
                        UNION ALL
                        MATCH (c:AISystem) RETURN count(c) as system_count
                        UNION ALL
                        MATCH (c:Emotion) RETURN count(c) as emotion_count
                        UNION ALL
                        MATCH (c:Belief) RETURN count(c) as belief_count
                        UNION ALL
                        MATCH (c:Synthesis) RETURN count(c) as synthesis_count
                        UNION ALL
                        MATCH (c:Goal) RETURN count(c) as goal_count
                        UNION ALL
                        MATCH (c:Pattern) RETURN count(c) as pattern_count
                        UNION ALL
                        MATCH (c:Concept) RETURN count(c) as total_count
                    }
                    RETURN 
                        collect(entity_count)[0] as Entity,
                        collect(topic_count)[1] as Topic,
                        collect(capability_count)[2] as Capability,
                        collect(evolution_count)[3] as Evolution,
                        collect(system_count)[4] as AISystem,
                        collect(emotion_count)[5] as Emotion,
                        collect(belief_count)[6] as Belief,
                        collect(synthesis_count)[7] as Synthesis,
                        collect(goal_count)[8] as Goal,
                        collect(pattern_count)[9] as Pattern,
                        collect(total_count)[10] as Total
                    """
                )
                record = await result.single()
                if record:
                    counts = {
                        "Entity": record["Entity"],
                        "Topic": record["Topic"],
                        "Capability": record["Capability"],
                        "Evolution": record["Evolution"],
                        "AISystem": record["AISystem"],
                        "Emotion": record["Emotion"],
                        "Belief": record["Belief"],
                        "Synthesis": record["Synthesis"],
                        "Goal": record["Goal"],
                        "Pattern": record["Pattern"],
                        "Total": record["Total"]
                    }
                    # Log the counts
                    logger.info("Concept counts by label:")
                    for label, count in counts.items():
                        if count > 0:  # Only log non-zero counts
                            logger.info(f"  - {label}: {count}")
                    return counts
                return {}
                
        except Exception as e:
            logger.error(f"Error counting concepts by label: {str(e)}")
            return {}

    async def count_concepts(self) -> int:
        """Count total number of concepts."""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (c:Concept)
                    RETURN count(c) as count
                    """
                )
                record = await result.single()
                return record["count"] if record else 0
                
        except Exception as e:
            logger.error(f"Error counting concepts: {str(e)}")
            return 0

    async def count_relationships(self) -> int:
        """Count total number of relationships."""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    MATCH ()-[r:RELATED_TO]->()
                    RETURN count(r) as count
                    """
                )
                record = await result.single()
                return record["count"] if record else 0
                
        except Exception as e:
            logger.error(f"Error counting relationships: {str(e)}")
            return 0

    async def clear_concepts(self) -> None:
        """Clear all concepts and relationships."""
        try:
            async with self.driver.session() as session:
                await session.run(
                    """
                    MATCH (c:Concept)
                    DETACH DELETE c
                    """
                )
                
        except Exception as e:
            logger.error(f"Error clearing concepts: {str(e)}")

    async def clear_relationships(self) -> None:
        """Clear all relationships between concepts."""
        try:
            async with self.driver.session() as session:
                await session.run(
                    """
                    MATCH ()-[r:RELATED_TO]->()
                    DELETE r
                    """
                )
                
        except Exception as e:
            logger.error(f"Error clearing relationships: {str(e)}")

    async def clear_memories(self) -> None:
        """Clear all memory nodes."""
        try:
            async with self.driver.session() as session:
                await session.run(
                    """
                    MATCH (m:Memory)
                    DETACH DELETE m
                    """
                )
                
        except Exception as e:
            logger.error(f"Error clearing memories: {str(e)}")
