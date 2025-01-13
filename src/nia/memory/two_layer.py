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

    async def store_memory(self, memory: EpisodicMemory) -> bool:
        """Store a memory in the vector store."""
        try:
            # Convert memory to dict for storage
            memory_dict = memory.dict()
            return await self.store.store_vector(
                content=memory_dict["content"],
                metadata=memory_dict.get("metadata", {}),
                layer=memory_dict["type"].value if isinstance(memory_dict["type"], MemoryType) else memory_dict["type"]
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

    async def store_experience(self, memory: Memory) -> bool:
        """Store an experience in the episodic layer."""
        try:
            if not self._initialized:
                raise Exception("Memory system not initialized")
            # Convert memory to dict for storage
            memory_dict = memory.dict()
            # Use metadata type if provided, otherwise use memory type
            layer = memory_dict["metadata"].get("type", memory_dict["type"])
            if isinstance(layer, MemoryType):
                layer = layer.value
            return await self.vector_store.store_vector(
                content=memory_dict["content"],
                metadata=memory_dict["metadata"],
                layer=layer  # Use type from metadata or memory type
            )
        except Exception as e:
            logger.error(f"Failed to store experience: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    async def get_experience(self, memory_id: str) -> Optional[Memory]:
        """Get an experience from the episodic layer."""
        try:
            if not self._initialized:
                raise Exception("Memory system not initialized")
            # Get memory from vector store
            memories = await self.vector_store.search_vectors(
                content={"id": memory_id},
                limit=1,
                score_threshold=0.99
            )
            if not memories:
                return None
            memory_data = memories[0]
            
            # Get metadata and preserve original type
            metadata = memory_data["metadata"]
            memory_type = metadata.get("type", "thread")  # Default to thread if not specified
            
            # Create Memory object
            return Memory(
                id=memory_id,
                content=memory_data["content"],
                type=memory_type,  # Use original type from metadata
                importance=memory_data.get("importance", 1.0),
                timestamp=datetime.fromisoformat(memory_data["timestamp"]) if "timestamp" in memory_data else datetime.now(),
                context=memory_data.get("context", {}),
                metadata=metadata  # Use original metadata
            )
        except Exception as e:
            logger.error(f"Failed to get experience: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    async def cleanup(self):
        """Clean up resources."""
        try:
            logger.info("Cleaning up memory system...")
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
