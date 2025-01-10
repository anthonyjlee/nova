"""Clear all Neo4j data."""

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

class CleanupStore(Neo4jBaseStore):
    """Store class for cleaning up Neo4j data."""
    
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

    async def clear_data(self):
        """Clear all Neo4j data with proper transaction handling."""
        try:
            await self.connect()
            
            # First drop all constraints and indexes
            logger.info("Dropping all constraints and indexes...")
            async with self.transaction() as tx:
                # Drop constraints
                result = await tx.run("SHOW CONSTRAINTS")
                constraints = await result.data()
                for constraint in constraints:
                    name = constraint.get('name')
                    if name:
                        await tx.run(f"DROP CONSTRAINT {name} IF EXISTS")
                
                # Drop indexes
                result = await tx.run("SHOW INDEXES")
                indexes = await result.data()
                for index in indexes:
                    name = index.get('name')
                    if name:
                        await tx.run(f"DROP INDEX {name} IF EXISTS")
            
            # Delete relationships and nodes in batches
            logger.info("Deleting all nodes and relationships in batches...")
            batch_size = 500  # Reduced batch size
            
            # Delete relationships first
            total_deleted = 0
            while True:
                async with self.transaction() as tx:
                    result = await tx.run(
                        f"MATCH ()-[r]->() WITH r LIMIT {batch_size} "
                        f"DELETE r RETURN count(r) as count"
                    )
                    data = await result.data()
                    deleted = data[0]["count"]
                    if deleted == 0:
                        break
                    total_deleted += deleted
                    logger.info(f"Deleted {deleted} relationships (Total: {total_deleted})")
                await asyncio.sleep(0.1)  # Brief pause between batches
            
            # Then delete nodes
            total_deleted = 0
            while True:
                async with self.transaction() as tx:
                    result = await tx.run(
                        f"MATCH (n) WITH n LIMIT {batch_size} "
                        f"DELETE n RETURN count(n) as count"
                    )
                    data = await result.data()
                    deleted = data[0]["count"]
                    if deleted == 0:
                        break
                    total_deleted += deleted
                    logger.info(f"Deleted {deleted} nodes (Total: {total_deleted})")
                await asyncio.sleep(0.1)  # Brief pause between batches
            
            # Verify deletion
            async with self.transaction() as tx:
                result = await tx.run("MATCH (n) RETURN count(n) as count")
                data = await result.data()
                remaining = data[0]["count"]
                logger.info(f"Remaining nodes: {remaining}")
                if remaining > 0:
                    logger.warning(f"Warning: {remaining} nodes could not be deleted")
                
                result = await tx.run("MATCH ()-[r]->() RETURN count(r) as count")
                data = await result.data()
                remaining = data[0]["count"]
                logger.info(f"Remaining relationships: {remaining}")
                if remaining > 0:
                    logger.warning(f"Warning: {remaining} relationships could not be deleted")
        except Exception as e:
            logger.error(f"Error clearing data: {str(e)}")
            raise
        finally:
            await self.close()

async def main():
    """Main entry point."""
    store = CleanupStore()
    try:
        await store.clear_data()
    finally:
        await store.close()

if __name__ == "__main__":
    asyncio.run(main())
