"""WebSocket connection manager for Nova API."""

from fastapi import WebSocket
from typing import Dict, Set, Optional
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.channel_subscribers: Dict[str, Set[str]] = {}
        self.client_channels: Dict[str, Set[str]] = {}
        self.client_api_keys: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, api_key: str) -> bool:
        """Accept connection and store client info."""
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            self.client_api_keys[client_id] = api_key
            self.client_channels[client_id] = set()
            logger.info(f"Client {client_id} connected")
            return True
        except Exception as e:
            logger.error(f"Error connecting client {client_id}: {e}")
            return False

    async def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove client connection and cleanup."""
        try:
            # Remove from active connections
            self.active_connections.pop(client_id, None)
            
            # Remove API key
            self.client_api_keys.pop(client_id, None)
            
            # Remove from all channels
            channels = self.client_channels.pop(client_id, set())
            for channel in channels:
                if channel in self.channel_subscribers:
                    self.channel_subscribers[channel].discard(client_id)
                    if not self.channel_subscribers[channel]:
                        del self.channel_subscribers[channel]
            
            logger.info(f"Client {client_id} disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting client {client_id}: {e}")

    async def broadcast_to_client(self, client_id: str, message: dict):
        """Send message to specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
                await self.disconnect(self.active_connections[client_id], client_id)

    async def broadcast_to_channel(self, channel: str, message: dict):
        """Send message to all clients in channel."""
        if channel in self.channel_subscribers:
            for client_id in self.channel_subscribers[channel].copy():
                await self.broadcast_to_client(client_id, message)

    async def join_channel(self, client_id: str, channel: str) -> bool:
        """Add client to channel."""
        try:
            if channel not in self.channel_subscribers:
                self.channel_subscribers[channel] = set()
            self.channel_subscribers[channel].add(client_id)
            self.client_channels[client_id].add(channel)
            return True
        except Exception as e:
            logger.error(f"Error adding client {client_id} to channel {channel}: {e}")
            return False

    async def leave_channel(self, client_id: str, channel: str) -> bool:
        """Remove client from channel."""
        try:
            if channel in self.channel_subscribers:
                self.channel_subscribers[channel].discard(client_id)
                if not self.channel_subscribers[channel]:
                    del self.channel_subscribers[channel]
            if client_id in self.client_channels:
                self.client_channels[client_id].discard(channel)
            return True
        except Exception as e:
            logger.error(f"Error removing client {client_id} from channel {channel}: {e}")
            return False

    async def broadcast_chat_message(self, client_id: str, message: dict, channel: Optional[str] = None):
        """Broadcast chat message."""
        data = {
            "type": "chat_message",
            "data": message
        }
        if channel:
            await self.broadcast_to_channel(channel, data)
        else:
            await self.broadcast_to_client(client_id, data)

    async def broadcast_task_update(self, client_id: str, update: dict, channel: Optional[str] = None):
        """Broadcast task update."""
        data = {
            "type": "task_update",
            "data": update
        }
        if channel:
            await self.broadcast_to_channel(channel, data)
        else:
            await self.broadcast_to_client(client_id, data)

    async def broadcast_agent_status(self, client_id: str, status: dict, channel: Optional[str] = None):
        """Broadcast agent status update."""
        data = {
            "type": "agent_status",
            "data": status
        }
        if channel:
            await self.broadcast_to_channel(channel, data)
        else:
            await self.broadcast_to_client(client_id, data)

    async def broadcast_graph_update(self, client_id: str, update: dict, channel: Optional[str] = None):
        """Broadcast knowledge graph update."""
        data = {
            "type": "graph_update",
            "data": update
        }
        if channel:
            await self.broadcast_to_channel(channel, data)
        else:
            await self.broadcast_to_client(client_id, data)

    async def broadcast_llm_stream(self, client_id: str, stream_data: dict):
        """Broadcast LLM stream chunk."""
        data = {
            "type": "llm_stream",
            "data": stream_data
        }
        await self.broadcast_to_client(client_id, data)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
