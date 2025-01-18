"""WebSocket server for real-time updates."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json
import asyncio
import logging
import traceback
from qdrant_client.http import models
from nia.core.types.memory_types import Memory, MemoryType, EpisodicMemory
from .celery_app import celery_app, store_chat_message, store_task_update, store_agent_status, store_graph_update
from .dependencies import get_memory_system, get_agent_store

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class ConnectionManager:
    """Manage WebSocket connections and channels."""
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {
            "chat": {},      # Chat/channel connections
            "tasks": {},     # Task board connections
            "agents": {},    # Agent status connections
            "graph": {}      # Knowledge graph connections
        }
        self.channel_subscriptions: Dict[str, Dict[str, set[str]]] = {
            "nova-team": {},      # NovaTeam channel subscriptions
            "nova-support": {}    # NovaSupport channel subscriptions
        }
        
    async def connect(self, websocket: WebSocket, client_id: str, connection_type: str):
        """Connect a client to a specific type of updates."""
        try:
            if connection_type not in self.active_connections:
                logger.error(f"Invalid connection type: {connection_type}")
                raise ValueError(f"Invalid connection type: {connection_type}")
                
            # Check if client already connected
            if client_id in self.active_connections[connection_type]:
                logger.warning(f"Client {client_id} already connected to {connection_type}, closing old connection")
                try:
                    old_websocket = self.active_connections[connection_type][client_id]
                    await old_websocket.close(code=1012, reason="Reconnecting")
                except Exception as e:
                    logger.error(f"Error closing old connection for client {client_id}: {str(e)}")
                
            # Store connection
            logger.debug(f"Storing connection for client {client_id} in {connection_type}")
            self.active_connections[connection_type][client_id] = websocket
            
            # Send initial connection success message
            message = {
                "type": "connection_success",
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "channel": None,
                "data": {
                    "connection_type": connection_type
                }
            }
            try:
                await websocket.send_json(message)
                logger.debug(f"Sent connection success message to client {client_id}")
            except Exception as e:
                logger.error(f"Error sending connection success message to client {client_id}: {str(e)}")
                raise RuntimeError(f"Failed to send connection success message: {str(e)}") from e
                
        except Exception as e:
            logger.error(f"Error connecting client {client_id}: {str(e)}")
            logger.error(traceback.format_exc())
            try:
                await websocket.close(code=1011, reason=str(e))
            except Exception as close_error:
                logger.error(f"Error closing websocket: {str(close_error)}")
                logger.error(traceback.format_exc())
            # Clean up connection if stored
            if connection_type in self.active_connections and client_id in self.active_connections[connection_type]:
                self.active_connections[connection_type].pop(client_id, None)
            raise
            
    async def disconnect(self, client_id: str, connection_type: str):
        """Disconnect a client."""
        try:
            if connection_type not in self.active_connections:
                logger.warning(f"Invalid connection type for disconnect: {connection_type}")
                return
                
            if client_id not in self.active_connections[connection_type]:
                logger.debug(f"Client {client_id} not found in {connection_type} connections")
                return
                
            logger.info(f"Disconnecting client {client_id} from {connection_type}")
            
            # Remove from active connections first
            self.active_connections[connection_type].pop(client_id, None)
            logger.debug(f"Removed client {client_id} from {connection_type} connections")
            
        except Exception as e:
            logger.error(f"Error disconnecting client {client_id}: {str(e)}")
            logger.error(traceback.format_exc())
            
    async def broadcast(self, message: Dict[str, Any], connection_type: str, channel: Optional[str] = None):
        """Broadcast message to all connections of a specific type or channel."""
        if connection_type not in self.active_connections:
            logger.warning(f"Invalid connection type for broadcast: {connection_type}")
            return
            
        try:
            # Add timestamp to message
            message["timestamp"] = datetime.now().isoformat()
            
            # Get target clients based on channel
            if channel and channel in self.channel_subscriptions:
                target_clients = self.channel_subscriptions[channel].keys()
                logger.debug(f"Broadcasting to {len(target_clients)} clients in channel {channel}")
            else:
                target_clients = self.active_connections[connection_type].keys()
                logger.debug(f"Broadcasting to {len(target_clients)} {connection_type} connections")
            
            if not target_clients:
                logger.debug(f"No target clients for broadcast")
                return
            
            # Track failed connections for cleanup
            failed_clients = []
            
            # Broadcast to target clients
            for client_id in target_clients:
                if client_id not in self.active_connections[connection_type]:
                    continue
                    
                connection = self.active_connections[connection_type][client_id]
                try:
                    await connection.send_json(message)
                    logger.debug(f"Successfully sent message to client {client_id}")
                except Exception as e:
                    logger.error(f"Error broadcasting message to client {client_id}: {str(e)}")
                    logger.error(traceback.format_exc())
                    failed_clients.append(client_id)
                    try:
                        await connection.close(code=1011, reason="Failed to send message")
                    except Exception as close_error:
                        logger.error(f"Error closing failed connection for client {client_id}: {str(close_error)}")
            
            # Clean up failed connections
            for client_id in failed_clients:
                logger.info(f"Removing failed connection for client {client_id}")
                self.active_connections[connection_type].pop(client_id, None)
                # Remove from channel subscriptions
                if channel:
                    self.channel_subscriptions[channel].pop(client_id, None)
                
        except Exception as e:
            logger.error(f"Error preparing broadcast message: {str(e)}")
            logger.error(traceback.format_exc())

    async def join_channel(self, client_id: str, channel: str) -> bool:
        """Subscribe a client to a channel."""
        try:
            if channel not in self.channel_subscriptions:
                logger.error(f"Invalid channel: {channel}")
                return False
                
            self.channel_subscriptions[channel][client_id] = set()
            logger.debug(f"Client {client_id} joined channel {channel}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining channel: {str(e)}")
            logger.error(traceback.format_exc())
            return False
            
    async def leave_channel(self, client_id: str, channel: str) -> bool:
        """Unsubscribe a client from a channel."""
        try:
            if channel not in self.channel_subscriptions:
                logger.error(f"Invalid channel: {channel}")
                return False
                
            if client_id in self.channel_subscriptions[channel]:
                self.channel_subscriptions[channel].pop(client_id)
                logger.debug(f"Client {client_id} left channel {channel}")
            return True
            
        except Exception as e:
            logger.error(f"Error leaving channel: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    async def handle_ping(self, websocket: WebSocket, client_id: str):
        """Handle ping message from client."""
        try:
            # Send pong response
            pong_message = {
                "type": "pong",
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "channel": None,
                "data": {}
            }
            await websocket.send_json(pong_message)
            logger.debug(f"Sent pong message to client {client_id}")
        except Exception as e:
            logger.error(f"Error sending pong message to client {client_id}: {str(e)}")
            logger.error(traceback.format_exc())

class WebSocketServer:
    """WebSocket server for real-time updates."""
    def __init__(self, memory_system_provider: Callable[[], Any]):
        """Initialize a new WebSocket server instance.
        
        Args:
            memory_system_provider: Memory system provider function
        """
        self.manager = ConnectionManager()
        self.memory_system_provider = memory_system_provider
        self._initialized = False
        self._init_lock = asyncio.Lock()
        self._init_task = None
        self._memory_update_task = None

    @classmethod
    async def create(cls, memory_system_provider: Callable[[], Any]) -> 'WebSocketServer':
        """Create and initialize a new WebSocket server instance.
        
        Args:
            memory_system_provider: Memory system provider function
            
        Returns:
            Initialized WebSocketServer instance
        """
        instance = cls(memory_system_provider)
        await instance.initialize()
        return instance

    async def initialize(self):
        """Initialize the WebSocket server asynchronously."""
        try:
            if self._initialized:
                logger.debug("WebSocket server already initialized")
                return

            async with self._init_lock:
                if self._initialized:  # Double-check inside lock
                    logger.debug("WebSocket server already initialized (double-check)")
                    return

                logger.info("Starting WebSocket server initialization...")
                
                # Get memory system
                logger.info("Getting memory system from provider...")
                try:
                    memory_system = await self.memory_system_provider()
                    logger.debug("Successfully got memory system")
                except Exception as e:
                    logger.error(f"Failed to get memory system: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise RuntimeError("Failed to get memory system") from e
                
                # Initialize memory system if needed
                if hasattr(memory_system, 'initialize'):
                    try:
                        logger.debug("Initializing memory system...")
                        await memory_system.initialize()
                        logger.debug("Memory system initialized successfully")
                    except Exception as e:
                        logger.error(f"Failed to initialize memory system: {str(e)}")
                        logger.error(traceback.format_exc())
                        raise RuntimeError("Failed to initialize memory system") from e
                
                self._initialized = True
                logger.info("WebSocket server initialization complete")
        except Exception as e:
            logger.error(f"Error during WebSocket server initialization: {str(e)}")
            logger.error(traceback.format_exc())
            self._initialized = False  # Reset initialization flag on error
            raise RuntimeError("WebSocket server initialization failed") from e

    async def ensure_initialized(self):
        """Ensure the WebSocket server is initialized."""
        try:
            if not self._initialized:
                logger.debug("WebSocket server not initialized, initializing...")
                if not self._init_task:
                    self._init_task = asyncio.create_task(self.initialize())
                try:
                    await self._init_task
                    logger.debug("WebSocket server initialization task completed")
                except Exception as e:
                    logger.error(f"WebSocket server initialization task failed: {str(e)}")
                    logger.error(traceback.format_exc())
                    self._init_task = None  # Clear failed task
                    raise
            else:
                logger.debug("WebSocket server already initialized")
        except Exception as e:
            logger.error(f"Error ensuring WebSocket server initialization: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError("Failed to ensure WebSocket server initialization") from e

    async def broadcast_memory_updates(self):
        """Start background task for broadcasting memory updates."""
        try:
            if self._memory_update_task is not None:
                logger.warning("Memory update task already running")
                return

            async def memory_update_loop():
                logger.info("Starting memory update loop")
                try:
                    while True:
                        try:
                            # Get memory updates from both vector and graph stores
                            memory_system = await self.memory_system_provider()
                            vector_updates = await memory_system.vector_store.get_updates()
                            graph_updates = await memory_system.graph_store.get_updates()

                            # Broadcast vector store updates
                            if vector_updates:
                                await self.manager.broadcast(
                                    {
                                        "type": "memory_update",
                                        "timestamp": datetime.now().isoformat(),
                                        "client_id": None,
                                        "channel": None,
                                        "data": {
                                            "store": "vector",
                                            "updates": vector_updates
                                        }
                                    },
                                    "graph"
                                )

                            # Broadcast graph store updates
                            if graph_updates:
                                await self.manager.broadcast(
                                    {
                                        "type": "memory_update",
                                        "timestamp": datetime.now().isoformat(),
                                        "client_id": None,
                                        "channel": None,
                                        "data": {
                                            "store": "graph",
                                            "updates": graph_updates
                                        }
                                    },
                                    "graph"
                                )

                            # Wait before next update check
                            await asyncio.sleep(1.0)  # 1 second interval

                        except Exception as e:
                            logger.error(f"Error in memory update loop: {str(e)}")
                            logger.error(traceback.format_exc())
                            await asyncio.sleep(5.0)  # Wait longer on error

                except asyncio.CancelledError:
                    logger.info("Memory update loop cancelled")
                except Exception as e:
                    logger.error(f"Memory update loop terminated with error: {str(e)}")
                    logger.error(traceback.format_exc())

            self._memory_update_task = asyncio.create_task(memory_update_loop())
            logger.info("Memory update task started")

        except Exception as e:
            logger.error(f"Error starting memory updates: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def handle_chat_connection(self, websocket: WebSocket, client_id: str):
        """Handle chat/channel WebSocket connections."""
        await self.ensure_initialized()
        await self.manager.connect(websocket, client_id, "chat")
        try:
            while True:
                data = await websocket.receive_json()
                logger.debug(f"Received chat message from {client_id}: {data}")
                
                try:
                    if data.get("type") == "ping":
                        await self.manager.handle_ping(websocket, client_id)
                        
                    elif data.get("type") == "subscribe":
                        channel = data.get("data", {}).get("channel")
                        if not channel or channel not in ["nova-team", "nova-support"]:
                            raise ValueError(f"Invalid channel: {channel}")
                            
                        # Join channel
                        success = await self.manager.join_channel(client_id, channel)
                        if success:
                            # Send subscription success
                            await websocket.send_json({
                                "type": "subscription_success",
                                "timestamp": datetime.now().isoformat(),
                                "client_id": client_id,
                                "channel": None,
                                "data": {
                                    "channel": channel
                                }
                            })
                        else:
                            raise RuntimeError(f"Failed to join channel {channel}")
                            
                    elif data.get("type") == "unsubscribe":
                        channel = data.get("data", {}).get("channel")
                        if not channel or channel not in ["nova-team", "nova-support"]:
                            raise ValueError(f"Invalid channel: {channel}")
                            
                        # Leave channel
                        success = await self.manager.leave_channel(client_id, channel)
                        if success:
                            # Send unsubscription success
                            await websocket.send_json({
                                "type": "unsubscription_success",
                                "timestamp": datetime.now().isoformat(),
                                "client_id": client_id,
                                "channel": None,
                                "data": {
                                    "channel": channel
                                }
                            })
                        else:
                            raise RuntimeError(f"Failed to leave channel {channel}")
                            
                    elif data.get("type") == "chat_message":
                        # Validate message format
                        if "data" not in data or "content" not in data["data"]:
                            raise ValueError("Invalid message format")
                            
                        # Get channel from data object
                        channel = data.get("data", {}).get("channel")
                        if channel:
                            if channel not in ["nova-team", "nova-support"]:
                                raise ValueError(f"Invalid channel: {channel}")
                                
                            # Validate message type for channels
                            if channel == "nova-team":
                                if data["data"].get("message_type") not in ["task_detection", "cognitive_processing"]:
                                    raise ValueError("Invalid message type for nova-team channel")
                            elif channel == "nova-support":
                                if data["data"].get("message_type") not in ["resource_allocation", "system_health"]:
                                    raise ValueError("Invalid message type for nova-support channel")
                        
                        # Store message using Celery task
                        store_chat_message.delay(data)
                        
                        # Broadcast to appropriate clients
                        if channel:
                            await self.manager.broadcast(
                                {
                                    "type": "message",
                                    "timestamp": datetime.now().isoformat(),
                                    "client_id": client_id,
                                    "channel": None,
                                    "data": data["data"]
                                },
                                "chat",
                                channel
                            )
                        else:
                            await self.manager.broadcast(
                                {
                                    "type": "message",
                                    "timestamp": datetime.now().isoformat(),
                                    "client_id": client_id,
                                    "channel": None,
                                    "data": data["data"]
                                },
                                "chat"
                            )
                            
                        # Send delivery confirmation
                        await websocket.send_json({
                            "type": "message_delivered",
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id,
                            "channel": None,
                            "data": {
                                "message": "Chat message received and processed",
                                "original_type": "chat_message",
                                "status": "success"
                            }
                        })
                except Exception as e:
                    logger.error(f"Error processing chat message: {str(e)}")
                    logger.error(traceback.format_exc())
                    error_message = {
                        "type": "error",
                        "timestamp": datetime.now().isoformat(),
                        "client_id": client_id,
                        "channel": None,
                        "data": {
                            "error": str(e)
                        }
                    }
                    await websocket.send_json(error_message)
        except WebSocketDisconnect:
            await self.manager.disconnect(client_id, "chat")
            logger.info(f"Client {client_id} disconnected from chat")
            
    async def handle_task_connection(self, websocket: WebSocket, client_id: str):
        """Handle task board WebSocket connections."""
        await self.ensure_initialized()
        await self.manager.connect(websocket, client_id, "tasks")
        try:
            while True:
                data = await websocket.receive_json()
                logger.debug(f"Received task update from {client_id}: {data}")
                
                try:
                    if data.get("type") == "ping":
                        await self.manager.handle_ping(websocket, client_id)
                    else:
                        # Store task update using Celery task
                        store_task_update.delay(data)
                        
                        # Broadcast to other clients
                        await self.manager.broadcast(
                            {
                                "type": "task_update",
                                "timestamp": datetime.now().isoformat(),
                                "client_id": client_id,
                                "channel": None,
                                "data": data["data"]
                            },
                            "tasks"
                        )
                except Exception as e:
                    logger.error(f"Error processing task update: {str(e)}")
                    logger.error(traceback.format_exc())
                    error_message = {
                        "type": "error",
                        "timestamp": datetime.now().isoformat(),
                        "client_id": client_id,
                        "channel": None,
                        "data": {
                            "error": str(e)
                        }
                    }
                    await websocket.send_json(error_message)
        except WebSocketDisconnect:
            await self.manager.disconnect(client_id, "tasks")
            logger.info(f"Client {client_id} disconnected from tasks")
            
    async def handle_agent_connection(self, websocket: WebSocket, client_id: str):
        """Handle agent status WebSocket connections."""
        await self.ensure_initialized()
        await self.manager.connect(websocket, client_id, "agents")
        
        try:
            # Get initial list of agents
            agent_store = await get_agent_store()
            agents = await agent_store.get_all_agents()
            
            # Format agents according to schema
            formatted_agents = []
            for agent in agents:
                formatted_agent = {
                    "id": agent["id"],
                    "name": agent["name"],
                    "type": agent.get("type", "agent"),
                    "status": agent.get("status", "active"),
                    "domain": agent.get("domain", "general"),
                    "workspace": agent.get("workspace", "personal"),
                }
                if agent.get("metadata"):
                    formatted_agent["metadata"] = agent["metadata"]
                formatted_agents.append(formatted_agent)
            
            # Send initial agent team message
            agent_team_message = {
                "type": "agent_team_created",
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "channel": None,
                "data": {
                    "agents": formatted_agents
                }
            }
            await websocket.send_json(agent_team_message)
            
            # Handle incoming messages
            while True:
                data = await websocket.receive_json()
                logger.debug(f"Received agent status from {client_id}: {data}")
                
                try:
                    if data.get("type") == "ping":
                        await self.manager.handle_ping(websocket, client_id)
                    else:
                        # Store agent status using Celery task
                        store_agent_status.delay(data)
                        
                        # Broadcast to other clients
                        await self.manager.broadcast(
                            {
                                "type": "agent_status",
                                "timestamp": datetime.now().isoformat(),
                                "client_id": client_id,
                                "channel": None,
                                "data": data["data"]
                            },
                            "agents"
                        )
                except Exception as e:
                    logger.error(f"Error processing agent status: {str(e)}")
                    logger.error(traceback.format_exc())
                    error_message = {
                        "type": "error",
                        "timestamp": datetime.now().isoformat(),
                        "client_id": client_id,
                        "channel": None,
                        "data": {
                            "error": str(e)
                        }
                    }
                    await websocket.send_json(error_message)
        except WebSocketDisconnect:
            await self.manager.disconnect(client_id, "agents")
            logger.info(f"Client {client_id} disconnected from agents")
        except Exception as e:
            logger.error(f"Error in agent connection: {str(e)}")
            logger.error(traceback.format_exc())
            error_message = {
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "channel": None,
                "data": {
                    "error": str(e)
                }
            }
            await websocket.send_json(error_message)
            # Ensure we still disconnect on error
            await self.manager.disconnect(client_id, "agents")
            
    async def handle_graph_connection(self, websocket: WebSocket, client_id: str):
        """Handle knowledge graph WebSocket connections."""
        await self.ensure_initialized()
        await self.manager.connect(websocket, client_id, "graph")
        try:
            while True:
                data = await websocket.receive_json()
                logger.debug(f"Received graph update from {client_id}: {data}")
                
                try:
                    if data.get("type") == "ping":
                        await self.manager.handle_ping(websocket, client_id)
                    else:
                        # Store graph update using Celery task
                        store_graph_update.delay(data)
                        
                        # Broadcast to other clients
                        await self.manager.broadcast(
                            {
                                "type": "graph_update",
                                "timestamp": datetime.now().isoformat(),
                                "client_id": client_id,
                                "channel": None,
                                "data": data["data"]
                            },
                            "graph"
                        )
                except Exception as e:
                    logger.error(f"Error processing graph update: {str(e)}")
                    logger.error(traceback.format_exc())
                    error_message = {
                        "type": "error",
                        "timestamp": datetime.now().isoformat(),
                        "client_id": client_id,
                        "channel": None,
                        "data": {
                            "error": str(e)
                        }
                    }
                    await websocket.send_json(error_message)
        except WebSocketDisconnect:
            await self.manager.disconnect(client_id, "graph")
            logger.info(f"Client {client_id} disconnected from graph")
