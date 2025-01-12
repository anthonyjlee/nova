#!/usr/bin/env python3
"""Script to inspect episodic layer data."""

import asyncio
import logging
from nia.memory.vector_store import VectorStore
from nia.memory.embedding import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_qdrant():
    """Check if Qdrant server is running."""
    import requests
    try:
        response = requests.get("http://localhost:6333/collections")
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Failed to connect to Qdrant: {str(e)}")
        return False

async def main():
    """Inspect episodic layer data."""
    try:
        # Check if Qdrant is running
        if not await check_qdrant():
            logger.error("Qdrant server is not running. Please start it first.")
            logger.info("You can start it with: cd scripts/docker && docker compose up -d")
            return
            
        # Initialize services
        embedding_service = EmbeddingService()
        vector_store = VectorStore(embedding_service)
        
        # Connect to vector store
        logger.info("Connecting to vector store...")
        await vector_store.connect()
        
        # Inspect collection
        logger.info("Inspecting memories collection...")
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
        logger.error(f"Error inspecting episodic layer: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
