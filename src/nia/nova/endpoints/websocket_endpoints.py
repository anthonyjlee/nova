"""WebSocket endpoints for real-time updates."""

from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect, Query, HTTPException
from typing import Dict, Any, Optional, Literal
import uuid
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from ..core.dependencies import get_memory_system
from ..core.auth import validate_api_key, ws_auth, API_KEYS
from ..core.websocket_server import WebSocketServer
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

@ws_router.websocket("/debug/client_{client_id}")
async def debug_websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
):
    """Debug WebSocket endpoint."""
    try:
        # Accept connection first
        await websocket.accept()

        # Send initial connection message
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "message": "Connection established, waiting for authentication"
            },
            "timestamp": datetime.now().isoformat(),
            "client_id": client_id
        })

        # Wait for authentication
        while True:
            try:
                message = await websocket.receive_json()
                logger.debug(f"Received debug message: {message}")

                if message["type"] == "connect":
                    # Handle authentication
                    try:
                        api_key = message["data"]["api_key"]
                        ws_auth(api_key)
                        await websocket.send_json({
                            "type": "connection_success",
                            "data": {
                                "message": "Connected",
                                "client_id": client_id
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })
                    except HTTPException as e:
                        await websocket.send_json({
                            "type": "error",
                            "data": {
                                "message": str(e.detail)
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })
                        await websocket.close(code=4000, reason=str(e.detail))
                        return
                else:
                    # Echo back the message for testing
                    await websocket.send_json({
                        **message,
                        "timestamp": datetime.now().isoformat(),
                        "client_id": client_id
                    })
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        logger.info("Debug client disconnected")
    except Exception as e:
        logger.error(f"Error in debug connection: {str(e)}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception as close_error:
            logger.error(f"Error closing debug websocket: {str(close_error)}")

@ws_router.websocket("/client_{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    memory_system=Depends(get_memory_system)
):
    """WebSocket endpoint for real-time updates."""
    try:
        # Accept connection first
        await websocket.accept()
        logger.debug(f"WebSocket connection accepted for client {client_id}")

        # Send initial connection message
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "message": "Connection established, waiting for authentication"
            },
            "timestamp": datetime.now().isoformat(),
            "client_id": client_id
        })

        # Wait for authentication
        while True:
            try:
                message = await websocket.receive_json()
                logger.debug(f"Received message: {message}")

                if message["type"] == "connect":
                    # Handle authentication
                    try:
                        api_key = message["data"]["api_key"]
                        ws_auth(api_key)
                        await websocket.send_json({
                            "type": "connection_success",
                            "data": {
                                "message": "Connected",
                                "client_id": client_id
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })
                    except HTTPException as e:
                        await websocket.send_json({
                            "type": "error",
                            "data": {
                                "message": str(e.detail)
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })
                        await websocket.close(code=4000, reason=str(e.detail))
                        return

                    # After successful authentication, handle the connection
                    server = get_websocket_server()
                    await server.handle_chat_connection(websocket, client_id)
                    return

            except WebSocketDisconnect:
                break
        
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except RuntimeError as e:
        logger.error(f"WebSocket server error: {str(e)}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception as close_error:
            logger.error(f"Error closing websocket: {str(close_error)}")
    except Exception as e:
        logger.error(f"Error handling client {client_id} connection: {str(e)}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception as close_error:
            logger.error(f"Error closing websocket: {str(close_error)}")
