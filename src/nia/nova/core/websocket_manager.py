"""WebSocket connection manager."""

from typing import Dict, Any
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Add a WebSocket connection."""
        self.active_connections[client_id] = websocket
        logger.debug(f"Client {client_id} connected")
        
    async def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.debug(f"Client {client_id} disconnected")
            
    async def send_json(self, client_id: str, message: Dict[str, Any]):
        """Send JSON message to a specific client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

# Create global instance
websocket_manager = WebSocketManager()
