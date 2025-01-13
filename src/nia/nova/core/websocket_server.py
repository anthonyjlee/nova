"""WebSocket server for real-time updates."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio
import logging
import traceback
from qdrant_client.http import models
from nia.core.types.memory_types import Memory, MemoryType, EpisodicMemory
from .celery_app import celery_app
from .dependencies import get_memory_system, get_agent_store

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class ConnectionManager:
    """Manage WebSocket connections."""
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {
            "chat": {},      # Chat/channel connections
            "tasks": {},     # Task board connections
            "agents": {},    # Agent status connections
            "graph": {}      # Knowledge graph connections
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
                "connection_type": connection_type,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
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
            
    async def broadcast(self, message: Dict[str, Any], connection_type: str):
        """Broadcast message to all connections of a specific type."""
        if connection_type not in self.active_connections:
            logger.warning(f"Invalid connection type for broadcast: {connection_type}")
            return
            
        try:
            # Add timestamp to message
            message["timestamp"] = datetime.now().isoformat()
            
            # Get active connections
            connections = list(self.active_connections[connection_type].items())
            if not connections:
                logger.debug(f"No active connections for {connection_type}")
                return
                
            logger.debug(f"Broadcasting to {len(connections)} {connection_type} connections")
            
            # Track failed connections for cleanup
            failed_clients = []
            
            # Broadcast to all connected clients
            for client_id, connection in connections:
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
                
        except Exception as e:
            logger.error(f"Error preparing broadcast message: {str(e)}")
            logger.error(traceback.format_exc())

class WebSocketServer:
    """WebSocket server for real-time updates."""
    def __init__(self, memory_system_provider: Any):
        """Initialize a new WebSocket server instance.
        
        Args:
            memory_system_provider: Memory system provider function or instance
        """
        self.manager = ConnectionManager()
        self.memory_system_provider = memory_system_provider
        self.memory_system = None
        self._initialized = False
        self._init_lock = asyncio.Lock()
        self._init_task = None

    @classmethod
    async def create(cls, memory_system_provider: Any) -> 'WebSocketServer':
        """Create and initialize a new WebSocket server instance.
        
        Args:
            memory_system_provider: Memory system provider function or instance
            
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
                    self.memory_system = self.memory_system_provider
                    memory_system = await self.memory_system()
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
                        pong_message = {
                            "type": "pong",
                            "timestamp": data.get("timestamp")
                        }
                        await websocket.send_json(pong_message)
                    else:
                        # Store message using Celery task
                        store_chat_message.delay(data)
                        
                        # Broadcast to other clients
                        await self.manager.broadcast(
                            {"type": "message", "data": data},
                            "chat"
                        )
                except Exception as e:
                    logger.error(f"Error processing chat message: {str(e)}")
                    logger.error(traceback.format_exc())
                    error_message = {
                        "type": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
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
                    # Store task update using Celery task
                    store_task_update.delay(data)
                    
                    # Broadcast to other clients
                    await self.manager.broadcast(
                        {"type": "task_update", "data": data},
                        "tasks"
                    )
                except Exception as e:
                    logger.error(f"Error processing task update: {str(e)}")
                    logger.error(traceback.format_exc())
                    error_message = {
                        "type": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
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
            
            # Send initial agent list
            agent_list_message = {
                "type": "agent_list",
                "data": agents,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_json(agent_list_message)
            
            # Handle incoming messages
            while True:
                data = await websocket.receive_json()
                logger.debug(f"Received agent status from {client_id}: {data}")
                
                try:
                    # Store agent status using Celery task
                    store_agent_status.delay(data)
                    
                    # Broadcast to other clients
                    await self.manager.broadcast(
                        {"type": "agent_status", "data": data},
                        "agents"
                    )
                except Exception as e:
                    logger.error(f"Error processing agent status: {str(e)}")
                    logger.error(traceback.format_exc())
                    error_message = {
                        "type": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
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
                "error": str(e),
                "timestamp": datetime.now().isoformat()
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
                    # Store graph update using Celery task
                    store_graph_update.delay(data)
                    
                    # Broadcast to other clients
                    await self.manager.broadcast(
                        {"type": "graph_update", "data": data},
                        "graph"
                    )
                except Exception as e:
                    logger.error(f"Error processing graph update: {str(e)}")
                    logger.error(traceback.format_exc())
                    error_message = {
                        "type": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_json(error_message)
        except WebSocketDisconnect:
            await self.manager.disconnect(client_id, "graph")
            logger.info(f"Client {client_id} disconnected from graph")
