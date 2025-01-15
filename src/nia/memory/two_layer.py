"""Two-layer memory system implementation for NIA."""

from typing import Optional, Dict, List, Any
import json
import logging
import traceback
from datetime import datetime, timezone
import uuid
import asyncio
from ..core.types.memory_types import Memory, MemoryType, ValidationSchema, CrossDomainSchema, EpisodicMemory
from .vector_store import VectorStore
from .embedding import EmbeddingService
from qdrant_client.http import models
from ..core.neo4j.concept_store import ConceptStore
from ..core.neo4j.base_store import Neo4jMemoryStore

logger = logging.getLogger(__name__)

def create_default_validation():
    """Create default validation data."""
    return {
        "domain": "general",
        "confidence": 0.5,
        "source": "system",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

class EpisodicLayer:
    """Handles short-term episodic memories using vector storage."""
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        try:
            logger.debug("Initializing EpisodicLayer")
            if vector_store is None:
                # Use provided configuration
                logger.debug("Creating default EmbeddingService")
                embedding_service = EmbeddingService()
                logger.debug("Creating VectorStore")
                self.store = VectorStore(embedding_service=embedding_service)
            else:
                logger.debug("Using provided vector store")
                self.store = vector_store
            self.pending_consolidation = set()
            logger.debug("EpisodicLayer initialization complete")
        except Exception as e:
            logger.error(f"Failed to initialize EpisodicLayer: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def get_consolidation_candidates(self) -> List[Dict]:
        """Get memories that are candidates for consolidation."""
        try:
            result = await self.store.search_vectors(
                filter={"metadata.consolidated": False}
            )
            return result
        except Exception as e:
            logger.error(f"Failed to get consolidation candidates: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    async def store_memory(self, memory: EpisodicMemory) -> bool:
        """Store a memory directly in the vector store."""
        try:
            # Generate ID if not present
            memory_id = getattr(memory, "id", str(uuid.uuid4()))
            
            # Create minimal metadata
            metadata = {
                "id": memory_id,
                "type": memory.type.value if isinstance(memory.type, MemoryType) else memory.type,
                "timestamp": getattr(memory, "timestamp", datetime.now().isoformat())
            }
            
            # Store directly in vector store
            return await self.store.store_vector(
                content=memory.content,
                metadata=metadata,
                layer="episodic"
            )
        except Exception as e:
            logger.error(f"Failed to store memory: {str(e)}")
            logger.error(traceback.format_exc())
            return False

class TwoLayerMemorySystem:
    """Implements episodic and semantic memory layers with consolidation support.
    
    The system uses a vector store for episodic memories and Neo4j for semantic knowledge.
    Episodic memories can be consolidated into semantic knowledge over time.
    """
    
    def __init__(self, neo4j_uri: Optional[str] = None, 
                 vector_store: Optional[VectorStore] = None,
                 llm = None):
        """Initialize the memory system.
        
        Note: This only sets up the basic structure. Call initialize() to fully initialize the system.
        """
        # Read config
        import configparser
        config = configparser.ConfigParser()
        config.read("config.ini")
        
        self.vector_store = vector_store
        self.episodic = None  # Will be initialized in initialize()
        self.semantic = None  # Will be initialized in initialize()
        self.consolidation_manager = None
        self._initialized = False
        self.llm = llm
        
        # Use config values or defaults
        self.neo4j_uri = neo4j_uri or config.get("NEO4J", "uri", fallback="bolt://localhost:7687")
        self.neo4j_user = config.get("NEO4J", "user", fallback="neo4j")
        self.neo4j_password = config.get("NEO4J", "password", fallback="password")
        
        # Get Qdrant config
        self.qdrant_host = config.get("QDRANT", "host", fallback="127.0.0.1")
        self.qdrant_port = config.getint("QDRANT", "port", fallback=6333)
        
        # Initialize memory pools
        self._memory_pools = {
            "episodic": {},
            "semantic": {}
        }
        
    async def initialize(self):
        """Initialize connections to Neo4j and vector store."""
        if not self._initialized:
            try:
                logger.info("Starting memory system initialization...")
                
                # Initialize layers with proper configuration
                logger.debug("Creating episodic layer...")
                if self.vector_store is None:
                    # Create new vector store with config
                    embedding_service = EmbeddingService()
                    self.vector_store = VectorStore(embedding_service=embedding_service)
                self.episodic = EpisodicLayer(vector_store=self.vector_store)
                logger.debug("Creating semantic layer...")
                self.semantic = ConceptStore(
                    uri=self.neo4j_uri,
                    user=self.neo4j_user,
                    password=self.neo4j_password
                )
                
                # Initialize connections with retries
                retry_count = 0
                max_retries = 5
                while retry_count < max_retries:
                    try:
                        # Try Neo4j connection
                        if hasattr(self.semantic, 'connect'):
                            await self.semantic.connect()
                            logger.debug("Neo4j connection established")
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            logger.warning(f"Neo4j connection failed after {max_retries} retries: {str(e)}")
                            # Continue without Neo4j - don't block startup
                        else:
                            logger.warning(f"Neo4j connection attempt {retry_count} failed: {str(e)}")
                            await asyncio.sleep(1)
                
                # Vector store is already initialized in constructor
                logger.debug("Vector store initialized")
                    
                self._initialized = True
                logger.info("Memory system initialization complete")
            except Exception as e:
                logger.error(f"Failed to initialize memory system: {str(e)}")
                logger.error(traceback.format_exc())
                raise

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from both episodic and semantic layers."""
        try:
            logger.debug(f"Deleting memory {memory_id}")
            
            # Remove from memory pools
            self._memory_pools["episodic"].pop(memory_id, None)
            self._memory_pools["semantic"].pop(memory_id, None)
            
            # Delete from vector store
            if self.vector_store:
                await self.vector_store.delete_vector(memory_id)
                logger.debug(f"Deleted memory {memory_id} from vector store")
            
            # Delete from Neo4j if semantic layer is available
            if self.semantic:
                await self.semantic.run_query(
                    """
                    MATCH (m {id: $id})
                    DETACH DELETE m
                    """,
                    {"id": memory_id}
                )
                logger.debug(f"Deleted memory {memory_id} from semantic store")
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    async def store_experience(self, memory: Memory, is_sync: bool = False, _depth: int = 0) -> bool:
        """Store an experience in the episodic layer."""
        try:
            # Circuit breaker to prevent infinite recursion
            if _depth > 2:  # Allow max 2 levels of recursion
                logger.error("Maximum recursion depth exceeded in store_experience")
                return False
                
            if not self._initialized:
                raise Exception("Memory system not initialized")
                
            # Convert memory to dict with minimal data
            memory_dict = memory.dict(minimal=True)
            
            # Generate ID if not present
            memory_id = memory_dict.get("id", str(uuid.uuid4()))
            
            # Check if already stored to prevent duplicates
            if memory_id in self._memory_pools["episodic"] or memory_id in self._memory_pools["semantic"]:
                logger.debug(f"Memory {memory_id} already stored")
                return True
            
            # Extract essential metadata
            essential_metadata = {
                "type": memory_dict["type"],
                "id": memory_id,
                "timestamp": memory_dict.get("timestamp", datetime.now().isoformat())
            }
            
            # Add only necessary additional metadata
            if memory_dict.get("metadata"):
                essential_metadata.update({
                    k: v for k, v in memory_dict["metadata"].items()
                    if k in ["domain", "thread_id", "task_id", "message_id"]
                })
            
            # Determine layer
            layer = essential_metadata.get("type")
            if isinstance(layer, MemoryType):
                layer = layer.value
                
            # Use direct storage pattern
            if hasattr(memory, 'knowledge'):
                content = {
                    "text": memory_dict["content"],
                    "knowledge": memory.knowledge
                }
                metadata = {
                    **essential_metadata,
                    "concepts": memory.knowledge.get("concepts", []),
                    "relationships": memory.knowledge.get("relationships", []),
                    "importance": getattr(memory, "importance", 0.8),
                    "context": getattr(memory, "context", {}),
                    "consolidated": False
                }
            else:
                content = memory_dict["content"]
                metadata = essential_metadata

            # Store directly in episodic layer
            success = await self.episodic.store_memory(
                EpisodicMemory(
                    content=content,
                    metadata=metadata,
                    type=memory_dict["type"]
                )
            )
            
            if not success:
                return False
                
            # Add to episodic pool
            self._memory_pools["episodic"][memory_id] = {
                "content": memory_dict["content"],
                "metadata": essential_metadata,
                "timestamp": essential_metadata["timestamp"]
            }
            
            return True
        except Exception as e:
            logger.error(f"Failed to store experience: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    async def get_experience(self, memory_id: str, sync_layers: bool = True) -> Optional[Memory]:
        """Get an experience from either memory layer."""
        try:
            if not self._initialized:
                raise Exception("Memory system not initialized")
            
            memory_data = None
            location = None
            
            # Check memory pools first
            if memory_id in self._memory_pools["semantic"]:
                memory_data = self._memory_pools["semantic"][memory_id]
                location = "semantic"
            elif memory_id in self._memory_pools["episodic"]:
                memory_data = self._memory_pools["episodic"][memory_id]
                location = "episodic"
            
            # If not in pools, check semantic layer
            if not memory_data and self.semantic:
                try:
                    result = await self.semantic.run_query(
                        """
                        MATCH (m {id: $id})
                        RETURN m
                        """,
                        {"id": memory_id}
                    )
                    if result and result[0]:
                        memory_data = result[0]["m"]
                        location = "semantic"
                        # Add to semantic pool
                        self._memory_pools["semantic"][memory_id] = memory_data
                except Exception as e:
                    logger.warning(f"Failed to query semantic layer: {str(e)}")
            
            # Check episodic layer if still not found
            if not memory_data:
                result = await self.vector_store.search_vectors(
                    content={"id": memory_id},
                    limit=1,
                    score_threshold=0.99
                )
                memories = result if result else []
                if memories:
                    memory_data = memories[0]
                    location = "episodic"
                    # Add to episodic pool
                    self._memory_pools["episodic"][memory_id] = memory_data
            
            if not memory_data:
                return None
                
            # Create memory object with minimal data
            memory = Memory(
                id=memory_id,
                content=memory_data["content"],
                type=memory_data.get("type", "thread"),
                importance=0.8,  # Default importance
                timestamp=datetime.fromisoformat(memory_data.get("timestamp", datetime.now().isoformat())),
                context={},  # Empty context by default
                metadata={
                    "type": memory_data.get("type", "thread"),
                    **(memory_data.get("metadata", {}))
                }
            )
            
            # Sync to other layer if needed
            if sync_layers and self.semantic and location in ["semantic", "episodic"]:
                try:
                    await self.store_experience(memory, is_sync=True)
                except Exception as e:
                    logger.warning(f"Failed to sync memory: {str(e)}")
            
            return memory
        except Exception as e:
            logger.error(f"Failed to get experience: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    async def query_episodic(self, query: Dict[str, Any]) -> List[Memory]:
        """Query the episodic layer with complex filters."""
        try:
            if not self._initialized:
                raise Exception("Memory system not initialized")
                
            content_filter = query.get("content", {})
            metadata_filter = query.get("filter", {})
            
            # Combine filters
            combined_filter = {**content_filter}
            if metadata_filter:
                combined_filter["metadata"] = metadata_filter
                
            result = await self.vector_store.search_vectors(
                content=combined_filter,
                limit=query.get("limit", 100),
                score_threshold=query.get("score_threshold", 0.7)
            )
            memories = result if result else []
            
            # Create memories with minimal metadata to avoid recursion
            result = []
            for m in memories:
                # All results from vector store should be dicts
                memory_dict = m if isinstance(m, dict) else m.dict()
                memory = Memory(
                    id=memory_dict.get("id", str(uuid.uuid4())),
                    content=memory_dict.get("content", ""),
                    type=memory_dict.get("type", MemoryType.EPISODIC),
                    importance=memory_dict.get("importance", 0.8),
                    timestamp=datetime.fromisoformat(memory_dict.get("timestamp", datetime.now().isoformat())),
                    context=memory_dict.get("context", {}),
                    metadata=memory_dict.get("metadata", {})
                )
                result.append(memory)
                
                # Add to episodic pool
                self._memory_pools["episodic"][memory.id] = {
                    "content": memory_dict.get("content", ""),
                    "metadata": memory_dict.get("metadata", {}),
                    "timestamp": memory_dict.get("timestamp", datetime.now().isoformat())
                }
            
            return result
        except Exception as e:
            logger.error(f"Failed to query episodic memory: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    async def consolidate_memories(self):
        """Consolidate memories from episodic to semantic layer."""
        if not self._initialized:
            raise Exception("Memory system not initialized")
        
        # Get consolidation candidates
        result = await self.episodic.store.search_vectors(
            filter={"metadata.consolidated": False}
        )
        candidates = result if result else []
        
        # Process each candidate
        for candidate in candidates:
            # Extract concepts and relationships
            if isinstance(candidate, dict):
                concepts = candidate.get("concepts", [])
                relationships = candidate.get("relationships", [])
            else:
                concepts = getattr(candidate, "concepts", [])
                relationships = getattr(candidate, "relationships", [])
            
            # Store concepts in semantic layer
            for concept in concepts:
                await self.semantic.store_concept(
                    name=concept["name"],
                    type=concept["type"],
                    description=concept.get("description", ""),
                    validation=concept.get("validation", {})
                )
            
            # Store relationships in semantic layer
            for rel in relationships:
                await self.semantic.store_relationship(
                    source=rel["source"],
                    target=rel["target"],
                    rel_type=rel["type"],
                    attributes={
                        "bidirectional": rel.get("bidirectional", False),
                        "confidence": rel.get("confidence", 1.0)
                    }
                )
            
            # Mark as consolidated
            await self.episodic.store.update_metadata(
                candidate["id"],
                {"consolidated": True}
            )

    async def query_semantic(self, query: Dict[str, Any]) -> List[Dict]:
        """Query the semantic layer."""
        try:
            if not self._initialized:
                raise Exception("Memory system not initialized")
            
            if not self.semantic:
                return []
            
            # Extract query parameters
            query_type = query.get("type")
            pattern = query.get("pattern")
            
            # Build Neo4j query
            cypher_query = """
            MATCH (n:Concept)
            WHERE n.type = $type
            """
            if pattern:
                cypher_query += " AND n.name =~ $pattern"
            
            cypher_query += " RETURN n"
            
            # Execute query
            params = {"type": query_type}
            if pattern:
                params["pattern"] = pattern
            
            results = await self.semantic.run_query(cypher_query, params)
            return results
        except Exception as e:
            logger.error(f"Failed to query semantic layer: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    async def cleanup(self):
        """Clean up resources."""
        try:
            logger.info("Cleaning up memory system...")
            # Clear memory pools
            self._memory_pools["episodic"].clear()
            self._memory_pools["semantic"].clear()
            # Clean up vector store
            if self.vector_store:
                await self.vector_store.cleanup()
            # Clean up semantic store
            if self.semantic:
                await self.semantic.cleanup()
            logger.info("Memory system cleanup complete")
        except Exception as e:
            logger.error(f"Failed to clean up memory system: {str(e)}")
            logger.error(traceback.format_exc())
