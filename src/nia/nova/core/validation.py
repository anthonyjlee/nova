"""Validation schemas for WebSocket messages."""

from typing import Dict, Any, Optional, Literal, Set, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class ValidationResult(BaseModel):
    """Result of a validation operation."""
    is_valid: bool
    issues: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    validations: List[Dict[str, Any]] = []
    confidence: float = 0.0

class ValidationPattern(BaseModel):
    """Base validation pattern."""
    type: str
    description: str
    severity: str = "low"
    first_seen: str
    last_seen: str
    metadata: Dict[str, Any] = {}

class ValidationTracker:
    """Track validation patterns over time."""
    def __init__(self):
        self.patterns: List[Dict[str, Any]] = []
        
    def add_issue(self, pattern: Dict[str, Any]):
        """Add a validation issue pattern."""
        self.patterns.append(pattern)
        
    def get_patterns(self) -> List[Dict[str, Any]]:
        """Get all tracked patterns."""
        return self.patterns
        
    def get_critical_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns marked as critical/high severity."""
        return [p for p in self.patterns if p.get("severity") == "high"]

class ChannelType(str, Enum):
    """Channel types for access control."""
    CORE = "core"
    SUPPORT = "support"

class ClientRole(str, Enum):
    """Client roles for access control."""
    ADMIN = "admin"
    AGENT = "agent"
    SUPPORT = "support"
    USER = "user"

class DomainType(str, Enum):
    """Domain types for boundary validation."""
    COGNITIVE = "cognitive"
    SYSTEM = "system"
    TASK = "task"
    MEMORY = "memory"

class BaseMessage(BaseModel):
    """Base model for all WebSocket messages."""
    type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    client_id: str
    channel: Optional[str] = None
    domain: Optional[DomainType] = None

    @validator('channel')
    def validate_channel(cls, v):
        if v and v not in {"NovaTeam", "NovaSupport"}:
            raise ValueError(f"Invalid channel: {v}")
        return v

    class Config:
        validate_assignment = True
        extra = "forbid"

class ChatMessage(BaseMessage):
    """Chat message model."""
    type: Literal["chat_message"]
    data: Dict[str, Any] = Field(..., description="Message content and metadata")
    thread_id: str
    sender_id: str
    domain: Optional[DomainType] = Field(default=None)  # Override with optional

class TaskUpdate(BaseMessage):
    """Task update model."""
    type: Literal["task_update"]
    data: Dict[str, Any] = Field(..., description="Task state and metadata")
    task_id: str
    status: str
    domain: DomainType = Field(default=DomainType.TASK)  # Override with default

class AgentStatus(BaseMessage):
    """Agent status update model."""
    type: Literal["agent_status"]
    data: Dict[str, Any] = Field(..., description="Agent state and metadata")
    agent_id: str
    status: str
    domain: DomainType = Field(default=DomainType.SYSTEM)  # Override with default

class GraphUpdate(BaseMessage):
    """Knowledge graph update model."""
    type: Literal["graph_update"]
    data: Dict[str, Any] = Field(..., description="Graph changes and metadata")
    nodes: Optional[list] = None
    edges: Optional[list] = None
    domain: DomainType = Field(default=DomainType.MEMORY)  # Override with default

class MemoryUpdate(BaseMessage):
    """Memory system update model."""
    type: Literal["memory_update"]
    data: Dict[str, Any] = Field(..., description="Memory data including id, content, metadata")
    memory_type: str = Field(..., description="Type of memory update (e.g. memory_stored, memory_retrieved)")
    layer: str = Field(..., description="Memory layer (episodic/semantic)")
    domain: DomainType = Field(default=DomainType.MEMORY)  # Override with default

class LLMStreamData(BaseModel):
    """LLM stream data model."""
    stream_id: str = Field(..., description="Unique identifier for this stream")
    chunk: str = Field(..., description="Text chunk from LLM")
    is_final: bool = Field(default=False, description="Indicates if this is the final chunk")
    template_id: str = Field(..., description="ID of template used for generation")

    @validator('chunk')
    def validate_chunk(cls, v):
        if not v:
            raise ValueError("Chunk cannot be empty")
        return v

class LLMStream(BaseMessage):
    """LLM stream message model."""
    type: Literal["llm_stream"]
    data: LLMStreamData = Field(..., description="LLM stream data")
    domain: DomainType = Field(default=DomainType.COGNITIVE)  # Override with default

# Channel access configuration
CHANNEL_ACCESS = {
    "NovaTeam": {
        "type": ChannelType.CORE,
        "allowed_roles": {ClientRole.ADMIN, ClientRole.AGENT},
        "allowed_domains": {DomainType.COGNITIVE, DomainType.TASK}
    },
    "NovaSupport": {
        "type": ChannelType.SUPPORT,
        "allowed_roles": {ClientRole.ADMIN, ClientRole.SUPPORT},
        "allowed_domains": {DomainType.SYSTEM, DomainType.MEMORY}
    }
}

# Client role cache (in practice, this would be backed by a database)
CLIENT_ROLES: Dict[str, Set[ClientRole]] = {}

def validate_message(message_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate WebSocket message based on type."""
    validators = {
        "chat_message": ChatMessage,
        "task_update": TaskUpdate,
        "agent_status": AgentStatus,
        "graph_update": GraphUpdate,
        "llm_stream": LLMStream,
        "memory_update": MemoryUpdate
    }
    
    if message_type not in validators:
        raise ValueError(f"Unknown message type: {message_type}")
        
    validator = validators[message_type]
    validated = validator(**data)
    return validated.dict()

def validate_channel_access(client_id: str, channel: str) -> bool:
    """Validate client's access to a channel."""
    if channel not in CHANNEL_ACCESS:
        return False
        
    # Get client roles (in practice, fetch from database)
    client_roles = CLIENT_ROLES.get(client_id, {ClientRole.USER})
    
    # Check if client has any allowed roles for channel
    channel_roles = CHANNEL_ACCESS[channel]["allowed_roles"]
    return bool(client_roles & channel_roles)

def validate_domain_boundaries(message: Dict[str, Any]) -> bool:
    """Validate message against domain boundaries."""
    # Skip validation if no channel specified
    if not message.get("channel"):
        return True
        
    channel = message["channel"]
    if channel not in CHANNEL_ACCESS:
        return False
        
    # Skip validation if no domain specified
    if not message.get("domain"):
        return True
        
    try:
        domain = DomainType(message["domain"])
    except ValueError:
        return False
        
    # Check if domain is allowed in channel
    allowed_domains = CHANNEL_ACCESS[channel]["allowed_domains"]
    return domain in allowed_domains

def register_client_role(client_id: str, role: ClientRole):
    """Register a client's role."""
    if client_id not in CLIENT_ROLES:
        CLIENT_ROLES[client_id] = set()
    CLIENT_ROLES[client_id].add(role)

def remove_client_role(client_id: str, role: ClientRole):
    """Remove a client's role."""
    if client_id in CLIENT_ROLES:
        CLIENT_ROLES[client_id].discard(role)
        if not CLIENT_ROLES[client_id]:
            del CLIENT_ROLES[client_id]

def get_client_roles(client_id: str) -> Set[ClientRole]:
    """Get all roles for a client."""
    return CLIENT_ROLES.get(client_id, {ClientRole.USER})
