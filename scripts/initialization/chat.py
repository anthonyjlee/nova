#!/usr/bin/env python3
"""Initialize chat system including channels and system agents."""

import asyncio
import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

from src.nia.core.types.memory_types import BaseDomain
from src.nia.agents.base import BaseAgent
from src.nia.core.neo4j.base_store import Neo4jBaseStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create session-specific log directory
session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = Path("test_results/initialization_logs/chat")
log_dir.mkdir(parents=True, exist_ok=True)

def log_breakpoint(phase: str, data: Optional[Dict[str, Any]] = None):
    """Log a breakpoint with optional data."""
    timestamp = datetime.now(timezone.utc).isoformat()
    log_file = log_dir / f"session_{session_id}_{phase}.json"
    
    log_entry = {
        "timestamp": timestamp,
        "phase": phase,
        "data": data or {},
        "session_id": session_id,
        "type": "chat_initialization",
        "status": "success",
        "metadata": {
            "log_version": "1.0",
            "component": "chat",
            "environment": {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "platform": sys.platform
            }
        }
    }
    
    with open(log_file, "w") as f:
        json.dump(log_entry, f, indent=2)
    
    logger.info(f"Phase complete: {phase}")

class ChatInitializer(Neo4jBaseStore):
    """Initialize chat system components."""
    
    def __init__(self):
        """Initialize chat system."""
        super().__init__(uri="bolt://localhost:7687", user="neo4j", password="password")
        self.logger = logging.getLogger("chat_init")
        
    async def verify_prerequisites(self):
        """Verify that all prerequisites are in place."""
        try:
            # Check Neo4j schema
            schema_result = await self.run_query("SHOW CONSTRAINTS")
            required_constraints = ["agent_id", "task_id", "task_state"]
            for constraint in required_constraints:
                if not any(c["name"] == constraint for c in schema_result):
                    raise ValueError(f"Missing required constraint: {constraint}")
                    
            # Check basic concepts
            concept_result = await self.run_query("""
            MATCH (c:Concept)
            WHERE c.name IN ['Belief', 'Desire', 'Emotion']
            RETURN count(c) as count
            """)
            if not concept_result or not concept_result[0] or concept_result[0]["count"] < 3:
                raise ValueError("Missing basic concepts")
                
            # Check task structures
            task_result = await self.run_query("""
            MATCH (s:TaskState)
            RETURN count(s) as count
            """)
            if not task_result or not task_result[0] or task_result[0]["count"] < 4:
                raise ValueError("Missing task states")
                
            # Log successful verification
            log_breakpoint("prerequisites_check", {
                "constraints": [c["name"] for c in schema_result],
                "concepts": concept_result[0]["count"] if concept_result and concept_result[0] else 0,
                "task_states": task_result[0]["count"] if task_result and task_result[0] else 0
            })
            
            return True
            
        except ValueError as e:
            self.logger.error(f"Prerequisite check failed: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during prerequisite check: {str(e)}")
            return False
        
    async def initialize(self):
        """Initialize all chat components."""
        try:
            # Connect to Neo4j
            await self.connect()
            # 1. Initialize system agents
            await self._initialize_system_agents()
            
            # 2. Initialize channels
            await self._initialize_channels()
            
            # 3. Set up agent-channel relationships
            await self._setup_channel_relationships()
            
            # 4. Initialize agent management
            await self._initialize_agent_management()
            
            self.logger.info("Chat system initialization complete")
            
        except ValueError as e:
            self.logger.error(f"Validation error during initialization: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during initialization: {str(e)}")
            raise
            
    async def _initialize_agent_management(self):
        """Initialize agent management system."""
        try:
            self.logger.info("Initializing agent management...")
            
            # Create agent management rules
            await self.run_query(
                """
                CREATE (r:AgentManagementRule {
                    name: 'agent_management',
                    description: 'Rules for agent management and coordination',
                    config_json: $config_json,
                    created_at: datetime()
                })
                """,
                {
                    "config_json": json.dumps({
                        "metrics": {
                            "collection": {
                                "interval": 300,  # 5 minutes
                                "metrics": [
                                    "response_time",
                                    "tasks_completed",
                                    "success_rate",
                                    "uptime"
                                ]
                            },
                            "thresholds": {
                                "response_time": 5.0,  # seconds
                                "success_rate": 0.8,
                                "uptime": 0.95
                            }
                        },
                        "interactions": {
                            "history_limit": 1000,
                            "retention_days": 30,
                            "types": [
                                "message",
                                "task",
                                "status",
                                "error"
                            ]
                        },
                        "coordination": {
                            "team_size_limit": 10,
                            "specialization": {
                                "enabled": True,
                                "domains": [
                                    "general",
                                    "tasks",
                                    "chat",
                                    "analysis"
                                ]
                            },
                            "load_balancing": {
                                "enabled": True,
                                "max_concurrent": 5,
                                "distribution": "round_robin"
                            }
                        },
                        "monitoring": {
                            "health_check": {
                                "interval": 60,  # 1 minute
                                "timeout": 5
                            },
                            "alerts": {
                                "channels": ["nova-support"],
                                "levels": ["warning", "error", "critical"]
                            }
                        }
                    })
                }
            )
            
            # Create agent roles
            await self.run_query(
                """
                CREATE (r:AgentRole {
                    name: 'agent_roles',
                    description: 'Agent roles and permissions',
                    config_json: $config_json,
                    created_at: datetime()
                })
                """,
                {
                    "config_json": json.dumps({
                        "system": {
                            "permissions": ["all"],
                            "capabilities": ["all"]
                        },
                        "team": {
                            "permissions": [
                                "read_messages",
                                "send_messages",
                                "execute_tasks",
                                "access_memory"
                            ],
                            "capabilities": [
                                "task_execution",
                                "message_handling",
                                "memory_access"
                            ]
                        },
                        "specialized": {
                            "permissions": [
                                "read_messages",
                                "send_messages",
                                "execute_specialized_tasks"
                            ],
                            "capabilities": [
                                "specialized_execution",
                                "domain_expertise"
                            ]
                        }
                    }
                }
            )
            
            self.logger.info("Agent management initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent management: {str(e)}")
            raise
            
    async def _initialize_system_agents(self):
        """Initialize system agents."""
        try:
            self.logger.info("Initializing system agents...")
            
            # Create system agents
            system_agents = [
                {
                    "name": "system",
                    "agentType": "system",
                    "workspace": "system",
                    "status": "active",
                    "emotions": json.dumps({
                        "task_focus": "neutral",
                        "collaboration_readiness": "active",
                        "domain_confidence": "high"
                    }),
                    "capabilities": [
                        "system_messaging",
                        "status_updates",
                        "error_handling"
                    ],
                    "metadata_json": json.dumps({
                        "type": "system",
                        "description": "System agent for automated messages",
                        "capabilities": [
                            "system_messaging",
                            "status_updates",
                            "error_handling"
                        ],
                        "created_at": datetime.utcnow().isoformat(),
                        "visualization": {
                            "position": "center",
                            "category": "system"
                        }
                    })
                },
                {
                    "name": "assistant",
                    "agentType": "system",
                    "workspace": "system",
                    "status": "active",
                    "emotions": json.dumps({
                        "task_focus": "neutral",
                        "collaboration_readiness": "active",
                        "domain_confidence": "high"
                    }),
                    "capabilities": [
                        "chat_interaction",
                        "task_handling",
                        "user_assistance"
                    ],
                    "metadata_json": json.dumps({
                        "type": "system",
                        "description": "Primary assistant agent for chat interactions",
                        "capabilities": [
                            "chat_interaction",
                            "task_handling",
                            "user_assistance"
                        ],
                        "created_at": datetime.utcnow().isoformat(),
                        "visualization": {
                            "position": "inner",
                            "category": "assistant"
                        }
                    })
                }
            ]
            
            # Create each system agent
            for agent in system_agents:
                await self.run_query(
                    """
                    MERGE (a:Agent {name: $name})
                    SET a.type = 'system',
                        a.id = randomUUID(),
                        a.emotions = $emotions,
                        a.capabilities = $capabilities,
                        a.metadata = $metadata_json,
                        a.workspace = $workspace,
                        a.status = $status,
                        a.agentType = $agentType,
                        a.confidence = 0.8,
                        a.specialization = $agentType
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
            
            self.logger.info("System agents initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize system agents: {str(e)}")
            raise
            
    async def _initialize_channels(self):
        """Initialize chat channels."""
        try:
            self.logger.info("Initializing channels...")
            
            # Create Nova Team channel
            await self._create_channel(
                name="nova-team",
                description="Core agent operations channel for task detection and cognitive processing",
                domain=BaseDomain.GENERAL,
                is_system=True
            )
            
            # Create Nova Support channel
            await self._create_channel(
                name="nova-support",
                description="System operations channel for resource allocation and system health",
                domain="system",
                is_system=True
            )
            
            self.logger.info("Channels initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize channels: {str(e)}")
            raise
            
    async def _create_channel(
        self,
        name: str,
        description: str,
        domain: str,
        is_system: bool = False
    ):
        """Create a chat channel."""
        try:
            self.logger.info(f"Creating channel: {name}")
            
            # Create channel node
            await self.run_query(
                """
                CREATE (c:Channel {
                    name: $name,
                    description: $description,
                    domain: $domain,
                    is_system: $is_system,
                    created_at: datetime(),
                    status: 'active',
                    metadata_json: $metadata_json
                })
                """,
                {
                    "name": name,
                    "description": description,
                    "domain": domain,
                    "is_system": is_system,
                    "metadata_json": json.dumps({
                        "status": "active",
                        "notifications": True,
                        "privacy": "public"
                    })
                }
            )
            
            self.logger.info(f"Channel {name} created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create channel {name}: {str(e)}")
            raise
            
    async def _setup_channel_relationships(self):
        """Set up relationships between agents and channels."""
        try:
            self.logger.info("Setting up channel relationships...")
            
            # Connect system agent to nova-team channel
            await self.run_query(
                """
                MATCH (a:Agent {name: 'system', type: 'system'})
                MATCH (c:Channel {name: 'nova-team'})
                MERGE (a)-[:MEMBER_OF {role: 'admin', joined_at: datetime()}]->(c)
                """
            )
            
            # Connect assistant agent to nova-support channel
            await self.run_query(
                """
                MATCH (a:Agent {name: 'assistant', type: 'system'})
                MATCH (c:Channel {name: 'nova-support'})
                MERGE (a)-[:MEMBER_OF {role: 'admin', joined_at: datetime()}]->(c)
                """
            )
            
            # Set up channel-to-channel relationships
            await self.run_query(
                """
                MATCH (team:Channel {name: 'nova-team'})
                MATCH (support:Channel {name: 'nova-support'})
                MERGE (team)-[:COORDINATES {type: 'system'}]->(support)
                MERGE (support)-[:SUPPORTS {type: 'system'}]->(team)
                """
            )
            
            self.logger.info("Channel relationships established successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to set up channel relationships: {str(e)}")
            raise

async def main():
    """Main entry point."""
    initializer = ChatInitializer()
    try:
        await initializer.initialize()
    except Exception as e:
        logger.error(f"Chat initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
