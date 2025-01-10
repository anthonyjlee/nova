"""Clear all Neo4j data."""

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

async def clear_data():
    """Clear all Neo4j data."""
    try:
        graph_store = GraphStore()
        await graph_store.connect()
        
        # Delete all nodes and relationships
        logger.info("Deleting all nodes and relationships...")
        await graph_store.run_query("MATCH (n) DETACH DELETE n")
        
        # Verify deletion
        result = await graph_store.run_query("MATCH (n) RETURN count(n) as count")
        logger.info(f"Remaining nodes: {result[0]['count']}")
        
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        raise
    finally:
        await graph_store.close()

if __name__ == "__main__":
    asyncio.run(clear_data())
