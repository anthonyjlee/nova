"""Initialize task management system."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

from src.nia.core.neo4j.base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)

class TaskInitializer(Neo4jBaseStore):
    """Initialize task management system."""
    
    def __init__(self):
        """Initialize task system."""
        super().__init__(uri="bolt://localhost:7687", user="neo4j", password="password")
        
    async def initialize(self):
        """Initialize task components."""
        try:
            logger.info("Initializing task management system...")
            
            # Create constraints
            await self.run_query(
                """
                CREATE CONSTRAINT task_id IF NOT EXISTS
                FOR (t:Task) REQUIRE t.id IS UNIQUE
                """
            )
            
            await self.run_query(
                """
                CREATE CONSTRAINT task_state_name IF NOT EXISTS
                FOR (s:TaskState) REQUIRE s.name IS UNIQUE
                """
            )
            
            # Create task states
            states = [
                {
                    "name": "pending",
                    "description": "Task is waiting to be started"
                },
                {
                    "name": "in_progress",
                    "description": "Task is currently being worked on"
                },
                {
                    "name": "completed",
                    "description": "Task has been successfully completed"
                },
                {
                    "name": "failed",
                    "description": "Task failed to complete"
                }
            ]
            
            for state in states:
                await self.run_query(
                    """
                    MERGE (s:TaskState {name: $name})
                    SET s.description = $description
                    """,
                    state
                )
            
            # Create state transitions
            transitions = [
                ("pending", "in_progress"),
                ("in_progress", "completed"),
                ("in_progress", "failed"),
                ("failed", "pending")
            ]
            
            for from_state, to_state in transitions:
                await self.run_query(
                    """
                    MATCH (from:TaskState {name: $from_state})
                    MATCH (to:TaskState {name: $to_state})
                    MERGE (from)-[:CAN_TRANSITION_TO]->(to)
                    """,
                    {"from_state": from_state, "to_state": to_state}
                )
            
            logger.info("Task management system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize task system: {str(e)}")
            raise

if __name__ == "__main__":
    async def main():
        initializer = TaskInitializer()
        await initializer.initialize()
        
    asyncio.run(main())
