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

def run_async(coro):
    """Run an async function synchronously.
    
    Args:
        coro: Coroutine to run
        
    Returns:
        Result of the coroutine execution
        
    Raises:
        RuntimeError: If there's an error running the coroutine
    """
    loop = None
    try:
        # Create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run coroutine and get result
        logger.debug("Running coroutine synchronously...")
        result = loop.run_until_complete(coro)
        logger.debug("Coroutine completed successfully")
        return result
        
    except asyncio.CancelledError:
        logger.error("Coroutine was cancelled")
        raise RuntimeError("Async operation was cancelled")
    except Exception as e:
        logger.error(f"Error running coroutine: {str(e)}")
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Failed to run async operation: {str(e)}") from e
    finally:
        if loop:
            try:
                # Cancel any pending tasks
                pending = asyncio.all_tasks(loop)
                if pending:
                    logger.warning(f"Cancelling {len(pending)} pending tasks")
                    for task in pending:
                        task.cancel()
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    
                # Close loop
                loop.close()
                logger.debug("Event loop closed")
            except Exception as e:
                logger.error(f"Error cleaning up event loop: {str(e)}")
                logger.error(traceback.format_exc())

def get_sync_memory_system():
    """Get memory system instance synchronously."""
    return run_async(get_memory_system())

def ensure_serializable(data: Any) -> Any:
    """Ensure data is JSON serializable.
    
    Args:
        data: Data to check/convert
        
    Returns:
        JSON serializable version of the data
    """
    try:
        # Convert data to string if it's not a basic type
        if not isinstance(data, (dict, list, str, int, float, bool, type(None))):
            data = str(data)
        elif isinstance(data, dict):
            # Handle dictionary values recursively
            return {k: ensure_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            # Handle list values recursively
            return [ensure_serializable(v) for v in data]
        # Verify it can be serialized
        json.dumps(data)
        return data
    except (TypeError, ValueError) as e:
        logger.error(f"Data is not JSON serializable: {str(e)}")
        return str(data)

@celery_app.task(name='nova.store_chat_message')
def store_chat_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """Store a chat message in the memory system."""
    try:
        logger.debug(f"Storing chat message: {json.dumps(data, indent=2)}")
        memory_system = get_sync_memory_system()
        if not memory_system:
            logger.error("Failed to get memory system")
            raise RuntimeError("Memory system not available")
            
        # Ensure data is JSON serializable
        logger.debug("Ensuring data is serializable...")
        data = ensure_serializable(data)
        logger.debug(f"Serializable data: {json.dumps(data, indent=2)}")
            
        # Validate and create memory object
        logger.debug("Validating and creating memory data...")
        # Ensure content is a dict
        if not isinstance(data, dict):
            logger.error(f"Invalid data type: {type(data)}, expected dict")
            raise ValueError("Message data must be a dictionary")
            
        # Create memory data with validation
        memory_data = {
            "content": data,
            "type": MemoryType.EPISODIC,
            "importance": 0.5,
            "context": {
                "type": "chat_message",
                "source": "nova",
                "domain": "chat",
                "timestamp": datetime.now().isoformat(),
                "message_type": data.get("type", "unknown"),
                "client_id": data.get("client_id", "unknown")
            }
        }
        logger.debug(f"Memory data: {json.dumps(memory_data, indent=2)}")
        
        # Create memory object with error handling
        try:
            memory = EpisodicMemory(**memory_data)
            logger.debug("Successfully created EpisodicMemory object")
        except Exception as e:
            logger.error(f"Failed to create EpisodicMemory object: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Invalid memory data structure: {str(e)}") from e
        
        try:
            # Run store_experience synchronously
            logger.debug("Storing experience in memory system...")
            try:
                result = run_async(memory_system.store_experience(memory))
                if result:
                    logger.debug(f"Store experience result: {json.dumps(result, indent=2)}")
                else:
                    logger.warning("Store experience returned None result")
                logger.debug("Successfully stored chat message")
            except asyncio.CancelledError:
                logger.error("Store experience operation was cancelled")
                raise
            except Exception as store_error:
                logger.error(f"Error in store_experience: {str(store_error)}")
                logger.error(traceback.format_exc())
                raise RuntimeError(f"Failed to store experience: {str(store_error)}") from store_error
            return data
        except Exception as e:
            logger.error(f"Error storing experience: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    except Exception as e:
        logger.error(f"Error in store_chat_message: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@celery_app.task(name='nova.store_task_update')
def store_task_update(data: Dict[str, Any]) -> Dict[str, Any]:
    """Store a task update in the memory system."""
    try:
        logger.debug(f"Storing task update: {json.dumps(data, indent=2)}")
        memory_system = get_sync_memory_system()
        if not memory_system:
            logger.error("Failed to get memory system")
            raise RuntimeError("Memory system not available")
            
        # Ensure data is JSON serializable
        logger.debug("Ensuring data is serializable...")
        data = ensure_serializable(data)
        logger.debug(f"Serializable data: {json.dumps(data, indent=2)}")
            
        # Validate and create memory object
        logger.debug("Validating and creating memory data...")
        # Ensure content is a dict
        if not isinstance(data, dict):
            logger.error(f"Invalid data type: {type(data)}, expected dict")
            raise ValueError("Task data must be a dictionary")
            
        # Create memory data with validation
        memory_data = {
            "content": data,
            "type": MemoryType.EPISODIC,
            "importance": 0.7,
            "context": {
                "type": "task_update",
                "source": "nova",
                "domain": "tasks",
                "timestamp": datetime.now().isoformat(),
                "task_id": data.get("task_id", "unknown"),
                "update_type": data.get("type", "unknown")
            }
        }
        logger.debug(f"Memory data: {json.dumps(memory_data, indent=2)}")
        
        # Create memory object with error handling
        try:
            memory = EpisodicMemory(**memory_data)
            logger.debug("Successfully created EpisodicMemory object")
        except Exception as e:
            logger.error(f"Failed to create EpisodicMemory object: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Invalid memory data structure: {str(e)}") from e
        # Run store_experience synchronously
        logger.debug("Storing experience in memory system...")
        try:
            result = run_async(memory_system.store_experience(memory))
            if result:
                logger.debug(f"Store experience result: {json.dumps(result, indent=2)}")
            else:
                logger.warning("Store experience returned None result")
            logger.debug("Successfully stored task update")
            return data
        except asyncio.CancelledError:
            logger.error("Store experience operation was cancelled")
            raise
        except Exception as store_error:
            logger.error(f"Error in store_experience: {str(store_error)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Failed to store experience: {str(store_error)}") from store_error
    except Exception as e:
        logger.error(f"Error in store_task_update: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@celery_app.task(name='nova.store_agent_status')
def store_agent_status(data: Dict[str, Any]) -> Dict[str, Any]:
    """Store an agent status update in the memory system."""
    try:
        logger.debug(f"Storing agent status: {json.dumps(data, indent=2)}")
        memory_system = get_sync_memory_system()
        if not memory_system:
            logger.error("Failed to get memory system")
            raise RuntimeError("Memory system not available")
            
        # Ensure data is JSON serializable
        logger.debug("Ensuring data is serializable...")
        data = ensure_serializable(data)
        logger.debug(f"Serializable data: {json.dumps(data, indent=2)}")
            
        # Validate and create memory object
        logger.debug("Validating and creating memory data...")
        # Ensure content is a dict
        if not isinstance(data, dict):
            logger.error(f"Invalid data type: {type(data)}, expected dict")
            raise ValueError("Agent status data must be a dictionary")
            
        # Create memory data with validation
        memory_data = {
            "content": data,
            "type": MemoryType.EPISODIC,
            "importance": 0.6,
            "context": {
                "type": "agent_status",
                "source": "nova",
                "domain": "agents",
                "timestamp": datetime.now().isoformat(),
                "agent_id": data.get("agent_id", "unknown"),
                "status_type": data.get("type", "unknown")
            }
        }
        logger.debug(f"Memory data: {json.dumps(memory_data, indent=2)}")
        
        # Create memory object with error handling
        try:
            memory = EpisodicMemory(**memory_data)
            logger.debug("Successfully created EpisodicMemory object")
        except Exception as e:
            logger.error(f"Failed to create EpisodicMemory object: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Invalid memory data structure: {str(e)}") from e
        # Run store_experience synchronously
        logger.debug("Storing experience in memory system...")
        try:
            result = run_async(memory_system.store_experience(memory))
            if result:
                logger.debug(f"Store experience result: {json.dumps(result, indent=2)}")
            else:
                logger.warning("Store experience returned None result")
            logger.debug("Successfully stored agent status")
            return data
        except asyncio.CancelledError:
            logger.error("Store experience operation was cancelled")
            raise
        except Exception as store_error:
            logger.error(f"Error in store_experience: {str(store_error)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Failed to store experience: {str(store_error)}") from store_error
    except Exception as e:
        logger.error(f"Error in store_agent_status: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@celery_app.task(name='nova.store_graph_update')
def store_graph_update(data: Dict[str, Any]) -> Dict[str, Any]:
    """Store a graph update in the memory system."""
    try:
        logger.debug(f"Storing graph update: {json.dumps(data, indent=2)}")
        memory_system = get_sync_memory_system()
        if not memory_system:
            logger.error("Failed to get memory system")
            raise RuntimeError("Memory system not available")
            
        # Ensure data is JSON serializable
        logger.debug("Ensuring data is serializable...")
        data = ensure_serializable(data)
        logger.debug(f"Serializable data: {json.dumps(data, indent=2)}")
            
        # Validate and create memory object
        logger.debug("Validating and creating memory data...")
        # Ensure content is a dict
        if not isinstance(data, dict):
            logger.error(f"Invalid data type: {type(data)}, expected dict")
            raise ValueError("Graph update data must be a dictionary")
            
        # Create memory data with validation
        memory_data = {
            "content": data,
            "type": MemoryType.EPISODIC,
            "importance": 0.8,
            "context": {
                "type": "graph_update",
                "source": "nova",
                "domain": "graph",
                "timestamp": datetime.now().isoformat(),
                "update_type": data.get("type", "unknown"),
                "node_ids": data.get("node_ids", []),
                "edge_ids": data.get("edge_ids", [])
            }
        }
        logger.debug(f"Memory data: {json.dumps(memory_data, indent=2)}")
        
        # Create memory object with error handling
        try:
            memory = EpisodicMemory(**memory_data)
            logger.debug("Successfully created EpisodicMemory object")
        except Exception as e:
            logger.error(f"Failed to create EpisodicMemory object: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Invalid memory data structure: {str(e)}") from e
        # Run store_experience synchronously
        logger.debug("Storing experience in memory system...")
        try:
            result = run_async(memory_system.store_experience(memory))
            if result:
                logger.debug(f"Store experience result: {json.dumps(result, indent=2)}")
            else:
                logger.warning("Store experience returned None result")
            logger.debug("Successfully stored graph update")
            return data
        except asyncio.CancelledError:
            logger.error("Store experience operation was cancelled")
            raise
        except Exception as store_error:
            logger.error(f"Error in store_experience: {str(store_error)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Failed to store experience: {str(store_error)}") from store_error
    except Exception as e:
        logger.error(f"Error in store_graph_update: {str(e)}")
        logger.error(traceback.format_exc())
        raise

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
                
            # Accept connection
            logger.debug(f"Accepting connection for client {client_id} to {connection_type}")
            try:
                await websocket.accept()
            except Exception as e:
                logger.error(f"Error accepting connection for client {client_id}: {str(e)}")
                raise RuntimeError(f"Failed to accept websocket connection: {str(e)}") from e
                
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
                await websocket.send_json(ensure_serializable(message))
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
            
            # Get websocket before removing from active connections
            websocket = self.active_connections[connection_type].get(client_id)
            if websocket:
                try:
                    await websocket.close(code=1000, reason="Client disconnected")
                    logger.debug(f"Successfully closed websocket for client {client_id}")
                except Exception as e:
                    logger.error(f"Error closing websocket for client {client_id}: {str(e)}")
                    logger.error(traceback.format_exc())
            
            # Remove from active connections
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
            
            # Ensure message is JSON serializable
            logger.debug(f"Ensuring broadcast message is serializable: {json.dumps(message, indent=2)}")
            message = ensure_serializable(message)
            
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
                        await websocket.send_json(ensure_serializable(pong_message))
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
                    await websocket.send_json(ensure_serializable(error_message))
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
                    await websocket.send_json(ensure_serializable(error_message))
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
            await websocket.send_json(ensure_serializable(agent_list_message))
            
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
                    await websocket.send_json(ensure_serializable(error_message))
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
            await websocket.send_json(ensure_serializable(error_message))
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
                    await websocket.send_json(ensure_serializable(error_message))
        except WebSocketDisconnect:
            await self.manager.disconnect(client_id, "graph")
            logger.info(f"Client {client_id} disconnected from graph")
            
    async def broadcast_memory_updates(self):
        """Background task to broadcast memory system updates."""
        # Initialize update buffer
        pending_updates = []
        
        while True:
            try:
                # Ensure memory system is properly initialized
                await self.ensure_initialized()
                
                # Verify memory system is ready
                memory_system = await self.memory_system()
                if not hasattr(memory_system, 'episodic') or not hasattr(memory_system.episodic, 'store'):
                    logger.warning("Memory system not properly initialized, retrying...")
                    await asyncio.sleep(5)
                    continue
                
                # Get recent updates from memory system
                try:
                    new_updates = await memory_system.episodic.store.search_vectors(
                        content={},
                        filter_conditions=[
                            models.FieldCondition(
                                key="metadata.type",
                                match=models.MatchAny(any=["chat_message", "task_update", "agent_status", "graph_update"])
                            )
                        ]
                    )
                except Exception as e:
                    logger.error(f"Error searching vectors: {str(e)}")
                    await asyncio.sleep(5)
                    continue

                # Add new updates to pending buffer
                pending_updates.extend(new_updates)
                
                # Process all pending updates
                if pending_updates:
                    # Group updates by type
                    grouped_updates = {
                        "chat": [],
                        "tasks": [],
                        "agents": [],
                        "graph": []
                    }
                    
                    for update in pending_updates:
                        if update.get("metadata", {}).get("type") == "chat_message":
                            grouped_updates["chat"].append(update)
                        elif update.get("metadata", {}).get("type") == "task_update":
                            grouped_updates["tasks"].append(update)
                        elif update.get("metadata", {}).get("type") == "agent_status":
                            grouped_updates["agents"].append(update)
                        elif update.get("metadata", {}).get("type") == "graph_update":
                            grouped_updates["graph"].append(update)
                    
                    # Broadcast updates to respective clients
                    broadcast_success = True
                    for update_type, updates in grouped_updates.items():
                        if updates:
                            try:
                                await self.manager.broadcast(
                                    {
                                        "type": f"{update_type}_updates",
                                        "data": updates
                                    },
                                    update_type
                                )
                            except Exception as e:
                                logger.error(f"Error broadcasting {update_type} updates: {str(e)}")
                                broadcast_success = False
                                break
                    
                    # Clear pending updates only if broadcast was successful
                    if broadcast_success:
                        pending_updates.clear()
                
                # Sleep for a short interval
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in memory update broadcast: {str(e)}")
                await asyncio.sleep(5)  # Sleep longer on error
