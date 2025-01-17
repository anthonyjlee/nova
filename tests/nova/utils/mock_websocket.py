"""Mock WebSocket implementation for testing."""

from typing import Dict, Any, Callable, Awaitable, Optional, MutableMapping
from fastapi import WebSocket
from starlette.types import Message, Send, Receive, Scope
import json
import asyncio
from collections import deque

class MockWebSocket(WebSocket):
    """Mock WebSocket for testing that implements required WebSocket interface."""
    
    def __init__(self):
        # Create mock functions for required parameters
        async def mock_receive() -> Message:
            return {"type": "websocket.connect", "text": ""}
            
        async def mock_send(message: Message) -> None:
            pass
            
        # Initialize with required parameters
        scope: Scope = {
            "type": "websocket",
            "path": "/ws",
            "headers": [],
            "client": ("127.0.0.1", 12345)
        }
        super().__init__(scope=scope, receive=mock_receive, send=mock_send)
        
        # Message queues
        self._receive_queue = deque()
        self._send_queue = deque()
        
        # Connection state
        self._connected = False
        
    async def accept(self):
        """Accept the connection."""
        self._connected = True
        
    async def close(self):
        """Close the connection."""
        self._connected = False
        
    async def receive_json(self) -> Dict[str, Any]:
        """Receive JSON data."""
        if not self._receive_queue:
            return {}  # Return empty dict if queue is empty
        return self._receive_queue.popleft()
        
    async def send_json(self, data: Dict[str, Any]):
        """Send JSON data."""
        self._send_queue.append(data)
        
    async def receive(self) -> Message:
        """Receive raw message."""
        if not self._receive_queue:
            return {"type": "websocket.disconnect", "code": 1000, "reason": ""}
        data = self._receive_queue.popleft()
        return {
            "type": "websocket.receive",
            "text": json.dumps(data),
            "bytes": None
        }
        
    async def send(self, message: Message) -> None:
        """Send raw message."""
        if message["type"] == "websocket.send":
            data = json.loads(message["text"])
            self._send_queue.append(data)
            
    def add_message(self, message: Dict[str, Any]):
        """Add message to receive queue for testing."""
        self._receive_queue.append(message)
        
    def get_sent_messages(self) -> list:
        """Get all sent messages for verification."""
        messages = list(self._send_queue)
        self._send_queue.clear()
        return messages
        
    @property
    def connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._connected
