#!/usr/bin/env python3
"""Script to test thread creation."""

import asyncio
import logging
from nia.memory.vector_store import VectorStore
from nia.memory.embedding import EmbeddingService
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Create and verify a test thread."""
    try:
        # Initialize services
        embedding_service = EmbeddingService()
        vector_store = VectorStore(embedding_service)
        
        # Connect to vector store
        logger.info("Connecting to vector store...")
        await vector_store.connect()
        
        # Create test thread
        now = datetime.now().isoformat()
        thread = {
            "id": "nova-team",
            "name": "Nova Team",
            "domain": "general",
            "messages": [],
            "createdAt": now,
            "updatedAt": now,
            "workspace": "personal",
            "participants": [],
            "metadata": {
                "type": "agent-team",
                "system": True,
                "pinned": True,
                "description": "This is where NOVA and core agents collaborate."
            }
        }
        
        # Store thread
        logger.info("Storing test thread...")
        metadata = {
            "thread_id": thread["id"],
            "type": "thread",
            "consolidated": False,
            "system": thread["metadata"]["system"],
            "pinned": thread["metadata"]["pinned"],
            "domain": thread["domain"],
            "source": "nova"
        }
        await vector_store.store_vector(thread, metadata=metadata)
        
        # Verify storage
        logger.info("Verifying storage...")
        points = await vector_store.inspect_collection()
        
        # Look for specific thread
        logger.info("\nSearching for nova-team thread...")
        for point in points:
            if point.payload.get("metadata_thread_id") == "nova-team":
                logger.info("Found nova-team thread:")
                logger.info(f"Point ID: {point.id}")
                logger.info("Metadata:")
                for k, v in point.payload.items():
                    if k.startswith("metadata_"):
                        logger.info(f"  {k}: {v}")
                logger.info("Content:")
                logger.info(point.payload.get("content"))
                break
        else:
            logger.info("nova-team thread not found")
    except Exception as e:
        logger.error(f"Error testing thread creation: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
