"""WebSocket testing utilities."""

from typing import Dict, Any, Optional, List, cast
from fastapi import WebSocket
from .mock_websocket import MockWebSocket
import json
import asyncio
from datetime import datetime

class WebSocketTestSession:
    """Test session for WebSocket connections with async context manager support."""
    
    def __init__(self, websocket: WebSocket):
        # Cast to MockWebSocket since we use its specific methods
        self.websocket = cast(MockWebSocket, websocket)
        self.received_messages: List[Dict[str, Any]] = []
        self.sent_messages: List[Dict[str, Any]] = []
        self._closed = False
        
    async def __aenter__(self) -> "WebSocketTestSession":
        """Enter async context."""
        await self.websocket.accept()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        if not self._closed:
            await self.websocket.close()
            self._closed = True
        
    async def send_json(self, data: Dict[str, Any]) -> None:
        """Send JSON data through WebSocket."""
        self.sent_messages.append(data)
        await self.websocket.send_json(data)
        
    async def receive_json(self) -> Dict[str, Any]:
        """Receive JSON data from WebSocket."""
        msg = await self.websocket.receive()
        if msg["type"] == "websocket.receive" and "text" in msg:
            data = json.loads(msg["text"])
            self.received_messages.append(data)
            return data
        return {}
        
    async def send_message(
        self,
        msg_type: str,
        data: Dict[str, Any],
        client_id: str = "test-client",
        channel: Optional[str] = None
    ) -> None:
        """Send a formatted WebSocket message."""
        message = {
            "type": msg_type,
            "timestamp": datetime.now().isoformat(),
            "client_id": client_id,
            "channel": channel,
            "data": data
        }
        await self.send_json(message)
        
    def get_received_messages(self, msg_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get received messages, optionally filtered by type."""
        # Get messages from websocket's send queue
        messages = self.websocket.get_sent_messages()
        self.received_messages.extend(messages)
        
        if msg_type is None:
            return self.received_messages
        return [msg for msg in self.received_messages if msg.get("type") == msg_type]
        
    def get_sent_messages(self, msg_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sent messages, optionally filtered by type."""
        if msg_type is None:
            return self.sent_messages
        return [msg for msg in self.sent_messages if msg.get("type") == msg_type]
        
    async def wait_for_message(
        self,
        msg_type: str,
        timeout: float = 5.0
    ) -> Optional[Dict[str, Any]]:
        """Wait for a specific message type with timeout."""
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            messages = self.get_received_messages(msg_type)
            if messages:
                return messages[-1]
            await asyncio.sleep(0.1)
        return None
        
    @property
    def closed(self) -> bool:
        """Check if WebSocket is closed."""
        return self._closed
