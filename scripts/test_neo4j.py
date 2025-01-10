"""Test Neo4j connection."""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.nia.memory.graph_store import GraphStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    """Test Neo4j connection with a simple query."""
    try:
        graph_store = GraphStore()
        await graph_store.connect()
        
        # Try a simple query
        logger.info("Testing simple query...")
        result = await graph_store.run_query("RETURN 1 as n")
        logger.info(f"Query result: {result}")
        
        # Try to count nodes
        logger.info("Counting nodes...")
        result = await graph_store.run_query("MATCH (n) RETURN count(n) as count")
        logger.info(f"Node count: {result}")
        
    except Exception as e:
        logger.error(f"Error testing connection: {str(e)}")
        raise
    finally:
        await graph_store.close()

if __name__ == "__main__":
    asyncio.run(test_connection())
