#!/usr/bin/env python3
"""Initialize memory system for NIA."""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.nia.memory.two_layer import TwoLayerMemorySystem
from src.nia.memory.embedding import EmbeddingService
from src.nia.memory.vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_memory():
    """Initialize memory system."""
    try:
        # Create embedding service with correct model
        embedding_service = EmbeddingService(
            model_name="text-embedding-nomic-embed-text-v1.5@f16",
            api_base="http://localhost:1234/v1"
        )
        
        # Create vector store
        vector_store = VectorStore(embedding_service=embedding_service)
        
        # Initialize memory system
        memory_system = TwoLayerMemorySystem(vector_store=vector_store)
        await memory_system.initialize()
        
        # Verify initialization
        dimension = await embedding_service.dimension
        logger.info(f"Embedding model produces {dimension}-dimensional vectors")
        
        collection_name = await vector_store.get_collection_name()
        logger.info(f"Using collection: {collection_name}")
        
        # Test storing a memory
        from src.nia.core.types.memory_types import Memory, MemoryType
        import uuid
        test_memory = Memory(
            id=str(uuid.uuid4()),
            content="Test memory",
            type="test",
            metadata={
                "type": "test",
                "description": "Test memory for initialization"
            }
        )
        success = await memory_system.store_experience(test_memory)
        if not success:
            raise Exception("Failed to store test memory")
            
        # Test retrieving the memory
        # Get memory ID with type checking
        memory_id = test_memory.id
        if not memory_id:
            raise ValueError("Test memory ID is None")
            
        retrieved = await memory_system.get_experience(memory_id)
        if not retrieved:
            raise Exception("Failed to retrieve test memory")
            
        logger.info("Memory system initialization successful")
        
    except Exception as e:
        logger.error(f"Failed to initialize memory system: {str(e)}")
        raise
    finally:
        if 'memory_system' in locals():
            await memory_system.cleanup()

if __name__ == "__main__":
    asyncio.run(initialize_memory())
