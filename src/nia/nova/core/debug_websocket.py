"""Debug WebSocket endpoint for real-time debug information."""

import json
import logging
from typing import Dict, Any, List, Tuple
from fastapi import WebSocket, WebSocketDisconnect, Query
from .auth import validate_api_key

logger = logging.getLogger(__name__)

class DebugConnectionManager:
    """Manages debug WebSocket connections."""
    
    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._active_sockets: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket) -> Tuple[WebSocket, str]:
        """Connect a new client and return socket with ID."""
        await websocket.accept()
        socket_id = str(id(websocket))
        self._active_sockets[socket_id] = websocket
        return websocket, socket_id
        
    async def disconnect(self, socket_id: str) -> None:
        """Disconnect a client by ID."""
        if socket_id in self._active_sockets:
            del self._active_sockets[socket_id]
        
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        # Convert to list to avoid dictionary size change during iteration
        for socket_id, websocket in list(self._active_sockets.items()):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send debug message: {str(e)}")
                await self.disconnect(socket_id)

# Global connection manager
manager = DebugConnectionManager()

async def debug_websocket_endpoint(
    websocket: WebSocket,
    key: str = Query(...),  # API key is required
) -> None:
    """Debug WebSocket endpoint."""
    # Validate API key
    try:
        await validate_api_key(key)
    except:
        await websocket.close(code=4003)
        return
        
    socket_id = ""
    try:
        socket, socket_id = await manager.connect(websocket)
        
        # Send initial connection message
        await socket.send_json({
            "type": "debug_update",
            "data": {
                "type": "connection",
                "level": "info",
                "data": "Debug WebSocket connected"
            }
        })
        
        try:
            while True:
                # Keep connection alive and handle any incoming messages
                data = await socket.receive_text()
                try:
                    message = json.loads(data)
                    # Echo back any received messages for now
                    await socket.send_json({
                        "type": "debug_update",
                        "data": {
                            "type": "echo",
                            "level": "info",
                            "data": message
                        }
                    })
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON: {data}")
                    
        except WebSocketDisconnect:
            await manager.disconnect(socket_id)
            
    except Exception as e:
        logger.error(f"Debug WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011)
        except:
            pass

async def broadcast_debug(message_type: str, level: str, data: Any) -> None:
    """Broadcast debug message to all connected clients."""
    await manager.broadcast({
        "type": "debug_update",
        "data": {
            "type": message_type,
            "level": level,
            "data": data
        }
    })
