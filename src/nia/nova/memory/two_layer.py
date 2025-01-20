"""Two-layer memory system implementation for NIA."""

from typing import Optional, Dict, List, Any, cast
import json
import logging
import traceback
from datetime import datetime, timezone
import uuid
import asyncio
import sys
import os

from nia.core.types.memory_types import Memory, MemoryType, ValidationSchema, CrossDomainSchema, EpisodicMemory
from nia.nova.memory.vector_store import VectorStore
from nia.nova.memory.embedding import EmbeddingService
from nia.core.neo4j.concept_store import ConceptStore
from nia.core.neo4j.base_store import Neo4jMemoryStore
from qdrant_client.http import models

logger = logging.getLogger(__name__)

# Circuit breaker settings
MAX_RETRIES = 3
TIMEOUT_SECONDS = 10
BACKOFF_FACTOR = 2

def create_default_validation():
    """Create default validation data."""
    return {
        "domain": "general",
        "confidence": 0.5,
        "source": "system",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""
    
    def __init__(self, max_failures=3, reset_timeout=60):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        
    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        self.failures += 1
        self.last_failure_time = datetime.now()
        if self.failures >= self.max_failures:
            self.state = "open"
            
    def record_success(self):
        """Record a success and potentially close the circuit."""
        self.failures = 0
        self.state = "closed"
        
    def allow_request(self) -> bool:
        """Check if a request should be allowed."""
        if self.state == "closed":
            return True
            
        if self.state == "open":
            # Check if enough time has passed to try again
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).total_seconds() > self.reset_timeout:
                self.state = "half-open"
                return True
            return False
            
        # In half-open state, allow one request
        return True

def _safe_convert_value(value: Any, depth: int = 0, max_depth: int = 3) -> Any:
    """Safely convert a value to a simple type to prevent recursion."""
    if depth > max_depth:
        return str(value)
        
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    elif isinstance(value, (list, tuple)):
        return [_safe_convert_value(v, depth + 1) for v in value[:100]]  # Limit array size
    elif isinstance(value, dict):
        return {str(k): _safe_convert_value(v, depth + 1) 
                for k, v in list(value.items())[:100]}  # Limit dict size
    else:
        return str(value)

def _prepare_search_params(query: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare search parameters safely without recursion."""
    # Convert content to dictionary format with safe type handling
    content = query.get("content")
    content_dict: Dict[str, str] = {}
    
    if content is None:
        content_dict["text"] = ""
    elif isinstance(content, str):
        content_dict["text"] = content
    elif isinstance(content, dict):
        # Convert all values to strings to prevent type issues
        for k, v in list(content.items())[:100]:  # Limit size
            content_dict[str(k)] = _safe_convert_value(v)
    else:
        content_dict["text"] = str(content)
        
    # Create filter conditions safely
    filter_conditions = []
    metadata_filter = query.get("filter", {})
    if metadata_filter:
        for key, value in list(metadata_filter.items())[:100]:  # Limit size
            safe_value = _safe_convert_value(value)
            filter_conditions.append(
                models.FieldCondition(
                    key=f"metadata_{key}",
                    match=models.MatchValue(value=safe_value)
                )
            )
            
    return {
        "content": content_dict,
        "filter_conditions": filter_conditions,
        "limit": min(int(query.get("limit", 100)), 1000),  # Enforce reasonable limit
        "score_threshold": float(query.get("score_threshold", 0.7))
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
            self.circuit_breaker = CircuitBreaker()
            logger.debug("EpisodicLayer initialization complete")
        except Exception as e:
            logger.error(f"Failed to initialize EpisodicLayer: {str(e)}")
            logger.error(traceback.format_exc())
            raise
            
    async def initialize(self):
        """Initialize vector store connection."""
        try:
            logger.debug("Initializing EpisodicLayer vector store")
            if self.store:
                async with asyncio.timeout(TIMEOUT_SECONDS):
                    if hasattr(self.store, 'connect'):
                        await self.store.connect()
                    logger.debug("EpisodicLayer vector store initialized")
            else:
                logger.warning("No vector store available for initialization")
        except Exception as e:
            logger.error(f"Failed to initialize EpisodicLayer vector store: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def get_consolidation_candidates(self) -> List[Dict]:
        """Get memories that are candidates for consolidation."""
        if not self.circuit_breaker.allow_request():
            logger.warning("Circuit breaker is open, skipping consolidation candidates request")
            return []

        try:
            # Create filter condition for unconsolidated memories
            filter_condition = models.FieldCondition(
                key="metadata_consolidated",
                match=models.MatchValue(value=False)
            )
            
            async with asyncio.timeout(TIMEOUT_SECONDS):
                if not self.store or not hasattr(self.store, 'search_vectors'):
                    logger.error("Vector store missing or search_vectors method not available")
                    return []
                    
                result = await self.store.search_vectors(
                    content={},  # Empty content since we're only filtering by metadata
                    filter_conditions=[filter_condition]
                )
            self.circuit_breaker.record_success()
            return result
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Failed to get consolidation candidates: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    async def store_memory(self, memory: EpisodicMemory) -> bool:
        """Store a memory directly in the vector store."""
        if not self.circuit_breaker.allow_request():
            logger.warning("Circuit breaker is open, skipping memory storage")
            return False
            
        if not self.store:
            logger.error("No vector store available for storing memory")
            return False
            
        try:
            # Generate ID if not present
            memory_id = getattr(memory, "id", None) or str(uuid.uuid4())
            
            # Use original metadata with a copy to prevent recursion
            metadata = {}
            if hasattr(memory, "metadata") and isinstance(memory.metadata, dict):
                # Only copy simple types to prevent recursion
                for k, v in memory.metadata.items():
                    metadata[k] = _safe_convert_value(v)
            
            # Keep original metadata and add required fields
            metadata.update({
                "id": memory_id,
                "timestamp": getattr(memory, "timestamp", datetime.now().isoformat()),
                "thread_id": metadata.get("thread_id"),
                "description": metadata.get("description", ""),
                "system": bool(metadata.get("system", False)),
                "pinned": bool(metadata.get("pinned", False)),
                "consolidated": bool(metadata.get("consolidated", False))
            })
            
            # Keep original type from metadata with safe type conversion
            if "type" in metadata:
                # Preserve original type if it's a string
                if isinstance(metadata["type"], str):
                    pass
                else:
                    metadata["type"] = str(metadata["type"])
            elif hasattr(memory, "type"):
                if isinstance(memory.type, str):
                    metadata["type"] = memory.type
                elif isinstance(memory.type, MemoryType):
                    metadata["type"] = memory.type.value
                else:
                    metadata["type"] = str(memory.type)
            else:
                metadata["type"] = "unknown"
            
            # Remove None values and ensure all values are simple types
            metadata = {k: _safe_convert_value(v)
                       for k, v in metadata.items() 
                       if v is not None}
            
            logger.debug(f"Storing memory with metadata: {metadata}")
            
            # Get content safely
            content = getattr(memory, "content", "")
            if not isinstance(content, str):
                content = str(content)
            
            # Add timeout to prevent infinite recursion
            async with asyncio.timeout(TIMEOUT_SECONDS):
                if hasattr(self.store, 'store_vector'):
                    success = await self.store.store_vector(
                        content=content,
                        metadata=metadata,
                        layer="episodic"
                    )
                else:
                    logger.error("Vector store missing store_vector method")
                    return False
            
            if success:
                self.circuit_breaker.record_success()
            else:
                self.circuit_breaker.record_failure()
                
            return success
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Failed to store memory: {str(e)}")
            logger.error(traceback.format_exc())
            return False
            
    async def cleanup(self):
        """Clean up resources and close connections."""
        try:
            logger.debug("Cleaning up EpisodicLayer")
            if self.store:
                try:
                    async with asyncio.timeout(TIMEOUT_SECONDS):
                        await self.store.cleanup()
                    logger.debug("Vector store cleaned up")
                except Exception as e:
                    logger.error(f"Failed to clean up vector store: {str(e)}")
                    
            # Clear any pending operations
            self.pending_consolidation.clear()
            
            # Reset circuit breaker
            self.circuit_breaker = CircuitBreaker()
            
            logger.debug("EpisodicLayer cleanup complete")
        except Exception as e:
            logger.error(f"Failed to clean up EpisodicLayer: {str(e)}")
            logger.error(traceback.format_exc())

class TwoLayerMemorySystem:
    """Implements episodic and semantic memory layers with consolidation support."""
    
    def __init__(self, neo4j_uri: Optional[str] = None, 
                 vector_store: Optional[VectorStore] = None,
                 llm = None):
        """Initialize the memory system."""
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
        
        # Initialize circuit breakers
        self.vector_circuit = CircuitBreaker()
        self.semantic_circuit = CircuitBreaker()
        
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
                while retry_count < MAX_RETRIES:
                    try:
                        # Try Neo4j connection
                        if hasattr(self.semantic, 'connect'):
                            async with asyncio.timeout(TIMEOUT_SECONDS):
                                await self.semantic.connect()
                            logger.debug("Neo4j connection established")
                            break
                    except Exception as e:
                        retry_count += 1
                        if retry_count == MAX_RETRIES:
                            logger.warning(f"Neo4j connection failed after {MAX_RETRIES} retries: {str(e)}")
                            # Continue without Neo4j - don't block startup
                        else:
                            logger.warning(f"Neo4j connection attempt {retry_count} failed: {str(e)}")
                            await asyncio.sleep(BACKOFF_FACTOR * retry_count)
                
                # Initialize vector store and episodic layer
                logger.debug("Initializing vector store and episodic layer...")
                async with asyncio.timeout(TIMEOUT_SECONDS):
                    await self.vector_store.connect()
                    await self.episodic.initialize()
                logger.debug("Vector store and episodic layer initialized")
                    
                self._initialized = True
                logger.info("Memory system initialization complete")
            except Exception as e:
                logger.error(f"Failed to initialize memory system: {str(e)}")
                logger.error(traceback.format_exc())
                raise

    async def store_experience(self, memory: Memory, is_sync: bool = False, recursion_depth: int = 0) -> bool:
        """Store an experience in the episodic layer."""
        # Prevent deep recursion and sync loops
        if recursion_depth > 3:
            logger.warning("Maximum recursion depth reached in store_experience")
            return False
            
        # Check for sync loops using metadata
        metadata = getattr(memory, "metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
            
        if is_sync and metadata.get("_synced"):
            logger.warning("Sync loop detected in store_experience")
            return False
            
        # Mark as synced to prevent loops
        metadata["_synced"] = True
        metadata["_recursion_depth"] = recursion_depth
        setattr(memory, "metadata", metadata)

        # Skip memory pool checks during sync to prevent loops
        if not is_sync:
            # Check if memory already exists with same properties
            memory_id = getattr(memory, "id", None) or str(uuid.uuid4())
            if memory_id in self._memory_pools["episodic"]:
                existing_memory = self._memory_pools["episodic"][memory_id]
                
                # Compare core properties
                if (str(existing_memory.get("content", "")) == str(getattr(memory, "content", "")) and
                    str(existing_memory.get("metadata", {}).get("type")) == str(getattr(memory, "type", "thread"))):
                    logger.info(f"Memory {memory_id} already exists with same properties, skipping store")
                    return True
            
            # Check semantic layer if available
            if self.semantic and self.semantic_circuit.allow_request() and memory_id in self._memory_pools["semantic"]:
                existing_memory = self._memory_pools["semantic"][memory_id]
                
                # Compare core properties
                if (str(existing_memory.get("content", "")) == str(getattr(memory, "content", "")) and
                    str(existing_memory.get("metadata", {}).get("type")) == str(getattr(memory, "type", "thread"))):
                    logger.info(f"Memory {memory_id} already exists in semantic layer with same properties, skipping store")
                    return True
                    
        if not self._initialized or not self.episodic:
            return False
            
        if not self.vector_circuit.allow_request():
            logger.warning("Circuit breaker is open, skipping experience storage")
            return False

        try:
            # Use existing ID or generate new one
            memory_id = getattr(memory, "id", None) or str(uuid.uuid4())
            
            # Extract memory attributes safely
            content = getattr(memory, "content", "")
            if not isinstance(content, str):
                content = str(content)
                
            memory_type = getattr(memory, "type", "thread")
            if not isinstance(memory_type, (str, MemoryType)):
                memory_type = str(memory_type)
                
            timestamp = getattr(memory, "timestamp", datetime.now()).isoformat()
            
            # Get existing metadata or create new
            existing_metadata = getattr(memory, "metadata", {})
            if not isinstance(existing_metadata, dict):
                existing_metadata = {}
                
            # Create metadata with type checking, preserving existing values
            metadata: Dict[str, Any] = {
                "id": memory_id,
                "timestamp": timestamp,
                "type": memory_type,
                "thread_id": existing_metadata.get("thread_id") or getattr(memory, "thread_id", None),
                "description": existing_metadata.get("description") or getattr(memory, "description", ""),
                "system": bool(existing_metadata.get("system", False)) or bool(getattr(memory, "system", False)),
                "pinned": bool(existing_metadata.get("pinned", False)) or bool(getattr(memory, "pinned", False)),
                "consolidated": bool(existing_metadata.get("consolidated", False)),
                "_synced": True,  # Mark as synced to prevent loops
                "_recursion_depth": recursion_depth,  # Track recursion depth
                "_sync_source": "episodic" if is_sync else "direct"  # Track sync source
            }
            
            # Remove None values and ensure all values are simple types
            metadata = {k: str(v) if not isinstance(v, (bool, int, float)) else v
                       for k, v in metadata.items() 
                       if v is not None}
            
            # Create episodic memory with flattened metadata
            episodic_memory = EpisodicMemory(
                id=memory_id,
                content=content,
                metadata=metadata,
                type=str(memory_type),  # Ensure type is string
                timestamp=datetime.now(timezone.utc)
            )
            
            # Store in episodic layer with timeout
            async with asyncio.timeout(TIMEOUT_SECONDS):
                success = await self.episodic.store_memory(episodic_memory)
            
            if success:
                self.vector_circuit.record_success()
                # Add to memory pool with flattened data
                self._memory_pools["episodic"][memory_id] = {
                    "content": str(content),
                    "metadata": metadata,
                    "timestamp": timestamp,
                    "layer": "episodic"
                }
            else:
                self.vector_circuit.record_failure()
                
            return success
        except Exception as e:
            self.vector_circuit.record_failure()
            logger.error(f"Failed to store experience: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    async def get_experience(self, memory_id: str, sync_layers: bool = True, recursion_depth: int = 0) -> Optional[Memory]:
        """Get an experience from either memory layer."""
        # Prevent deep recursion
        if recursion_depth > 3:
            logger.warning("Maximum recursion depth reached in get_experience")
            return None
            
        try:
            if not self._initialized:
                raise Exception("Memory system not initialized")
            
            memory_data = None
            location = None
            
            # Check memory pools first with payload structure
            if memory_id in self._memory_pools["semantic"]:
                pool_data = self._memory_pools["semantic"][memory_id]
                memory_data = {
                    "content": str(pool_data["content"]),
                    "metadata": {k: str(v) if not isinstance(v, (bool, int, float)) else v 
                               for k, v in pool_data["metadata"].items()}
                }
                location = "semantic"
            elif memory_id in self._memory_pools["episodic"]:
                pool_data = self._memory_pools["episodic"][memory_id]
                memory_data = {
                    "content": str(pool_data["content"]),
                    "metadata": {k: str(v) if not isinstance(v, (bool, int, float)) else v 
                               for k, v in pool_data["metadata"].items()}
                }
                location = "episodic"
            
            # If not in pools, check semantic layer if circuit allows
            if not memory_data and self.semantic and self.semantic_circuit.allow_request():
                try:
                    async with asyncio.timeout(TIMEOUT_SECONDS):
                        result = await self.semantic.run_query(
                            """
                            MATCH (m {id: $id})
                            RETURN m
                            """,
                            {"id": memory_id}
                        )
                    if result and result[0]:
                        raw_data = result[0]["m"]
                        # Flatten and sanitize data
                        memory_data = {
                            "content": str(raw_data.get("content", "")),
                            "metadata": {k: str(v) if not isinstance(v, (bool, int, float)) else v 
                                       for k, v in raw_data.get("metadata", {}).items()}
                        }
                        location = "semantic"
                        # Add to semantic pool
                        self._memory_pools["semantic"][memory_id] = memory_data
                    self.semantic_circuit.record_success()
                except Exception as e:
                    self.semantic_circuit.record_failure()
                    logger.warning(f"Failed to query semantic layer: {str(e)}")
            
            # Check episodic layer if still not found and circuit allows
            if not memory_data and self.vector_circuit.allow_request():
                try:
                    async with asyncio.timeout(TIMEOUT_SECONDS):
                        if not self.vector_store or not hasattr(self.vector_store, 'search_vectors'):
                            logger.error("Vector store missing search_vectors method")
                            return None
                            
                        result = await self.vector_store.search_vectors(
                            content={"id": memory_id},
                            limit=1,
                            score_threshold=0.99
                        )
                        memories = result if result else []
                        
                        if memories:
                            raw_data = memories[0]
                            location = "episodic"
                            # Extract and flatten metadata
                            if isinstance(raw_data, dict):
                                content = str(raw_data.get("content", ""))
                                metadata = {k: str(v) if not isinstance(v, (bool, int, float)) else v 
                                          for k, v in raw_data.get("metadata", {}).items()}
                                memory_data = {"content": content, "metadata": metadata}
                                # Add to episodic pool
                                self._memory_pools["episodic"][memory_id] = memory_data
                        self.vector_circuit.record_success()
                except Exception as e:
                    self.vector_circuit.record_failure()
                    logger.warning(f"Failed to query vector store: {str(e)}")
            
            if not memory_data:
                return None
                
            # Create memory object with safe defaults and proper sync tracking
            try:
                content = str(memory_data.get("content", ""))
                metadata = memory_data.get("metadata", {})
                
                # Get type with safe default
                memory_type = str(metadata.get("type", "thread"))
                
                # Parse timestamp safely
                try:
                    timestamp = datetime.fromisoformat(str(metadata.get("timestamp", datetime.now().isoformat())))
                except (ValueError, TypeError):
                    timestamp = datetime.now()
                
                # Create memory with sanitized data and sync tracking
                memory = Memory(
                    id=str(metadata.get("id", str(uuid.uuid4()))),
                    content=content,
                    type=memory_type,
                    importance=float(metadata.get("importance", 0.8)),
                    timestamp=timestamp,
                    context={},  # Simplified context to prevent recursion
                    metadata={
                        **metadata,
                        "_synced": True,  # Mark as synced
                        "_sync_source": location,  # Track source
                        "_recursion_depth": recursion_depth
                    }
                )
                
                # Only sync if conditions allow and not too deep
                if (sync_layers and self.semantic and 
                    location in ["semantic", "episodic"] and 
                    not metadata.get("_synced") and
                    recursion_depth < 2):  # Reduced recursion limit
                    try:
                        await self.store_experience(memory, is_sync=True, recursion_depth=recursion_depth + 1)
                    except Exception as e:
                        logger.warning(f"Failed to sync memory: {str(e)}")
                
                return memory
            except Exception as e:
                logger.error(f"Failed to create memory object: {str(e)}")
                logger.error(traceback.format_exc())
                return None
                
        except Exception as e:
            logger.error(f"Failed to get experience: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from both episodic and semantic layers."""
        try:
            logger.debug(f"Deleting memory {memory_id}")
            
            # Remove from memory pools
            self._memory_pools["episodic"].pop(memory_id, None)
            self._memory_pools["semantic"].pop(memory_id, None)
            
            # Delete from vector store if circuit allows
            if self.vector_store and self.vector_circuit.allow_request():
                try:
                    async with asyncio.timeout(TIMEOUT_SECONDS):
                        await self.vector_store.delete_vector(memory_id)
                    logger.debug(f"Deleted memory {memory_id} from vector store")
                    self.vector_circuit.record_success()
                except Exception as e:
                    self.vector_circuit.record_failure()
                    logger.error(f"Failed to delete from vector store: {str(e)}")
            
            # Delete from Neo4j if semantic layer is available and circuit allows
            if self.semantic and self.semantic_circuit.allow_request():
                try:
                    async with asyncio.timeout(TIMEOUT_SECONDS):
                        await self.semantic.run_query(
                            """
                            MATCH (m {id: $id})
                            DETACH DELETE m
                            """,
                            {"id": memory_id}
                        )
                    logger.debug(f"Deleted memory {memory_id} from semantic store")
                    self.semantic_circuit.record_success()
                except Exception as e:
                    self.semantic_circuit.record_failure()
                    logger.error(f"Failed to delete from semantic store: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    async def cleanup(self):
        """Clean up resources and close connections."""
        try:
            logger.debug("Cleaning up memory system")
            
            # Clean up episodic layer
            if self.episodic:
                try:
                    await self.episodic.cleanup()
                except Exception as e:
                    logger.error(f"Failed to clean up episodic layer: {str(e)}")
                    
            # Clean up semantic layer
            if self.semantic:
                try:
                    async with asyncio.timeout(TIMEOUT_SECONDS):
                        await self.semantic.cleanup()
                except Exception as e:
                    logger.error(f"Failed to clean up semantic layer: {str(e)}")
                    
            # Clean up vector store
            if self.vector_store:
                try:
                    async with asyncio.timeout(TIMEOUT_SECONDS):
                        await self.vector_store.cleanup()
                except Exception as e:
                    logger.error(f"Failed to clean up vector store: {str(e)}")
                    
            # Clear memory pools
            self._memory_pools["episodic"].clear()
            self._memory_pools["semantic"].clear()
            
            # Reset circuit breakers
            self.vector_circuit = CircuitBreaker()
            self.semantic_circuit = CircuitBreaker()
            
            logger.debug("Memory system cleanup complete")
        except Exception as e:
            logger.error(f"Failed to clean up memory system: {str(e)}")
            logger.error(traceback.format_exc())

    async def consolidate_memories(self, memory_ids: List[str]) -> bool:
        """Consolidate specific memories from episodic to semantic layer."""
        if not self._initialized or not self.episodic or not self.semantic:
            return False
            
        try:
            success = True
            for memory_id in memory_ids:
                try:
                    # Get memory from episodic layer
                    memory = await self.get_experience(memory_id, sync_layers=False)
                    if not memory:
                        logger.warning(f"Memory {memory_id} not found for consolidation")
                        continue
                        
                    # Store in semantic layer
                    if self.semantic_circuit.allow_request():
                        try:
                            async with asyncio.timeout(TIMEOUT_SECONDS):
                                # Extract relationships and metadata with validation
                                related = []
                                metadata_fields = {}
                                retry_count = 0
                                
                                while retry_count < MAX_RETRIES:
                                    try:
                                        # Validate and extract metadata
                                        if memory.metadata and isinstance(memory.metadata, dict):
                                            # Get relationships with validation
                                            related = memory.metadata.get("related", [])
                                            if not isinstance(related, list):
                                                related = []
                                                
                                            # Collect metadata fields with validation
                                            for key in ["importance", "thread_id", "description"]:
                                                if key in memory.metadata:
                                                    metadata_fields[key] = str(memory.metadata[key])
                                        
                                        # Create concept with metadata in a single atomic transaction
                                        # Use APOC procedures for atomic operations
                                        await self.semantic.run_query(
                                            """
                                            CALL apoc.do.when(
                                                EXISTS((:Concept {id: $id})),
                                                'MATCH (c:Concept {id: $id})
                                                 SET c += $properties
                                                 WITH c
                                                 OPTIONAL MATCH (c)-[r:RELATED_TO]->()
                                                 DELETE r
                                                 WITH c
                                                 UNWIND $related as rel
                                                 OPTIONAL MATCH (r:Concept {id: rel})
                                                 WITH c, r
                                                 WHERE r IS NOT NULL
                                                 MERGE (c)-[:RELATED_TO]->(r)
                                                 RETURN c',
                                                'CREATE (c:Concept)
                                                 SET c = $properties
                                                 SET c.id = $id
                                                 WITH c
                                                 UNWIND $related as rel
                                                 OPTIONAL MATCH (r:Concept {id: rel})
                                                 WITH c, r
                                                 WHERE r IS NOT NULL
                                                 MERGE (c)-[:RELATED_TO]->(r)
                                                 RETURN c',
                                                {id: $id, properties: $properties, related: $related}
                                            ) YIELD value
                                            RETURN value
                                            """,
                                            {
                                                "id": str(memory.id),
                                                "properties": {
                                                    "type": str(memory.type),
                                                    "description": str(memory.content),
                                                    "importance": metadata_fields.get("importance", "0.5"),
                                                    "thread_id": metadata_fields.get("thread_id", ""),
                                                    "description_meta": metadata_fields.get("description", ""),
                                                    "updated_at": datetime.now(timezone.utc).isoformat(),
                                                    "version": 1  # Add version for optimistic locking
                                                },
                                                "related": related
                                            }
                                        )
                                        break  # Success, exit retry loop
                                        
                                    except Exception as e:
                                        retry_count += 1
                                        if retry_count == MAX_RETRIES:
                                            logger.error(f"Failed to consolidate concept after {MAX_RETRIES} attempts: {str(e)}")
                                            logger.error(traceback.format_exc())
                                            raise
                                        else:
                                            logger.warning(f"Consolidation attempt {retry_count} failed: {str(e)}")
                                            await asyncio.sleep(BACKOFF_FACTOR * retry_count)
                            self.semantic_circuit.record_success()
                            
                            # Mark as consolidated in episodic layer
                            if memory.metadata:
                                memory.metadata["consolidated"] = True
                                await self.store_experience(memory, is_sync=True)
                        except Exception as e:
                            self.semantic_circuit.record_failure()
                            logger.error(f"Failed to consolidate memory {memory_id}: {str(e)}")
                            success = False
                except Exception as e:
                    logger.error(f"Failed to process memory {memory_id} for consolidation: {str(e)}")
                    success = False
                    
            return success
        except Exception as e:
            logger.error(f"Failed to consolidate memories: {str(e)}")
            logger.error(traceback.format_exc())
            return False
