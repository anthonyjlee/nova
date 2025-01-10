"""Initialize test data in graph store."""

import asyncio
import json
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.nia.core.neo4j.base_store import Neo4jBaseStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InitializeStore(Neo4jBaseStore):
    """Store class for initializing graph data."""
    
    async def _execute_with_retry(self, operation):
        """Execute an operation with retry logic."""
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                return await operation()
            except Exception as e:
                last_error = e
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Operation failed after {max_retries} attempts: {str(e)}")
                    raise
                logger.warning(f"Operation failed, attempt {retry_count}/{max_retries}: {str(e)}")
                await asyncio.sleep(1)  # Wait before retry
                continue
        
        raise last_error if last_error else Exception("Operation failed after retries")

    async def initialize_graph(self):
        """Initialize test data in graph store."""
        try:
            await self.connect()
            
            # Check existing nodes
            logger.info("Checking existing nodes...")
            async with self.transaction() as tx:
                result = await tx.run("""
                MATCH (n) 
                RETURN labels(n) as labels, n.name as name
                """)
                data = await result.data()
                
                existing_nodes = {
                    f"{r['labels'][0]}:{r['name']}" 
                    for r in data 
                    if r['labels'] and r['name']
                }
                logger.info(f"Found existing nodes: {existing_nodes}")
            
            # Create nodes if they don't exist
            logger.info("Creating missing nodes...")
            
            nodes_to_create = [
                ("Concept", "Belief", "concept"),
                ("Concept", "Desire", "concept"),
                ("Concept", "Emotion", "concept")
            ]
            
            async with self.transaction() as tx:
                for node in nodes_to_create:
                    node_key = f"{node[0]}:{node[1]}"
                    if node_key not in existing_nodes:
                        await tx.run(f"""
                        CREATE (n:{node[0]} {{
                            name: '{node[1]}',
                            type: '{node[2]}'
                        }})
                        """)
                        logger.info(f"Created {node_key}")
                    else:
                        logger.info(f"Node {node_key} already exists")
            
            # Create relationships
            logger.info("Creating relationships...")
            
            async with self.transaction() as tx:
                # Create all relationships in a single query
                await tx.run("""
                // Concept relationships
                MATCH (belief:Concept {name: 'Belief'})
                MATCH (desire:Concept {name: 'Desire'})
                MATCH (emotion:Concept {name: 'Emotion'})
                MERGE (belief)-[:INFLUENCES]->(desire)
                MERGE (desire)-[:AFFECTS]->(emotion)
                MERGE (emotion)-[:IMPACTS]->(belief)

                """)
            
            logger.info("Test data created successfully")
            
            # Verify data was created
            async with self.transaction() as tx:
                result = await tx.run("""
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->()
                RETURN count(DISTINCT n) as nodes, count(r) as edges
                """)
                data = await result.data()
                logger.info(f"Graph contains {data[0]['nodes']} nodes and {data[0]['edges']} edges")
            
        except Exception as e:
            logger.error(f"Error initializing graph: {str(e)}")
            raise

async def main():
    """Main entry point."""
    store = InitializeStore()
    try:
        await store.initialize_graph()
    finally:
        await store.close()

if __name__ == "__main__":
    asyncio.run(main())
