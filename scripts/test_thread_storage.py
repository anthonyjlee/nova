#!/usr/bin/env python3
"""Test script for thread storage functionality."""

import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.nova.core.thread_manager import ThreadManager
from nia.memory.embedding import EmbeddingService
from nia.memory.vector_store import VectorStore

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_test_metadata() -> List[Dict[str, Any]]:
    """Get test cases for thread metadata."""
    return [
        {
            "type": "test",
            "system": False,
            "pinned": False,
            "description": "Test thread"
        },
        {
            "type": "system",
            "system": True,
            "pinned": True,
            "description": "System thread"
        },
        {
            "type": "user",
            "system": False,
            "pinned": True,
            "description": "Pinned user thread"
        },
        {
            "type": "agent",
            "system": True,
            "pinned": False,
            "description": "Agent thread"
        },
        {
            "type": "chat",
            "system": False,
            "pinned": False,
            "description": "Chat thread"
        },
        {
            "type": "task",
            "system": False,
            "pinned": True,
            "description": "Task thread"
        }
    ]

async def create_test_thread(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Create a test thread with given metadata."""
    thread_id = str(uuid.uuid4())
    return {
        "id": thread_id,
        "name": f"Test Thread ({metadata['type']})",
        "domain": "test",
        "messages": [],
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
        "workspace": "test",
        "participants": [],
        "metadata": metadata
    }

async def verify_vector_store_directly(vector_store: VectorStore, thread_id: str, metadata: Dict[str, Any]) -> bool:
    """Verify thread exists in vector store using direct API calls."""
    logger.info(f"Verifying thread {thread_id} in vector store...")
    
    # Try direct point retrieval
    logger.info("Retrieving point from vector store...")
    points = vector_store.client.retrieve(
        collection_name="memories",
        ids=[thread_id]
    )
    
    # Log raw response for debugging
    logger.debug(f"Vector store response: {points}")
    
    if not points:
        logger.error("Point not found in vector store")
        return False
        
    point = points[0]  # Get first (and only) point since we're retrieving by ID
    if not point.payload:
        logger.error("Point has no payload")
        return False
    
    # Log full payload structure for debugging
    logger.debug("Full payload structure:")
    logger.debug(f"Point ID: {point.id}")
    logger.debug(f"Raw payload: {point.payload}")
    
    # Verify metadata fields
    payload = point.payload
    
    # Log each level of nesting
    logger.debug("Payload structure analysis:")
    logger.debug(f"Top level keys: {list(payload.keys())}")
    
    if "content" not in payload:
        logger.error("Missing 'content' key in payload")
        return False
        
    content = payload["content"]
    logger.debug(f"Content level keys: {list(content.keys())}")
    
    if "content" not in content:
        logger.error("Missing nested 'content' key in content")
        return False
        
    thread_content = content["content"]
    logger.debug(f"Thread content keys: {list(thread_content.keys())}")
    
    if "metadata" not in thread_content:
        logger.error("Missing 'metadata' key in thread content")
        return False
        
    thread_metadata = thread_content["metadata"]
    logger.debug(f"Thread metadata: {thread_metadata}")
    
    # Verify thread ID
    if payload.get("metadata_thread_id") != thread_id:
        logger.error(f"Thread ID mismatch: {payload.get('metadata_thread_id')} != {thread_id}")
        return False
    
    # Verify metadata fields
    if thread_metadata.get("type") != metadata["type"]:
        logger.error(f"Thread type mismatch: {thread_metadata.get('type')} != {metadata['type']}")
        return False
    logger.debug(f"Thread type verified: {thread_metadata['type']}")
    
    if thread_metadata.get("system") != metadata["system"]:
        logger.error(f"System flag mismatch: {thread_metadata.get('system')} != {metadata['system']}")
        return False
    logger.debug(f"System flag verified: {thread_metadata['system']}")
    
    if thread_metadata.get("pinned") != metadata["pinned"]:
        logger.error(f"Pinned flag mismatch: {thread_metadata.get('pinned')} != {metadata['pinned']}")
        return False
    logger.debug(f"Pinned flag verified: {thread_metadata['pinned']}")
    
    logger.info(f"Successfully verified thread {thread_id}")
    return True

async def run_tests():
    """Run all thread storage tests."""
    # Initialize components
    embedding_service = EmbeddingService()
    vector_store = VectorStore(embedding_service)
    memory_system = TwoLayerMemorySystem(vector_store=vector_store)
    
    try:
        # Initialize components
        logger.info("Initializing components...")
        await vector_store.connect()
        await memory_system.initialize()
        
        # Create thread manager
        thread_manager = ThreadManager(memory_system)
        
        # Run tests for each metadata configuration
        for metadata in get_test_metadata():
            try:
                # Create test thread
                thread = await create_test_thread(metadata)
                logger.info(f"Testing thread storage with metadata type: {metadata['type']}")
                
                # Store thread
                await thread_manager._store_thread(thread)
                
                # Verify storage using direct vector store API
                if not await verify_vector_store_directly(vector_store, thread["id"], metadata):
                    raise Exception(f"Thread verification failed for type {metadata['type']}")
                
                logger.info(f"Successfully verified thread with type: {metadata['type']}")
                
            except Exception as e:
                logger.error(f"Test failed for metadata type {metadata['type']}: {str(e)}")
                raise
                
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}")
        raise
    finally:
        if hasattr(memory_system, 'cleanup'):
            await memory_system.cleanup()

if __name__ == "__main__":
    asyncio.run(run_tests())
