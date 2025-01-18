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
            
        except Exception as e:
            self.logger.error(f"Prerequisite check failed: {str(e)}")
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
            
        except Exception as e:
            self.logger.error(f"Failed to initialize chat system: {str(e)}")
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
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
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
                    }
                }
            )
            
            # Create agent roles
            await self.run_query(
                """
                CREATE (r:AgentRole {
                    name: 'agent_roles',
                    description: 'Agent roles and permissions',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
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
            
            # Create Nova Team agent
            nova_team = await BaseAgent.create(
                name="NovaTeam",
                agent_type="system",
                attributes={
                    "type": "system",
                    "workspace": "system",
                    "domain": BaseDomain.GENERAL,
                    "status": "active",
                    "capabilities": [
                        "task_detection",
                        "cognitive_processing",
                        "direct_messaging",
                        "thread_management",
                        "agent_spawning",
                        "memory_coordination",
                        "swarm_orchestration",
                        "emergent_task_detection"
                    ],
                    "visualization": {
                        "position": "center",
                        "category": "orchestrator"
                    }
                }
            )
            
            # Create Nova Support agent
            nova_support = await BaseAgent.create(
                name="NovaSupport",
                agent_type="system",
                attributes={
                    "type": "system",
                    "workspace": "system",
                    "domain": "system",
                    "status": "active",
                    "capabilities": [
                        "resource_allocation",
                        "system_health",
                        "direct_messaging",
                        "memory_management",
                        "system_operations",
                        "memory_consolidation"
                    ],
                    "visualization": {
                        "position": "inner",
                        "category": "system"
                    }
                }
            )
            
            # Create specialized agents
            specialized_agents = [
                {
                    "name": "TaskAgent",
                    "agent_type": "agent",
                    "attributes": {
                        "type": "task",
                        "workspace": "personal",
                        "domain": "tasks",
                        "status": "active",
                        "capabilities": [
                            "task_coordination",
                            "thread_management",
                            "resource_management",
                            "dependency_tracking"
                        ],
                        "visualization": {
                            "position": "inner",
                            "category": "task"
                        }
                    }
                },
                {
                    "name": "AnalyticsAgent",
                    "agent_type": "agent",
                    "attributes": {
                        "type": "analytics",
                        "workspace": "personal",
                        "domain": "analysis",
                        "status": "active",
                        "capabilities": [
                            "metrics_tracking",
                            "data_analysis",
                            "memory_store",
                            "memory_recall"
                        ],
                        "visualization": {
                            "position": "outer",
                            "category": "analysis"
                        }
                    }
                },
                {
                    "name": "ParsingAgent",
                    "agent_type": "agent",
                    "attributes": {
                        "type": "parsing",
                        "workspace": "personal",
                        "domain": "analysis",
                        "status": "active",
                        "capabilities": [
                            "content_parsing",
                            "data_extraction",
                            "memory_store",
                            "memory_recall"
                        ],
                        "visualization": {
                            "position": "outer",
                            "category": "analysis"
                        }
                    }
                },
                {
                    "name": "CoordinationAgent",
                    "agent_type": "agent",
                    "attributes": {
                        "type": "coordination",
                        "workspace": "personal",
                        "domain": "general",
                        "status": "active",
                        "capabilities": [
                            "agent_coordination",
                            "message_handling",
                            "memory_store",
                            "memory_recall"
                        ],
                        "visualization": {
                            "position": "inner",
                            "category": "coordination"
                        }
                    }
                },
                {
                    "name": "OrchestrationAgent",
                    "agent_type": "agent",
                    "attributes": {
                        "type": "orchestration",
                        "workspace": "personal",
                        "domain": "general",
                        "status": "active",
                        "capabilities": [
                            "task_orchestration",
                            "agent_coordination",
                            "memory_store",
                            "memory_recall"
                        ],
                        "visualization": {
                            "position": "inner",
                            "category": "orchestration"
                        }
                    }
                },
                {
                    "name": "ThreadAgent",
                    "agent_type": "agent",
                    "attributes": {
                        "type": "thread",
                        "workspace": "personal",
                        "domain": "chat",
                        "status": "active",
                        "capabilities": [
                            "thread_coordination",
                            "message_management",
                            "summarization",
                            "layer_sync"
                        ],
                        "visualization": {
                            "position": "inner",
                            "category": "communication"
                        }
                    }
                },
                {
                    "name": "DialogueAgent",
                    "agent_type": "agent",
                    "attributes": {
                        "type": "dialogue",
                        "workspace": "personal",
                        "domain": "chat",
                        "status": "active",
                        "capabilities": [
                            "thread_context",
                            "message_routing",
                            "conversation_tracking",
                            "llm_integration"
                        ],
                        "visualization": {
                            "position": "outer",
                            "category": "communication"
                        }
                    }
                }
            ]
            
            # Create each specialized agent
            for agent_spec in specialized_agents:
                await BaseAgent.create(**agent_spec)
            
            # Create visualization structure
            await self._create_visualization_structure()
            
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
                    metadata: $metadata
                })
                """,
                {
                    "name": name,
                    "description": description,
                    "domain": domain,
                    "is_system": is_system,
                    "metadata": {
                        "status": "active",
                        "notifications": True,
                        "privacy": "public"
                    }
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
            
            # Connect Nova Team agent to nova-team channel
            await self.run_query(
                """
                MATCH (a:Agent {name: 'NovaTeam'})
                MATCH (c:Channel {name: 'nova-team'})
                MERGE (a)-[:MEMBER_OF {role: 'admin', joined_at: datetime()}]->(c)
                """
            )
            
            # Connect Nova Support agent to nova-support channel
            await self.run_query(
                """
                MATCH (a:Agent {name: 'NovaSupport'})
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
            

    async def _create_visualization_structure(self):
        """Create visualization structure for agents."""
        try:
            self.logger.info("Creating agent visualization structure...")
            
            # Create constraint for visualization nodes
            await self.run_query(
                """
                CREATE CONSTRAINT agent_viz_id IF NOT EXISTS
                FOR (v:AgentVisualization) REQUIRE v.id IS UNIQUE
                """
            )
            
            # Create visualization nodes
            await self.run_query(
                """
                MATCH (a:Agent)
                WHERE a.attributes.visualization IS NOT NULL
                MERGE (v:AgentVisualization {
                    id: a.name,
                    position: a.attributes.visualization.position,
                    category: a.attributes.visualization.category
                })
                MERGE (a)-[:HAS_VISUALIZATION]->(v)
                """
            )
            
            # Create position-based relationships
            await self.run_query(
                """
                MATCH (center:AgentVisualization {position: 'center'})
                MATCH (inner:AgentVisualization {position: 'inner'})
                MERGE (center)-[:COORDINATES]->(inner)
                """
            )
            
            await self.run_query(
                """
                MATCH (center:AgentVisualization {position: 'center'})
                MATCH (outer:AgentVisualization {position: 'outer'})
                MERGE (center)-[:COORDINATES]->(outer)
                """
            )
            
            # Create category-based relationships
            await self.run_query(
                """
                MATCH (a:AgentVisualization)
                MATCH (b:AgentVisualization)
                WHERE a.category = b.category AND a <> b
                MERGE (a)-[:COLLABORATES]->(b)
                """
            )
            
            # Create memory sync relationships
            await self.run_query(
                """
                MATCH (a:Agent)
                MATCH (b:Agent)
                WHERE 'memory_store' IN a.attributes.capabilities
                AND 'memory_store' IN b.attributes.capabilities
                AND a <> b
                MERGE (a)-[:SYNCS_MEMORY {type: 'functional'}]->(b)
                """
            )
            
            # Create memory operations relationships
            await self.run_query(
                """
                MATCH (a:Agent)
                MATCH (b:Agent)
                WHERE 'memory_recall' IN a.attributes.capabilities
                AND 'memory_recall' IN b.attributes.capabilities
                AND a <> b
                MERGE (a)-[:SHARES_MEMORY {type: 'functional'}]->(b)
                """
            )
            
            self.logger.info("Agent visualization structure created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create visualization structure: {str(e)}")
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
