"""WebSocket testing utilities for Nova core functionality."""

from typing import Optional, Dict, Any, AsyncGenerator
from fastapi import FastAPI
from starlette.testclient import TestClient, WebSocketTestSession
import asyncio
from contextlib import asynccontextmanager

class AsyncWebSocketSession:
    """Async test session for WebSocket connections."""
    
    def __init__(self, app: FastAPI, url: str):
        """Initialize test session.
        
        Args:
            app: FastAPI application instance
            url: WebSocket endpoint URL
        """
        self.app = app
        self.url = url
        self.client = TestClient(app)
        self._ws: Optional[WebSocketTestSession] = None
        
    async def connect(self) -> None:
        """Connect to WebSocket endpoint."""
        self._ws = self.client.websocket_connect(self.url).__enter__()
        
    async def close(self) -> None:
        """Close WebSocket connection."""
        if self._ws:
            try:
                self._ws.__exit__(None, None, None)
            except Exception:
                pass
            self._ws = None
            
    async def send_json(self, data: Dict[str, Any]) -> None:
        """Send JSON message through WebSocket.
        
        Args:
            data: Message data to send
        """
        assert self._ws is not None, "WebSocket not connected"
        self._ws.send_json(data)
        await asyncio.sleep(0)  # Allow message to be processed
        
    async def receive_json(self) -> Dict[str, Any]:
        """Receive JSON message from WebSocket.
        
        Returns:
            Received message data
        """
        assert self._ws is not None, "WebSocket not connected"
        return self._ws.receive_json()

    async def receive_json_with_timeout(self, timeout: float = 5.0) -> Dict[str, Any]:
        """Receive JSON message with timeout.
        
        Args:
            timeout: Maximum time to wait for message in seconds
            
        Returns:
            Received message data
            
        Raises:
            asyncio.TimeoutError: If no message received within timeout
        """
        try:
            return await asyncio.wait_for(self.receive_json(), timeout=timeout)
        except asyncio.TimeoutError:
            raise

@asynccontextmanager
async def create_websocket_session(app: FastAPI, url: str) -> AsyncGenerator[AsyncWebSocketSession, None]:
    """Create a WebSocket test session."""
    session = AsyncWebSocketSession(app, url)
    try:
        await session.connect()
        yield session
    finally:
        await session.close()
