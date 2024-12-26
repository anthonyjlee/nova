"""Neo4j memory store."""

import logging
import asyncio
import random
from typing import Dict, List, Optional, Union
from datetime import datetime
from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, SessionExpired

from .json_utils import validate_json_structure
from .concept_utils import validate_concept_structure
from .memory_types import Memory, Concept

logger = logging.getLogger(__name__)

class Neo4jMemoryStore:
    """Neo4j memory store."""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password",
        max_retry_time: int = 30,
        retry_interval: int = 1,
        llm: Optional['LLMInterface'] = None
    ):
        """Initialize Neo4j store with connection settings."""
        self.uri = uri
        self.user = user
        self.password = password
        self.max_retry_time = max_retry_time
        self.retry_interval = retry_interval
        self.driver = AsyncGraphDatabase.driver(
            uri,
            auth=(user, password),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=60
        )
        
        # Initialize LLM interface if not provided
        if llm is None:
            from .llm_interface import LLMInterface
            self.llm = LLMInterface()
        else:
            self.llm = llm

    async def verify_database(self) -> Dict[str, bool]:
        """Verify database connection, plugins, and required indexes."""
        status = {
            "connection": False,
            "concept_index": False,
            "fulltext_index": False,
            "apoc": False,
            "gds": False
        }
        
        try:
            async with self.driver.session() as session:
                # Check connection
                result = await session.run("RETURN 1")
                await result.single()
                status["connection"] = True
                logger.info("Database connection verified")
                
                # Check plugins
                result = await session.run("CALL dbms.procedures()")
                procedures = [record["name"] async for record in result]
                
                # Check APOC
                if any(p.startswith("apoc.") for p in procedures):
                    status["apoc"] = True
                    logger.info("APOC plugin verified")
                else:
                    logger.warning("APOC plugin not found")
                
                # Check Graph Data Science
                if any(p.startswith("gds.") for p in procedures):
                    status["gds"] = True
                    logger.info("Graph Data Science plugin verified")
                else:
                    logger.warning("Graph Data Science plugin not found")
                
                # Check indexes
                result = await session.run("SHOW INDEXES")
                async for record in result:
                    index_name = record.get("name", "")
                    index_state = record.get("state", "")
                    
                    if "concept_name_idx" in index_name:
                        status["concept_index"] = index_state == "ONLINE"
                    elif "concept_search" in index_name:
                        status["fulltext_index"] = index_state == "ONLINE"
                
                if not status["concept_index"] or not status["fulltext_index"]:
                    logger.warning("Missing or offline indexes. Creating/Rebuilding...")
                    
                    # Drop existing indexes if they're not online
                    if not status["concept_index"]:
                        await session.run("DROP INDEX concept_name_idx IF EXISTS")
                    if not status["fulltext_index"]:
                        await session.run("CALL db.index.fulltext.drop('concept_search') IF EXISTS")
                    
                    # Create indexes
                    await session.run(
                        """
                        CREATE INDEX concept_name_idx IF NOT EXISTS FOR (c:Concept) ON (c.name);
                        CALL db.index.fulltext.createIfNot('concept_search', ['Concept'], ['name', 'description']);
                        """
                    )
                    
                    # Wait for indexes to come online
                    logger.info("Waiting for indexes to come online...")
                    while True:
                        result = await session.run("SHOW INDEXES")
                        indexes = [record async for record in result]
                        all_online = all(
                            record["state"] == "ONLINE" 
                            for record in indexes 
                            if "concept_name_idx" in record["name"] or "concept_search" in record["name"]
                        )
                        if all_online:
                            status["concept_index"] = status["fulltext_index"] = True
                            logger.info("All indexes are online")
                            break
                        await asyncio.sleep(1)
                else:
                    logger.info("All required indexes verified")
                
                # Log verification results
                logger.info("Database verification results:")
                for component, verified in status.items():
                    logger.info(f"  {component}: {'✓' if verified else '✗'}")
                
        except Exception as e:
            logger.error(f"Database verification failed: {str(e)}")
            if not status["connection"]:
                logger.error("Could not connect to Neo4j. Please check:")
                logger.error("1. Neo4j is running (docker-compose up)")
                logger.error("2. Credentials are correct (neo4j/password)")
                logger.error("3. Port 7687 is accessible")
            elif not (status["apoc"] and status["gds"]):
                logger.error("Required plugins not found. Please check:")
                logger.error("1. APOC and GDS plugins are in ./plugins/")
                logger.error("2. Plugin settings in docker-compose.yml")
                logger.error("3. Neo4j container logs for plugin loading errors")
        
        return status

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
                    concept = record["c"]
                    related = record["related"]
                    result = {
                        "name": concept["name"],
                        "type": concept["type"],
                        "description": concept["description"],
                        "related": related,
                        "is_consolidation": concept.get("is_consolidation", False)
                    }
                    
                    # Only include validation if there are validation fields
                    has_validation = False
                    validation = {}
                    
                    if concept.get("confidence") is not None:
                        validation["confidence"] = concept["confidence"]
                        has_validation = True
                    
                    for field in ["uncertainties", "supported_by", "contradicted_by", "needs_verification"]:
                        if concept.get(field):
                            validation[field] = concept[field]
                            has_validation = True
                    
                    # Handle consolidation validation
                    if concept.get("is_consolidation", False) and (not validation or validation.get("confidence", 0) < 0.8):
                        validation["confidence"] = 0.8
                        has_validation = True
                    
                    # Only include validation in result if there are validation fields
                    if has_validation:
                        result["validation"] = validation
                    
                    return result
                return None

        try:
            return await self._execute_with_retry(get_operation)
        except Exception as e:
            logger.error(f"Error getting concept {name}: {str(e)}")
            return None

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
        
        # Handle consolidation validation
        if is_consolidation:
            if not validation:
                validation = {"confidence": 0.8}
            elif "confidence" not in validation:
                validation["confidence"] = 0.8
            elif validation["confidence"] < 0.8:
                validation["confidence"] = 0.8

        async def store_operation():
            async with self.driver.session() as session:
                # Create concept node
                create_query = """
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
                
                # Add validation fields if present
                if validation:
                    for key, value in validation.items():
                        params[key] = value
                        create_query += f",\n    c.{key} = ${key}"
                
                await session.run(create_query, params)
                
                # Handle related concepts
                if related:
                    # Create related concepts that don't exist
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
                    
                    # Create relationships
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

        try:
            await self._execute_with_retry(store_operation)
        except Exception as e:
            logger.error(f"Error storing concept {name}: {str(e)}")
            raise

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
                
                concepts = []
                async for record in result:
                    concept = record["c"]
                    related = record["related"]
                    
                    concept_dict = {
                        "name": concept["name"],
                        "type": concept["type"],
                        "description": concept["description"],
                        "related": related,
                        "is_consolidation": concept.get("is_consolidation", False)
                    }
                    
                    # Handle validation
                    validation = {}
                    if concept.get("confidence") is not None:
                        validation["confidence"] = concept["confidence"]
                    for field in ["uncertainties", "supported_by", "contradicted_by", "needs_verification"]:
                        if concept.get(field):
                            validation[field] = concept[field]
                    
                    if validation:
                        concept_dict["validation"] = validation
                    
                    concepts.append(concept_dict)
                
                return concepts

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
                    RETURN r, collect(r2.name) as related
                    """,
                    name=name
                )
                
                concepts = []
                async for record in result:
                    concept = record["r"]
                    related = record["related"]
                    
                    concept_dict = {
                        "name": concept["name"],
                        "type": concept["type"],
                        "description": concept["description"],
                        "related": related,
                        "is_consolidation": concept.get("is_consolidation", False)
                    }
                    
                    # Handle validation
                    validation = {}
                    if concept.get("confidence") is not None:
                        validation["confidence"] = concept["confidence"]
                    for field in ["uncertainties", "supported_by", "contradicted_by", "needs_verification"]:
                        if concept.get(field):
                            validation[field] = concept[field]
                    
                    if validation:
                        concept_dict["validation"] = validation
                    
                    concepts.append(concept_dict)
                
                return concepts

        try:
            return await self._execute_with_retry(get_operation)
        except Exception as e:
            logger.error(f"Error getting related concepts for {name}: {str(e)}")
            return []

    async def search_concepts(self, query: str) -> List[Dict]:
        """Search concepts using full-text search."""
        async def search_operation():
            async with self.driver.session() as session:
                # First ensure the fulltext index exists
                await session.run(
                    """
                    CALL db.index.fulltext.createIfNot('concept_search', ['Concept'], ['name', 'description'])
                    """
                )
                
                # Use a more flexible search query that includes both name and description
                result = await session.run(
                    """
                    MATCH (c:Concept)
                    WHERE c.name CONTAINS $query OR c.description CONTAINS $query
                    OPTIONAL MATCH (c)-[:RELATED_TO]->(r:Concept)
                    RETURN c, collect(r.name) as related
                    """,
                    query=query
                )
                
                concepts = []
                async for record in result:
                    concept = record["c"]
                    related = record["related"]
                    
                    concept_dict = {
                        "name": concept["name"],
                        "type": concept["type"],
                        "description": concept["description"],
                        "related": related,
                        "is_consolidation": concept.get("is_consolidation", False)
                    }
                    
                    # Handle validation
                    validation = {}
                    if concept.get("confidence") is not None:
                        validation["confidence"] = concept["confidence"]
                    for field in ["uncertainties", "supported_by", "contradicted_by", "needs_verification"]:
                        if concept.get(field):
                            validation[field] = concept[field]
                    
                    if validation:
                        concept_dict["validation"] = validation
                    
                    concepts.append(concept_dict)
                
                return concepts

        try:
            return await self._execute_with_retry(search_operation)
        except Exception as e:
            logger.error(f"Error searching concepts with query {query}: {str(e)}")
            return []

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

    async def _execute_with_retry(self, operation):
        """Execute Neo4j operation with retry logic."""
        start_time = datetime.now()
        last_error = None
        attempt = 0
        
        while (datetime.now() - start_time).total_seconds() < self.max_retry_time:
            try:
                # Check driver health
                if not self.driver or not await self._check_connection():
                    logger.warning("Neo4j driver unhealthy, recreating...")
                    await self._recreate_driver()
                
                attempt += 1
                try:
                    result = await operation()
                    if attempt > 1:
                        logger.info(f"Operation succeeded after {attempt} attempts")
                    return result
                except (ServiceUnavailable, SessionExpired) as e:
                    last_error = e
                    logger.warning(f"Neo4j operation failed (attempt {attempt}): {str(e)}")
                    
                    # Exponential backoff with jitter
                    delay = min(self.retry_interval * (2 ** (attempt - 1)), 10)  # Cap at 10 seconds
                    jitter = random.uniform(0, 0.1 * delay)  # 10% jitter
                    await asyncio.sleep(delay + jitter)
                    
                    # Force driver recreation on connection errors
                    await self._recreate_driver()
                    continue
                    
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error during retry: {str(e)}")
                break
                
        error_msg = f"Operation failed after {attempt} attempts over {self.max_retry_time}s: {str(last_error)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    async def _check_connection(self) -> bool:
        """Check if the Neo4j connection is healthy."""
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1")
                await result.single()
                return True
        except Exception as e:
            logger.warning(f"Connection check failed: {str(e)}")
            return False
            
    async def _recreate_driver(self):
        """Recreate the Neo4j driver with current settings."""
        try:
            if self.driver:
                await self.driver.close()
        except Exception as e:
            logger.warning(f"Error closing existing driver: {str(e)}")
            
        self.driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=60
        )
    
    async def close(self):
        """Close Neo4j connection."""
        await self.driver.close()

    async def store_concept_from_json(self, data: Union[str, Dict]) -> None:
        """Store concept(s) from JSON data with validation."""
        try:
            validated = validate_json_structure(data)
            if isinstance(validated, list):
                # Store multiple concepts
                stored = 0
                errors = 0
                for concept in validated:
                    try:
                        validation = concept.get("validation", {})
                        is_consolidation = concept.get("is_consolidation", False)
                        
                        # Add default validation for consolidated concepts
                        if is_consolidation:
                            if not validation:
                                validation = {"confidence": 0.8}
                            elif "confidence" not in validation:
                                validation["confidence"] = 0.8
                            elif validation["confidence"] < 0.8:
                                validation["confidence"] = 0.8
                        
                        # Store concept
                        await self.store_concept(
                            name=concept["name"],
                            type=concept["type"],
                            description=concept["description"],
                            related=concept.get("related"),
                            validation=validation,
                            is_consolidation=is_consolidation
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
                # Store single concept
                validation = validated.get("validation", {})
                is_consolidation = validated.get("is_consolidation", False)
                
                # Add default validation for consolidated concepts
                if is_consolidation:
                    if not validation:
                        validation = {"confidence": 0.8}
                    elif "confidence" not in validation:
                        validation["confidence"] = 0.8
                    elif validation["confidence"] < 0.8:
                        validation["confidence"] = 0.8
                
                # Store concept
                await self.store_concept(
                    name=validated["name"],
                    type=validated["type"],
                    description=validated["description"],
                    related=validated.get("related"),
                    validation=validation,
                    is_consolidation=is_consolidation
                )
                logger.info(f"Successfully stored concept {validated['name']}")
        except Exception as e:
            logger.error(f"Error storing concepts from JSON: {str(e)}")
            raise
