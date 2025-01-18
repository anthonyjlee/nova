"""WebSocket types and models for Nova."""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union, Literal
from datetime import datetime
from enum import Enum

class WebSocketState(str, Enum):
    """WebSocket connection state enum."""
    NOT_AUTHENTICATED = "not_authenticated"
    AUTHENTICATED = "authenticated"
    ERROR = "error"
    RECONNECTING = "reconnecting"
    CONNECTING = "connecting"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"

class WebSocketMessageType(str, Enum):
    """WebSocket message type enum."""
    AUTH = "auth"
    CHAT_MESSAGE = "chat_message"
    TASK_UPDATE = "task_update"
    AGENT_STATUS = "agent_status"
    GRAPH_UPDATE = "graph_update"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    CLOSE = "close"
    TEXT = "text"
    BINARY = "binary"

class WebSocketCloseCode(int, Enum):
    """WebSocket close code enum."""
    NORMAL = 1000
    SERVER_ERROR = 1011
    AUTH_ERROR = 4000
    RATE_LIMIT = 4001
    INVALID_FORMAT = 4002
    PROTOCOL_VIOLATION = 4003

class BaseWebSocketMessage(BaseModel):
    """Base WebSocket message model."""
    type: WebSocketMessageType
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    client_id: str
    channel: Optional[str] = None
    data: Dict[str, Any]

    @validator('timestamp')
    def validate_timestamp(cls, v):
        """Validate ISO timestamp format."""
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Invalid ISO timestamp format")

class AuthMessage(BaseWebSocketMessage):
    """Authentication message model."""
    type: Literal[WebSocketMessageType.AUTH]
    data: Dict[str, str] = Field(
        default_factory=dict,
        description="Authentication data"
    )

    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "api_key": "valid-test-key",
                    "connection_type": "chat",
                    "domain": "personal",
                    "workspace": "personal"
                }
            }
        }

class ChatMessage(BaseWebSocketMessage):
    """Chat message model."""
    type: Literal[WebSocketMessageType.CHAT_MESSAGE]
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Chat message data"
    )

    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "thread_id": "thread-123",
                    "content": "Hello team",
                    "sender": "user-123"
                }
            }
        }

class TaskUpdateMessage(BaseWebSocketMessage):
    """Task update message model."""
    type: Literal[WebSocketMessageType.TASK_UPDATE]
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Task update data"
    )

    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "task_id": "task-123",
                    "status": "in_progress",
                    "metadata": {"priority": "high"}
                }
            }
        }

class AgentStatusMessage(BaseWebSocketMessage):
    """Agent status message model."""
    type: Literal[WebSocketMessageType.AGENT_STATUS]
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent status data"
    )

    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "agent_id": "agent-123",
                    "status": "active",
                    "metadata": {"task_id": "task-123"}
                }
            }
        }

class GraphUpdateMessage(BaseWebSocketMessage):
    """Graph update message model."""
    type: Literal[WebSocketMessageType.GRAPH_UPDATE]
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Graph update data"
    )

    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "nodes": [{"id": "node-1", "type": "task"}],
                    "edges": [{"from": "node-1", "to": "node-2", "type": "depends_on"}]
                }
            }
        }

class WebSocketError(BaseModel):
    """WebSocket error model."""
    type: Literal["error"]
    code: int
    message: str
    error_type: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "type": "error",
                "code": 403,
                "message": "Invalid API key",
                "error_type": "invalid_key",
                "timestamp": "2025-01-21T10:00:00Z"
            }
        }

class WebSocketSession(BaseModel):
    """WebSocket session model."""
    id: str
    state: WebSocketState
    client_id: str
    workspace: str
    domain: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_ping: Optional[str] = None
    subscribed_channels: List[str] = []
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "session-123",
                "state": "authenticated",
                "client_id": "client-123",
                "workspace": "personal",
                "domain": "personal",
                "created_at": "2025-01-21T10:00:00Z",
                "subscribed_channels": ["nova-team"]
            }
        }

class WebSocketStats(BaseModel):
    """WebSocket statistics model."""
    total_messages: int = 0
    messages_by_type: Dict[WebSocketMessageType, int] = Field(default_factory=dict)
    bytes_sent: int = 0
    bytes_received: int = 0
    errors: Dict[str, int] = Field(default_factory=dict)
    latency: float = 0.0
    uptime: float = 0.0
    active_sessions: int = 0
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "total_messages": 100,
                "messages_by_type": {
                    "chat_message": 50,
                    "task_update": 30,
                    "agent_status": 20
                },
                "bytes_sent": 50000,
                "bytes_received": 40000,
                "errors": {
                    "auth_error": 2,
                    "rate_limit": 1
                },
                "latency": 50.5,
                "uptime": 3600.0,
                "active_sessions": 10
            }
        }

class WebSocketConfig(BaseModel):
    """WebSocket configuration model."""
    ping_interval: float = 30.0
    ping_timeout: float = 10.0
    max_message_size: int = 65536  # 64KB
    max_connections: int = 1000
    auth_timeout: float = 30.0
    subscription_timeout: float = 30.0
    rate_limits: Dict[str, Dict[str, int]] = Field(
        default_factory=lambda: {
            "messages": {"max": 100, "window": 60},
            "subscriptions": {"max": 10, "window": 60}
        }
    )
    compression: bool = True
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "ping_interval": 30.0,
                "ping_timeout": 10.0,
                "max_message_size": 65536,
                "max_connections": 1000,
                "auth_timeout": 30.0,
                "subscription_timeout": 30.0,
                "rate_limits": {
                    "messages": {"max": 100, "window": 60},
                    "subscriptions": {"max": 10, "window": 60}
                },
                "compression": True
            }
        }

class WebSocketEvent(BaseModel):
    """WebSocket event model."""
    type: str
    data: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    source: str
    severity: str = "info"
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "type": "connection_established",
                "data": {
                    "message": "Connection established, waiting for authentication"
                },
                "timestamp": "2025-01-21T10:00:00Z",
                "source": "websocket_server",
                "severity": "info"
            }
        }

class WebSocketRequest(BaseModel):
    """WebSocket request model."""
    type: WebSocketMessageType
    data: Dict[str, Any]
    request_id: str = Field(default_factory=lambda: f"req_{int(datetime.now().timestamp())}")
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "type": "chat_message",
                "data": {
                    "thread_id": "thread-123",
                    "content": "Hello team"
                },
                "request_id": "req_1705831200",
                "metadata": {"priority": "normal"}
            }
        }

class WebSocketResponse(BaseModel):
    """WebSocket response model."""
    type: str
    data: Dict[str, Any]
    request_id: str
    success: bool = True
    error: Optional[WebSocketError] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "type": "message_delivered",
                "data": {
                    "message": "Chat message received and processed",
                    "original_type": "chat_message",
                    "status": "success"
                },
                "request_id": "req_1705831200",
                "success": True
            }
        }

class WebSocketValidation(BaseModel):
    """WebSocket validation model."""
    is_valid: bool
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    validation_type: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "is_valid": False,
                "errors": [{
                    "type": "missing_field",
                    "field": "api_key",
                    "message": "Missing required field: api_key"
                }],
                "warnings": [{
                    "type": "deprecated_field",
                    "field": "old_field",
                    "message": "This field is deprecated"
                }],
                "validation_type": "message_format",
                "timestamp": "2025-01-21T10:00:00Z"
            }
        }

class WebSocketMetrics(BaseModel):
    """WebSocket metrics model."""
    connected_clients: int = 0
    authenticated_clients: int = 0
    message_rate: float = 0.0
    error_rate: float = 0.0
    average_latency: float = 0.0
    channel_stats: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    memory_usage: Dict[str, float] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "connected_clients": 100,
                "authenticated_clients": 95,
                "message_rate": 50.5,
                "error_rate": 0.01,
                "average_latency": 45.2,
                "channel_stats": {
                    "nova-team": {
                        "subscribers": 50,
                        "messages_per_minute": 30
                    }
                },
                "memory_usage": {
                    "sessions": 10.5,
                    "messages": 25.3
                },
                "timestamp": "2025-01-21T10:00:00Z"
            }
        }

class WebSocketTestSession(BaseModel):
    """WebSocket test session model."""
    id: str
    state: WebSocketState
    messages: List[BaseWebSocketMessage] = []
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
            content = message.decode() if isinstance(message, bytes) else message
            msg = BaseWebSocketMessage(
                type=WebSocketMessageType.TEXT if isinstance(message, str) else WebSocketMessageType.BINARY,
                client_id=self.id,
                data={"content": content}
            )
        elif isinstance(message, (bytearray, memoryview)):
            content = bytes(message).decode()
            msg = BaseWebSocketMessage(
                type=WebSocketMessageType.BINARY,
                client_id=self.id,
                data={"content": content}
            )
        else:
            msg = BaseWebSocketMessage(
                type=WebSocketMessageType.TEXT,
                client_id=self.id,
                data=dict(message)
            )
        self.messages.append(msg)
        return msg

    async def receive(self) -> Optional[BaseWebSocketMessage]:
        """Receive a message from the test session."""
        if self.messages:
            return self.messages.pop(0)
        return None

    async def close(self, code: int = 1000, reason: str = ""):
        """Close the test session."""
        self.state = WebSocketState.CLOSED
        if code != 1000:
            self.errors.append(WebSocketError(
                type="error",
                code=code,
                message=reason,
                error_type="close_error"
            ))

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
