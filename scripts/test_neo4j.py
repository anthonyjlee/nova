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
        
        # Count nodes
        logger.info("\nCounting nodes...")
        result = await graph_store.run_query("MATCH (n) RETURN count(n) as count")
        logger.info(f"Node count: {result}")
        
        # List all nodes
        logger.info("\nListing all nodes...")
        result = await graph_store.run_query("""
        MATCH (n) 
        RETURN labels(n) as type, n.name as name, n.id as id
        """)
        for row in result:
            logger.info(f"{row['type'][0]}: {row['name']} (id: {row.get('id', 'N/A')})")
            
        # List all relationships
        logger.info("\nListing all relationships...")
        result = await graph_store.run_query("""
        MATCH (a)-[r]->(b)
        RETURN a.name as from, type(r) as rel, b.name as to
        """)
        for row in result:
            logger.info(f"{row['from']} -{row['rel']}-> {row['to']}")
        
    except Exception as e:
        logger.error(f"Error testing connection: {str(e)}")
        raise
    finally:
        await graph_store.close()

if __name__ == "__main__":
    asyncio.run(test_connection())
