"""Memory initialization module."""

from typing import Optional
from src.nia.memory.two_layer import TwoLayerMemorySystem
from src.nia.memory.vector_store import VectorStore
from src.nia.memory.embedding import EmbeddingService

class MemoryInitializer:
    """Handles initialization of memory systems."""
    
    def __init__(self):
        """Initialize the memory initializer."""
        self._memory_system: Optional[TwoLayerMemorySystem] = None
        self.vector_store = None
        self.embedding_service = None

    @property
    def memory_system(self) -> TwoLayerMemorySystem:
        """Get the memory system, raising an error if not initialized."""
        if not self._memory_system:
            raise RuntimeError("Memory system not initialized")
        return self._memory_system

    async def connect(self):
        """Connect to memory systems."""
        if not self.embedding_service:
            # Initialize embedding service
            self.embedding_service = EmbeddingService()
        
        if not self.vector_store:
            # Initialize vector store with embedding service
            self.vector_store = VectorStore(
                embedding_service=self.embedding_service
            )
            # Connect vector store
            await self.vector_store.connect()

    async def initialize(self):
        """Initialize memory systems."""
        # First connect to ensure everything is set up
        await self.connect()
        
        # Initialize two-layer memory system with vector store
        self._memory_system = TwoLayerMemorySystem(
            vector_store=self.vector_store
        )
        
        # Initialize the memory system
        await self._memory_system.initialize()
        
        if not self._memory_system or not self._memory_system._initialized:
            raise RuntimeError("Failed to initialize memory system")
