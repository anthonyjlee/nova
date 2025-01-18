"""Channel types and models for Nova."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

class ChannelType(str, Enum):
    """Channel type enum."""
    PUBLIC = "public"          # Visible to all users
    PRIVATE = "private"        # Visible only to members
    DIRECT = "direct"          # One-to-one communication
    GROUP = "group"            # Group communication
    SYSTEM = "system"          # System notifications
    AGENT = "agent"            # Agent communication
    DEBUG = "debug"            # Debug channel
    BROADCAST = "broadcast"    # Broadcast messages

class ChannelStatus(str, Enum):
    """Channel status enum."""
    ACTIVE = "active"          # Channel is active and available
    ARCHIVED = "archived"      # Channel is archived but readable
    DELETED = "deleted"        # Channel is marked for deletion
    SUSPENDED = "suspended"    # Channel is temporarily disabled
    CONNECTING = "connecting"  # Channel is establishing connection
    ERROR = "error"           # Channel is in error state
    RECONNECTING = "reconnecting"  # Channel is attempting to reconnect

class ChannelRole(str, Enum):
    """Channel role enum."""
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"
    GUEST = "guest"

class ChannelPermission(str, Enum):
    """Channel permission enum."""
    READ = "read"
    WRITE = "write"
    MANAGE = "manage"
    DELETE = "delete"
    INVITE = "invite"
    KICK = "kick"
    BAN = "ban"

class ChannelMember(BaseModel):
    """Channel member model."""
    user_id: str
    role: ChannelRole
    permissions: List[ChannelPermission] = []
    joined_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_read: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChannelMessage(BaseModel):
    """Channel message model."""
    id: str
    channel_id: str
    sender_id: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    edited: bool = False
    edited_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChannelEventType(str, Enum):
    """Channel event type enum."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    MESSAGE_SENT = "message_sent"
    MESSAGE_UPDATED = "message_updated"
    MESSAGE_DELETED = "message_deleted"
    CONNECTION_STATE = "connection_state"
    SUBSCRIPTION_STATE = "subscription_state"
    ERROR = "error"

class ChannelEvent(BaseModel):
    """Channel event model."""
    id: str
    channel_id: str
    event_type: ChannelEventType
    actor_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "evt_123",
                "channel_id": "ch_123",
                "event_type": "message_sent",
                "actor_id": "user_123",
                "timestamp": "2025-01-21T10:00:00Z",
                "data": {
                    "message_id": "msg_123",
                    "content": "Hello channel!"
                }
            }
        }

class ChannelSettings(BaseModel):
    """Channel settings model."""
    name: str
    description: Optional[str] = None
    type: ChannelType
    is_public: bool = True
    allow_threads: bool = True
    allow_reactions: bool = True
    allow_files: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    retention_days: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class ChannelDetails(BaseModel):
    """Channel details model."""
    id: str
    name: str
    description: Optional[str] = None
    type: ChannelType
    status: ChannelStatus
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    created_by: str
    settings: ChannelSettings
    metadata: Optional[Dict[str, Any]] = None

class PinnedItem(BaseModel):
    """Pinned item model."""
    id: str
    channel_id: str
    item_type: str
    item_id: str
    pinned_by: str
    pinned_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class ChannelInvite(BaseModel):
    """Channel invite model."""
    id: str
    channel_id: str
    inviter_id: str
    invitee_id: str
    role: ChannelRole
    expires_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChannelBan(BaseModel):
    """Channel ban model."""
    id: str
    channel_id: str
    user_id: str
    banned_by: str
    reason: str
    expires_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChannelMetrics(BaseModel):
    """Channel metrics model."""
    channel_id: str
    member_count: int = 0
    message_count: int = 0
    thread_count: int = 0
    file_count: int = 0
    last_activity: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class ChannelNotification(BaseModel):
    """Channel notification model."""
    id: str
    channel_id: str
    user_id: str
    type: str
    content: str
    read: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class ChannelReaction(BaseModel):
    """Channel reaction model."""
    id: str
    channel_id: str
    message_id: str
    user_id: str
    reaction: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class ChannelMention(BaseModel):
    """Channel mention model."""
    id: str
    channel_id: str
    message_id: str
    user_id: str
    context: str
    resolved: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class ChannelFile(BaseModel):
    """Channel file model."""
    id: str
    channel_id: str
    name: str
    size: int
    mime_type: str
    url: str
    uploaded_by: str
    uploaded_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class ChannelSearch(BaseModel):
    """Channel search model."""
    query: str
    filters: Optional[Dict[str, Any]] = None
    sort: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ChannelValidation(BaseModel):
    """Channel validation model."""
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
                    "type": "invalid_permission",
                    "field": "role",
                    "message": "User does not have required role"
                }],
                "warnings": [{
                    "type": "rate_limit",
                    "message": "Approaching rate limit"
                }],
                "validation_type": "permission_check",
                "timestamp": "2025-01-21T10:00:00Z"
            }
        }
class ChannelSubscription(BaseModel):
    """Channel subscription model."""
    id: str
    channel_id: str
    subscriber_id: str
    state: str  # active, pending, paused
    subscription_type: str  # all, mentions, none
    last_read_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "sub_123",
                "channel_id": "ch_123",
                "subscriber_id": "user_123",
                "state": "active",
                "subscription_type": "all",
                "last_read_at": "2025-01-21T09:45:00Z",
                "created_at": "2025-01-21T09:00:00Z"
            }
        }

class ChannelState(BaseModel):
    """Channel state model."""
    channel_id: str
    status: ChannelStatus
    connection_state: str  # connected, disconnected, error
    last_event_id: Optional[str] = None
    last_sync_at: Optional[str] = None
    active_members: List[str] = []
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "channel_id": "ch_123",
                "status": "active",
                "connection_state": "connected",
                "last_event_id": "evt_456",
                "last_sync_at": "2025-01-21T10:00:00Z",
                "active_members": ["user_123", "user_456"]
            }
        }
