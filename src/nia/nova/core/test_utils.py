"""Test utilities for Nova."""

from typing import Dict, Any, Optional, AsyncIterator
import json
import asyncio
from fastapi import WebSocket

class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        """Initialize mock websocket."""
        self.sent_messages = []
        self.closed = False
        self.close_code = None
        self.close_reason = None
        self.accepted = False
        
    async def accept(self):
        """Accept the connection."""
        self.accepted = True
        
    async def close(self, code: int = 1000, reason: Optional[str] = None):
        """Close the connection."""
        self.closed = True
        self.close_code = code
        self.close_reason = reason
        
    async def send_json(self, data: Dict[str, Any]):
        """Send JSON data."""
        self.sent_messages.append(data)
        
    async def receive_json(self) -> Dict[str, Any]:
        """Receive JSON data."""
        # Override in tests to return specific messages
        return {}

class WebSocketTestSession:
    """WebSocket test session with async context manager support."""
    
    def __init__(self, websocket: Optional[MockWebSocket] = None):
        """Initialize test session."""
        self.websocket = websocket or MockWebSocket()
        self.connected = False
        self.messages: list[Dict[str, Any]] = []
        
    async def __aenter__(self) -> 'WebSocketTestSession':
        """Enter async context."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        await self.disconnect()
        
    async def connect(self):
        """Connect to websocket."""
        if not self.connected:
            await self.websocket.accept()
            self.connected = True
            
    async def disconnect(self):
        """Disconnect from websocket."""
        if self.connected:
            await self.websocket.close()
            self.connected = False
            
    async def send_json(self, data: Dict[str, Any]):
        """Send JSON message."""
        if not self.connected:
            raise RuntimeError("WebSocket not connected")
        await self.websocket.send_json(data)
        self.messages.append(data)
        
    async def receive_json(self) -> Dict[str, Any]:
        """Receive JSON message."""
        if not self.connected:
            raise RuntimeError("WebSocket not connected")
        data = await self.websocket.receive_json()
        self.messages.append(data)
        return data
        
    def get_messages(self) -> list[Dict[str, Any]]:
        """Get all messages sent/received."""
        return self.messages
        
    def clear_messages(self):
        """Clear message history."""
        self.messages.clear()

class MockAnalyticsAgent:
    """Mock analytics agent for testing."""
    
    def __init__(self):
        """Initialize mock agent."""
        self.processed_analytics = []
        
    async def process_analytics(self, content: Dict[str, Any], analytics_type: str, metadata: Dict[str, Any]) -> Any:
        """Process analytics request."""
        self.processed_analytics.append({
            "content": content,
            "type": analytics_type,
            "metadata": metadata
        })
        return {
            "analytics": {
                "events": []
            }
        }
        
    async def close(self):
        """Close the agent."""
        pass

    def __aiter__(self):
        """Make agent async iterable."""
        return self
        
    async def __anext__(self):
        """Return self for async iteration."""
        return self
