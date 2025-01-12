"""Channel and DM-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from datetime import datetime

from .dependencies import get_memory_system
from .auth import get_permission
from .error_handling import ServiceError
from .models import (
    ChannelDetails, ChannelMember, PinnedItem, ChannelSettings,
    AgentMetrics, AgentInteraction, AgentInfo
)
from nia.core.types.memory_types import Memory, MemoryType

channel_router = APIRouter(
    prefix="/api/channels",
    tags=["Channels"],
    dependencies=[Depends(get_permission("write"))]
)

agent_router = APIRouter(
    prefix="/api/agents",
    tags=["Agents"],
    dependencies=[Depends(get_permission("write"))]
)

@channel_router.get("/{channel_id}/details", response_model=ChannelDetails)
async def get_channel_details(
    channel_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> ChannelDetails:
    """Get detailed information about a channel."""
    try:
        # Query channel from semantic layer
        channel = await memory_system.semantic.run_query(
            """
            MATCH (c:Concept {id: $channel_id, type: 'channel'})
            RETURN c
            """,
            {"channel_id": channel_id}
        )
        
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel {channel_id} not found"
            )
            
        return ChannelDetails(**channel[0])
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@channel_router.get("/{channel_id}/members", response_model=List[ChannelMember])
async def get_channel_members(
    channel_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> List[ChannelMember]:
    """Get list of members in a channel."""
    try:
        # Query members from semantic layer
        members = await memory_system.semantic.run_query(
            """
            MATCH (c:Concept {id: $channel_id, type: 'channel'})
            MATCH (c)-[:HAS_MEMBER]->(m:Concept)
            RETURN m
            """,
            {"channel_id": channel_id}
        )
        
        return [ChannelMember(**m) for m in members]
    except Exception as e:
        raise ServiceError(str(e))

@channel_router.get("/{channel_id}/pinned", response_model=List[PinnedItem])
async def get_pinned_items(
    channel_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> List[PinnedItem]:
    """Get pinned items in a channel."""
    try:
        # Get pinned items from episodic memory
        pinned = await memory_system.episodic.search(
            filter={
                "type": "pinned_item",
                "channel_id": channel_id
            },
            limit=100
        )
        
        return [PinnedItem(**item) for item in pinned]
    except Exception as e:
        raise ServiceError(str(e))

@channel_router.post("/{channel_id}/settings", response_model=ChannelSettings)
async def update_channel_settings(
    channel_id: str,
    settings: ChannelSettings,
    memory_system: Any = Depends(get_memory_system)
) -> ChannelSettings:
    """Update channel settings."""
    try:
        # Update settings in semantic layer
        await memory_system.semantic.run_query(
            """
            MATCH (c:Concept {id: $channel_id, type: 'channel'})
            SET c.settings = $settings
            """,
            {
                "channel_id": channel_id,
                "settings": settings.dict()
            }
        )
        
        return settings
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/details", response_model=AgentInfo)
async def get_agent_details(
    agent_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> AgentInfo:
    """Get detailed information about an agent."""
    try:
        # Query agent from semantic layer
        agent = await memory_system.semantic.run_query(
            """
            MATCH (a:Concept {id: $agent_id, type: 'agent'})
            RETURN a
            """,
            {"agent_id": agent_id}
        )
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
            
        return AgentInfo(**agent[0])
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/metrics", response_model=AgentMetrics)
async def get_agent_metrics(
    agent_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> AgentMetrics:
    """Get performance metrics for an agent."""
    try:
        # Get metrics from episodic memory
        metrics = await memory_system.episodic.search(
            filter={
                "type": "agent_metrics",
                "agent_id": agent_id
            },
            limit=1,
            sort=[("timestamp", "desc")]
        )
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No metrics found for agent {agent_id}"
            )
            
        return AgentMetrics(**metrics[0])
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/interactions", response_model=List[AgentInteraction])
async def get_agent_interactions(
    agent_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> List[AgentInteraction]:
    """Get recent interactions for an agent."""
    try:
        # Get interactions from episodic memory
        interactions = await memory_system.episodic.search(
            filter={
                "type": "agent_interaction",
                "agent_id": agent_id
            },
            limit=100,
            sort=[("timestamp", "desc")]
        )
        
        return [AgentInteraction(**interaction) for interaction in interactions]
    except Exception as e:
        raise ServiceError(str(e))
