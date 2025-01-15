"""Neo4j concept store implementation with enhanced memory management."""

import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union, Any
import uuid
from collections import deque

from .base_store import Neo4jBaseStore
from .validation_handler import ValidationHandler
from ..types.json_utils.validation import validate_json_structure
from ..types.concept_utils.validation import validate_concept_structure

logger = logging.getLogger(__name__)

class ConceptStore(Neo4jBaseStore):
    """Handles concept storage and retrieval in Neo4j with memory optimization."""

    def __init__(self, uri: str, user: str = None, password: str = None, max_retry_time: int = 30, retry_interval: int = 1):
        """Initialize the concept store and create indexes."""
        super().__init__(
            uri=uri, 
            user=user,
            password=password,
            max_retry_time=max_retry_time,
            retry_interval=retry_interval
        )
        # Initialize indexes asynchronously
        self._init_task = None
        self.max_retry_time = max_retry_time
        self.retry_interval = retry_interval
        
        # Initialize memory pools
        self._concept_pool = {}  # Cache for frequently accessed concepts
        self._relationship_pool = {}  # Cache for frequently accessed relationships
        self._memory_pool = {}  # Cache for frequently accessed memories
        self._pool_lock = asyncio.Lock()
        self._max_pool_size = 1000  # Maximum number of items in each pool
        self._access_queue = deque()  # Queue for tracking access order
        
    async def _manage_pool(self, pool: Dict, key: str, value: Any):
        """Manage pool size and contents."""
        async with self._pool_lock:
            # Add new item
            pool[key] = value
            self._access_queue.append((pool, key))
            
            # Remove oldest items if pool is too large
            while len(self._access_queue) > self._max_pool_size:
                old_pool, old_key = self._access_queue.popleft()
                old_pool.pop(old_key, None)

    async def _execute_with_retry(self, operation):
        """Execute an operation with retry logic."""
        start_time = asyncio.get_event_loop().time()
        last_error = None
        
        while True:
            try:
                return await operation()
            except Exception as e:
                last_error = e
                current_time = asyncio.get_event_loop().time()
                if current_time - start_time >= self.max_retry_time:
                    logger.error(f"Operation failed after {self.max_retry_time} seconds: {str(e)}")
                    raise last_error
                logger.warning(f"Operation failed, retrying in {self.retry_interval} seconds: {str(e)}")
                await asyncio.sleep(self.retry_interval)

    async def _ensure_indexes(self):
        """Ensure indexes are created."""
        if not self._init_task:
            self._init_task = self.initialize_indexes()
            await self._init_task

    async def initialize_indexes(self) -> None:
        """Initialize required indexes for the concept store."""
        try:
            # Create indexes for efficient concept lookup
            await self.run_query("""
                CREATE INDEX concept_name IF NOT EXISTS
                FOR (c:Concept)
                ON (c.name)
            """)
            
            await self.run_query("""
                CREATE INDEX concept_type IF NOT EXISTS
                FOR (c:Concept)
                ON (c.type)
            """)
            
            await self.run_query("""
                CREATE INDEX concept_validation IF NOT EXISTS
                FOR (c:Concept)
                ON (c.validation_json)
            """)
            
            # Create composite index for relationship properties
            await self.run_query("""
                CREATE INDEX relationship_type IF NOT EXISTS
                FOR ()-[r:RELATED_TO]-()
                ON (r.type)
            """)
            
            logger.info("Successfully initialized concept store indexes")
        except Exception as e:
            logger.error(f"Error initializing indexes: {str(e)}")
            raise

    async def store_concept(
        self,
        name: str,
        type: str,
        description: str,
        related: Optional[List[str]] = None,
        validation: Optional[Dict] = None,
        is_consolidation: bool = False,
        _depth: int = 0
    ) -> None:
        """Store a concept with validation."""
        logger.info(f"Storing concept - Name: {name}, Type: {type}")
        
        # Ensure indexes are created
        await self._ensure_indexes()
        
        # Validate concept data
        try:
            validate_concept_structure({
                "name": name,
                "type": type,
                "description": description,
                "related": related or [],
                "validation": validation or {}
            })
            logger.info("Concept structure validation passed")
        except Exception as e:
            logger.error(f"Concept validation failed: {str(e)}")
            raise

        # Circuit breaker
        if _depth > 2:  # Maximum recursion depth
            logger.error("Maximum recursion depth exceeded in store_concept")
            raise RuntimeError("Maximum recursion depth exceeded")

        # Check if concept already exists in pool
        if name in self._concept_pool:
            logger.info(f"Concept {name} already in pool")
            return

        async def store_operation():
            # Process validation data with minimal fields
            validation_dict = ValidationHandler.process_validation(validation, is_consolidation)
            essential_validation = {
                "access_domain": validation_dict.get("access_domain", "general"),
                "domain": validation_dict.get("domain", "general"),
                "confidence": validation_dict.get("confidence", 0.5)
            }
            
            # Include minimal cross-domain information if present
            if validation and "cross_domain" in validation:
                essential_validation["cross_domain"] = {
                    "approved": validation["cross_domain"].get("approved", False),
                    "source_domain": validation["cross_domain"].get("source_domain", "general"),
                    "target_domain": validation["cross_domain"].get("target_domain", "general")
                }
            
            # Build base query with only essential properties
            base_query = """
            MERGE (c:Concept {name: $name})
            SET c.type = $type,
                c.description = $description,
                c.is_consolidation = $is_consolidation,
                c.validation = $validation_json,
                c.validation_json = $validation_json
            """
            params = {
                "name": name,
                "type": type,
                "description": description,
                "is_consolidation": is_consolidation,
                "validation_json": json.dumps(essential_validation)
            }

            query = base_query
            result = await self.run_query(query, params)

            # Process the result to get the stored concept
            stored_concept = None
            if result and len(result) > 0:
                stored_concept = self._process_concept_record({
                    "c": result[0]["c"],
                    "relationships": []
                })
                
                # Add to concept pool
                await self._manage_pool(self._concept_pool, name, stored_concept)

            # Handle related concepts in transaction
            if related:
                logger.info(f"Creating related concepts: {related}")
                async with self.transaction() as tx:
                    # Create related concepts
                    for rel in related:
                        # Create default validation with minimal data
                        default_validation = {
                            "confidence": 0.5,
                            "access_domain": "general",
                            "domain": "general"
                        }
                        
                        await tx.run(
                            """
                            MERGE (c:Concept {name: $name})
                            ON CREATE SET c.type = 'pending',
                                        c.description = 'Pending concept',
                                        c.is_consolidation = false,
                                        c.validation = $validation_json,
                                        c.validation_json = $validation_json
                            """,
                            {
                                "name": rel,
                                "validation_json": json.dumps(default_validation)
                            }
                        )
                    
                    # Create relationships
                    attributes = {
                        'bidirectional': True,
                        'type': 'RELATED_TO',
                        'validation': json.dumps({
                            "confidence": 0.9,
                            "access_domain": "general",
                            "domain": "general"
                        })
                    }
                    
                    await tx.run(
                        """
                        MATCH (c:Concept {name: $name})
                        UNWIND $related as rel_name
                        MATCH (r:Concept {name: rel_name})
                        MERGE (c)-[rel1:RELATED_TO]->(r)
                        SET rel1 += $attributes,
                            rel1.direction = 'forward',
                            rel1.bidirectional = true
                        WITH c, r
                        MERGE (r)-[rel2:RELATED_TO]->(c)
                        SET rel2 += $attributes,
                            rel2.direction = 'reverse',
                            rel2.bidirectional = true
                        """,
                        {
                            "name": name,
                            "related": related,
                            "attributes": attributes
                        }
                    )

            return stored_concept

        try:
            await self._execute_with_retry(store_operation)
        except Exception as e:
            logger.error(f"Error storing concept {name}: {str(e)}")
            raise


    async def store_relationship(self, source: str, target: str, rel_type: str, attributes: Dict = None, _depth: int = 0) -> None:
        """Store a relationship between concepts with optional attributes."""
        # Ensure indexes are created
        await self._ensure_indexes()
        
        # Convert complex attributes to string representation
        if attributes:
            attributes = {k: str(v) if isinstance(v, (dict, list)) else v 
                        for k, v in attributes.items()}
        
        # Check if relationship should be bidirectional
        is_bidirectional = attributes.get('bidirectional', False) if attributes else False
        
        # Ensure bidirectional flag is included in attributes
        if attributes is None:
            attributes = {}
        attributes['bidirectional'] = is_bidirectional
        
        # Add validation data with minimal fields
        attributes['validation'] = json.dumps({
            "confidence": 0.9,
            "access_domain": "general",
            "domain": "general"
        })
        
        # Circuit breaker
        if _depth > 2:  # Maximum recursion depth
            logger.error("Maximum recursion depth exceeded in store_relationship")
            raise RuntimeError("Maximum recursion depth exceeded")

        # Create both relationships in a single transaction
        async with self.transaction() as tx:
            await tx.run(
            """
            MATCH (s:Concept {name: $source})
            MATCH (t:Concept {name: $target})
            MERGE (s)-[r1:RELATED_TO]->(t)
            SET r1.type = $rel_type,
                r1 += $attributes,
                r1.direction = 'forward',
                r1.bidirectional = true
            MERGE (t)-[r2:RELATED_TO]->(s)
            SET r2.type = $rel_type,
                r2 += $attributes,
                r2.direction = 'reverse',
                r2.bidirectional = true
            """,
            {
                "source": source,
                "target": target,
                "rel_type": rel_type,
                "attributes": attributes,
                "is_bidirectional": is_bidirectional
            }
        )
        
        # Add to relationship pool
        rel_key = f"{source}-{target}"
        await self._manage_pool(self._relationship_pool, rel_key, {
            "source": source,
            "target": target,
            "type": rel_type,
            "attributes": attributes
        })

    async def get_concept(self, name: str, _depth: int = 0) -> Optional[Dict]:
        """Get concept by name with retry logic."""
        # Check concept pool first
        if name in self._concept_pool:
            return self._concept_pool[name]
            
        # Ensure indexes are created
        await self._ensure_indexes()
        
        # Circuit breaker
        if _depth > 2:  # Maximum recursion depth
            logger.error("Maximum recursion depth exceeded in get_concept")
            raise RuntimeError("Maximum recursion depth exceeded")

        async def get_operation():
            result = await self.run_query(
                """
                MATCH (c:Concept {name: $name})
                OPTIONAL MATCH (c)-[r1:RELATED_TO]->(related1:Concept)
                WHERE r1.bidirectional = true OR r1.direction = 'forward'
                OPTIONAL MATCH (c)<-[r2:RELATED_TO]-(related2:Concept)
                WHERE r2.bidirectional = true OR r2.direction = 'reverse'
                WITH c, 
                    collect(DISTINCT {
                        name: related1.name, 
                        type: r1.type, 
                        attributes: r1, 
                        direction: 'forward',
                        bidirectional: r1.bidirectional
                    }) as outgoing,
                    collect(DISTINCT {
                        name: related2.name, 
                        type: r2.type, 
                        attributes: r2, 
                        direction: 'reverse',
                        bidirectional: r2.bidirectional
                    }) as incoming
                RETURN c, outgoing + incoming as relationships
                """,
                {"name": name}
            )
            
            if result and len(result) > 0:
                concept = self._process_concept_record(result[0])
                # Add to concept pool
                await self._manage_pool(self._concept_pool, name, concept)
                return concept
            return None

        try:
            return await self._execute_with_retry(get_operation)
        except Exception as e:
            logger.error(f"Error getting concept {name}: {str(e)}")
            return None

    def _process_concept_record(self, record) -> Dict:
        """Process a Neo4j record into a concept dictionary with minimal data."""
        logger.info(f"Processing concept record: {record}")
        concept = record["c"]
        relationships = record.get("relationships", [])
        if relationships is None:
            relationships = []
        
        # Get validation from stored JSON with minimal fields
        validation = None
        for field in ["validation_json", "validation"]:
            try:
                if concept.get(field):
                    full_validation = json.loads(concept[field])
                    validation = {
                        "confidence": full_validation.get("confidence", 0.5),
                        "access_domain": full_validation.get("access_domain", "general"),
                        "domain": full_validation.get("domain", "general")
                    }
                    # Include minimal cross-domain info if present
                    if "cross_domain" in full_validation:
                        validation["cross_domain"] = {
                            "approved": full_validation["cross_domain"].get("approved", False),
                            "source_domain": full_validation["cross_domain"].get("source_domain", "general"),
                            "target_domain": full_validation["cross_domain"].get("target_domain", "general")
                        }
                    break
            except (json.JSONDecodeError, TypeError, KeyError):
                continue

        if validation is None:
            # Fallback to minimal validation
            validation = {
                "confidence": 0.5,
                "access_domain": "general",
                "domain": "general"
            }
        
        # Process relationships with proper null checking
        processed_relationships = []
        for rel in relationships[:100]:  # Limit relationships
            if rel and rel.get("name") is not None:
                processed_rel = self._process_relationship_record(rel)
                if processed_rel:
                    processed_relationships.append(processed_rel)
        
        result = {
            "name": concept["name"],
            "type": concept["type"],
            "description": concept["description"],
            "relationships": processed_relationships,
            "is_consolidation": concept.get("is_consolidation", False),
            "validation": validation
        }
        
        logger.info(f"Processed concept result: {result}")
        return result

    def _process_relationship_record(self, record) -> Dict:
        """Process a Neo4j relationship record with minimal data."""
        if not record:
            return None
            
        # Extract minimal attributes
        attributes = {}
        if isinstance(record.get('attributes'), dict):
            attributes = {
                k: v for k, v in record['attributes'].items()
                if k in ['bidirectional', 'type', 'direction']
            }
        elif isinstance(record.get('attributes'), tuple):
            # Handle tuple case
            _, attrs = record['attributes']
            if isinstance(attrs, dict):
                attributes = {
                    k: v for k, v in attrs.items()
                    if k in ['bidirectional', 'type', 'direction']
                }
            
        result = {
            'name': record.get('name'),
            'type': record.get('type'),
            'attributes': attributes,
            'direction': record.get('direction', 'forward')
        }
        
        # Include bidirectional flag if present
        if attributes.get('bidirectional'):
            result['bidirectional'] = True
            
        return result

    async def get_concepts_by_type(self, type: str) -> List[Dict]:
        """Get all concepts of a specific type."""
        # Ensure indexes are created
        await self._ensure_indexes()
        
        async def get_operation():
            result = await self.run_query(
                """
                MATCH (c:Concept {type: $type})
                OPTIONAL MATCH (c)-[r1:RELATED_TO]->(related1:Concept)
                WHERE r1.bidirectional = true OR r1.direction = 'forward'
                OPTIONAL MATCH (c)<-[r2:RELATED_TO]-(related2:Concept)
                WHERE r2.bidirectional = true OR r2.direction = 'reverse'
                WITH c, 
                    collect(DISTINCT {
                        name: related1.name, 
                        type: r1.type, 
                        attributes: r1, 
                        direction: 'forward',
                        bidirectional: r1.bidirectional
                    }) as outgoing,
                    collect(DISTINCT {
                        name: related2.name, 
                        type: r2.type, 
                        attributes: r2, 
                        direction: 'reverse',
                        bidirectional: r2.bidirectional
                    }) as incoming
                RETURN c, outgoing + incoming as relationships
                LIMIT 1000
                """,
                {"type": type}
            )
            
            concepts = [self._process_concept_record(record) for record in result]
            
            # Add to concept pool
            for concept in concepts:
                await self._manage_pool(self._concept_pool, concept["name"], concept)
                
            return concepts

        try:
            return await self._execute_with_retry(get_operation)
        except Exception as e:
            logger.error(f"Error getting concepts by type {type}: {str(e)}")
            return []

    async def get_related_concepts(self, name: str) -> List[Dict]:
        """Get all concepts related to the given concept."""
        # Ensure indexes are created
        await self._ensure_indexes()
        
        async def get_operation():
            result = await self.run_query(
                """
                MATCH (c:Concept {name: $name})
                OPTIONAL MATCH (c)-[r1:RELATED_TO]->(related1:Concept)
                WHERE r1.bidirectional = true OR r1.direction = 'forward'
                OPTIONAL MATCH (c)<-[r2:RELATED_TO]-(related2:Concept)
                WHERE r2.bidirectional = true OR r2.direction = 'reverse'
                WITH c, 
                     collect(DISTINCT {node: related1, rel: r1}) as outgoing,
                     collect(DISTINCT {node: related2, rel: r2}) as incoming
                UNWIND outgoing + incoming as related
                WITH DISTINCT related.node as related_node,
                     related.rel as relationship
                WHERE related_node IS NOT NULL
                OPTIONAL MATCH (related_node)-[r3:RELATED_TO]->(other:Concept)
                WHERE r3.bidirectional = true OR r3.direction = 'forward'
                RETURN related_node as c,
                       collect({
                           name: other.name, 
                           type: r3.type, 
                           attributes: r3,
                           direction: 'forward',
                           bidirectional: r3.bidirectional
                       }) as relationships
                LIMIT 1000
                """,
                {"name": name}
            )
            
            concepts = [self._process_concept_record(record) for record in result]
            
            # Add to concept pool
            for concept in concepts:
                await self._manage_pool(self._concept_pool, concept["name"], concept)
                
            return concepts

        try:
            return await self._execute_with_retry(get_operation)
        except Exception as e:
            logger.error(f"Error getting related concepts for {name}: {str(e)}")
            return []

    async def search_concepts(self, query: str) -> List[Dict]:
        """Search concepts using full-text search."""
        # Ensure indexes are created
        await self._ensure_indexes()
        
        async def search_operation():
            result = await self.run_query(
                """
                MATCH (c:Concept)
                WHERE c.name = $query OR c.description = $query OR
                      toLower(c.name) CONTAINS toLower($query) OR 
                      toLower(c.description) CONTAINS toLower($query)
                OPTIONAL MATCH (c)-[r1:RELATED_TO]->(related1:Concept)
                WHERE r1.bidirectional = true OR r1.direction = 'forward'
                OPTIONAL MATCH (c)<-[r2:RELATED_TO]-(related2:Concept)
                WHERE r2.bidirectional = true OR r2.direction = 'reverse'
                WITH c, 
                    collect(DISTINCT {
                        name: related1.name, 
                        type: r1.type, 
                        attributes: r1, 
                        direction: 'forward',
                        bidirectional: r1.bidirectional
                    }) as outgoing,
                    collect(DISTINCT {
                        name: related2.name, 
                        type: r2.type, 
                        attributes: r2, 
                        direction: 'reverse',
                        bidirectional: r2.bidirectional
                    }) as incoming
                RETURN c, outgoing + incoming as relationships
                LIMIT 1000
                """,
                {"query": query}
            )
            
            concepts = [self._process_concept_record(record) for record in result]
            
            # Add to concept pool
            for concept in concepts:
                await self._manage_pool(self._concept_pool, concept["name"], concept)
                
            return concepts

        try:
            return await self._execute_with_retry(search_operation)
        except Exception as e:
            logger.error(f"Error searching concepts with query {query}: {str(e)}")
            return []

    async def query_knowledge(self, query: Dict) -> List[Dict]:
        """Query semantic knowledge."""
        try:
            conditions = []
            params = {}
            
            # Handle entity queries with number conversion
            if query.get("type") == "entity" and "names" in query:
                names = []
                for name in query["names"]:
                    # Try to convert name to int if it's a digit
                    if str(name).isdigit():
                        names.append(str(name))
                    else:
                        names.append(name)
                params["names"] = names
                conditions.append("n.name IN $names")
            
            # Handle concept queries with pattern
            elif query.get("type") == "concept" and "pattern" in query:
                pattern = query["pattern"]
                params["pattern"] = f".*{pattern}.*"
                conditions.append("(n.name =~ $pattern OR n.description =~ $pattern)")
            
            # Handle context filtering with improved validation handling
            if "context" in query:
                for key, value in query["context"].items():
                    if key == "access_domain":
                        params[f"context_{key}"] = value
                        conditions.append("""
                            EXISTS(n.validation_json)
                            AND apoc.convert.fromJsonMap(n.validation_json).access_domain = $context_access_domain
                        """)
                    elif key == "domain":
                        params[f"context_{key}"] = str(value)
                        conditions.append("""
                            EXISTS(n.validation_json)
                            AND apoc.convert.fromJsonMap(n.validation_json).domain = $context_domain
                        """)
                    elif key == "cross_domain.approved":
                        params[f"context_{key}"] = value
                        conditions.append("""
                            EXISTS(n.validation_json)
                            AND apoc.convert.fromJsonMap(n.validation_json).cross_domain.approved = $context_cross_domain_approved
                        """)
                    elif key == "cross_domain.requested":
                        params[f"context_{key}"] = value
                        conditions.append("""
                            EXISTS(n.validation_json)
                            AND apoc.convert.fromJsonMap(n.validation_json).cross_domain.requested = $context_cross_domain_requested
                        """)
                    elif key == "cross_domain.source_domain":
                        params[f"context_{key}"] = value
                        conditions.append("""
                            EXISTS(n.validation_json)
                            AND apoc.convert.fromJsonMap(n.validation_json).cross_domain.source_domain = $context_cross_domain_source_domain
                        """)
                    elif key == "cross_domain.target_domain":
                        params[f"context_{key}"] = value
                        conditions.append("""
                            EXISTS(n.validation_json)
                            AND apoc.convert.fromJsonMap(n.validation_json).cross_domain.target_domain = $context_cross_domain_target_domain
                        """)
                    else:
                        params[f"context_{key}"] = value
                        conditions.append(f"n.{key} = $context_{key}")
            
            where_clause = " AND ".join(conditions) if conditions else "true"
            
            cypher = f"""
            MATCH (n:Concept)
            WHERE {where_clause}
            WITH n
            OPTIONAL MATCH (n)-[r:RELATED_TO]-(related:Concept)
            WHERE r.bidirectional = true OR r.direction IN ['forward', 'reverse']
            WITH n, collect(DISTINCT {{
                name: related.name,
                type: r.type,
                attributes: properties(r),
                direction: CASE 
                    WHEN startNode(r) = n AND r.direction = 'forward' THEN 'forward'
                    WHEN endNode(r) = n AND r.direction = 'reverse' THEN 'reverse'
                    ELSE 'bidirectional'
                END,
                bidirectional: r.bidirectional
            }}) as relationships
            RETURN n, relationships
            LIMIT 1000
            """
            
            logger.info(f"Executing semantic query: {cypher}")
            logger.info(f"Query parameters: {params}")
            
            # Execute query
            records = await self.run_query(cypher, params)
            logger.info(f"Raw query results: {records}")
            
            # Process results
            results = []
            for record in records:
                if record["n"] is not None:
                    try:
                        concept = self._process_concept_record({
                            "c": record["n"],
                            "relationships": record["relationships"]
                        })
                        results.append(concept)
                        
                        # Add to concept pool
                        await self._manage_pool(self._concept_pool, concept["name"], concept)
                        
                        logger.info(f"Processed concept: {concept}")
                    except Exception as e:
                        logger.error(f"Failed to process concept record: {str(e)}")
                        logger.error(f"Record data: {record}")
            
            logger.info(f"Final processed results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query knowledge: {str(e)}")
            return []

    async def store_concept_from_json(self, data: Union[str, Dict]) -> None:
        """Store concept(s) from JSON data with validation."""
        try:
            validated = validate_json_structure(data)
            if isinstance(validated, dict) and "concepts" in validated:
                validated = validated["concepts"]
            
            if isinstance(validated, list):
                # Store multiple concepts in batches
                batch_size = 100
                stored = 0
                errors = 0
                
                for i in range(0, len(validated), batch_size):
                    batch = validated[i:i + batch_size]
                    for concept in batch:
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
            result = await self.run_query("MATCH (n:Concept) RETURN count(n) as count")
            return result[0]["count"] if result else 0

        try:
            return await self._execute_with_retry(count_operation)
        except Exception as e:
            logger.error(f"Error counting concepts: {str(e)}")
            return 0

    async def count_concepts_by_label(self) -> Dict[str, int]:
        """Count concepts grouped by label/type."""
        async def count_operation():
            result = await self.run_query("""
                MATCH (n:Concept)
                WITH n.type as type, count(n) as count
                RETURN collect({type: type, count: count}) as counts
            """)
            if result and result[0]["counts"]:
                return {item["type"]: item["count"] for item in result[0]["counts"]}
            return {}

        try:
            return await self._execute_with_retry(count_operation)
        except Exception as e:
            logger.error(f"Error counting concepts by label: {str(e)}")
            return {}

    async def count_relationships(self) -> int:
        """Count total number of relationships in the database."""
        async def count_operation():
            result = await self.run_query("MATCH ()-[r:RELATED_TO]->() RETURN count(r) as count")
            return result[0]["count"] if result else 0

        try:
            return await self._execute_with_retry(count_operation)
        except Exception as e:
            logger.error(f"Error counting relationships: {str(e)}")
            return 0

    async def clear_relationships(self) -> None:
        """Clear all relationships from the database."""
        async def clear_operation():
            await self.run_query("MATCH ()-[r:RELATED_TO]->() DELETE r")
            # Clear relationship pool
            async with self._pool_lock:
                self._relationship_pool.clear()

        try:
            await self._execute_with_retry(clear_operation)
        except Exception as e:
            logger.error(f"Error clearing relationships: {str(e)}")
            raise

    async def clear_concepts(self) -> None:
        """Clear all concepts from the database."""
        async def clear_operation():
            await self.run_query("MATCH (n:Concept) DETACH DELETE n")
            # Clear concept pool
            async with self._pool_lock:
                self._concept_pool.clear()

        try:
            await self._execute_with_retry(clear_operation)
        except Exception as e:
            logger.error(f"Error clearing concepts: {str(e)}")
            raise

    async def cleanup(self):
        """Clean up resources."""
        try:
            # Clear all pools
            async with self._pool_lock:
                self._concept_pool.clear()
                self._relationship_pool.clear()
                self._memory_pool.clear()
                self._access_queue.clear()
                
            # Clear database
            await self.clear_concepts()
            await self.clear_relationships()
            
            # Close Neo4j connection
            await super().close()
            
        except Exception as e:
            logger.error(f"Error cleaning up concept store: {str(e)}")
            raise
