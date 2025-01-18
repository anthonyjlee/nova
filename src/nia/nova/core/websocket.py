"""Custom WebSocket implementation for Nova."""

from fastapi import WebSocket as FastAPIWebSocket
from typing import Optional, Dict, Any
import logging
from .websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class NovaWebSocket(FastAPIWebSocket):
    """Custom WebSocket class that handles authentication after connection."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    async def accept(
        self,
        subprotocol: Optional[str] = None,
        headers: Optional[list[tuple[bytes, bytes]]] = None,
    ) -> None:
        """Accept the WebSocket connection without authentication."""
        logger.debug("Accepting WebSocket connection")
        
        # Create base headers list
        base_headers = [
            (b"upgrade", b"websocket"),
            (b"connection", b"upgrade")
        ]
        
        # Combine with any additional headers
        final_headers = base_headers + (headers or [])
        
        await super().accept(subprotocol=subprotocol, headers=final_headers)
        logger.debug("WebSocket connection accepted")
        
    async def send_message(self, message: Dict[str, Any], client_id: str) -> None:
        """Send a message through the WebSocket manager."""
        await websocket_manager.send_json(client_id, message)
