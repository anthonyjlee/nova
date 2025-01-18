#!/usr/bin/env python3
"""Initialize memory system including Qdrant and Neo4j."""

import asyncio
import sys
import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

from src.nia.core.neo4j.base_store import Neo4jBaseStore
from src.nia.memory.vector_store import VectorStore
from src.nia.memory.embedding import EmbeddingService
from src.nia.memory.two_layer import TwoLayerMemorySystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check Python version."""
    logger.info("Checking Python version...")
    if sys.version_info < (3, 9):
        logger.error("Error: Python 3.9 or higher is required")
        sys.exit(1)
    logger.info(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_docker():
    """Check Docker installation."""
    logger.info("Checking Docker installation...")
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        logger.info("Docker is installed")
    except FileNotFoundError:
        logger.error("Docker not found. Please install Docker first:")
        logger.error("Visit: https://docs.docker.com/get-docker/")
        sys.exit(1)
    
    logger.info("Checking Docker Compose installation...")
    try:
        subprocess.run(["docker", "compose", "version"], check=True, capture_output=True)
        logger.info("Docker Compose is installed")
    except subprocess.CalledProcessError:
        logger.error("Docker Compose not found. Please install Docker Compose first:")
        logger.error("Visit: https://docs.docker.com/compose/install/")
        sys.exit(1)

def create_directories():
    """Create necessary directories."""
    logger.info("Creating directories...")
    directories = [
        "logs",
        "data",
        "visualizations"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True)
            logger.info(f"Created directory: {directory}")
        else:
            logger.info(f"Directory already exists: {directory}")

def setup_env():
    """Set up environment configuration."""
    logger.info("Setting up environment configuration...")
    
    # Create .env file with Neo4j credentials
    env_path = Path(".env")
    if not env_path.exists():
        logger.info("Creating .env file with Neo4j credentials...")
        with open(env_path, "w") as f:
            f.write("""# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password  # Change this in production
""")
        logger.info(".env file created")
    else:
        logger.info(".env file already exists")

class MemoryInitializer(Neo4jBaseStore):
    """Initialize memory system components."""
    
    def __init__(self):
        """Initialize memory system."""
        super().__init__(uri="bolt://localhost:7687", user="neo4j", password="password")
        self.logger = logging.getLogger("memory_init")
        self.embedding_service = EmbeddingService(
            api_base="http://localhost:1234/v1",
            model_name="text-embedding-nomic-embed-text-v1.5@q8_0"
        )
        self.vector_store = VectorStore(
            embedding_service=self.embedding_service
        )
        self.memory_system = TwoLayerMemorySystem(
            neo4j_uri="bolt://localhost:7687",
            vector_store=self.vector_store
        )
        
    async def initialize(self):
        """Initialize all memory components."""
        try:
            # Check system requirements
            check_python_version()
            check_docker()
            
            # Create required directories
            create_directories()
            
            # Set up environment
            setup_env()
            
            # Connect to Neo4j
            await self.connect()
            
            # Initialize memory system
            await self.memory_system.initialize()
            
            # 1. Initialize Neo4j schema
            await self._initialize_neo4j_schema()
            
            # 2. Initialize Qdrant collections
            await self._initialize_qdrant()
            
            # 3. Set up memory consolidation rules
            await self._setup_consolidation_rules()
            
            # 4. Initialize knowledge graph
            await self._initialize_knowledge_graph()
            
            # 5. Initialize system endpoints
            await self._initialize_system_endpoints()
            
            # 6. Initialize base agents
            await self._initialize_base_agents()
            
            # 7. Initialize core cognitive agents
            await self._initialize_core_agents()
            
            # 8. Verify memory system
            await self._verify_memory_system()
            
            self.logger.info("Memory system initialization complete")
        except Exception as e:
            self.logger.error(f"Failed to initialize memory system: {str(e)}")
            raise
            
    async def _verify_memory_system(self):
        """Verify memory system functionality."""
        try:
            self.logger.info("Verifying memory system...")
            
            # Verify embedding model
            dimension = await self.embedding_service.dimension
            self.logger.info(f"Embedding model produces {dimension}-dimensional vectors")
            
            # Verify vector store collection
            collection_name = await self.vector_store.get_collection_name()
            self.logger.info(f"Using collection: {collection_name}")
            
            # Test memory storage and retrieval
            from src.nia.core.types.memory_types import Memory, MemoryType
            import uuid
            
            test_memory = Memory(
                id=str(uuid.uuid4()),
                content="Test memory",
                type="test",
                metadata={
                    "type": "test",
                    "description": "Test memory for initialization"
                }
            )
            
            # Test storing memory
            success = await self.memory_system.store_experience(test_memory)
            if not success:
                raise Exception("Failed to store test memory")
            
            # Test retrieving memory
            memory_id = test_memory.id
            if not memory_id:
                raise ValueError("Test memory ID is None")
                
            retrieved = await self.memory_system.get_experience(memory_id)
            if not retrieved:
                raise Exception("Failed to retrieve test memory")
            
            # Create test tasks
            test_tasks = [
                {
                    "id": "TEST-001",
                    "label": "Test Development Task",
                    "type": "task",
                    "status": "pending",
                    "domain": "professional",
                    "description": "A test task for development",
                    "metadata": {
                        "priority": "high",
                        "estimated_hours": 4
                    }
                },
                {
                    "id": "TEST-002",
                    "label": "Test Personal Task",
                    "type": "task",
                    "status": "in_progress",
                    "domain": "personal",
                    "description": "A test task for organization",
                    "metadata": {
                        "priority": "medium",
                        "category": "organization"
                    }
                }
            ]
            
            for task in test_tasks:
                await self.run_query(
                    """
                    CREATE (t:Task)
                    SET t += $props
                    """,
                    {"props": task}
                )
            
            # Create test relationships
            await self.run_query(
                """
                MATCH (t1:Task {id: 'TEST-001'})
                MATCH (t2:Task {id: 'TEST-002'})
                CREATE (t1)-[:BLOCKS]->(t2)
                """
            )
            
            # Verify test data
            result = await self.run_query(
                """
                MATCH (t:Task)
                WHERE t.id IN ['TEST-001', 'TEST-002']
                RETURN count(t) as count
                """
            )
            if not result or result[0]["count"] != 2:
                raise Exception("Test tasks not properly created")
            
            # Test cleanup
            try:
                await self.memory_system.cleanup()
                self.logger.info("Memory system cleanup successful")
            except Exception as e:
                self.logger.error(f"Memory system cleanup failed: {str(e)}")
                raise
            
            # Test reconnection after cleanup
            try:
                await self.memory_system.initialize()
                self.logger.info("Memory system reconnection successful")
            except Exception as e:
                self.logger.error(f"Memory system reconnection failed: {str(e)}")
                raise
            
            self.logger.info("Memory system verification successful")
            
        except Exception as e:
            self.logger.error(f"Memory system verification failed: {str(e)}")
            raise
            
    async def _initialize_system_endpoints(self):
        """Initialize system endpoints."""
        try:
            self.logger.info("Initializing system endpoints...")
            
            # Create system endpoint rules
            await self.run_query(
                """
                CREATE (r:SystemEndpointRule {
                    name: 'system_endpoints',
                    description: 'Rules for system endpoints and operations',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "status": {
                            "health_check": {
                                "interval": 60,  # 1 minute
                                "timeout": 5,
                                "required_services": [
                                    "neo4j",
                                    "redis",
                                    "qdrant"
                                ]
                            },
                            "metrics": [
                                "uptime",
                                "request_count",
                                "error_rate",
                                "response_time"
                            ]
                        },
                        "memory": {
                            "store": {
                                "validation": {
                                    "required_fields": ["content", "type"],
                                    "optional_fields": ["metadata", "domain"]
                                },
                                "rate_limit": {
                                    "max_requests": 100,
                                    "window": 60  # 1 minute
                                }
                            },
                            "search": {
                                "validation": {
                                    "required_fields": ["query"],
                                    "optional_fields": ["domain", "limit"]
                                },
                                "rate_limit": {
                                    "max_requests": 50,
                                    "window": 60
                                }
                            },
                            "cross_domain": {
                                "validation": {
                                    "required_fields": ["operation", "domains"],
                                    "optional_fields": ["metadata"]
                                },
                                "requires_approval": True,
                                "rate_limit": {
                                    "max_requests": 10,
                                    "window": 60
                                }
                            },
                            "consolidate": {
                                "validation": {
                                    "optional_fields": ["domain"]
                                },
                                "schedule": {
                                    "interval": 3600,  # 1 hour
                                    "max_duration": 300  # 5 minutes
                                }
                            },
                            "prune": {
                                "validation": {
                                    "optional_fields": ["domain"]
                                },
                                "requires_approval": True,
                                "schedule": {
                                    "interval": 86400,  # 1 day
                                    "max_duration": 1800  # 30 minutes
                                }
                            }
                        }
                    }
                }
            )
            
            # Create endpoint monitoring rules
            await self.run_query(
                """
                CREATE (r:EndpointMonitoringRule {
                    name: 'endpoint_monitoring',
                    description: 'Rules for monitoring system endpoints',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "logging": {
                            "enabled": True,
                            "level": "INFO",
                            "include_metadata": True
                        },
                        "alerts": {
                            "channels": ["nova-support"],
                            "levels": ["warning", "error", "critical"]
                        },
                        "metrics": {
                            "collection": {
                                "enabled": True,
                                "interval": 60  # 1 minute
                            },
                            "thresholds": {
                                "response_time": 5.0,  # seconds
                                "error_rate": 0.01,  # 1%
                                "success_rate": 0.99  # 99%
                            }
                        }
                    }
                }
            )
            
            # Initialize WebSocket endpoints
            await self.run_query(
                """
                CREATE (e:WebSocketEndpoint {
                    name: 'debug_endpoint',
                    path: '/debug/client_{client_id}',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "auth": {
                            "required": True,
                            "api_keys": {
                                "development": {
                                    "permissions": ["all"],
                                    "expires": None
                                },
                                "valid-test-key": {
                                    "permissions": ["test"],
                                    "expires": None
                                }
                            }
                        },
                        "connection": {
                            "timeout": 30,
                            "ping_interval": 5,
                            "max_message_size": 65536,
                            "max_connections": 1000
                        },
                        "rate_limit": {
                            "max_messages": 100,
                            "window": 60
                        },
                        "error_handling": {
                            "retry_attempts": 3,
                            "retry_delay": 1,
                            "timeout": 10
                        }
                    }
                }
            )
            
            # Create authentication rules
            await self.run_query(
                """
                CREATE (r:AuthenticationRule {
                    name: 'ws_auth',
                    description: 'WebSocket authentication rules',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "auth_flow": {
                            "initial_state": "not_authenticated",
                            "steps": [
                                "connection_established",
                                "auth_message",
                                "validation",
                                "confirmation"
                            ],
                            "timeout": 30
                        },
                        "validation": {
                            "required_fields": [
                                "api_key",
                                "connection_type",
                                "domain",
                                "workspace"
                            ],
                            "allowed_types": ["chat", "debug"],
                            "allowed_domains": ["personal", "professional", "system"],
                            "allowed_workspaces": ["personal", "professional", "system"]
                        },
                        "error_codes": {
                            "invalid_key": 403,
                            "token_expired": 403,
                            "server_error": 500,
                            "rate_limit": 429
                        },
                        "close_codes": {
                            "normal": 1000,
                            "server_error": 1011,
                            "auth_error": 4000,
                            "rate_limit": 4001,
                            "invalid_format": 4002,
                            "protocol_violation": 4003
                        }
                    }
                }
            )
            
            # Create connection states
            states = [
                {
                    "name": "not_authenticated",
                    "description": "Initial connection state",
                    "value": "not_authenticated",
                    "metadata": {
                        "can_transition_to": ["authenticated"],
                        "requires_auth": False,
                        "timeout": 30
                    }
                },
                {
                    "name": "authenticated",
                    "description": "Successfully authenticated connection",
                    "value": "authenticated",
                    "metadata": {
                        "can_transition_to": ["not_authenticated"],
                        "requires_auth": True,
                        "timeout": None
                    }
                },
                {
                    "name": "error",
                    "description": "Connection error state",
                    "value": "error",
                    "metadata": {
                        "can_transition_to": ["not_authenticated"],
                        "requires_auth": False,
                        "timeout": 5
                    }
                },
                {
                    "name": "reconnecting",
                    "description": "Attempting to reconnect",
                    "value": "reconnecting",
                    "metadata": {
                        "can_transition_to": ["not_authenticated", "authenticated"],
                        "requires_auth": False,
                        "timeout": 30
                    }
                }
            ]
            
            for state in states:
                await self.run_query(
                    """
                    CREATE (s:ConnectionState {
                        name: $name,
                        description: $description,
                        value: $value,
                        metadata: $metadata,
                        created_at: datetime()
                    })
                    """,
                    state
                )
            
            # Create agent team rules
            await self.run_query(
                """
                CREATE (r:AgentTeamRule {
                    name: 'team_management',
                    description: 'Rules for agent team management',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "team_types": {
                            "core": {
                                "description": "Permanent specialized agents",
                                "channel": "#NovaTeam",
                                "capabilities": ["core_cognitive"]
                            },
                            "support": {
                                "description": "Permanent utility agents",
                                "channel": "#NovaSupport",
                                "capabilities": ["system_operations"]
                            },
                            "spawned": {
                                "description": "Ephemeral task-specific agents",
                                "channel": None,
                                "capabilities": ["task_specific"]
                            }
                        },
                        "team_composition": {
                            "min_agents": 1,
                            "max_agents": 10,
                            "required_roles": ["coordinator"],
                            "optional_roles": ["specialist", "executor"]
                        },
                        "team_lifecycle": {
                            "creation": {
                                "requires_approval": True,
                                "auto_channel_creation": True,
                                "initialization_timeout": 30
                            },
                            "operation": {
                                "heartbeat_interval": 60,
                                "status_updates": True,
                                "performance_monitoring": True
                            },
                            "termination": {
                                "cleanup_required": True,
                                "archive_data": True,
                                "notification_required": True
                            }
                        }
                    }
                }
            )
            
            # Create agent message rules
            await self.run_query(
                """
                CREATE (r:AgentMessageRule {
                    name: 'message_handling',
                    description: 'Rules for agent messaging',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "message_types": {
                            "direct": {
                                "requires_auth": True,
                                "delivery_confirmation": True,
                                "max_size": 65536
                            },
                            "broadcast": {
                                "requires_auth": True,
                                "scope_validation": True,
                                "rate_limit": {
                                    "max_messages": 10,
                                    "window": 60
                                }
                            },
                            "system": {
                                "requires_auth": False,
                                "priority": "high",
                                "persistence": True
                            }
                        },
                        "validation": {
                            "schema_validation": True,
                            "content_validation": True,
                            "size_validation": True
                        },
                        "routing": {
                            "smart_routing": True,
                            "fallback_handlers": True,
                            "dead_letter_queue": True
                        },
                        "persistence": {
                            "store_messages": True,
                            "retention_period": "30d",
                            "index_content": True
                        }
                    }
                }
            )
            
            # Create debug rules
            await self.run_query(
                """
                CREATE (r:DebugRule {
                    name: 'debug_integration',
                    description: 'Rules for debug integration',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "feature_flags": {
                            "log_validation": {
                                "enabled": False,
                                "description": "Log all validation attempts"
                            },
                            "log_websocket": {
                                "enabled": False,
                                "description": "Log WebSocket messages"
                            },
                            "log_storage": {
                                "enabled": False,
                                "description": "Log storage operations"
                            },
                            "strict_mode": {
                                "enabled": False,
                                "description": "Throw on any validation error"
                            }
                        },
                        "logging": {
                            "validation": {
                                "enabled": True,
                                "level": "INFO",
                                "format": "detailed"
                            },
                            "websocket": {
                                "enabled": True,
                                "level": "INFO",
                                "include_payload": True
                            },
                            "storage": {
                                "enabled": True,
                                "level": "INFO",
                                "track_performance": True
                            }
                        },
                        "monitoring": {
                            "metrics_collection": True,
                            "performance_tracking": True,
                            "error_tracking": True,
                            "agent_activity_logging": True
                        },
                        "ui_integration": {
                            "debug_panel": True,
                            "metrics_display": True,
                            "log_viewer": True,
                            "control_panel": True
                        }
                    }
                }
            )
            
            # Create message schemas
            await self.run_query(
                """
                CREATE (r:MessageSchema {
                    name: 'websocket_messages',
                    description: 'WebSocket message schemas',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "base_schema": {
                            "type": "string",
                            "timestamp": "string",
                            "client_id": "string",
                            "channel": "string|null",
                            "data": "Record<string, any>"
                        },
                        "message_types": {
                            "auth": {
                                "type": "auth",
                                "data": {
                                    "api_key": "string"
                                }
                            },
                            "chat_message": {
                                "type": "chat_message",
                                "data": {
                                    "thread_id": "string",
                                    "content": "string",
                                    "sender": "string?"
                                }
                            },
                            "task_update": {
                                "type": "task_update",
                                "data": {
                                    "task_id": "string",
                                    "status": "string?",
                                    "metadata": "Record<string, any>?"
                                }
                            },
                            "agent_status": {
                                "type": "agent_status",
                                "data": {
                                    "agent_id": "string",
                                    "status": "string",
                                    "metadata": "Record<string, any>?"
                                }
                            },
                            "graph_update": {
                                "type": "graph_update",
                                "data": {
                                    "nodes": "Array<Node>",
                                    "edges": "Array<Edge>"
                                }
                            }
                        },
                        "validation": {
                            "strict": True,
                            "coerce_types": False,
                            "additional_properties": False
                        }
                    }
                }
            )
            
            # Create validation rules
            await self.run_query(
                """
                CREATE (r:ValidationRule {
                    name: 'schema_validation',
                    description: 'Schema validation rules',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "message_validation": {
                            "required_fields": [
                                "type",
                                "timestamp",
                                "client_id",
                                "data"
                            ],
                            "field_types": {
                                "type": "string",
                                "timestamp": "ISO8601",
                                "client_id": "string",
                                "channel": "string|null",
                                "data": "object"
                            },
                            "custom_validation": {
                                "timestamp": "isValidISODate",
                                "client_id": "isValidUUID"
                            }
                        },
                        "error_handling": {
                            "invalid_format": {
                                "code": 4002,
                                "message": "Invalid message format"
                            },
                            "missing_field": {
                                "code": 4002,
                                "message": "Missing required field: {field}"
                            },
                            "invalid_type": {
                                "code": 4002,
                                "message": "Invalid type for field: {field}"
                            }
                        },
                        "validation_flow": {
                            "pre_validation": [
                                "parseJSON",
                                "checkRequiredFields"
                            ],
                            "main_validation": [
                                "validateTypes",
                                "validateCustomRules"
                            ],
                            "post_validation": [
                                "sanitizeData",
                                "logValidation"
                            ]
                        }
                    }
                }
            )
            
            # Create channel rules
            await self.run_query(
                """
                CREATE (r:ChannelRule {
                    name: 'channel_management',
                    description: 'Channel management rules',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "channels": {
                            "nova-team": {
                                "description": "Core specialized agents",
                                "allowed_types": [
                                    "task_detection",
                                    "cognitive_processing"
                                ],
                                "requires_auth": True
                            },
                            "nova-support": {
                                "description": "Supporting agents",
                                "allowed_types": [
                                    "resource_allocation",
                                    "system_health"
                                ],
                                "requires_auth": True
                            }
                        },
                        "subscription": {
                            "max_channels": 10,
                            "requires_auth": True,
                            "auto_subscribe": False,
                            "subscription_timeout": 30
                        },
                        "message_flow": {
                            "requires_subscription": True,
                            "validate_message_type": True,
                            "delivery_confirmation": True,
                            "error_handling": {
                                "not_subscribed": {
                                    "code": 4003,
                                    "message": "Not subscribed to channel: {channel}"
                                },
                                "invalid_type": {
                                    "code": 4003,
                                    "message": "Invalid message type for channel: {channel}"
                                }
                            }
                        }
                    }
                }
            )
            
            # Create API endpoints
            await self.run_query(
                """
                CREATE (r:APIEndpoint {
                    name: 'api_endpoints',
                    description: 'API endpoint configurations',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "system": {
                            "health_check": {
                                "path": "/api/status",
                                "method": "GET",
                                "description": "Health check endpoint"
                            }
                        },
                        "memory": {
                            "store": {
                                "path": "/api/memory/store",
                                "method": "POST",
                                "description": "Store content in memory system",
                                "parameters": {
                                    "domain": {
                                        "in": "query",
                                        "required": False,
                                        "description": "Domain context"
                                    }
                                }
                            },
                            "search": {
                                "path": "/api/memory/search",
                                "method": "GET",
                                "description": "Search memory with domain filtering",
                                "parameters": {
                                    "query": {
                                        "in": "query",
                                        "required": True,
                                        "description": "Search query"
                                    },
                                    "domain": {
                                        "in": "query",
                                        "required": False,
                                        "description": "Domain filter"
                                    },
                                    "memory_type": {
                                        "in": "query",
                                        "required": False,
                                        "description": "Type filter"
                                    },
                                    "limit": {
                                        "in": "query",
                                        "required": False,
                                        "description": "Result limit",
                                        "default": 10
                                    }
                                }
                            }
                        },
                        "chat": {
                            "channels": {
                                "details": {
                                    "path": "/api/channels/{channel_id}/details",
                                    "method": "GET",
                                    "description": "Get channel details",
                                    "parameters": {
                                        "channel_id": {
                                            "in": "path",
                                            "required": True,
                                            "description": "Channel identifier"
                                        }
                                    }
                                },
                                "members": {
                                    "path": "/api/channels/{channel_id}/members",
                                    "method": "GET",
                                    "description": "Get channel members",
                                    "parameters": {
                                        "channel_id": {
                                            "in": "path",
                                            "required": True,
                                            "description": "Channel identifier"
                                        }
                                    }
                                }
                            },
                            "threads": {
                                "list": {
                                    "path": "/api/threads",
                                    "method": "GET",
                                    "description": "List all threads",
                                    "parameters": {
                                        "domain": {
                                            "in": "query",
                                            "required": False,
                                            "description": "Domain filter"
                                        }
                                    }
                                },
                                "messages": {
                                    "path": "/api/threads/{thread_id}",
                                    "method": "GET",
                                    "description": "Get thread messages",
                                    "parameters": {
                                        "thread_id": {
                                            "in": "path",
                                            "required": True,
                                            "description": "Thread identifier"
                                        },
                                        "start": {
                                            "in": "query",
                                            "required": False,
                                            "description": "Starting index",
                                            "default": 0
                                        },
                                        "limit": {
                                            "in": "query",
                                            "required": False,
                                            "description": "Maximum messages",
                                            "default": 100
                                        }
                                    }
                                }
                            }
                        },
                        "agents": {
                            "list": {
                                "path": "/api/agents",
                                "method": "GET",
                                "description": "Get list of all agents"
                            },
                            "details": {
                                "path": "/api/agents/{agent_id}/details",
                                "method": "GET",
                                "description": "Get agent details",
                                "parameters": {
                                    "agent_id": {
                                        "in": "path",
                                        "required": True,
                                        "description": "Agent identifier"
                                    }
                                }
                            },
                            "metrics": {
                                "path": "/api/agents/{agent_id}/metrics",
                                "method": "GET",
                                "description": "Get agent metrics",
                                "parameters": {
                                    "agent_id": {
                                        "in": "path",
                                        "required": True,
                                        "description": "Agent identifier"
                                    }
                                }
                            }
                        }
                    }
                }
            )
            
            # Create API security rules
            await self.run_query(
                """
                CREATE (r:APISecurityRule {
                    name: 'api_security',
                    description: 'API security rules',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "authentication": {
                            "type": "apiKey",
                            "in": "header",
                            "name": "X-API-Key",
                            "description": "API key authentication"
                        },
                        "rate_limiting": {
                            "enabled": True,
                            "default_limit": 100,
                            "window": 60,
                            "by_endpoint": {
                                "/api/memory/store": {
                                    "limit": 50,
                                    "window": 60
                                },
                                "/api/memory/search": {
                                    "limit": 200,
                                    "window": 60
                                }
                            }
                        },
                        "cors": {
                            "enabled": True,
                            "allowed_origins": ["*"],
                            "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
                            "allowed_headers": ["*"],
                            "expose_headers": ["*"],
                            "max_age": 86400
                        },
                        "ssl": {
                            "enabled": True,
                            "min_version": "TLSv1.2",
                            "verify_client": False
                        }
                    }
                }
            )
            
            # Create API schemas
            await self.run_query(
                """
                CREATE (r:APISchema {
                    name: 'api_schemas',
                    description: 'API request/response schemas',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "channel": {
                            "details": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "created_at": {"type": "string", "format": "datetime"},
                                    "updated_at": {"type": "string", "format": "datetime"},
                                    "is_public": {"type": "boolean"},
                                    "workspace": {"type": "string"},
                                    "domain": {"type": "string"},
                                    "type": {"type": "string"},
                                    "metadata": {"type": "object"}
                                },
                                "required": ["id", "name", "type"]
                            },
                            "member": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "role": {"type": "string"},
                                    "status": {"type": "string"},
                                    "joined_at": {"type": "string", "format": "datetime"},
                                    "metadata": {"type": "object"}
                                },
                                "required": ["id", "name", "type", "role"]
                            }
                        },
                        "agent": {
                            "response": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "agentType": {"type": "string"},
                                    "status": {"type": "string"},
                                    "capabilities": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "workspace": {"type": "string"},
                                    "metadata": {"type": "object"},
                                    "timestamp": {"type": "string"}
                                },
                                "required": ["id", "name", "type", "status"]
                            }
                        },
                        "task": {
                            "node": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "label": {"type": "string"},
                                    "type": {"type": "string"},
                                    "status": {"type": "string"},
                                    "description": {"type": "string"},
                                    "team_id": {"type": "string"},
                                    "domain": {"type": "string"},
                                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                                    "assignee": {"type": "string"},
                                    "tags": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "dependencies": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "blocked_by": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "sub_tasks": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "string"},
                                                "description": {"type": "string"},
                                                "completed": {"type": "boolean"}
                                            },
                                            "required": ["id", "description"]
                                        }
                                    }
                                },
                                "required": ["id", "label", "type", "status"]
                            }
                        }
                    }
                }
            )
            
            # Create WebSocket states
            await self.run_query(
                """
                CREATE (r:WebSocketState {
                    name: 'websocket_states',
                    description: 'WebSocket connection states',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "states": {
                            "initial": {
                                "name": "Not Authenticated",
                                "description": "Initial connection state",
                                "can_transition_to": ["authenticated"],
                                "requires_auth": False
                            },
                            "authenticated": {
                                "name": "Authenticated",
                                "description": "Successfully authenticated connection",
                                "can_transition_to": ["not_authenticated"],
                                "requires_auth": True
                            },
                            "error": {
                                "name": "Error",
                                "description": "Connection error state",
                                "can_transition_to": ["not_authenticated"],
                                "requires_auth": False
                            },
                            "reconnecting": {
                                "name": "Reconnecting",
                                "description": "Attempting to reconnect",
                                "can_transition_to": ["not_authenticated", "authenticated"],
                                "requires_auth": False
                            }
                        },
                        "state_preservation": {
                            "channel_operations": True,
                            "agent_updates": True,
                            "message_handling": True
                        },
                        "state_reset": {
                            "after_error": True,
                            "after_cleanup": True,
                            "after_reconnection": True
                        }
                    }
                }
            )
            
            # Create WebSocket error handling rules
            await self.run_query(
                """
                CREATE (r:WebSocketErrorRule {
                    name: 'websocket_errors',
                    description: 'WebSocket error handling rules',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "close_codes": {
                            "1000": {
                                "description": "Normal closure",
                                "requires_cleanup": True,
                                "can_reconnect": True
                            },
                            "1011": {
                                "description": "Server error",
                                "requires_cleanup": True,
                                "can_reconnect": True
                            },
                            "4000": {
                                "description": "Authentication error",
                                "requires_cleanup": True,
                                "can_reconnect": False
                            },
                            "4001": {
                                "description": "Rate limit exceeded",
                                "requires_cleanup": True,
                                "can_reconnect": True
                            },
                            "4002": {
                                "description": "Invalid message format",
                                "requires_cleanup": True,
                                "can_reconnect": True
                            },
                            "4003": {
                                "description": "Protocol violation",
                                "requires_cleanup": True,
                                "can_reconnect": False
                            }
                        },
                        "error_handling": {
                            "authentication": {
                                "invalid_key": {
                                    "code": 403,
                                    "message": "Invalid API key",
                                    "close_code": 4000
                                },
                                "token_expired": {
                                    "code": 403,
                                    "message": "Token expired",
                                    "close_code": 4000
                                }
                            },
                            "server": {
                                "internal_error": {
                                    "code": 500,
                                    "message": "Internal server error",
                                    "close_code": 1011
                                }
                            }
                        },
                        "recovery": {
                            "retry_attempts": 3,
                            "retry_delay": 1000,
                            "exponential_backoff": True,
                            "max_retry_delay": 5000
                        }
                    }
                }
            )
            
            # Create WebSocket authentication rules
            await self.run_query(
                """
                CREATE (r:WebSocketAuthRule {
                    name: 'websocket_auth',
                    description: 'WebSocket authentication rules',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "authentication_flow": {
                            "initial_connection": {
                                "endpoint": "/debug/client_{client_id}",
                                "requires_auth": False,
                                "response": {
                                    "type": "connection_established",
                                    "data": {
                                        "message": "Connection established, waiting for authentication"
                                    }
                                }
                            },
                            "authentication": {
                                "message_type": "connect",
                                "required_fields": {
                                    "api_key": "string",
                                    "connection_type": "string",
                                    "domain": "string",
                                    "workspace": "string"
                                },
                                "success_response": {
                                    "type": "connection_success",
                                    "data": {
                                        "message": "Connected"
                                    }
                                },
                                "error_response": {
                                    "type": "error",
                                    "data": {
                                        "message": "Invalid API key",
                                        "error_type": "invalid_key"
                                    }
                                }
                            },
                            "post_authentication": {
                                "requires_auth": True,
                                "track_state": True,
                                "delivery_confirmation": True
                            }
                        },
                        "api_keys": {
                            "development": {
                                "permissions": ["all"],
                                "expires": None
                            },
                            "valid-test-key": {
                                "permissions": ["test"],
                                "expires": None
                            }
                        }
                    }
                }
            )
            
            self.logger.info("System endpoints initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize system endpoints: {str(e)}")
            raise
            
    async def _initialize_knowledge_graph(self):
        """Initialize knowledge graph schema and base concepts."""
        try:
            self.logger.info("Initializing knowledge graph...")
            
            # Create concept constraints
            await self.run_query(
                """
                CREATE CONSTRAINT concept_id IF NOT EXISTS
                FOR (c:Concept) REQUIRE c.id IS UNIQUE
                """
            )
            
            # Initialize task states
            states = [
                {
                    "name": "PENDING",
                    "description": "New or unstarted tasks",
                    "value": "pending"
                },
                {
                    "name": "IN_PROGRESS",
                    "description": "Tasks currently being worked on",
                    "value": "in_progress"
                },
                {
                    "name": "BLOCKED",
                    "description": "Tasks blocked by dependencies",
                    "value": "blocked"
                },
                {
                    "name": "COMPLETED",
                    "description": "Finished tasks",
                    "value": "completed"
                }
            ]
            
            for state in states:
                validation = {
                    "domain": BaseDomain.GENERAL,
                    "access_domain": BaseDomain.GENERAL,
                    "confidence": 1.0,
                    "source": "system",
                    "metadata": {
                        "enum_name": state["name"],
                        "value": state["value"]
                    }
                }
                
                await self.run_query(
                    """
                    CREATE (s:TaskState {
                        name: $name,
                        description: $description,
                        value: $value,
                        validation: $validation
                    })
                    """,
                    {
                        "name": f"TaskState_{state['value']}",
                        "description": state["description"],
                        "value": state["value"],
                        "validation": validation
                    }
                )
            
            # Initialize task templates
            templates = [
                {
                    "name": "development_task",
                    "type": "entity",
                    "description": "Software development task template",
                    "domain": BaseDomain.PROFESSIONAL,
                    "metadata": {
                        "template": True,
                        "category": "development",
                        "default_state": "pending",
                        "workspace": "professional",
                        "priority": "medium",
                        "capabilities": ["development", "coding", "testing"],
                        "validation_rules": {
                            "requires_review": True,
                            "requires_testing": True
                        }
                    }
                },
                {
                    "name": "organization_task",
                    "type": "entity",
                    "description": "Personal organization task template",
                    "domain": BaseDomain.PERSONAL,
                    "metadata": {
                        "template": True,
                        "category": "organization",
                        "default_state": "pending",
                        "workspace": "personal",
                        "priority": "medium",
                        "capabilities": ["organization", "planning", "tracking"],
                        "validation_rules": {
                            "requires_review": False,
                            "requires_testing": False
                        }
                    }
                }
            ]
            
            for template in templates:
                validation = {
                    "domain": template["domain"],
                    "access_domain": template["domain"],
                    "confidence": 1.0,
                    "source": "system",
                    "metadata": template["metadata"]
                }
                
                await self.run_query(
                    """
                    MERGE (c:Concept {name: $name})
                    SET c.type = $type,
                        c.description = $description,
                        c.validation = $validation,
                        c.created_at = datetime()
                    """,
                    {
                        "name": template["name"],
                        "type": template["type"],
                        "description": template["description"],
                        "validation": validation
                    }
                )
            
            # Initialize domains and access rules
            domains = ["tasks", "professional", "personal"]
            for domain in domains:
                # Create domain node
                await self.run_query(
                    """
                    MERGE (d:Domain {name: $name})
                    SET d.created = datetime()
                    """,
                    {"name": domain}
                )
                
                # Create access rule for domain
                await self.run_query(
                    """
                    MATCH (d:Domain {name: $name})
                    MERGE (d)-[:HAS_RULE]->(r:AccessRule {
                        type: 'domain_access',
                        created: datetime(),
                        config: $config
                    })
                    """,
                    {
                        "name": domain,
                        "config": {
                            "read": ["system", "admin"],
                            "write": ["system", "admin"],
                            "execute": ["system", "admin"],
                            "delegate": ["system"]
                        }
                    }
                )
            
            # Create concept type index
            await self.run_query(
                """
                CREATE INDEX concept_type IF NOT EXISTS
                FOR (c:Concept)
                ON (c.type)
                """
            )
            
            # Create domain index
            await self.run_query(
                """
                CREATE INDEX concept_domain IF NOT EXISTS
                FOR (c:Concept)
                ON (c.domain)
                """
            )
            
            # Create base domain concepts
            domains = [
                {
                    "name": "personal",
                    "type": "domain",
                    "description": "Personal knowledge domain"
                },
                {
                    "name": "professional",
                    "type": "domain",
                    "description": "Professional knowledge domain"
                },
                {
                    "name": "system",
                    "type": "domain",
                    "description": "System knowledge domain"
                }
            ]
            
            for domain in domains:
                await self.run_query(
                    """
                    MERGE (c:Concept {name: $name})
                    SET c.type = $type,
                        c.description = $description,
                        c.created_at = datetime()
                    """,
                    domain
                )
            
            # Create knowledge verticals
            verticals = [
                {
                    "name": "retail",
                    "type": "vertical",
                    "description": "Retail domain knowledge"
                },
                {
                    "name": "business",
                    "type": "vertical", 
                    "description": "Business domain knowledge"
                },
                {
                    "name": "psychology",
                    "type": "vertical",
                    "description": "Psychology domain knowledge"
                },
                {
                    "name": "technology",
                    "type": "vertical",
                    "description": "Technology domain knowledge"
                },
                {
                    "name": "backend",
                    "type": "vertical",
                    "description": "Backend development knowledge"
                },
                {
                    "name": "database",
                    "type": "vertical",
                    "description": "Database systems knowledge"
                },
                {
                    "name": "general",
                    "type": "vertical",
                    "description": "General domain knowledge"
                }
            ]
            
            for vertical in verticals:
                await self.run_query(
                    """
                    MERGE (c:Concept {name: $name})
                    SET c.type = $type,
                        c.description = $description,
                        c.created_at = datetime()
                    """,
                    vertical
                )
            
            # Create relationships between domains and verticals
            await self.run_query(
                """
                MATCH (d:Concept)
                WHERE d.type = 'domain'
                MATCH (v:Concept)
                WHERE v.type = 'vertical'
                MERGE (d)-[:CONTAINS]->(v)
                """
            )
            
            # Initialize task workflow rules
            await self.run_query(
                """
                CREATE (w:WorkflowRule {
                    name: 'dependency_check',
                    description: 'Check dependencies before state transitions',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "check_dependencies": True,
                        "auto_block_on_dependency": True,
                        "auto_unblock_on_dependency_complete": True,
                        "notify_on_block": True,
                        "notify_on_unblock": True
                    }
                }
            )
            
            # Create state transition rules
            await self.run_query(
                """
                CREATE (r:TransitionRule {
                    name: 'state_transition',
                    description: 'Rules for task state transitions',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "validate_transitions": True,
                        "require_approval_for_completion": True,
                        "allow_reopen": False,
                        "track_transition_history": True
                    }
                }
            )
            
            # Create orchestration rules
            await self.run_query(
                """
                CREATE (r:OrchestrationRule {
                    name: 'task_orchestration',
                    description: 'Rules for task orchestration and coordination',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "proposal": {
                            "requires_approval": True,
                            "auto_approve_threshold": 0.8,
                            "validation": {
                                "required_fields": ["title", "description"],
                                "optional_fields": ["priority", "assignee", "due_date"]
                            }
                        },
                        "approval": {
                            "roles": ["admin", "manager", "lead"],
                            "auto_approval": {
                                "enabled": True,
                                "confidence_threshold": 0.9,
                                "domain_restrictions": ["system", "security"]
                            }
                        },
                        "creation": {
                            "validation": {
                                "required_fields": ["title", "description", "type"],
                                "optional_fields": ["priority", "assignee", "tags"]
                            },
                            "defaults": {
                                "priority": "medium",
                                "status": "pending"
                            }
                        },
                        "transitions": {
                            "validation": {
                                "required_fields": ["new_state"],
                                "optional_fields": ["reason", "metadata"]
                            },
                            "allowed_transitions": {
                                "pending": ["in_progress"],
                                "in_progress": ["blocked", "completed"],
                                "blocked": ["in_progress"],
                                "completed": []
                            },
                            "requires_approval": {
                                "to_completed": True,
                                "to_blocked": True
                            }
                        }
                    }
                }
            )
            
            # Create workflow patterns
            await self.run_query(
                """
                CREATE (p:WorkflowPattern {
                    name: 'task_patterns',
                    description: 'Common task workflow patterns',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "standard": {
                            "steps": ["propose", "approve", "create", "execute", "complete"],
                            "roles": ["proposer", "approver", "assignee"],
                            "validations": ["proposal", "approval", "completion"]
                        },
                        "expedited": {
                            "steps": ["create", "execute", "complete"],
                            "roles": ["creator", "assignee"],
                            "validations": ["creation", "completion"],
                            "conditions": {
                                "priority": "high",
                                "auto_approve": True
                            }
                        },
                        "collaborative": {
                            "steps": ["propose", "discuss", "approve", "create", "execute", "review", "complete"],
                            "roles": ["proposer", "reviewer", "approver", "assignee"],
                            "validations": ["proposal", "discussion", "approval", "completion"],
                            "requirements": {
                                "min_reviewers": 2,
                                "consensus_threshold": 0.75
                            }
                        }
                    }
                }
            )
            
            # Create domain validation rules
            await self.run_query(
                """
                CREATE (r:DomainValidationRule {
                    name: 'domain_validation',
                    description: 'Rules for domain validation',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "validation": {
                            "required_fields": [
                                "domain",
                                "access_level",
                                "operation_type"
                            ],
                            "allowed_domains": [
                                "personal",
                                "professional",
                                "system"
                            ],
                            "allowed_access_levels": [
                                "read",
                                "write",
                                "execute",
                                "admin"
                            ],
                            "allowed_operations": [
                                "view",
                                "edit",
                                "delete",
                                "share"
                            ]
                        },
                        "access_control": {
                            "default_level": "read",
                            "elevation_requires_approval": True,
                            "admin_override": True
                        },
                        "history_tracking": {
                            "enabled": True,
                            "retention_days": 30,
                            "include_metadata": True
                        }
                    }
                }
            )
            
            # Create cross-domain operation rules
            await self.run_query(
                """
                CREATE (r:CrossDomainRule {
                    name: 'cross_domain',
                    description: 'Rules for cross-domain operations',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "validation": {
                            "required_fields": [
                                "source_domain",
                                "target_domain",
                                "operation_type",
                                "content_type"
                            ],
                            "allowed_operations": [
                                "read",
                                "copy",
                                "link",
                                "move"
                            ]
                        },
                        "permissions": {
                            "requires_approval": True,
                            "allowed_roles": ["admin", "manager"],
                            "auto_approve_conditions": {
                                "same_workspace": True,
                                "related_domains": True
                            }
                        },
                        "content_rules": {
                            "validate_content": True,
                            "preserve_metadata": True,
                            "track_lineage": True
                        },
                        "history": {
                            "track_operations": True,
                            "retention_period": "90d",
                            "include_metadata": True
                        }
                    }
                }
            )
            
            # Create knowledge transfer rules
            await self.run_query(
                """
                CREATE (r:KnowledgeTransferRule {
                    name: 'knowledge_transfer',
                    description: 'Rules for knowledge transfer',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "validation": {
                            "required_fields": [
                                "source_type",
                                "target_type",
                                "content_type",
                                "transfer_type"
                            ],
                            "allowed_types": [
                                "concept",
                                "task",
                                "memory",
                                "pattern"
                            ]
                        },
                        "transfer_rules": {
                            "preserve_context": True,
                            "validate_content": True,
                            "track_lineage": True,
                            "update_references": True
                        },
                        "content_validation": {
                            "check_format": True,
                            "validate_references": True,
                            "preserve_metadata": True
                        },
                        "pattern_matching": {
                            "detect_patterns": True,
                            "similarity_threshold": 0.8,
                            "context_window": "30d"
                        }
                    }
                }
            )
            
            self.logger.info("Knowledge graph initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize knowledge graph: {str(e)}")
            raise
            
    async def _initialize_neo4j_schema(self):
        """Initialize Neo4j schema for memory storage."""
        try:
            self.logger.info("Initializing Neo4j schema...")
            
            # Memory constraints and indices
            await self.run_query(
                """
                CREATE CONSTRAINT memory_id IF NOT EXISTS
                FOR (m:Memory) REQUIRE m.id IS UNIQUE
                """
            )
            await self.run_query(
                """
                CREATE INDEX memory_type IF NOT EXISTS
                FOR (m:Memory)
                ON (m.type)
                """
            )
            await self.run_query(
                """
                CREATE INDEX memory_timestamp IF NOT EXISTS
                FOR (m:Memory)
                ON (m.timestamp)
                """
            )
            
            # Agent constraints and indices
            await self.run_query(
                """
                CREATE CONSTRAINT agent_id IF NOT EXISTS
                FOR (a:Agent) REQUIRE a.id IS UNIQUE
                """
            )
            await self.run_query(
                """
                CREATE INDEX agent_name IF NOT EXISTS
                FOR (a:Agent) ON (a.name)
                """
            )
            await self.run_query(
                """
                CREATE INDEX agent_type IF NOT EXISTS
                FOR (a:Agent) ON (a.type)
                """
            )
            await self.run_query(
                """
                CREATE INDEX agent_workspace IF NOT EXISTS
                FOR (a:Agent) ON (a.workspace)
                """
            )
            await self.run_query(
                """
                CREATE INDEX agent_status IF NOT EXISTS
                FOR (a:Agent) ON (a.status)
                """
            )
            await self.run_query(
                """
                CREATE INDEX agent_timestamp IF NOT EXISTS
                FOR (a:Agent) ON (a.timestamp)
                """
            )
            await self.run_query(
                """
                CREATE INDEX agent_metadata IF NOT EXISTS
                FOR (a:Agent) ON (a.metadata)
                """
            )
            await self.run_query(
                """
                CREATE INDEX agent_capabilities IF NOT EXISTS
                FOR (a:Agent) ON (a.capabilities)
                """
            )
            
            # Optional agent indices
            await self.run_query(
                """
                CREATE INDEX agent_agent_type IF NOT EXISTS
                FOR (a:Agent) ON (a.agentType)
                """
            )
            await self.run_query(
                """
                CREATE INDEX agent_role IF NOT EXISTS
                FOR (a:Agent) ON (a.role)
                """
            )
            await self.run_query(
                """
                CREATE INDEX agent_domain IF NOT EXISTS
                FOR (a:Agent) ON (a.domain)
                """
            )
            await self.run_query(
                """
                CREATE INDEX agent_thread_id IF NOT EXISTS
                FOR (a:Agent) ON (a.threadId)
                """
            )
            
            # Task memory indices
            await self.run_query(
                """
                CREATE INDEX task_memory_type IF NOT EXISTS
                FOR (m:Memory)
                ON (m.task_type)
                """
            )
            await self.run_query(
                """
                CREATE INDEX task_memory_status IF NOT EXISTS
                FOR (m:Memory)
                ON (m.task_status)
                """
            )
            await self.run_query(
                """
                CREATE INDEX task_memory_priority IF NOT EXISTS
                FOR (m:Memory)
                ON (m.task_priority)
                """
            )
            await self.run_query(
                """
                CREATE INDEX task_memory_assignee IF NOT EXISTS
                FOR (m:Memory)
                ON (m.task_assignee)
                """
            )
            await self.run_query(
                """
                CREATE INDEX task_memory_deadline IF NOT EXISTS
                FOR (m:Memory)
                ON (m.task_deadline)
                """
            )
            
            # Task constraints
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
            
            await self.run_query(
                """
                CREATE CONSTRAINT task_group_id IF NOT EXISTS
                FOR (g:TaskGroup) REQUIRE g.id IS UNIQUE
                """
            )
            
            # Task indices
            await self.run_query(
                """
                CREATE INDEX task_status IF NOT EXISTS
                FOR (t:Task)
                ON (t.status)
                """
            )
            
            await self.run_query(
                """
                CREATE INDEX task_priority IF NOT EXISTS
                FOR (t:Task)
                ON (t.priority)
                """
            )
            
            # Task relationship indices
            await self.run_query(
                """
                CREATE INDEX task_dependency IF NOT EXISTS
                FOR ()-[r:DEPENDS_ON]->() ON (r.type)
                """
            )
            await self.run_query(
                """
                CREATE INDEX task_assignment IF NOT EXISTS
                FOR ()-[r:ASSIGNED_TO]->() ON (r.timestamp)
                """
            )
            
            # Channel constraints and indices
            await self.run_query(
                """
                CREATE CONSTRAINT channel_id IF NOT EXISTS
                FOR (c:Channel) REQUIRE c.id IS UNIQUE
                """
            )
            await self.run_query(
                """
                CREATE INDEX channel_name IF NOT EXISTS
                FOR (c:Channel) ON (c.name)
                """
            )
            await self.run_query(
                """
                CREATE INDEX channel_type IF NOT EXISTS
                FOR (c:Channel) ON (c.type)
                """
            )
            await self.run_query(
                """
                CREATE INDEX channel_workspace IF NOT EXISTS
                FOR (c:Channel) ON (c.workspace)
                """
            )
            await self.run_query(
                """
                CREATE INDEX channel_domain IF NOT EXISTS
                FOR (c:Channel) ON (c.domain)
                """
            )
            await self.run_query(
                """
                CREATE INDEX channel_metadata IF NOT EXISTS
                FOR (c:Channel) ON (c.metadata)
                """
            )
            
            # Relationship indices
            await self.run_query(
                """
                CREATE INDEX channel_member IF NOT EXISTS
                FOR ()-[r:MEMBER_OF]->() ON (r.role)
                """
            )
            await self.run_query(
                """
                CREATE INDEX channel_subscription IF NOT EXISTS
                FOR ()-[r:SUBSCRIBES_TO]->() ON (r.status)
                """
            )
            
            self.logger.info("Neo4j schema initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Neo4j schema: {str(e)}")
            raise
            
    async def _initialize_qdrant(self):
        """Initialize Qdrant collections."""
        try:
            self.logger.info("Initializing Qdrant collections...")
            
            # Ensure memories collection exists
            await self.vector_store.connect()
            
            self.logger.info("Qdrant collections initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Qdrant collections: {str(e)}")
            raise
            
    async def _setup_consolidation_rules(self):
        """Set up memory consolidation rules."""
        try:
            self.logger.info("Setting up consolidation rules...")
            
            # Create general consolidation rules
            await self.run_query(
                """
                CREATE (r:ConsolidationRule {
                    name: 'time_based',
                    description: 'Consolidate memories based on time intervals',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "short_term_threshold": "24h",  # Consolidate memories older than 24h
                        "long_term_threshold": "7d",    # Move to long-term after 7 days
                        "importance_threshold": 0.7,    # Minimum importance for long-term storage
                        "batch_size": 100              # Number of memories to process per batch
                    }
                }
            )
            
            # Create task-specific consolidation rules
            await self.run_query(
                """
                CREATE (r:ConsolidationRule {
                    name: 'task_based',
                    description: 'Consolidate task memories based on status',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "completed_task_threshold": "30d",  # Archive completed tasks after 30 days
                        "blocked_task_threshold": "7d",     # Review blocked tasks after 7 days
                        "stale_task_threshold": "14d",     # Review stale tasks after 14 days
                        "priority_thresholds": {
                            "high": "12h",    # Review high priority tasks every 12 hours
                            "medium": "24h",   # Review medium priority tasks daily
                            "low": "72h"      # Review low priority tasks every 3 days
                        },
                        "consolidation_rules": {
                            "completed": {
                                "retain_metadata": True,
                                "compress_history": True,
                                "archive_after": "90d"
                            },
                            "blocked": {
                                "retain_dependencies": True,
                                "alert_threshold": "3d"
                            },
                            "in_progress": {
                                "track_updates": True,
                                "stale_threshold": "7d"
                            }
                        }
                    }
                }
            )
            
            self.logger.info("Consolidation rules set up successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to set up consolidation rules: {str(e)}")
            raise

    async def _initialize_base_agents(self):
        """Initialize base agents."""
        try:
            self.logger.info("Initializing base agents...")
            
            # Create base agent
            await self.run_query(
                """
                CREATE (a:Agent {
                    name: 'BaseAgent',
                    type: 'base',
                    workspace: 'system',
                    domain: $domain,
                    status: 'active',
                    created_at: datetime(),
                    emotions: {
                        task_focus: 'neutral',
                        collaboration_readiness: 'active',
                        domain_confidence: 'high'
                    },
                    capabilities: [
                        'emotional_processing',
                        'goal_management',
                        'world_interaction'
                    ]
                })
                """,
                {"domain": BaseDomain.GENERAL}
            )
            
            self.logger.info("Base agents initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize base agents: {str(e)}")
            raise
            
    async def _initialize_core_agents(self):
        """Initialize core cognitive agents."""
        try:
            self.logger.info("Initializing core cognitive agents...")
            
            # Create meta agent
            await self.run_query(
                """
                CREATE (a:Agent {
                    name: 'MetaAgent',
                    type: 'meta',
                    workspace: 'system',
                    domain: $domain,
                    status: 'active',
                    created_at: datetime(),
                    capabilities: [
                        'team_coordination',
                        'task_distribution',
                        'cognitive_oversight'
                    ]
                })
                """,
                {"domain": BaseDomain.GENERAL}
            )
            
            # Create core cognitive agents
            core_agents = [
                {
                    "name": "BeliefAgent",
                    "type": "belief"
                },
                {
                    "name": "DesireAgent",
                    "type": "desire"
                },
                {
                    "name": "EmotionAgent",
                    "type": "emotion"
                }
            ]
            
            for agent in core_agents:
                await self.run_query(
                    """
                    CREATE (a:Agent {
                        name: $name,
                        type: $type,
                        workspace: 'system',
                        domain: $domain,
                        status: 'active',
                        created_at: datetime()
                    })
                    """,
                    {
                        "name": agent["name"],
                        "type": agent["type"],
                        "domain": BaseDomain.GENERAL
                    }
                )
                
                # Set up relationship with meta agent
                await self.run_query(
                    """
                    MATCH (m:Agent {name: 'MetaAgent'})
                    MATCH (a:Agent {name: $name})
                    MERGE (m)-[:COORDINATES]->(a)
                    """,
                    {"name": agent["name"]}
                )
            
            self.logger.info("Core cognitive agents initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize core cognitive agents: {str(e)}")
            raise

async def main():
    """Main entry point."""
    initializer = MemoryInitializer()
    try:
        await initializer.initialize()
        
        logger.info("\nSetup complete! You can now:")
        logger.info("1. Access Neo4j browser at http://localhost:7474")
        logger.info("2. Connect using:")
        logger.info("   - URL: bolt://localhost:7687")
        logger.info("   - Username: neo4j")
        logger.info("   - Password: password")
        
    except Exception as e:
        logger.error(f"Memory initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
