"""Initialize chat system components."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

from src.nia.core.neo4j.base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)

class ChatInitializer(Neo4jBaseStore):
    """Initialize chat system."""
    
    def __init__(self):
        """Initialize chat system."""
        super().__init__(uri="bolt://localhost:7687", user="neo4j", password="password")
        
    async def initialize(self):
        """Initialize chat components."""
        try:
            logger.info("Initializing chat system...")
            
            # Create constraints
            await self.run_query(
                """
                CREATE CONSTRAINT chat_thread_id IF NOT EXISTS
                FOR (t:ChatThread) REQUIRE t.id IS UNIQUE
                """
            )
            
            await self.run_query(
                """
                CREATE CONSTRAINT chat_message_id IF NOT EXISTS
                FOR (m:ChatMessage) REQUIRE m.id IS UNIQUE
                """
            )
            
            # Create system agents
            agents = [
                {
                    "name": "system",
                    "type": "system",
                    "description": "System agent for automated messages"
                },
                {
                    "name": "assistant",
                    "type": "system",
                    "description": "Primary assistant agent for chat interactions"
                }
            ]
            
            for agent in agents:
                await self.run_query(
                    """
                    MERGE (a:Agent {name: $name})
                    SET a.type = $type,
                        a.description = $description
                    """,
                    agent
                )
            
            # Create message types
            message_types = [
                {
                    "name": "text",
                    "description": "Plain text message"
                },
                {
                    "name": "system",
                    "description": "System notification or status update"
                },
                {
                    "name": "error",
                    "description": "Error message or warning"
                },
                {
                    "name": "action",
                    "description": "Action or command message"
                }
            ]
            
            for msg_type in message_types:
                await self.run_query(
                    """
                    MERGE (t:MessageType {name: $name})
                    SET t.description = $description
                    """,
                    msg_type
                )
            
            # Create thread types
            thread_types = [
                {
                    "name": "chat",
                    "description": "General chat thread"
                },
                {
                    "name": "task",
                    "description": "Task-specific discussion thread"
                },
                {
                    "name": "system",
                    "description": "System-level communication thread"
                }
            ]
            
            for thread_type in thread_types:
                await self.run_query(
                    """
                    MERGE (t:ThreadType {name: $name})
                    SET t.description = $description
                    """,
                    thread_type
                )
            
            logger.info("Chat system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize chat system: {str(e)}")
            raise

if __name__ == "__main__":
    async def main():
        initializer = ChatInitializer()
        await initializer.initialize()
        
    asyncio.run(main())
