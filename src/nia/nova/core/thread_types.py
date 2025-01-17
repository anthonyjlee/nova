"""Thread types and models for Nova."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

class ThreadState(str, Enum):
    """Thread state enum."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    CLOSED = "closed"
    LOCKED = "locked"
    PENDING = "pending"

class MessageType(str, Enum):
    """Message type enum."""
    TEXT = "text"
    SYSTEM = "system"
    ACTION = "action"
    NOTIFICATION = "notification"
    ERROR = "error"

class Message(BaseModel):
    """Message model."""
    id: str
    thread_id: str
    content: str
    type: MessageType = MessageType.TEXT
    sender: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class Thread(BaseModel):
    """Thread model."""
    id: str
    title: str
    creator: str
    state: ThreadState = ThreadState.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class ThreadRequest(BaseModel):
    """Thread request model."""
    title: str
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ThreadResponse(BaseModel):
    """Thread response model."""
    thread: Thread
    message: Optional[Message] = None
    metadata: Optional[Dict[str, Any]] = None

class MessageRequest(BaseModel):
    """Message request model."""
    thread_id: str
    content: str
    type: MessageType = MessageType.TEXT
    metadata: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    """Message response model."""
    message: Message
    thread: Thread
    metadata: Optional[Dict[str, Any]] = None

class ThreadListResponse(BaseModel):
    """Thread list response model."""
    threads: List[Thread]
    total_count: int
    page_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class ThreadParticipant(BaseModel):
    """Thread participant model."""
    thread_id: str
    user_id: str
    role: str
    joined_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class ThreadActivity(BaseModel):
    """Thread activity model."""
    thread_id: str
    activity_type: str
    actor: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class ThreadMetrics(BaseModel):
    """Thread metrics model."""
    thread_id: str
    message_count: int = 0
    participant_count: int = 0
    last_activity: str = Field(default_factory=lambda: datetime.now().isoformat())
    average_response_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

class ThreadSettings(BaseModel):
    """Thread settings model."""
    thread_id: str
    is_public: bool = True
    allow_reactions: bool = True
    allow_edits: bool = True
    retention_days: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class ThreadNotification(BaseModel):
    """Thread notification model."""
    thread_id: str
    user_id: str
    type: str
    content: str
    read: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class ThreadSearch(BaseModel):
    """Thread search model."""
    query: str
    filters: Optional[Dict[str, Any]] = None
    sort: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ThreadTag(BaseModel):
    """Thread tag model."""
    thread_id: str
    name: str
    color: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ThreadReaction(BaseModel):
    """Thread reaction model."""
    message_id: str
    user_id: str
    reaction: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class ThreadMention(BaseModel):
    """Thread mention model."""
    message_id: str
    user_id: str
    context: str
    resolved: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class ThreadStatus(BaseModel):
    """Thread status model."""
    thread_id: str
    status: str
    last_update: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None
