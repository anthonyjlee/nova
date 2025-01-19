"""Channel management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from ..endpoints.auth import validate_api_key as get_current_user
from ..core.dependencies import get_memory_system

channel_router = APIRouter(
    prefix="",
    tags=["Channels"]
)

# Models
class ChannelDetails(BaseModel):
    """Channel details model."""
    id: str
    name: str
    description: Optional[str] = None
    type: str
    created_at: datetime
    updated_at: datetime
    workspace: str
    domain: Optional[str] = None
    is_public: bool
    metadata: dict = {}

class ChannelMember(BaseModel):
    """Channel member model."""
    id: str
    name: str
    type: str  # "user" or "agent"
    role: str
    status: str
    joined_at: datetime
    metadata: dict = {}

class PinnedItem(BaseModel):
    """Pinned item model."""
    id: str
    type: str
    content: str
    metadata: dict = {}
    pinned_by: str
    pinned_at: datetime

class ChannelSettings(BaseModel):
    """Channel settings model."""
    notification_preferences: dict = {}
    privacy_settings: dict = {}
    message_retention: dict = {}
    metadata: dict = {}

# Endpoints
@channel_router.get("", response_model=List[ChannelDetails])
async def list_channels(
    current_user = Depends(get_current_user),
    memory = Depends(get_memory_system)
):
    """Get list of available channels."""
    try:
        # Get channels from memory system
        channels = await memory.get_channels()
        if not channels:
            return []
            
        # Filter out private channels user doesn't have access to
        accessible_channels = []
        for channel in channels:
            if channel.is_public or await memory.check_channel_access(current_user.id, channel.id):
                accessible_channels.append(channel)
                
        return accessible_channels
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@channel_router.get("/{channel_id}/details", response_model=ChannelDetails)
async def get_channel_details(
    channel_id: str,
    current_user = Depends(get_current_user),
    memory = Depends(get_memory_system)
):
    """Get detailed channel information."""
    try:
        # Get channel details from memory system
        channel = await memory.get_channel(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
            
        # Check access permissions
        if not channel.is_public and not await memory.check_channel_access(current_user.id, channel_id):
            raise HTTPException(status_code=403, detail="Access denied")
            
        return channel
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@channel_router.get("/{channel_id}/members", response_model=List[ChannelMember])
async def get_channel_members(
    channel_id: str,
    current_user = Depends(get_current_user),
    memory = Depends(get_memory_system)
):
    """Get list of channel members."""
    try:
        # Check channel exists and user has access
        channel = await memory.get_channel(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
            
        if not channel.is_public and not await memory.check_channel_access(current_user.id, channel_id):
            raise HTTPException(status_code=403, detail="Access denied")
            
        # Get member list
        members = await memory.get_channel_members(channel_id)
        return members
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@channel_router.get("/{channel_id}/pinned", response_model=List[PinnedItem])
async def get_pinned_items(
    channel_id: str,
    current_user = Depends(get_current_user),
    memory = Depends(get_memory_system)
):
    """Get pinned items in channel."""
    try:
        # Check channel exists and user has access
        channel = await memory.get_channel(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
            
        if not channel.is_public and not await memory.check_channel_access(current_user.id, channel_id):
            raise HTTPException(status_code=403, detail="Access denied")
            
        # Get pinned items
        pinned = await memory.get_channel_pinned(channel_id)
        return pinned
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@channel_router.post("/{channel_id}/settings", response_model=ChannelSettings)
async def update_channel_settings(
    channel_id: str,
    settings: ChannelSettings,
    current_user = Depends(get_current_user),
    memory = Depends(get_memory_system)
):
    """Update channel settings."""
    try:
        # Check channel exists and user has admin access
        channel = await memory.get_channel(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
            
        if not await memory.check_channel_admin(current_user.id, channel_id):
            raise HTTPException(status_code=403, detail="Admin access required")
            
        # Update settings
        updated = await memory.update_channel_settings(channel_id, settings.dict())
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
