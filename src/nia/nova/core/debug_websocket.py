"""Debug WebSocket endpoint for real-time debug information."""

import json
import logging
from typing import List
from fastapi import WebSocket, WebSocketDisconnect, Query, Depends
from .auth import validate_api_key

logger = logging.getLogger(__name__)

class DebugConnectionManager:
    """Manages debug WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        """Connect a new client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        """Disconnect a client."""
        self.active_connections.remove(websocket)
        
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send debug message: {str(e)}")
                await self.disconnect(connection)

# Global connection manager
manager = DebugConnectionManager()

async def debug_websocket_endpoint(
    websocket: WebSocket,
    key: str = Query(...),  # API key is required
):
    """Debug WebSocket endpoint."""
    # Validate API key
    if not validate_api_key(key):
        await websocket.close(code=4003)
        return
        
    try:
        await manager.connect(websocket)
        
        # Send initial connection message
        await websocket.send_json({
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
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    # Echo back any received messages for now
                    await websocket.send_json({
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
            manager.disconnect(websocket)
            
    except Exception as e:
        logger.error(f"Debug WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011)
        except:
            pass

# Broadcast debug message to all connected clients
async def broadcast_debug(message_type: str, level: str, data: any):
    """Broadcast debug message to all connected clients."""
    await manager.broadcast({
        "type": "debug_update",
        "data": {
            "type": message_type,
            "level": level,
            "data": data
        }
    })
