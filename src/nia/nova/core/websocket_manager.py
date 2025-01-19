"""WebSocket connection manager."""

from typing import Dict, Any, Optional
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_connections: Dict[str, Dict[str, WebSocket]] = {}  # agent_id -> {client_id -> websocket}
        
    async def connect(self, websocket: WebSocket, client_id: str, agent_id: Optional[str] = None):
        """Add a WebSocket connection."""
        self.active_connections[client_id] = websocket
        if agent_id:
            if agent_id not in self.agent_connections:
                self.agent_connections[agent_id] = {}
            self.agent_connections[agent_id][client_id] = websocket
        logger.debug(f"Client {client_id} connected" + (f" to agent {agent_id}" if agent_id else ""))
        
    async def disconnect(self, client_id: str, agent_id: Optional[str] = None):
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            if agent_id and agent_id in self.agent_connections:
                if client_id in self.agent_connections[agent_id]:
                    del self.agent_connections[agent_id][client_id]
                if not self.agent_connections[agent_id]:
                    del self.agent_connections[agent_id]
            logger.debug(f"Client {client_id} disconnected" + (f" from agent {agent_id}" if agent_id else ""))
            
    async def send_json(self, client_id: str, message: Dict[str, Any], agent_id: Optional[str] = None):
        """Send JSON message to a specific client."""
        if agent_id:
            # Send to specific agent-client connection
            if agent_id in self.agent_connections and client_id in self.agent_connections[agent_id]:
                await self.agent_connections[agent_id][client_id].send_json(message)
        elif client_id in self.active_connections:
            # Send to general client connection
            await self.active_connections[client_id].send_json(message)

    async def broadcast_agent_message(self, agent_id: str, message: Dict[str, Any]):
        """Broadcast message to all clients connected to a specific agent."""
        if agent_id in self.agent_connections:
            for websocket in self.agent_connections[agent_id].values():
                await websocket.send_json(message)

    async def join_channel(self, client_id: str, channel: str):
        """Join a channel."""
        if client_id in self.active_connections:
            if channel not in self.agent_connections:
                self.agent_connections[channel] = {}
            self.agent_connections[channel][client_id] = self.active_connections[client_id]
            logger.debug(f"Client {client_id} joined channel {channel}")

    async def leave_channel(self, client_id: str, channel: str):
        """Leave a channel."""
        if channel in self.agent_connections and client_id in self.agent_connections[channel]:
            del self.agent_connections[channel][client_id]
            if not self.agent_connections[channel]:
                del self.agent_connections[channel]
            logger.debug(f"Client {client_id} left channel {channel}")

    async def broadcast_chat_message(self, message: Dict[str, Any], channel: Optional[str] = None):
        """Broadcast chat message to all connected clients in a channel or globally."""
        if channel and channel in self.agent_connections:
            for websocket in self.agent_connections[channel].values():
                await websocket.send_json(message)
        else:
            for websocket in self.active_connections.values():
                await websocket.send_json(message)

    async def broadcast_task_update(self, message: Dict[str, Any], channel: Optional[str] = None):
        """Broadcast task update to all connected clients in a channel or globally."""
        if channel and channel in self.agent_connections:
            for websocket in self.agent_connections[channel].values():
                await websocket.send_json(message)
        else:
            for websocket in self.active_connections.values():
                await websocket.send_json(message)

    async def broadcast_agent_status(self, message: Dict[str, Any], channel: Optional[str] = None):
        """Broadcast agent status update to all connected clients in a channel or globally."""
        if channel and channel in self.agent_connections:
            for websocket in self.agent_connections[channel].values():
                await websocket.send_json(message)
        else:
            for websocket in self.active_connections.values():
                await websocket.send_json(message)

    async def broadcast_graph_update(self, message: Dict[str, Any], channel: Optional[str] = None):
        """Broadcast graph update to all connected clients in a channel or globally."""
        if channel and channel in self.agent_connections:
            for websocket in self.agent_connections[channel].values():
                await websocket.send_json(message)
        else:
            for websocket in self.active_connections.values():
                await websocket.send_json(message)

    async def broadcast_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to a specific client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

# Create global instance
websocket_manager = WebSocketManager()
