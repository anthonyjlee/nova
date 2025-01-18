"""Initialize WebSocket system components."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

from src.nia.core.neo4j.base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)

class WebSocketInitializer(Neo4jBaseStore):
    """Initialize WebSocket system."""
    
    def __init__(self):
        """Initialize WebSocket system."""
        super().__init__(uri="bolt://localhost:7687", user="neo4j", password="password")
        
    async def initialize(self):
        """Initialize WebSocket components."""
        try:
            logger.info("Initializing WebSocket system...")
            
            # Create constraints
            await self.run_query(
                """
                CREATE CONSTRAINT websocket_endpoint_name IF NOT EXISTS
                FOR (e:WebSocketEndpoint) REQUIRE e.name IS UNIQUE
                """
            )
            
            await self.run_query(
                """
                CREATE CONSTRAINT websocket_channel_name IF NOT EXISTS
                FOR (c:WebSocketChannel) REQUIRE c.name IS UNIQUE
                """
            )
            
            # Create default endpoints
            endpoints = [
                {
                    "name": "debug",
                    "path": "/ws/debug",
                    "description": "Debug WebSocket endpoint for real-time debug information"
                },
                {
                    "name": "chat",
                    "path": "/ws/chat",
                    "description": "Chat WebSocket endpoint for real-time messaging"
                }
            ]
            
            for endpoint in endpoints:
                await self.run_query(
                    """
                    MERGE (e:WebSocketEndpoint {name: $name})
                    SET e.path = $path,
                        e.description = $description
                    """,
                    endpoint
                )
            
            # Create default channels
            channels = [
                {
                    "name": "system",
                    "description": "System-wide notifications and events"
                },
                {
                    "name": "debug",
                    "description": "Debug messages and logs"
                }
            ]
            
            for channel in channels:
                await self.run_query(
                    """
                    MERGE (c:WebSocketChannel {name: $name})
                    SET c.description = $description
                    """,
                    channel
                )
            
            # Link endpoints to channels
            await self.run_query(
                """
                MATCH (e:WebSocketEndpoint {name: 'debug'})
                MATCH (c:WebSocketChannel {name: 'debug'})
                MERGE (e)-[:BROADCASTS_TO]->(c)
                """
            )
            
            await self.run_query(
                """
                MATCH (e:WebSocketEndpoint {name: 'chat'})
                MATCH (c:WebSocketChannel {name: 'system'})
                MERGE (e)-[:BROADCASTS_TO]->(c)
                """
            )
            
            logger.info("WebSocket system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket system: {str(e)}")
            raise

if __name__ == "__main__":
    async def main():
        initializer = WebSocketInitializer()
        await initializer.initialize()
        
    asyncio.run(main())
