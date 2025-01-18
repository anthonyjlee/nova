"""Initialize user management system."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

from src.nia.core.neo4j.base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)

class UserInitializer(Neo4jBaseStore):
    """Initialize user management system."""
    
    def __init__(self):
        """Initialize user system."""
        super().__init__(uri="bolt://localhost:7687", user="neo4j", password="password")
        
    async def initialize(self):
        """Initialize user components."""
        try:
            logger.info("Initializing user management system...")
            
            # Create constraints
            await self.run_query(
                """
                CREATE CONSTRAINT user_id IF NOT EXISTS
                FOR (u:User) REQUIRE u.id IS UNIQUE
                """
            )
            
            await self.run_query(
                """
                CREATE CONSTRAINT profile_template_name IF NOT EXISTS
                FOR (t:ProfileTemplate) REQUIRE t.name IS UNIQUE
                """
            )
            
            import json
            
            # Create default profile template
            settings = {
                "memory_threshold": 0.5,
                "consolidation_interval": 300,
                "max_context_length": 2000,
                "max_memory_age": 86400,  # 24 hours
                "importance_threshold": 0.7
            }
            
            permissions = {
                "can_create_workspace": True,
                "can_delete_workspace": True,
                "can_modify_agents": True,
                "can_access_system": True
            }
            
            # Convert dictionaries to JSON strings
            default_template = {
                "name": "default",
                "settings": json.dumps(settings),
                "permissions": json.dumps(permissions)
            }
            
            await self.run_query(
                """
                MERGE (t:ProfileTemplate {name: $name})
                SET t.settings = $settings,
                    t.permissions = $permissions
                """,
                default_template
            )
            
            # Create system user if not exists
            await self.run_query(
                """
                MERGE (u:User {id: "system"})
                SET u.name = "System",
                    u.type = "system",
                    u.profile = "default"
                """
            )
            
            logger.info("User management system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize user system: {str(e)}")
            raise

if __name__ == "__main__":
    async def main():
        initializer = UserInitializer()
        await initializer.initialize()
        
    asyncio.run(main())
