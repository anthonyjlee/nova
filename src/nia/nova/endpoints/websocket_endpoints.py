"""WebSocket endpoints for real-time updates."""

from fastapi import APIRouter, Depends, WebSocketDisconnect, Query, HTTPException
from ..core.websocket import NovaWebSocket
from typing import Dict, Any, Optional, Literal
import uuid
import logging
import asyncio
import base64
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from ..core.dependencies import get_memory_system
from ..core.auth import ws_auth, API_KEYS
from ..core.websocket_server import WebSocketServer
from nia.memory.two_layer import TwoLayerMemorySystem

ws_router = APIRouter(
    tags=["WebSocket"]
)

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
    global _websocket_server
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

# Initialize server at module load time
_websocket_server = None

ConnectionType = Literal["chat", "tasks", "agents", "graph"]

@ws_router.websocket("/debug/client_{client_id}")
async def debug_websocket_endpoint(
    websocket: NovaWebSocket,
    client_id: str,
    api_key: Optional[str] = None,
):
    """Debug WebSocket endpoint."""
    logger.debug(f"Received WebSocket connection request for client {client_id}")
    logger.debug(f"WebSocket headers: {websocket.headers}")
    logger.debug(f"WebSocket scope: {websocket.scope}")
    try:
        # Check origin before accepting connection
        origin = websocket.headers.get("origin")
        logger.debug(f"Origin: {origin}")
        if origin != "http://localhost:5173":
            logger.error(f"Invalid origin: {origin}")
            return
            
        # Accept connection without authentication
        logger.debug("Accepting WebSocket connection")
        await websocket.accept()
        logger.debug("WebSocket connection accepted")

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
                        api_key = message.get("data", {}).get("api_key")
                        if not isinstance(api_key, str) or not api_key.strip():
                            raise HTTPException(
                                status_code=403,
                                detail="Invalid API key format"
                            )
                            
                        normalized_key = ws_auth(api_key.strip())
                        logger.debug(f"API key validated: {normalized_key}")
                        
                        await websocket.send_json({
                            "type": "connection_success",
                            "data": {
                                "message": "Connected",
                                "client_id": client_id
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })
                        # Send delivery confirmation
                        await websocket.send_json({
                            "type": "message_delivered",
                            "data": {
                                "message": "Authentication message received and processed",
                                "original_type": "connect",
                                "status": "success"
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })
                        continue
                    except HTTPException as e:
                        error_type = "token_expired" if "expired" in str(e.detail).lower() else "invalid_key"
                        await websocket.send_json({
                            "type": "error",
                            "data": {
                                "message": str(e.detail),
                                "error_type": error_type,
                                "code": 403
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })
                        await websocket.send_json({
                            "type": "disconnect",
                            "data": {
                                "reason": str(e.detail)
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })
                        await websocket.close(code=4000)
                        return
                elif message["type"] == "join_channel":
                    try:
                        # Validate channel name
                        channel = message["data"]["channel"]
                        if channel not in ["NovaTeam", "NovaSupport"]:
                            raise ValueError(f"Invalid channel: {channel}")
                            
                        # Send delivery confirmation
                        await websocket.send_json({
                            "type": "message_delivered",
                            "data": {
                                "message": "Join channel request received",
                                "original_type": "join_channel",
                                "status": "success"
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })
                        
                        # Send subscription success
                        await websocket.send_json({
                            "type": "subscription_success",
                            "data": {
                                "channel": channel,
                                "status": "success",
                                "message": "Successfully joined channel"
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id,
                            "channel": channel
                        })
                    except Exception as e:
                        logger.error(f"Error joining channel: {str(e)}")
                        await websocket.send_json({
                            "type": "error",
                            "data": {
                                "message": f"Failed to join channel: {str(e)}",
                                "error_type": "channel_error",
                                "code": 400
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })

                elif message["type"] == "leave_channel":
                    try:
                        # Validate channel name
                        channel = message["data"]["channel"]
                        if channel not in ["NovaTeam", "NovaSupport"]:
                            raise ValueError(f"Invalid channel: {channel}")
                            
                        # Send delivery confirmation
                        await websocket.send_json({
                            "type": "message_delivered",
                            "data": {
                                "message": "Leave channel request received",
                                "original_type": "leave_channel",
                                "status": "success"
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })
                        
                        # Send unsubscription success
                        await websocket.send_json({
                            "type": "unsubscription_success",
                            "data": {
                                "channel": channel,
                                "status": "success",
                                "message": "Successfully left channel"
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id,
                            "channel": channel
                        })
                    except Exception as e:
                        logger.error(f"Error leaving channel: {str(e)}")
                        await websocket.send_json({
                            "type": "error",
                            "data": {
                                "message": f"Failed to leave channel: {str(e)}",
                                "error_type": "channel_error",
                                "code": 400
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })

                elif message["type"] == "chat_message":
                    try:
                        # Validate message format
                        if "data" not in message or "content" not in message["data"]:
                            raise ValueError("Invalid message format")
                            
                        # Validate channel if present
                        channel = message.get("channel")
                        if channel and channel not in ["NovaTeam", "NovaSupport"]:
                            raise ValueError(f"Invalid channel: {channel}")
                            
                        # Validate message type for channels
                        if channel == "NovaTeam":
                            if message["data"].get("message_type") not in ["task_detection", "cognitive_processing"]:
                                raise ValueError("Invalid message type for NovaTeam channel")
                        elif channel == "NovaSupport":
                            if message["data"].get("message_type") not in ["resource_allocation", "system_health"]:
                                raise ValueError("Invalid message type for NovaSupport channel")
                                
                        # Echo message back
                        await websocket.send_json({
                            **message,
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })
                        
                        # Send delivery confirmation
                        await websocket.send_json({
                            "type": "message_delivered",
                            "data": {
                                "message": "Chat message received and processed",
                                "original_type": "chat_message",
                                "status": "success"
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })
                    except Exception as e:
                        logger.error(f"Error processing chat message: {str(e)}")
                        await websocket.send_json({
                            "type": "error",
                            "data": {
                                "message": f"Failed to process message: {str(e)}",
                                "error_type": "message_error",
                                "code": 400
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        })

                else:
                    # Echo back other messages for testing
                    await websocket.send_json({
                        **message,
                        "timestamp": datetime.now().isoformat(),
                        "client_id": client_id
                    })
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        logger.info("Debug client disconnected")
    except HTTPException as e:
        logger.error(f"HTTP error in debug connection: {str(e)}")
        try:
            error_type = "token_expired" if "expired" in str(e.detail).lower() else "invalid_key"
            await websocket.send_json({
                "type": "error",
                "data": {
                    "message": str(e.detail),
                    "error_type": error_type,
                    "code": e.status_code
                },
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id
            })
            await websocket.close(code=4000, reason=str(e.detail))
        except Exception as close_error:
            logger.error(f"Error closing debug websocket: {str(close_error)}")
    except Exception as e:
        logger.error(f"Unexpected error in debug connection: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "data": {
                    "message": "Internal server error",
                    "error_type": "server_error",
                    "code": 500
                },
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id
            })
            await websocket.close(code=1011, reason="Internal server error")
        except Exception as close_error:
            logger.error(f"Error closing debug websocket: {str(close_error)}")

@ws_router.websocket("/client_{client_id}")
async def websocket_endpoint(
    websocket: NovaWebSocket,
    client_id: str,
):
    """WebSocket endpoint for real-time updates."""
    try:
        # Check origin before accepting connection
        origin = websocket.headers.get("origin")
        logger.debug(f"Origin: {origin}")
        if origin != "http://localhost:5173":
            logger.error(f"Invalid origin: {origin}")
            return
            
        # Accept connection
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
                        api_key = message.get("data", {}).get("api_key")
                        if not isinstance(api_key, str) or not api_key.strip():
                            raise HTTPException(
                                status_code=403,
                                detail="Invalid API key format"
                            )
                            
                        auth_result = ws_auth(api_key.strip())
                        logger.debug(f"Auth result: {auth_result}")
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
                        # Send error with specific type for expired vs invalid
                        error_type = "token_expired" if "expired" in str(e.detail).lower() else "invalid_key"
                        error_message = {
                            "type": "error",
                            "data": {
                                "message": str(e.detail),
                                "error_type": error_type
                            },
                            "timestamp": datetime.now().isoformat(),
                            "client_id": client_id
                        }
                        await websocket.send_json(error_message)
                        
                        # Send disconnect status before closing
                        await websocket.send_json({
                            "type": "disconnect",
                            "data": {
                                "reason": str(e.detail)
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
    except HTTPException as e:
        logger.error(f"HTTP error in connection: {str(e)}")
        try:
            error_type = "token_expired" if "expired" in str(e.detail).lower() else "invalid_key"
            await websocket.send_json({
                "type": "error",
                "data": {
                    "message": str(e.detail),
                    "error_type": error_type,
                    "code": e.status_code
                },
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id
            })
            await websocket.close(code=4000, reason=str(e.detail))
        except Exception as close_error:
            logger.error(f"Error closing websocket: {str(close_error)}")
    except RuntimeError as e:
        logger.error(f"WebSocket server error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "data": {
                    "message": "Server error",
                    "error_type": "server_error",
                    "code": 500
                },
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id
            })
            await websocket.close(code=1011, reason=str(e))
        except Exception as close_error:
            logger.error(f"Error closing websocket: {str(close_error)}")
    except Exception as e:
        logger.error(f"Unexpected error in connection: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "data": {
                    "message": "Internal server error",
                    "error_type": "server_error",
                    "code": 500
                },
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id
            })
            await websocket.close(code=1011, reason="Internal server error")
        except Exception as close_error:
            logger.error(f"Error closing websocket: {str(close_error)}")
