"""Two-layer memory system implementation for NIA."""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from ..core.types.memory_types import ValidationSchema, CrossDomainSchema


from nia.core.vector.vector_store import VectorStore, serialize_for_vector_store
from nia.core.neo4j.neo4j_store import Neo4jMemoryStore
from nia.core.neo4j.concept_store import ConceptStore
from nia.core.vector.embeddings import EmbeddingService
from nia.core.types.memory_types import Memory, MemoryType, EpisodicMemory

logger = logging.getLogger(__name__)

class EpisodicLayer:
    """Handles short-term episodic memories using vector storage."""
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        if vector_store is None:
            # Use default configuration
            embedding_service = EmbeddingService()
            self.store = VectorStore(embedding_service)
        else:
            self.store = vector_store
        self.pending_consolidation = set()
        
    def _validate_memory(self, memory: Memory) -> None:
        """Validate memory before storage."""
        # Validate content type
        if not isinstance(memory.content, (str, dict)):
            raise ValueError(f"Invalid content type: {type(memory.content)}. Must be str or dict.")
            
        # Validate importance range
        if not 0 <= memory.importance <= 1:
            raise ValueError(f"Importance must be between 0 and 1, got {memory.importance}")
            
        # Validate context structure
        if memory.context:
            if not isinstance(memory.context, dict):
                raise ValueError(f"Context must be a dictionary, got {type(memory.context)}")
            # Required context fields
            required_fields = {"domain", "source"}
            missing_fields = required_fields - set(memory.context.keys())
            if missing_fields:
                raise ValueError(f"Missing required context fields: {missing_fields}")
                
        # Get concepts from either direct access or knowledge field
        concepts = []
        if hasattr(memory, "concepts") and memory.concepts:
            concepts.extend(memory.concepts)
        if hasattr(memory, "knowledge") and isinstance(memory.knowledge, dict):
            if "concepts" in memory.knowledge:
                for concept in memory.knowledge["concepts"]:
                    if isinstance(concept, dict):
                        if "name" not in concept:
                            raise ValueError("Concepts must have a name")
                        if "validation" not in concept or "confidence" not in concept["validation"] or not 0 <= concept["validation"]["confidence"] <= 1:
                            raise ValueError(f"Concept {concept['name']} must have valid confidence (0-1)")
                    else:
                        if not hasattr(concept, "name") or not concept.name:
                            raise ValueError("Concepts must have a name")
                        if not concept.validation or "confidence" not in concept.validation or not 0 <= concept.validation["confidence"] <= 1:
                            raise ValueError(f"Concept {concept.name} must have valid confidence (0-1)")

        # Get relationships from either direct access or knowledge field
        relationships = []
        if hasattr(memory, "relationships") and memory.relationships:
            relationships.extend(memory.relationships)
        if hasattr(memory, "knowledge") and isinstance(memory.knowledge, dict):
            if "relationships" in memory.knowledge:
                for rel in memory.knowledge["relationships"]:
                    if isinstance(rel, dict):
                        if "source" not in rel or "target" not in rel:
                            raise ValueError("Relationships must have source and target fields")
                        if "confidence" not in rel or not 0 <= rel["confidence"] <= 1:
                            raise ValueError(f"Relationship must have valid confidence (0-1)")
                    else:
                        if not hasattr(rel, "source") or not hasattr(rel, "target"):
                            raise ValueError("Relationships must have source and target fields")
                        if not hasattr(rel, "confidence") or not 0 <= rel.confidence <= 1:
                            raise ValueError(f"Relationship must have valid confidence (0-1)")

    async def store_memory(self, memory: Memory) -> str:
        """Store a new episodic memory."""
        try:
            # Validate memory
            self._validate_memory(memory)
            
            # Create embedding and store
            # Convert memory to dict and ensure type is string
            memory_dict = memory.dict()
            memory_dict["consolidated"] = False  # Ensure consolidated field is set
            memory_dict["type"] = str(memory_dict["type"])

            # Handle knowledge field if present
            if hasattr(memory, "knowledge") and isinstance(memory.knowledge, dict):
                # Map concepts from knowledge field
                if "concepts" in memory.knowledge:
                    memory_dict["concepts"] = [
                        c if isinstance(c, dict) else c.dict()
                        for c in memory.knowledge["concepts"]
                    ]
                # Map relationships from knowledge field
                if "relationships" in memory.knowledge:
                    memory_dict["relationships"] = [
                        r if isinstance(r, dict) else r.dict()
                        for r in memory.knowledge["relationships"]
                    ]
            
            # Store with original content and set layer based on memory type
            memory_id = await self.store.store_vector(
                content=memory_dict,
                metadata={
                    "type": memory_dict["type"],
                    "timestamp": datetime.now().isoformat(),
                    "importance": memory.importance,
                    "domain": memory.context.get("domain", "general"),
                    "concepts": memory_dict.get("concepts", []),
                    "relationships": memory_dict.get("relationships", [])
                },
                layer=memory_dict["type"].lower()
            )
            
            # Track for consolidation if important enough
            if memory.importance >= 0.7:  # High importance threshold
                self.pending_consolidation.add(memory_id)
            
            return memory_id
        except Exception as e:
            logger.error(f"Failed to store episodic memory: {str(e)}")
            raise
            
    async def get_consolidation_candidates(self) -> List[Dict]:
        """Get memories ready for consolidation."""
        try:
            # Get all memories
            results = await self.store.search_vectors()
            
            # Convert each result to EpisodicMemory
            formatted_results = []
            for r in results:
                try:
                    memory = EpisodicMemory(
                        id=r.get("id"),
                        content=r.get("content", ""),
                        type=r.get("type", MemoryType.EPISODIC.value),
                        importance=r.get("importance", 0.5),
                        timestamp=r.get("timestamp", datetime.now(timezone.utc).isoformat()),
                        context=r.get("context", {}),
                        consolidated=r.get("consolidated", False),
                        participants=r.get("participants", []),
                        concepts=r.get("concepts", []),
                        relationships=r.get("relationships", []),
                        emotions=r.get("emotions", {}),
                        related_memories=r.get("related_memories", [])
                    )
                    formatted_results.append(memory)
                except Exception as e:
                    logger.error(f"Failed to create EpisodicMemory: {str(e)}")
                    continue
                
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to get consolidation candidates: {str(e)}")
            return []
            
    async def archive_memories(self, memory_ids: List[str]):
        """Archive memories after consolidation."""
        try:
            for memory_id in memory_ids:
                # First mark as consolidated
                await self.store.update_metadata(
                    memory_id,
                    {"consolidated": True}
                )
                # Then delete the memory
                if hasattr(self.store, 'delete_vector'):
                    await self.store.delete_vector(memory_id)
                if memory_id in self.pending_consolidation:
                    self.pending_consolidation.remove(memory_id)
        except Exception as e:
            logger.error(f"Failed to archive memories: '{memory_id}' ({str(e)})")

class SemanticLayer(ConceptStore):
    """Handles long-term semantic knowledge using Neo4j.
    
    Inherits from ConceptStore to leverage existing Neo4j functionality.
    """
    
    async def search(self, query: str) -> List[Dict]:
        """Search semantic knowledge using Cypher query."""
        try:
            # Parse domain query
            if query.startswith("domain:"):
                cypher = """
                MATCH (n:Concept)
                WHERE n.validation.domain = $domain
                RETURN n
                """
                params = {"domain": query.split(":")[1]}
            else:
                # Default to text search
                cypher = """
                MATCH (n:Concept)
                WHERE n.description CONTAINS $query
                RETURN n
                """
                params = {"query": query}
            
            # Use base store's run_query which handles sessions properly
            records = await self.run_query(cypher, params)
            
            # Process results
            processed = []
            for record in records:
                if "n" in record:
                    if isinstance(record["n"], dict) and "properties" in record["n"]:
                        processed.append(record["n"]["properties"])
                    else:
                        processed.append(record["n"])
            return processed
        except Exception as e:
            logger.error(f"Failed to search semantic layer: {str(e)}")
            return []
    
    async def _execute_with_retry(self, operation):
        """Execute an operation with retry logic."""
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                return await operation()
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    raise e
                await asyncio.sleep(1)  # Wait before retrying

    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        await self.store_concept(
            name=f"reflection_{datetime.now().isoformat()}",
            type="reflection",
            description=content
        )
    
    def __init__(self, store: Optional[Neo4jMemoryStore] = None, uri: str = "bolt://localhost:7687"):
        if store is None:
            super().__init__(
                uri=uri,
                user="neo4j",
                password="password",
                max_retry_time=30,
                retry_interval=1
            )
        else:
            # Initialize ConceptStore with store's connection details
            super().__init__(
                uri=store.uri,
                user=store.user,
                password=store.password,
                max_retry_time=30,
                retry_interval=1
            )
            # Use the provided store's driver
            self.driver = store.driver if hasattr(store, 'driver') else store
            
        self.knowledge_patterns = {
            "concepts": self._create_concept_pattern(),
            "relationships": self._create_relationship_pattern(),
            "beliefs": self._create_belief_pattern()
        }
        
    def _create_concept_pattern(self) -> Dict:
        """Create pattern for concept extraction with enhanced validation."""
        return {
            "type": "concept",
            "properties": {
                "required": ["name", "type", "domain"],
                "optional": ["category", "attributes", "confidence"],
                "validation": {
                    "name": lambda x: isinstance(x, str) and len(x) > 0,
                    "type": lambda x: x in ["entity", "action", "property", "event", "abstract"],
                    "domain": lambda x: isinstance(x, str) and len(x) > 0,
                    "confidence": lambda x: isinstance(x, float) and 0 <= x <= 1
                }
            }
        }
        
    def _create_relationship_pattern(self) -> Dict:
        """Create pattern for relationship extraction with cross-domain support."""
        return {
            "type": "relationship",
            "properties": {
                "required": ["from", "to", "type", "domains"],
                "optional": ["attributes", "confidence", "bidirectional"],
                "validation": {
                    "from": lambda x: isinstance(x, str) and len(x) > 0,
                    "to": lambda x: isinstance(x, str) and len(x) > 0,
                    "type": lambda x: x in [
                        "is_a", "has_a", "part_of", "related_to", 
                        "causes", "implies", "precedes", "similar_to"
                    ],
                    "domains": lambda x: isinstance(x, list) and len(x) > 0,
                    "confidence": lambda x: isinstance(x, float) and 0 <= x <= 1,
                    "bidirectional": lambda x: isinstance(x, bool)
                }
            }
        }
        
    def _create_belief_pattern(self) -> Dict:
        """Create pattern for belief extraction with confidence scoring."""
        return {
            "type": "belief",
            "properties": {
                "required": ["subject", "predicate", "object", "confidence", "domains"],
                "optional": ["context", "timestamp", "source"],
                "validation": {
                    "subject": lambda x: isinstance(x, str) and len(x) > 0,
                    "predicate": lambda x: isinstance(x, str) and len(x) > 0,
                    "object": lambda x: isinstance(x, str) and len(x) > 0,
                    "confidence": lambda x: isinstance(x, float) and 0 <= x <= 1,
                    "domains": lambda x: isinstance(x, list) and len(x) > 0,
                    "context": lambda x: isinstance(x, dict),
                    "timestamp": lambda x: isinstance(x, str) and len(x) > 0,
                    "source": lambda x: isinstance(x, str) and len(x) > 0
                }
            }
        }
        
    def _validate_pattern(self, data: Dict, pattern: Dict) -> bool:
        """Validate data against a pattern."""
        try:
            # Check required properties
            for prop in pattern["properties"]["required"]:
                if prop not in data:
                    logger.error(f"Missing required property: {prop}")
                    return False
                    
            # Validate properties
            for prop, value in data.items():
                if prop in pattern["properties"]["validation"]:
                    validator = pattern["properties"]["validation"][prop]
                    if not validator(value):
                        logger.error(f"Invalid value for {prop}: {value}")
                        return False
                        
            return True
        except Exception as e:
            logger.error(f"Pattern validation failed: {str(e)}")
            return False
        
    async def _create_belief(
        self, 
        subject: str, 
        predicate: str, 
        object: str, 
        confidence: float = 1.0,
        domains: List[str] = None,
        context: Dict = None,
        source: str = "system"
    ):
        """Create a belief in the knowledge graph with enhanced context."""
        # Validate confidence
        if not 0 <= confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {confidence}")
            
        # Ensure domains list
        if domains is None:
            domains = ["general"]
            
        # Ensure context dict
        if context is None:
            context = {}
            
        # Create belief with full context
        await self.run_query(
            """
            MATCH (s:Concept {name: $subject})
            MATCH (o:Concept {name: $object})
            MERGE (s)-[r:BELIEVES]->(o)
            SET 
                r.predicate = $predicate,
                r.confidence = $confidence,
                r.domains = $domains,
                r.context = $context,
                r.source = $source,
                r.created_at = CASE WHEN r.created_at IS NULL THEN datetime() ELSE r.created_at END,
                r.last_updated = datetime()
            """,
            {
                "subject": subject,
                "predicate": predicate,
                "object": object,
                "confidence": confidence,
                "domains": domains,
                "context": json.dumps(context),
                "source": source
            }
        )

    async def store_knowledge(self, knowledge: Dict):
        """Store extracted semantic knowledge with pattern validation and cross-domain support."""
        try:
            # Validate and store concepts
            for concept in knowledge.get("concepts", []):
                if not self._validate_pattern(concept, self.knowledge_patterns["concepts"]):
                    logger.warning(f"Skipping invalid concept: {concept}")
                    continue
                    
                # Store concept with validated metadata
                    # Create validation data with proper schema
                    validation_data = concept.get("validation", {})
                    validation_schema = ValidationSchema(
                        domain=validation_data.get("domain", "professional"),
                        confidence=validation_data.get("confidence", 1.0),
                        source=validation_data.get("source", "system"),
                        timestamp=validation_data.get("timestamp", datetime.now(timezone.utc).isoformat())
                    )
                    
                    # Add cross-domain information if present
                    if "cross_domain" in validation_data:
                        cross_domain = CrossDomainSchema(**validation_data["cross_domain"])
                        validation_schema.cross_domain = cross_domain
                    
                    validation = json.dumps(validation_schema.dict())
                    stored_concept = await self.store_concept(
                        name=concept["name"],
                        type=concept["type"],
                        description=concept.get("description", ""),
                        validation=validation,
                        is_consolidation=concept.get("is_consolidation", False)
                    )
                    if not stored_concept:
                        logger.error(f"Failed to store concept: {concept['name']}")
                        continue
                    logger.info(f"Successfully stored concept: {stored_concept}")
                
            # Validate and store relationships with cross-domain support
            for rel in knowledge.get("relationships", []):
                if not self._validate_pattern(rel, self.knowledge_patterns["relationships"]):
                    logger.warning(f"Skipping invalid relationship: {rel}")
                    continue
                    
                # Create relationship with domain awareness
                await self.run_query(
                    """
                    MERGE (c1:Concept {name: $from})
                    ON CREATE SET 
                        c1.type = $from_type,
                        c1.description = $from_description,
                        c1.domain = $from_domain,
                        c1.created_at = datetime()
                    WITH c1
                    MERGE (c2:Concept {name: $to})
                    ON CREATE SET 
                        c2.type = $to_type,
                        c2.description = $to_description,
                        c2.domain = $to_domain,
                        c2.created_at = datetime()
                    WITH c1, c2
                    MERGE (c1)-[r:RELATED_TO]->(c2)
                    SET 
                        r.type = $rel_type,
                        r.domains = $domains,
                        r.confidence = $confidence,
                        r.bidirectional = $bidirectional,
                        r.last_updated = datetime()
                    """,
                    {
                        "from": rel["from"],
                        "from_type": rel.get("from_type", "concept"),
                        "from_description": rel.get("from_description", ""),
                        "from_domain": rel["domains"][0],  # Primary domain for source
                        "to": rel["to"],
                        "to_type": rel.get("to_type", "concept"),
                        "to_description": rel.get("to_description", ""),
                        "to_domain": rel["domains"][-1],  # Primary domain for target
                        "rel_type": rel["type"],
                        "domains": rel["domains"],
                        "confidence": rel.get("confidence", 1.0),
                        "bidirectional": rel.get("bidirectional", False)
                    }
                )
                
                # Create reverse relationship if bidirectional
                if rel.get("bidirectional", False):
                    await self.run_query(
                        """
                        MATCH (c1:Concept {name: $from})
                        MATCH (c2:Concept {name: $to})
                        MERGE (c2)-[r:RELATED_TO]->(c1)
                        SET 
                            r.type = $rel_type,
                            r.domains = $domains,
                            r.confidence = $confidence,
                            r.bidirectional = true,
                            r.last_updated = datetime()
                        """,
                        {
                            "from": rel["from"],
                            "to": rel["to"],
                            "rel_type": rel["type"],
                            "domains": rel["domains"],
                            "confidence": rel.get("confidence", 1.0)
                        }
                    )
                
            # Validate and store beliefs with enhanced context
            for belief in knowledge.get("beliefs", []):
                if not self._validate_pattern(belief, self.knowledge_patterns["beliefs"]):
                    logger.warning(f"Skipping invalid belief: {belief}")
                    continue
                    
                # Store belief with full context
                await self._create_belief(
                    belief["subject"],
                    belief["predicate"],
                    belief["object"],
                    belief.get("confidence", 1.0),
                    belief.get("domains", []),
                    belief.get("context", {}),
                    belief.get("source", "system")
                )
        except Exception as e:
            logger.error(f"Failed to store semantic knowledge: {str(e)}")
            raise
            
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
            
            # Handle context filtering with improved validation field handling
            if "context" in query:
                for key, value in query["context"].items():
                    if key == "access_domain":
                        params[f"context_{key}"] = value
                        conditions.append("""
                            (n.access_domain = $context_access_domain OR 
                             n.validation_source = $context_access_domain OR
                             n.domain = $context_access_domain)
                        """)
                    elif key == "cross_domain.approved":
                        params["context_cross_domain_approved"] = value
                        conditions.append("""
                            n.validation IS NOT NULL AND
                            n.validation <> '' AND
                            (
                                apoc.convert.fromJsonMap(n.validation).cross_domain.approved = $context_cross_domain_approved OR
                                apoc.convert.fromJsonMap(n.validation).cross_domain_approved = $context_cross_domain_approved OR
                                n.validation CONTAINS '"cross_domain":{"approved":true' OR
                                n.validation CONTAINS '"cross_domain_approved":true' OR
                                n.validation CONTAINS '"approved":true' OR
                                n.validation CONTAINS '"cross_domain":{"approved":true,"requested":true'
                            )
                        """)
                        logger.info(f"Added cross-domain condition with params: {params}")
                    elif "." in key:  # Handle other nested context
                        field, subfield = key.split(".")
                        params[f"context_{field}_{subfield}"] = value
                        conditions.append(f"""
                            n.validation IS NOT NULL AND
                            n.validation <> '' AND
                            n.validation CONTAINS '"{field}":{{"{subfield}":{json.dumps(value)}}}'
                        """)
                    else:
                        params[f"context_{key}"] = value
                        conditions.append(f"""
                            (n.{key} = $context_{key} OR
                             n.validation CONTAINS '\"{key}\":\"{value}\"')
                        """)
            
            where_clause = " AND ".join(conditions) if conditions else "true"
            

            cypher = f"""
            MATCH (n:Concept)
            WHERE {where_clause}
            WITH n
            OPTIONAL MATCH (n)-[r:RELATED_TO]-(related:Concept)
            WHERE r.bidirectional = true OR r.direction IN ['forward', 'reverse']
            WITH n, collect(DISTINCT {{
                name: related.name,
                type: COALESCE(r.type, 'RELATED_TO'),
                attributes: CASE WHEN r IS NULL THEN {{}} ELSE properties(r) END,
                direction: CASE
                    WHEN r IS NULL THEN 'none'
                    WHEN startNode(r) = n AND r.direction = 'forward' THEN 'forward'
                    WHEN endNode(r) = n AND r.direction = 'reverse' THEN 'reverse'
                    ELSE 'bidirectional'
                END,
                bidirectional: COALESCE(r.bidirectional, false)
            }}) as relationships
            RETURN n {{
                .name,
                .type,
                .description,
                .is_consolidation,
                validation: CASE 
                    WHEN n.validation_json IS NOT NULL THEN n.validation_json
                    WHEN n.validation IS NOT NULL THEN n.validation
                    ELSE null
                END,
                relationships: relationships
            }} as n, relationships
            """
            
            logger.info(f"Generated Cypher query: {cypher}")
            logger.info(f"Query parameters: {params}")
            
            # Log query details
            logger.info(f"Executing semantic query: {cypher}")
            logger.info(f"Query parameters: {params}")
            
            # Execute query
            records = await self.run_query(cypher, params)
            logger.info(f"Raw query results: {records}")
            
            # Process results with enhanced relationship and validation handling
            results = []
            for record in records:
                if record["n"] is not None:
                    try:
                        concept = record["n"]
                        
                        # Parse validation data
                        if concept.get("validation"):
                            try:
                                if isinstance(concept["validation"], str):
                                    concept["validation"] = json.loads(concept["validation"])
                            except json.JSONDecodeError:
                                logger.error(f"Failed to parse validation JSON: {concept['validation']}")
                                concept["validation"] = create_default_validation()
                        else:
                            concept["validation"] = create_default_validation()
                        
                        # Ensure relationships is a list
                        if "relationships" not in concept or concept["relationships"] is None:
                            concept["relationships"] = []
                            
                        results.append(concept)
                        logger.info(f"Processed concept with relationships: {concept}")
                    except Exception as e:
                        logger.error(f"Failed to process concept record: {str(e)}")
                        logger.error(f"Record data: {record}")
                        continue
            
            logger.info(f"Final processed results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query knowledge: {str(e)}")
            return []
        return ""
        
    def _process_query_results(self, results: List[Dict]) -> List[Dict]:
        """Process Neo4j results into standard format."""
        processed = []
        for result in results:
            if "n" in result:  # Single node
                node = result["n"]
                if isinstance(node, dict):
                    # Extract node properties
                    processed.append(node)
            elif "p" in result:  # Path
                processed.append(self._process_path(result["p"]))
        return processed
        
    def _process_path(self, path: Dict) -> Dict:
        """Process Neo4j path into standard format."""
        return {
            "nodes": path.nodes,
            "relationships": path.relationships
        }

class TwoLayerMemorySystem:
    """Implements episodic and semantic memory layers."""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687", 
                 vector_store: Optional[VectorStore] = None,
                 llm = None):
        self.episodic = EpisodicLayer(vector_store)
        self.semantic = SemanticLayer(uri=neo4j_uri)
        self.consolidation_manager = None  # Will be set by ConsolidationManager
        self._initialized = False
        self.llm = llm  # Store LLM interface
        self.vector_store = vector_store  # Expose vector_store for external use
        
    def _create_validation_metadata(
        self,
        source: str,
        confidence: float,
        access_domain: str
    ) -> Dict:
        """Create validation metadata for concepts."""
        return {
            "source": source,
            "confidence": confidence,
            "access_domain": access_domain,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    async def initialize(self):
        """Initialize connections to Neo4j and vector store."""
        if not self._initialized:
            # Initialize Neo4j connection
            if hasattr(self.semantic, 'connect'):
                await self.semantic.connect()
            
            # Initialize vector store if needed
            if hasattr(self.episodic.store, 'connect'):
                await self.episodic.store.connect()
                
            self._initialized = True
            
    async def cleanup(self):
        """Clean up connections."""
        if self._initialized:
            # Close Neo4j connection
            if hasattr(self.semantic, 'close'):
                await self.semantic.close()
                
            # Close vector store connection if needed
            if hasattr(self.episodic.store, 'close'):
                await self.episodic.store.close()
                
            self._initialized = False
            
    async def prune(
        self,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, int]:
        """Prune old memories and unused nodes."""
        pruned_nodes = 0
        pruned_relationships = 0
        pruned_memories = 0
        
        try:
            # Prune episodic memories
            if hasattr(self.episodic.store, 'delete_vectors'):
                # Get old consolidated memories
                old_memories = await self.episodic.store.search_vectors(
                    filter={
                        "consolidated": True,
                        "domain": domain
                    } if domain else {"consolidated": True}
                )
                
                # Delete old memories
                if old_memories:
                    memory_ids = [m.id for m in old_memories if hasattr(m, 'id')]
                    await self.episodic.store.delete_vectors(memory_ids)
                    pruned_memories = len(memory_ids)
            
            # Prune semantic nodes
            if hasattr(self.semantic, 'run_query'):
                # Find unused nodes (no relationships)
                unused_query = """
                MATCH (n)
                WHERE NOT (n)--()
                AND (n.domain = $domain OR $domain IS NULL)
                WITH n
                LIMIT 1000
                DETACH DELETE n
                RETURN count(n) as deleted
                """
                
                result = await self.semantic.run_query(
                    unused_query,
                    {"domain": domain}
                )
                pruned_nodes = result[0]["deleted"] if result else 0
                
                # Find and remove dangling relationships
                dangling_query = """
                MATCH ()-[r]->()
                WHERE (r.domain = $domain OR $domain IS NULL)
                AND r.last_accessed < datetime() - duration('P30D')
                WITH r
                LIMIT 1000
                DELETE r
                RETURN count(r) as deleted
                """
                
                result = await self.semantic.run_query(
                    dangling_query,
                    {"domain": domain}
                )
                pruned_relationships = result[0]["deleted"] if result else 0
                
            return {
                "pruned_nodes": pruned_nodes,
                "pruned_relationships": pruned_relationships,
                "pruned_memories": pruned_memories,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to prune memory system: {str(e)}")
            raise
        
    async def store_experience(self, experience: Memory) -> str:
        """Store new experience in episodic memory."""
        # Store in episodic memory first
        memory_id = await self.episodic.store_memory(experience)
        
        # Check for consolidation if manager exists
        if self.consolidation_manager and await self.consolidation_manager.should_consolidate():
            await self.consolidate_memories()
            
        return memory_id
            
    async def consolidate_memories(self):
        """Convert episodic memories to semantic knowledge."""
        logger.info("Starting memory consolidation")
        if not self.consolidation_manager:
            logger.warning("No consolidation manager set")
            return
            
        # Get memories ready for consolidation
        memories = await self.episodic.get_consolidation_candidates()
        logger.info(f"Found {len(memories)} consolidation candidates")
        
        if not memories:
            logger.info("No memories to consolidate")
            return
            
        # Log memory details
        for memory in memories:
            logger.info(f"Memory candidate - ID: {memory.id if hasattr(memory, 'id') else 'unknown'}, "
                       f"Importance: {memory.importance if hasattr(memory, 'importance') else 'unknown'}, "
                       f"Content: {memory.content if hasattr(memory, 'content') else 'unknown'}")
            
        # Extract patterns and relationships
        logger.info("Extracting knowledge from memories")
        knowledge = await self.consolidation_manager.extract_knowledge(memories)
        logger.info(f"Extracted knowledge: {json.dumps(knowledge, separators=(',', ':'), ensure_ascii=False)}")
        
        # Store in semantic layer
        logger.info("Storing knowledge in semantic layer")
        await self.semantic.store_knowledge(knowledge)
        
        # Archive processed memories
        memory_ids = [m.id for m in memories if hasattr(m, 'id')]
        logger.info(f"Archiving {len(memory_ids)} processed memories")
        await self.episodic.archive_memories(memory_ids)
        logger.info("Memory consolidation complete")
        
    async def query_episodic(self, query: Dict) -> List[EpisodicMemory]:
        """Query episodic memories."""
        try:
            # Extract filter and convert to vector store format
            filter_dict = query.get("filter", {})
            
            # Search with type and filter
            results = await self.episodic.store.search_vectors(
                content={"text": query.get("text", "")},  # Match the stored format
                filter=filter_dict,  # Pass filter directly
                limit=query.get("limit", 5),
                score_threshold=query.get("score_threshold", 0.7),
                layer=query.get("type", "episodic").lower()  # Use specified type or default to episodic
            )
            return results
        except Exception as e:
            logger.error(f"Failed to query episodic memories: {str(e)}")
            return []
            
    async def query_semantic(self, query: Dict) -> List[Dict]:
        """Query semantic knowledge."""
        return await self.semantic.query_knowledge(query)
        
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by its ID."""
        try:
            # Search for memory in episodic store
            # Convert memory_id to content for searching
            results = await self.episodic.store.search_vectors(
                content={"id": memory_id},
                limit=1,
                score_threshold=0.99  # High threshold for exact match
            )
            if results and len(results) > 0:
                # Convert first result to Memory object
                memory_data = results[0]
                
                # Ensure content is properly formatted
                content = memory_data.get("content", {})
                if isinstance(content, dict):
                    content = content.get("text", "")
                elif isinstance(content, str):
                    content = content
                else:
                    content = str(content)
                    
                memory_data["content"] = content
                return Memory(**memory_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id}: {str(e)}")
            return None
            
    async def store(
        self,
        memory_id: Optional[str] = None,
        content: Any = None,
        memory_type: Optional[str] = None,
        importance: float = 0.5,
        context: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> str:
        """Store data in memory system.
        
        Args:
            memory_id: Optional memory ID to use
            content: Content to store
            memory_type: Optional memory type
            importance: Importance score (0-1)
            context: Optional context dictionary
            metadata: Optional metadata dictionary
            data: Optional legacy data dictionary
            
        Returns:
            str: Memory ID of the stored memory
        """
        try:
            # Create Memory object
            memory = Memory(
                id=memory_id,
                content=content or (data["content"] if data else ""),
                type=MemoryType(memory_type) if memory_type else MemoryType.EPISODIC,
                importance=importance,
                timestamp=datetime.now(timezone.utc).isoformat(),
                context=context or (data.get("context", {}) if data else {})
            )
            
            # Store in episodic memory
            memory_id = await self.episodic.store_memory(memory)
            
            # If semantic memory, also store in Neo4j
            if memory.type == MemoryType.SEMANTIC:
                # Store concept using base store's run_query
                await self.semantic.run_query(
                    """
                    MERGE (c:Concept {name: $name})
                    SET c.type = $type,
                        c.description = $description,
                        c.validation = $validation
                    """,
                    {
                        "name": f"concept_{datetime.now().isoformat()}",
                        "type": "concept",
                        "description": memory.content if isinstance(memory.content, str) else memory.content.get("text", ""),
                        "validation": json.dumps(ValidationSchema(
                            domain=memory.context.get("domain", "general"),
                            source=memory.context.get("source", "system"),
                            confidence=memory.importance
                        ).dict()) if memory.context else None
                    }
                )
            return memory_id
        except Exception as e:
            logger.error(f"Failed to store data: {str(e)}")
            raise  # Re-raise the exception to be handled by the caller
