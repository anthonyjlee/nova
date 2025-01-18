"""Channel management endpoints for persistent spaces with settings, members, and pinned content.

These endpoints handle:
- Channel metadata and settings
- Member management 
- Pinned content
- WebSocket connections
- Real-time state management
- Event handling

For messaging and conversation functionality, use the chat/threads endpoints instead.
"""

from fastapi import (
    APIRouter, Depends, HTTPException, status, 
    WebSocket, WebSocketDisconnect
)
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio
from uuid import uuid4

from ..core.dependencies import get_memory_system
from ..core.auth import get_permission
from ..core.auth import verify_token
from ..core.error_handling import ServiceError
from ..core.channel_types import (
    ChannelDetails, ChannelMember, PinnedItem, ChannelSettings,
    ChannelState, ChannelSubscription, ChannelEventType, ChannelEvent,
    ChannelType, ChannelStatus, ChannelRole
)
from ..core.websocket_types import (
    WebSocketState, WebSocketError, WebSocketSession,
    WebSocketConfig, WebSocketEvent, WebSocketMessageType
)
from ..core.models import AgentInfo, AgentMetrics, AgentInteraction
from nia.core.types.memory_types import Memory, MemoryType

channel_router = APIRouter(
    prefix="/api/channels",
    tags=["Channels"]
)

# Store active WebSocket connections
active_connections: Dict[str, Dict[str, Any]] = {}  # connection_id -> {session, websocket}
# Store channel subscriptions
channel_subscriptions: Dict[str, List[str]] = {}  # channel_id -> [connection_id]
# Store channel states
channel_states: Dict[str, ChannelState] = {}

@channel_router.websocket("/{channel_id}/ws")
async def channel_websocket(
    websocket: WebSocket,
    channel_id: str,
    token: str,
    memory_system: Any = Depends(get_memory_system)
):
    """WebSocket endpoint for channel connections."""
    connection_id = str(uuid4())
    try:
        # Verify token and create session
        try:
            # Verify token returns the normalized token string
            normalized_token = await verify_token(token)
            
            # Accept connection
            await websocket.accept()
            
            # Create session with default values since we only have the token
            session = WebSocketSession(
                id=connection_id,
                state=WebSocketState.NOT_AUTHENTICATED,
                client_id=normalized_token,  # Use token as client ID for now
                workspace="default",
                domain="default"
            )
        except Exception as e:
            await websocket.close(code=4000)
            return
            
        # Store both session and websocket
        active_connections[connection_id] = {
            "session": session,
            "websocket": websocket
        }
        
        # Initialize channel state if needed
        if channel_id not in channel_states:
            channel_states[channel_id] = ChannelState(
                channel_id=channel_id,
                status=ChannelStatus.ACTIVE,
                connection_state="connected"
            )
        
        # Add to channel subscriptions
        if channel_id not in channel_subscriptions:
            channel_subscriptions[channel_id] = []
        channel_subscriptions[channel_id].append(connection_id)
        
        # Update session state
        session.state = WebSocketState.AUTHENTICATED
        session.subscribed_channels.append(channel_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "connection_id": connection_id,
                "channel_id": channel_id,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Listen for messages
        try:
            while True:
                data = await websocket.receive_json()
                await handle_channel_message(websocket, data, session, channel_id, memory_system)
        except WebSocketDisconnect:
            # Clean up on disconnect
            await handle_disconnect(connection_id, channel_id)
            
    except Exception as e:
        # Handle errors
        if connection_id in active_connections:
            await handle_disconnect(connection_id, channel_id)
        await websocket.close(code=1011)

async def handle_channel_message(
    websocket: WebSocket,
    data: Dict[str, Any],
    session: WebSocketSession,
    channel_id: str,
    memory_system: Any
):
    """Handle incoming channel WebSocket messages."""
    try:
        msg_type = data.get("type")
        
        if msg_type == "ping":
            await websocket.send_json({"type": "pong"})
            return
            
        # Create channel event
        event = ChannelEvent(
            id=str(uuid4()),
            channel_id=channel_id,
            event_type=ChannelEventType(msg_type),
            actor_id=session.client_id,
            data=data.get("data", {})
        )
        
        # Store event
        await memory_system.store_experience(Memory(
            id=event.id,
            type="channel_event",
            content=event.dict(),
            metadata={
                "channel_id": channel_id,
                "event_type": msg_type
            }
        ))
        
        # Broadcast to channel subscribers
        await broadcast_channel_event(channel_id, event)
        
    except Exception as e:
        error = WebSocketError(
            type="error",
            code=1011,
            message=str(e),
            error_type="message_handling_error"
        )
        await websocket.send_json(error.dict())

async def broadcast_channel_event(channel_id: str, event: ChannelEvent):
    """Broadcast event to all channel subscribers."""
    if channel_id not in channel_subscriptions:
        return
        
    for conn_id in channel_subscriptions[channel_id]:
        if conn_id in active_connections:
            connection = active_connections[conn_id]
            try:
                websocket = connection["websocket"]
                await websocket.send_json(event.dict())
            except:
                continue

async def handle_disconnect(connection_id: str, channel_id: str):
    """Handle WebSocket disconnection."""
    if connection_id in active_connections:
        del active_connections[connection_id]
        
    if channel_id in channel_subscriptions:
        if connection_id in channel_subscriptions[channel_id]:
            channel_subscriptions[channel_id].remove(connection_id)
            
        # Update channel state if no more connections
        if not channel_subscriptions[channel_id]:
            if channel_id in channel_states:
                channel_states[channel_id].connection_state = "disconnected"

@channel_router.get("/graph/concepts", response_model=Dict[str, Any], dependencies=[Depends(get_permission("read"))])
async def get_graph_concepts(
    memory_system: Any = Depends(get_memory_system)
) -> JSONResponse:
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

@channel_router.get("/{channel_id}/details", response_model=ChannelDetails, dependencies=[Depends(get_permission("read"))])
async def get_channel_details(
    channel_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> JSONResponse:
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
        
        # Create ChannelDetails instance with required fields
        channel_details = ChannelDetails(
            id=channel_data['id'],
            name=channel_data['name'],
            type=ChannelType(channel_data.get('type', 'channel')),
            status=ChannelStatus.ACTIVE,
            created_by=channel_data.get('created_by', 'system'),
            settings=ChannelSettings(
                name=channel_data['name'],
                type=ChannelType(channel_data.get('type', 'channel')),
                description=channel_data.get('description'),
                is_public=channel_data.get('is_public', True)
            ),
            description=channel_data.get('description'),
            created_at=channel_data['created_at'],
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

@channel_router.get("/{channel_id}/members", response_model=List[ChannelMember], dependencies=[Depends(get_permission("read"))])
async def get_channel_members(
    channel_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> JSONResponse:
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
            
            # Create ChannelMember instance with required fields
            member = ChannelMember(
                user_id=member_data['id'],
                role=ChannelRole(member_data.get('role', 'member')),
                permissions=[],  # Initialize empty permissions list
                joined_at=member_data['joined_at'],
                metadata=metadata
            )
            member_list.append(member)
        
        return JSONResponse(
            content=[m.dict() for m in member_list],
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        raise ServiceError(str(e))

@channel_router.get("/{channel_id}/pinned", response_model=List[PinnedItem], dependencies=[Depends(get_permission("read"))])
async def get_pinned_items(
    channel_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> JSONResponse:
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

@channel_router.post("/{channel_id}/settings", response_model=ChannelSettings, dependencies=[Depends(get_permission("write"))])
async def update_channel_settings(
    channel_id: str,
    settings: ChannelSettings,
    memory_system: Any = Depends(get_memory_system)
) -> JSONResponse:
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

@channel_router.get("/{channel_id}/state", response_model=ChannelState, dependencies=[Depends(get_permission("read"))])
async def get_channel_state(
    channel_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> JSONResponse:
    """Get current state of a channel."""
    try:
        if channel_id not in channel_states:
            channel_states[channel_id] = ChannelState(
                channel_id=channel_id,
                status=ChannelStatus.ACTIVE,
                connection_state="disconnected"
            )
            
        return JSONResponse(
            content=channel_states[channel_id].dict(),
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        raise ServiceError(str(e))

@channel_router.get("/{channel_id}/subscriptions", response_model=List[ChannelSubscription], dependencies=[Depends(get_permission("read"))])
async def get_channel_subscriptions(
    channel_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> JSONResponse:
    """Get list of subscriptions for a channel."""
    try:
        # Get subscriptions from memory
        subscriptions = await memory_system.episodic.search(
            filter={
                "type": "channel_subscription",
                "channel_id": channel_id
            },
            limit=100,
            sort=[("created_at", "desc")]
        )
        
        return JSONResponse(
            content=[ChannelSubscription(**sub).dict() for sub in subscriptions],
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        raise ServiceError(str(e))

@channel_router.post("/{channel_id}/subscribe", response_model=ChannelSubscription, dependencies=[Depends(get_permission("write"))])
async def subscribe_to_channel(
    channel_id: str,
    subscription_type: str,
    memory_system: Any = Depends(get_memory_system)
) -> JSONResponse:
    """Subscribe to a channel."""
    try:
        subscription = ChannelSubscription(
            id=str(uuid4()),
            channel_id=channel_id,
            subscriber_id=str(uuid4()),  # TODO: Get from auth
            state="active",
            subscription_type=subscription_type
        )
        
        # Store subscription
        await memory_system.store_experience(Memory(
            id=subscription.id,
            type="channel_subscription",
            content=subscription.dict(),
            metadata={
                "channel_id": channel_id,
                "subscription_type": subscription_type
            }
        ))
        
        return JSONResponse(
            content=subscription.dict(),
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/details", response_model=AgentInfo, dependencies=[Depends(get_permission("read"))])
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

@agent_router.get("/{agent_id}/metrics", response_model=AgentMetrics, dependencies=[Depends(get_permission("read"))])
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

@agent_router.get("/{agent_id}/interactions", response_model=List[AgentInteraction], dependencies=[Depends(get_permission("read"))])
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
