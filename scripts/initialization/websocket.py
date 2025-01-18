#!/usr/bin/env python3
"""Initialize WebSocket system including endpoints and authentication."""

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

class WebSocketInitializer(Neo4jBaseStore):
    """Initialize WebSocket system components."""
    
    def __init__(self):
        """Initialize WebSocket system."""
        super().__init__(uri="bolt://localhost:7687", user="neo4j", password="password")
        self.logger = logging.getLogger("websocket_init")
        
    async def initialize(self):
        """Initialize all WebSocket components."""
        try:
            # Connect to Neo4j
            await self.connect()
            
            # 1. Initialize WebSocket endpoints
            await self._initialize_endpoints()
            
            # 2. Set up authentication
            await self._setup_authentication()
            
            # 3. Initialize channel operations
            await self._initialize_channels()
            
            self.logger.info("WebSocket system initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebSocket system: {str(e)}")
            raise
            
    async def _initialize_endpoints(self):
        """Initialize WebSocket endpoints."""
        try:
            self.logger.info("Initializing WebSocket endpoints...")
            
            # Create WebSocket endpoints with channel support
            endpoints = [
                {
                    "name": "debug",
                    "path": "/debug/client_{client_id}",
                    "description": "Debug endpoint for testing",
                    "tags": ["Real-time Updates"],
                    "config": {
                        "requires_auth": True,
                        "message_confirmation": True,
                        "error_handling": True,
                        "reconnection": True,
                        "operations": {
                            "chat": "/api/threads/api/threads/{thread_id}/message",
                            "task_update": "/api/tasks/api/tasks/{task_id}/transition",
                            "agent_status": "/api/agents/api/agents/{agent_id}/metrics",
                            "channel": {
                                "details": "/api/channels/api/channels/{channel_id}/details",
                                "members": "/api/channels/api/channels/{channel_id}/members",
                                "settings": "/api/channels/api/channels/{channel_id}/settings",
                                "pinned": "/api/channels/api/channels/{channel_id}/pinned"
                            }
                        },
                        "channels": {
                            "nova_hq": {
                                "type": "system",
                                "name": "NOVA HQ",
                                "description": "Core agent interactions",
                                "is_public": true
                            },
                            "nova_support": {
                                "type": "system",
                                "name": "NOVA Support",
                                "description": "Support agent interactions",
                                "is_public": true
                            }
                        }
                    }
                },
                {
                    "name": "client",
                    "path": "/client_{client_id}",
                    "description": "Production client endpoint",
                    "tags": ["Real-time Updates"],
                    "config": {
                        "requires_auth": True,
                        "message_confirmation": True,
                        "error_handling": True,
                        "reconnection": True,
                        "operations": {
                            "chat": "/api/threads/api/threads/{thread_id}/message",
                            "task_update": "/api/tasks/api/tasks/{task_id}/transition",
                            "agent_status": "/api/agents/api/agents/{agent_id}/metrics",
                            "channel": {
                                "details": "/api/channels/api/channels/{channel_id}/details",
                                "members": "/api/channels/api/channels/{channel_id}/members",
                                "settings": "/api/channels/api/channels/{channel_id}/settings",
                                "pinned": "/api/channels/api/channels/{channel_id}/pinned"
                            }
                        },
                        "channels": {
                            "nova_hq": {
                                "type": "system",
                                "name": "NOVA HQ",
                                "description": "Core agent interactions",
                                "is_public": true
                            },
                            "nova_support": {
                                "type": "system",
                                "name": "NOVA Support",
                                "description": "Support agent interactions",
                                "is_public": true
                            }
                        }
                    }
                }
            ]
            
            for endpoint in endpoints:
                await self.run_query(
                    """
                    CREATE (e:WebSocketEndpoint {
                        name: $name,
                        path: $path,
                        description: $description,
                        tags: $tags,
                        config: $config,
                        created_at: datetime()
                    })
                    """,
                    endpoint
                )
            
            self.logger.info("WebSocket endpoints initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebSocket endpoints: {str(e)}")
            raise
            
    async def _setup_authentication(self):
        """Set up WebSocket authentication."""
        try:
            self.logger.info("Setting up WebSocket authentication...")
            
            # Create authentication rules matching FastAPI security
            auth_config = {
                "name": "ws_auth",
                "description": "WebSocket authentication rules",
                "config": {
                    "api_keys": {
                        "development": {
                            "permissions": ["all"],
                            "expires": None,
                            "header": "X-API-Key"  # Match FastAPI security scheme
                        },
                        "valid-test-key": {
                            "permissions": ["test"],
                            "expires": None,
                            "header": "X-API-Key"
                        }
                    },
                    "close_codes": {
                        "normal": 1000,
                        "server_error": 1011,
                        "auth_error": 4000,
                        "rate_limit": 4001,
                        "invalid_format": 4002,
                        "protocol_violation": 4003
                    },
                    "validation": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "data": {"type": "object"}
                            },
                            "required": ["type", "data"]
                        }
                    }
                }
            }
            
            await self.run_query(
                """
                CREATE (r:AuthRule {
                    name: $name,
                    description: $description,
                    config: $config,
                    created_at: datetime()
                })
                """,
                auth_config
            )
            
            # Create error handling rules
            await self.run_query(
                """
                CREATE (r:ErrorRule {
                    name: 'ws_errors',
                    description: 'WebSocket error handling rules',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "auth_errors": {
                            "invalid_key": {
                                "message": "Invalid API key",
                                "code": 403,
                                "close_code": 4000
                            },
                            "token_expired": {
                                "message": "Token expired",
                                "code": 403,
                                "close_code": 4000
                            }
                        },
                        "server_errors": {
                            "internal_error": {
                                "message": "Internal server error",
                                "code": 500,
                                "close_code": 1011
                            }
                        }
                    }
                }
            )
            
            self.logger.info("WebSocket authentication set up successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to set up WebSocket authentication: {str(e)}")
            raise
            
    async def _initialize_channels(self):
        """Initialize WebSocket channel operations."""
        try:
            self.logger.info("Initializing WebSocket channels...")
            
            # Create enhanced channel rules matching FastAPI endpoints
            channel_config = {
                "name": "ws_channels",
                "description": "WebSocket channel operation rules",
                "config": {
                    "operations": {
                        "join": {
                            "requires_auth": True,
                            "confirm_delivery": True,
                            "error_handling": True,
                            "endpoint": "/api/channels/api/channels/{channel_id}/members",
                            "validation": {
                                "permissions": ["join_channel"],
                                "rate_limit": {"max": 10, "window": 60}
                            }
                        },
                        "leave": {
                            "requires_auth": True,
                            "confirm_delivery": True,
                            "error_handling": True,
                            "endpoint": "/api/channels/api/channels/{channel_id}/members",
                            "validation": {
                                "permissions": ["leave_channel"],
                                "rate_limit": {"max": 10, "window": 60}
                            }
                        },
                        "message": {
                            "requires_auth": True,
                            "confirm_delivery": True,
                            "error_handling": True,
                            "endpoint": "/api/threads/api/threads/{thread_id}/message",
                            "validation": {
                                "permissions": ["send_message"],
                                "rate_limit": {"max": 60, "window": 60}
                            }
                        },
                        "settings": {
                            "requires_auth": True,
                            "confirm_delivery": True,
                            "error_handling": True,
                            "endpoint": "/api/channels/api/channels/{channel_id}/settings",
                            "validation": {
                                "permissions": ["manage_settings"],
                                "rate_limit": {"max": 10, "window": 60}
                            }
                        },
                        "pin": {
                            "requires_auth": True,
                            "confirm_delivery": True,
                            "error_handling": True,
                            "endpoint": "/api/channels/api/channels/{channel_id}/pinned",
                            "validation": {
                                "permissions": ["pin_message"],
                                "rate_limit": {"max": 10, "window": 60}
                            }
                        }
                    },
                    "timeouts": {
                        "join": 5000,
                        "leave": 5000,
                        "message": 10000,
                        "settings": 5000,
                        "pin": 5000
                    },
                    "retries": {
                        "max_attempts": 3,
                        "backoff_factor": 1.5
                    },
                    "validation": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "channel_id": {"type": "string"},
                                "operation": {"type": "string", "enum": ["join", "leave", "message", "settings", "pin"]},
                                "data": {"type": "object"},
                                "workspace": {"type": "string", "enum": ["personal", "professional"]},
                                "domain": {"type": "string"}
                            },
                            "required": ["channel_id", "operation"]
                        }
                    },
                    "channel_types": {
                        "system": {
                            "description": "System channels like NOVA HQ",
                            "permissions": ["view", "send_message"],
                            "features": ["pinned_messages", "agent_status"]
                        },
                        "team": {
                            "description": "Agent team channels",
                            "permissions": ["view", "send_message", "pin_message"],
                            "features": ["pinned_messages", "agent_status", "task_updates"]
                        },
                        "direct": {
                            "description": "Direct message channels",
                            "permissions": ["view", "send_message"],
                            "features": ["agent_status"]
                        }
                    }
                }
            }
            
            await self.run_query(
                """
                CREATE (r:ChannelRule {
                    name: $name,
                    description: $description,
                    config: $config,
                    created_at: datetime()
                })
                """,
                channel_config
            )
            
            self.logger.info("WebSocket channels initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebSocket channels: {str(e)}")
            raise

async def main():
    """Main entry point."""
    initializer = WebSocketInitializer()
    try:
        await initializer.initialize()
    except Exception as e:
        logger.error(f"WebSocket initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
