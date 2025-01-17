"""WebSocket types and models for Nova."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

class WebSocketState(str, Enum):
    """WebSocket state enum."""
    CONNECTING = "connecting"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"

class WebSocketMessageType(str, Enum):
    """WebSocket message type enum."""
    TEXT = "text"
    BINARY = "binary"
    PING = "ping"
    PONG = "pong"
    CLOSE = "close"

class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    id: str
    type: WebSocketMessageType
    data: Any
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class WebSocketError(BaseModel):
    """WebSocket error model."""
    code: int
    reason: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class WebSocketSession(BaseModel):
    """WebSocket session model."""
    id: str
    state: WebSocketState
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_ping: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class WebSocketStats(BaseModel):
    """WebSocket statistics model."""
    total_messages: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    errors: int = 0
    latency: float = 0.0
    uptime: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

class WebSocketConfig(BaseModel):
    """WebSocket configuration model."""
    ping_interval: float = 30.0
    ping_timeout: float = 10.0
    max_message_size: int = 1024 * 1024  # 1MB
    compression: bool = True
    metadata: Optional[Dict[str, Any]] = None

class WebSocketEvent(BaseModel):
    """WebSocket event model."""
    type: str
    data: Any
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class WebSocketRequest(BaseModel):
    """WebSocket request model."""
    type: str
    data: Any
    id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class WebSocketResponse(BaseModel):
    """WebSocket response model."""
    type: str
    data: Any
    request_id: Optional[str] = None
    error: Optional[WebSocketError] = None
    metadata: Optional[Dict[str, Any]] = None

class WebSocketValidation(BaseModel):
    """WebSocket validation model."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    metadata: Optional[Dict[str, Any]] = None

class WebSocketMetrics(BaseModel):
    """WebSocket metrics model."""
    connected_clients: int = 0
    message_rate: float = 0.0
    error_rate: float = 0.0
    average_latency: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

class WebSocketTestSession(BaseModel):
    """WebSocket test session model."""
    id: str
    state: WebSocketState
    messages: List[WebSocketMessage] = []
    errors: List[WebSocketError] = []
    metadata: Optional[Dict[str, Any]] = None

    async def __aenter__(self):
        """Async context manager enter."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

    async def send(self, message: Union[str, bytes, Dict[str, Any]]):
        """Send a message through the test session."""
        if isinstance(message, (str, bytes)):
            msg_type = WebSocketMessageType.TEXT if isinstance(message, str) else WebSocketMessageType.BINARY
            msg = WebSocketMessage(
                id=f"msg_{len(self.messages)}",
                type=msg_type,
                data=message,
            )
        else:
            msg = WebSocketMessage(
                id=f"msg_{len(self.messages)}",
                type=WebSocketMessageType.TEXT,
                data=message,
            )
        self.messages.append(msg)
        return msg

    async def receive(self) -> Optional[WebSocketMessage]:
        """Receive a message from the test session."""
        if self.messages:
            return self.messages.pop(0)
        return None

    async def close(self, code: int = 1000, reason: str = ""):
        """Close the test session."""
        self.state = WebSocketState.CLOSED
        if code != 1000:
            self.errors.append(WebSocketError(code=code, reason=reason))

class WebSocketTestClient(BaseModel):
    """WebSocket test client model."""
    session: WebSocketTestSession
    config: WebSocketConfig = Field(default_factory=lambda: WebSocketConfig())
    metadata: Optional[Dict[str, Any]] = None

    async def connect(self) -> WebSocketTestSession:
        """Connect to a test session."""
        self.session.state = WebSocketState.OPEN
        return self.session

    async def disconnect(self):
        """Disconnect from the test session."""
        await self.session.close()
