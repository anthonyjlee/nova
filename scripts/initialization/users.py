#!/usr/bin/env python3
"""Initialize user management system including profiles and settings."""

import asyncio
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

from src.nia.core.neo4j.base_store import Neo4jBaseStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserInitializer(Neo4jBaseStore):
    """Initialize user management components."""
    
    def __init__(self):
        """Initialize user management system."""
        super().__init__(uri="bolt://localhost:7687", user="neo4j", password="password")
        self.logger = logging.getLogger("user_init")
        
    async def initialize(self):
        """Initialize all user management components."""
        try:
            # Connect to Neo4j
            await self.connect()
            
            # 1. Initialize user schema
            await self._initialize_user_schema()
            
            # 2. Set up profile templates
            await self._setup_profile_templates()
            
            # 3. Initialize auto-approval rules
            await self._initialize_approval_rules()
            
            # 4. Set up adaptation rules
            await self._setup_adaptation_rules()
            
            self.logger.info("User management system initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize user management system: {str(e)}")
            raise
            
    async def _initialize_user_schema(self):
        """Initialize user schema."""
        try:
            self.logger.info("Initializing user schema...")
            
            # Create user constraints
            await self.run_query(
                """
                CREATE CONSTRAINT user_id IF NOT EXISTS
                FOR (u:User) REQUIRE u.id IS UNIQUE
                """
            )
            
            # Create profile constraints
            await self.run_query(
                """
                CREATE CONSTRAINT profile_id IF NOT EXISTS
                FOR (p:Profile) REQUIRE p.id IS UNIQUE
                """
            )
            
            # Create workspace index
            await self.run_query(
                """
                CREATE INDEX user_workspace IF NOT EXISTS
                FOR (u:User)
                ON (u.workspace)
                """
            )
            
            # Create domain index
            await self.run_query(
                """
                CREATE INDEX user_domain IF NOT EXISTS
                FOR (u:User)
                ON (u.domain)
                """
            )
            
            self.logger.info("User schema initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize user schema: {str(e)}")
            raise
            
    async def _setup_profile_templates(self):
        """Set up profile templates."""
        try:
            self.logger.info("Setting up profile templates...")
            
            # Create profile template
            await self.run_query(
                """
                CREATE (t:ProfileTemplate {
                    name: 'default',
                    description: 'Default user profile template',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "psychometrics": {
                            "big_five": {
                                "openness": 0.5,
                                "conscientiousness": 0.5,
                                "extraversion": 0.5,
                                "agreeableness": 0.5,
                                "neuroticism": 0.5
                            },
                            "learning_style": {
                                "visual": 0.33,
                                "auditory": 0.33,
                                "kinesthetic": 0.34
                            },
                            "communication": {
                                "direct": 0.5,
                                "detailed": 0.5,
                                "formal": 0.5
                            }
                        },
                        "auto_approval": {
                            "auto_approve_domains": [],
                            "approval_thresholds": {},
                            "restricted_operations": []
                        },
                        "adaptations": {
                            "task_format": "default",
                            "communication_style": "balanced",
                            "interface_mode": "standard"
                        }
                    }
                }
            )
            
            self.logger.info("Profile templates set up successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to set up profile templates: {str(e)}")
            raise
            
    async def _initialize_approval_rules(self):
        """Initialize auto-approval rules."""
        try:
            self.logger.info("Initializing auto-approval rules...")
            
            # Create approval rules
            await self.run_query(
                """
                CREATE (r:ApprovalRule {
                    name: 'auto_approval',
                    description: 'Auto-approval rules for tasks and operations',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "domains": {
                            "personal": {
                                "auto_approve": True,
                                "threshold": 0.8
                            },
                            "professional": {
                                "auto_approve": False,
                                "threshold": 0.9
                            }
                        },
                        "operations": {
                            "task_creation": {
                                "auto_approve": True,
                                "threshold": 0.7
                            },
                            "task_transition": {
                                "auto_approve": True,
                                "threshold": 0.8
                            },
                            "task_deletion": {
                                "auto_approve": False,
                                "threshold": 0.9
                            }
                        },
                        "restricted": [
                            "system_config",
                            "agent_creation",
                            "knowledge_deletion"
                        ]
                    }
                }
            )
            
            self.logger.info("Auto-approval rules initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize auto-approval rules: {str(e)}")
            raise
            
    async def _setup_adaptation_rules(self):
        """Set up adaptation rules."""
        try:
            self.logger.info("Setting up adaptation rules...")
            
            # Create adaptation rules
            await self.run_query(
                """
                CREATE (r:AdaptationRule {
                    name: 'user_adaptations',
                    description: 'Rules for adapting system behavior to user preferences',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "task_types": {
                            "analysis": {
                                "format": "detailed",
                                "style": "structured",
                                "validation": "strict"
                            },
                            "creative": {
                                "format": "flexible",
                                "style": "exploratory",
                                "validation": "lenient"
                            },
                            "routine": {
                                "format": "compact",
                                "style": "efficient",
                                "validation": "standard"
                            }
                        },
                        "communication_styles": {
                            "direct": {
                                "message_format": "concise",
                                "detail_level": "minimal",
                                "formality": "casual"
                            },
                            "detailed": {
                                "message_format": "comprehensive",
                                "detail_level": "high",
                                "formality": "professional"
                            },
                            "balanced": {
                                "message_format": "adaptive",
                                "detail_level": "moderate",
                                "formality": "flexible"
                            }
                        },
                        "interface_modes": {
                            "standard": {
                                "layout": "default",
                                "density": "medium",
                                "animations": True
                            },
                            "compact": {
                                "layout": "condensed",
                                "density": "high",
                                "animations": False
                            },
                            "comfortable": {
                                "layout": "spacious",
                                "density": "low",
                                "animations": True
                            }
                        }
                    }
                }
            )
            
            self.logger.info("Adaptation rules set up successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to set up adaptation rules: {str(e)}")
            raise

async def main():
    """Main entry point."""
    initializer = UserInitializer()
    try:
        await initializer.initialize()
    except Exception as e:
        logger.error(f"User management initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
