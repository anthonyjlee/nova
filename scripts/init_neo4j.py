"""Initialize Neo4j database schema."""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.nia.core.neo4j.base_store import Neo4jBaseStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_neo4j():
    """Initialize Neo4j database schema."""
    try:
        store = Neo4jBaseStore()
        await store.connect()
        
        # Create constraints and indexes
        queries = [
            # Unique constraint on Agent id
            """
            CREATE CONSTRAINT agent_id IF NOT EXISTS
            FOR (a:Agent) REQUIRE a.id IS UNIQUE
            """,
            
            # Index on Agent type
            """
            CREATE INDEX agent_type IF NOT EXISTS
            FOR (a:Agent) ON (a.type)
            """,
            
            # Index on Agent workspace
            """
            CREATE INDEX agent_workspace IF NOT EXISTS
            FOR (a:Agent) ON (a.workspace)
            """
        ]
        
        for query in queries:
            logger.info(f"Executing query: {query}")
            try:
                await store.run_query(query)
                logger.info("Query executed successfully")
            except Exception as e:
                logger.error(f"Error executing query: {str(e)}")
                raise
                
        logger.info("Neo4j initialization complete")
        
    except Exception as e:
        logger.error(f"Error initializing Neo4j: {str(e)}")
        raise
    finally:
        await store.close()

if __name__ == "__main__":
    asyncio.run(init_neo4j())
