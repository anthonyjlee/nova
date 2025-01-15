"""Channel management endpoints for persistent spaces with settings, members, and pinned content.

These endpoints handle the structural aspects of channels like:
- Graph visualization data
- Channel metadata and settings
- Member management 
- Pinned content

For messaging and conversation functionality, use the chat/threads endpoints instead.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
from datetime import datetime
import json

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

@channel_router.options("/{path:path}")
async def channel_options_handler():
    """Handle CORS preflight requests for channel endpoints."""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@channel_router.get("/graph/concepts", response_model=Dict[str, Any])
async def get_graph_concepts(
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Get graph concepts for visualization."""
    try:
        # Query all concepts from semantic layer
        result = await memory_system.semantic.run_query(
            """
            // Get all nodes
            MATCH (c:Concept)
            WITH collect({
                id: toString(id(c)),
                name: c.name,
                type: c.type,
                description: c.description,
                created_at: toString(c.created_at),
                updated_at: toString(c.updated_at),
                metadata: apoc.convert.fromJsonMap(coalesce(c.metadata, '{}'))
            }) as nodes
            // Get all edges
            OPTIONAL MATCH (c1:Concept)-[r]->(c2:Concept)
            WITH nodes, collect({
                id: toString(id(r)),
                source: toString(id(c1)),
                target: toString(id(c2)),
                type: type(r),
                label: type(r)
            }) as edges
            RETURN {nodes: nodes, edges: edges} as result
            """,
            {}
        )
        
        return JSONResponse(
            content={
                "nodes": result[0]["result"]["nodes"],
                "edges": result[0]["result"]["edges"],
                "timestamp": datetime.utcnow().isoformat()
            },
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        raise ServiceError(str(e))

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
            RETURN {
                id: toString(id(c)),
                name: coalesce(c.name, 'Unnamed Channel'),
                description: c.description,
                created_at: datetime(coalesce(c.created_at, datetime())),
                updated_at: datetime(coalesce(c.updated_at, datetime())),
                is_public: coalesce(c.is_public, true),
                workspace: coalesce(c.workspace, 'personal'),
                domain: coalesce(c.domain, 'general'),
                type: coalesce(c.type, 'channel'),
                metadata: apoc.convert.toJson(coalesce(c.metadata, {}))
            } as channel_data
            """,
            {"channel_id": channel_id}
        )
        
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel {channel_id} not found"
            )
            
        channel_data = channel[0]['channel_data']
        # Parse metadata JSON
        metadata = {}
        if isinstance(channel_data.get('metadata'), str):
            try:
                metadata = json.loads(channel_data['metadata'])
            except:
                pass
        
        # Create ChannelDetails instance
        channel_details = ChannelDetails(
            id=channel_data['id'],
            name=channel_data['name'],
            workspace=channel_data['workspace'],
            description=channel_data.get('description'),
            created_at=channel_data['created_at'],  # Already a datetime from Neo4j
            updated_at=channel_data['updated_at'],  # Already a datetime from Neo4j
            is_public=channel_data.get('is_public', True),
            domain=channel_data.get('domain', 'general'),
            type=channel_data.get('type', 'channel'),
            metadata=metadata
        )
        return JSONResponse(
            content=channel_details.dict(),
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
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
            RETURN {
                id: toString(id(m)),
                name: coalesce(m.name, 'Unknown Member'),
                type: coalesce(m.type, 'agent'),
                role: 'member',
                status: coalesce(m.status, 'active'),
                joined_at: datetime(),
                metadata: apoc.convert.toJson(coalesce(m.metadata, {}))
            } as member_data
            """,
            {"channel_id": channel_id}
        )
        
        member_list = []
        for m in members:
            member_data = m['member_data']
            # Parse metadata JSON
            metadata = {}
            if isinstance(member_data.get('metadata'), str):
                try:
                    metadata = json.loads(member_data['metadata'])
                except:
                    pass
            
            # Create ChannelMember instance
            member = ChannelMember(
                id=member_data['id'],
                name=member_data['name'],
                type=member_data['type'],
                role=member_data['role'],
                status=member_data['status'],
                joined_at=member_data['joined_at'],
                metadata=metadata
            )
            member_list.append(member)
        
        return JSONResponse(
            content=member_list,
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
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
        
        return JSONResponse(
            content=[PinnedItem(**item).dict() for item in pinned],
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
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
        
        return JSONResponse(
            content=settings.dict(),
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
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
