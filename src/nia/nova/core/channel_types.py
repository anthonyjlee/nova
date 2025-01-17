"""Channel types and models for Nova."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

class ChannelType(str, Enum):
    """Channel type enum."""
    PUBLIC = "public"
    PRIVATE = "private"
    DIRECT = "direct"
    GROUP = "group"
    SYSTEM = "system"

class ChannelStatus(str, Enum):
    """Channel status enum."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    SUSPENDED = "suspended"

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

class ChannelEvent(BaseModel):
    """Channel event model."""
    id: str
    channel_id: str
    event_type: str
    actor_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

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
    errors: List[str] = []
    warnings: List[str] = []
    metadata: Optional[Dict[str, Any]] = None
