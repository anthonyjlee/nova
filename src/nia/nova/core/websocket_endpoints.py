"""WebSocket endpoints for real-time updates."""

from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect, Query
from typing import Dict, Any, Optional, Literal
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from .dependencies import get_memory_system
from .auth import validate_api_key
from .websocket_server import WebSocketServer
from nia.memory.two_layer import TwoLayerMemorySystem

ws_router = APIRouter(prefix="/api/ws", tags=["WebSocket"])

# Initialize WebSocket server and memory system
_websocket_server: Optional[WebSocketServer] = None
_memory_system: Optional[TwoLayerMemorySystem] = None
_init_lock = asyncio.Lock()

async def initialize_websocket_server():
    """Initialize the WebSocket server if not already initialized."""
    global _websocket_server
    
    async with _init_lock:
        if _websocket_server is None:
            try:
                # Create and initialize WebSocket server instance
                _websocket_server = await WebSocketServer.create(get_memory_system)
                logger.info("WebSocket server initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing WebSocket server: {str(e)}")
                raise

def get_websocket_server() -> WebSocketServer:
    """Get the WebSocket server instance. Must be initialized first."""
    if _websocket_server is None:
        raise RuntimeError("WebSocket server not initialized")
    return _websocket_server

async def start_memory_updates():
    """Start background task for broadcasting memory updates."""
    try:
        server = get_websocket_server()
        return await server.broadcast_memory_updates()
    except Exception as e:
        logger.error(f"Error starting memory updates: {str(e)}")
        raise

# Register startup event handler
@ws_router.on_event("startup")
async def startup_event():
    """Handle FastAPI startup event."""
    try:
        logger.info("Starting WebSocket server initialization...")
        # Initialize server and wait for completion
        await initialize_websocket_server()
        logger.info("WebSocket server initialization completed")
    except Exception as e:
        logger.error(f"Error in startup event: {str(e)}", exc_info=True)
        raise

ConnectionType = Literal["chat", "tasks", "agents", "graph"]

@ws_router.websocket("/{connection_type}/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    connection_type: ConnectionType,
    client_id: str,
    api_key: str = Query(...),
    memory_system=Depends(get_memory_system)
):
    """WebSocket endpoint for real-time updates."""
    try:
        # Accept connection first
        await websocket.accept()

        # Validate API key
        if not validate_api_key(api_key):
            await websocket.close(code=4000, reason="Invalid API key")
            return

        # Ensure server is initialized
        server = get_websocket_server()
        
        # Map connection type to handler
        handlers = {
            "chat": server.handle_chat_connection,
            "tasks": server.handle_task_connection,
            "agents": server.handle_agent_connection,
            "graph": server.handle_graph_connection
        }
        
        if connection_type not in handlers:
            raise ValueError(f"Invalid connection type: {connection_type}")
            
        handler = handlers[connection_type]
        await handler(websocket, client_id)
        
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from {connection_type}")
    except RuntimeError as e:
        logger.error(f"WebSocket server error: {str(e)}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception as close_error:
            logger.error(f"Error closing websocket: {str(close_error)}")
    except Exception as e:
        logger.error(f"Error handling {connection_type} connection: {str(e)}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception as close_error:
            logger.error(f"Error closing websocket: {str(close_error)}")
