"""Neo4j concept store implementation."""

import logging
from typing import Dict, List, Optional, Union

from .base_store import Neo4jBaseStore
from .validation_handler import ValidationHandler
from ..json_utils import validate_json_structure
from ..concept_utils import validate_concept_structure

logger = logging.getLogger(__name__)

class ConceptStore(Neo4jBaseStore):
    """Handles concept storage and retrieval in Neo4j."""

    async def store_concept(
        self,
        name: str,
        type: str,
        description: str,
        related: Optional[List[str]] = None,
        validation: Optional[Dict] = None,
        is_consolidation: bool = False
    ) -> None:
        """Store a concept with validation."""
        # Validate concept data
        validate_concept_structure({
            "name": name,
            "type": type,
            "description": description,
            "related": related or [],
            "validation": validation or {}
        })

        # Process validation data
        validation = ValidationHandler.process_validation(validation, is_consolidation)

        async def store_operation():
            async with self.driver.session() as session:
                # Build base query
                base_query = """
                MERGE (c:Concept {name: $name})
                SET c.type = $type,
                    c.description = $description,
                    c.is_consolidation = $is_consolidation
                """
                params = {
                    "name": name,
                    "type": type,
                    "description": description,
                    "is_consolidation": is_consolidation
                }

                # Add validation fields to query
                query = ValidationHandler.build_validation_query(
                    validation, is_consolidation, params, base_query
                )
                await session.run(query, params)

                # Handle related concepts
                if related:
                    await self._create_related_concepts(session, related)
                    await self._create_relationships(session, name, related)

        try:
            await self._execute_with_retry(store_operation)
        except Exception as e:
            logger.error(f"Error storing concept {name}: {str(e)}")
            raise

    async def _create_related_concepts(self, session, related: List[str]) -> None:
        """Create related concepts that don't exist."""
        for rel in related:
            await session.run(
                """
                MERGE (c:Concept {name: $name})
                ON CREATE SET c.type = 'pending',
                            c.description = 'Pending concept',
                            c.is_consolidation = false
                """,
                name=rel
            )

    async def _create_relationships(self, session, name: str, related: List[str]) -> None:
        """Create relationships between concepts."""
        await session.run(
            """
            MATCH (c:Concept {name: $name})
            UNWIND $related as rel_name
            MATCH (r:Concept {name: rel_name})
            MERGE (c)-[:RELATED_TO]->(r)
            """,
            name=name,
            related=related
        )

    async def get_concept(self, name: str) -> Optional[Dict]:
        """Get concept by name with retry logic."""
        async def get_operation():
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
                    return self._process_concept_record(record)
                return None

        try:
            return await self._execute_with_retry(get_operation)
        except Exception as e:
            logger.error(f"Error getting concept {name}: {str(e)}")
            return None

    def _process_concept_record(self, record) -> Dict:
        """Process a Neo4j record into a concept dictionary."""
        concept = record["c"]
        related = record["related"]
        result = {
            "name": concept["name"],
            "type": concept["type"],
            "description": concept["description"],
            "related": related,
            "is_consolidation": concept.get("is_consolidation", False)
        }

        # Extract validation data if present
        validation = ValidationHandler.extract_validation(concept)
        if validation:
            result["validation"] = validation

        return result

    async def get_concepts_by_type(self, type: str) -> List[Dict]:
        """Get all concepts of a specific type."""
        async def get_operation():
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (c:Concept {type: $type})
                    OPTIONAL MATCH (c)-[:RELATED_TO]->(r:Concept)
                    RETURN c, collect(r.name) as related
                    """,
                    type=type
                )
                
                return [
                    self._process_concept_record(record)
                    async for record in result
                ]

        try:
            return await self._execute_with_retry(get_operation)
        except Exception as e:
            logger.error(f"Error getting concepts by type {type}: {str(e)}")
            return []

    async def get_related_concepts(self, name: str) -> List[Dict]:
        """Get all concepts related to the given concept."""
        async def get_operation():
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (c:Concept {name: $name})-[:RELATED_TO]->(r:Concept)
                    OPTIONAL MATCH (r)-[:RELATED_TO]->(r2:Concept)
                    RETURN r as c, collect(r2.name) as related
                    """,
                    name=name
                )
                
                return [
                    self._process_concept_record(record)
                    async for record in result
                ]

        try:
            return await self._execute_with_retry(get_operation)
        except Exception as e:
            logger.error(f"Error getting related concepts for {name}: {str(e)}")
            return []

    async def search_concepts(self, query: str) -> List[Dict]:
        """Search concepts using full-text search."""
        async def search_operation():
            async with self.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (c:Concept)
                    WHERE c.name = $query OR c.description = $query OR
                          toLower(c.name) CONTAINS toLower($query) OR 
                          toLower(c.description) CONTAINS toLower($query)
                    OPTIONAL MATCH (c)-[:RELATED_TO]->(r:Concept)
                    RETURN c, collect(r.name) as related
                    """,
                    {"query": query}
                )
                
                return [
                    self._process_concept_record(record)
                    async for record in result
                ]

        try:
            return await self._execute_with_retry(search_operation)
        except Exception as e:
            logger.error(f"Error searching concepts with query {query}: {str(e)}")
            return []

    async def store_concept_from_json(self, data: Union[str, Dict]) -> None:
        """Store concept(s) from JSON data with validation."""
        try:
            validated = validate_json_structure(data)
            if isinstance(validated, dict) and "concepts" in validated:
                validated = validated["concepts"]
            
            if isinstance(validated, list):
                # Store multiple concepts
                stored = 0
                errors = 0
                for concept in validated:
                    try:
                        await self.store_concept(
                            name=concept["name"],
                            type=concept["type"],
                            description=concept["description"],
                            related=concept.get("related"),
                            validation=concept.get("validation"),
                            is_consolidation=concept.get("is_consolidation", False)
                        )
                        stored += 1
                    except Exception as e:
                        logger.error(f"Error storing concept {concept.get('name', 'unknown')}: {str(e)}")
                        errors += 1
                
                if errors > 0:
                    logger.warning(f"Stored {stored} concepts with {errors} errors")
                else:
                    logger.info(f"Successfully stored {stored} concepts")
            else:
                await self.store_concept(
                    name=validated["name"],
                    type=validated["type"],
                    description=validated["description"],
                    related=validated.get("related"),
                    validation=validated.get("validation"),
                    is_consolidation=validated.get("is_consolidation", False)
                )
                logger.info(f"Successfully stored concept {validated['name']}")
        except Exception as e:
            logger.error(f"Error storing concepts from JSON: {str(e)}")
            raise

    async def count_concepts(self) -> int:
        """Count total number of concepts in the database."""
        async def count_operation():
            async with self.driver.session() as session:
                result = await session.run("MATCH (n:Concept) RETURN count(n) as count")
                record = await result.single()
                return record["count"] if record else 0

        try:
            return await self._execute_with_retry(count_operation)
        except Exception as e:
            logger.error(f"Error counting concepts: {str(e)}")
            return 0

    async def count_concepts_by_label(self) -> Dict[str, int]:
        """Count concepts grouped by label/type."""
        async def count_operation():
            async with self.driver.session() as session:
                result = await session.run("""
                    MATCH (n:Concept)
                    WITH n.type as type, count(n) as count
                    RETURN collect({type: type, count: count}) as counts
                """)
                record = await result.single()
                if record and record["counts"]:
                    return {item["type"]: item["count"] for item in record["counts"]}
                return {}

        try:
            return await self._execute_with_retry(count_operation)
        except Exception as e:
            logger.error(f"Error counting concepts by label: {str(e)}")
            return {}

    async def count_relationships(self) -> int:
        """Count total number of relationships in the database."""
        async def count_operation():
            async with self.driver.session() as session:
                result = await session.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r) as count")
                record = await result.single()
                return record["count"] if record else 0

        try:
            return await self._execute_with_retry(count_operation)
        except Exception as e:
            logger.error(f"Error counting relationships: {str(e)}")
            return 0

    async def clear_relationships(self) -> None:
        """Clear all relationships from the database."""
        async def clear_operation():
            async with self.driver.session() as session:
                await session.run("MATCH ()-[r:RELATED_TO]->() DELETE r")

        try:
            await self._execute_with_retry(clear_operation)
        except Exception as e:
            logger.error(f"Error clearing relationships: {str(e)}")
            raise

    async def clear_memories(self) -> None:
        """Clear all memories from the database."""
        async def clear_operation():
            async with self.driver.session() as session:
                await session.run("MATCH (n:Memory) DETACH DELETE n")

        try:
            await self._execute_with_retry(clear_operation)
        except Exception as e:
            logger.error(f"Error clearing memories: {str(e)}")
            raise

    async def clear_concepts(self) -> None:
        """Clear all concepts from the database."""
        async def clear_operation():
            async with self.driver.session() as session:
                await session.run("MATCH (n:Concept) DETACH DELETE n")

        try:
            await self._execute_with_retry(clear_operation)
        except Exception as e:
            logger.error(f"Error clearing concepts: {str(e)}")
            raise
