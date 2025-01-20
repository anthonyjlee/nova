"""Nova API endpoints."""

from fastapi import APIRouter, WebSocket, Depends, HTTPException, WebSocketDisconnect, Request
from typing import Dict, Any, Optional, List
import logging
import asyncio
import json
import uuid
from datetime import datetime, timezone
import traceback

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from nia.core.types.memory_types import EpisodicMemory
from nia.core.auth import validate_api_key, check_rate_limit, get_permission
from nia.core.websocket import NovaWebSocket
from nia.core.dependencies import (
    get_memory_system,
    get_meta_agent,
    get_tiny_factory,
    get_analytics_agent,
    get_graph_store,
    get_agent_store,
    get_thread_manager
)
from nia.core.error_handling import (
    NovaError,
    ValidationError,
    ResourceNotFoundError,
    ServiceError
)
from nia.core.models import (
    ThreadRequest,
    ThreadResponse,
    MessageRequest,
    Message,
    MessageResponse,
    ThreadListResponse,
    StatusResponse
)

# Constants
API_KEYS = ["development"]  # For testing only

# Create Nova router
nova_router = APIRouter()

# Export routers
__all__ = ['nova_router']

# Create routers with dependencies
root_router = APIRouter(
    prefix="/api",
    tags=["System"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "Not found"}}
)

@root_router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """Get server status."""
    return StatusResponse(
        request_id=str(uuid.uuid4()),
        status="running",
        version="0.1.0",
        uptime=0.0,  # TODO: Implement actual uptime tracking
        services={},
        metrics={},
        timestamp=datetime.now().isoformat()
    )

graph_router = APIRouter(
    prefix="",
    tags=["Knowledge Graph"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "not found"}}
)

agent_router = APIRouter(
    prefix="",
    tags=["Agent Management"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "not found"}}
)

user_router = APIRouter(
    prefix="",
    tags=["User Management"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "not found"}}
)

analytics_router = APIRouter(
    prefix="",
    tags=["Analytics & Insights"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "not found"}}
)

orchestration_router = APIRouter(
    prefix="",
    tags=["Task Orchestration"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "not found"}}
)

chat_router = APIRouter(
    prefix="",
    tags=["Chat & Threads"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "not found"}}
)

ws_router = APIRouter(
    prefix="",
    tags=["Real-time Updates"]
)

# Include all routers at the end
nova_router.include_router(root_router)
nova_router.include_router(graph_router)
nova_router.include_router(agent_router)
nova_router.include_router(user_router)
nova_router.include_router(analytics_router)
nova_router.include_router(orchestration_router)
nova_router.include_router(chat_router, prefix="/api")
nova_router.include_router(ws_router)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG to see metadata processing logs

@graph_router.get("/data")
async def get_graph_data(
    _: None = Depends(get_permission("read")),
    graph_store: Any = Depends(get_graph_store)
) -> Dict[str, Any]:
    """Get graph data."""
    try:
        graph_data = await graph_store.get_graph_data()
        return {
            "nodes": graph_data.get("nodes", []),
            "edges": graph_data.get("edges", []),
            "timestamp": datetime.now().isoformat()
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in add_thread_agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@agent_router.options("/{path:path}")
async def agent_options_handler(request: Request):
    """Handle CORS preflight requests for agent endpoints."""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        },
    )

@agent_router.get("")
async def get_agents(
    _: None = Depends(get_permission("read")),
    agent_store: Any = Depends(get_agent_store)
) -> List[Dict[str, Any]]:
    """List all available agents."""
    try:
        agents = await agent_store.get_all_agents()
        return [
            {
                "id": agent["id"],
                "name": agent["name"],
                "type": agent.get("type"),
                "workspace": agent.get("workspace", "personal"),
                "status": agent.get("status", "active"),
                "metadata": (lambda m: (
                    logger.debug(f"Processing metadata for agent {agent['id']}: {m}"),
                    json.loads(m) if isinstance(m, str) else m
                )[1])(agent.get("metadata", "{}"))
            }
            for agent in agents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@agent_router.get("/graph")
async def get_agent_graph(
    _: None = Depends(get_permission("read")),
    agent_store: Any = Depends(get_agent_store)
) -> Dict[str, Any]:
    """Get agent DAG visualization data."""
    try:
        # Get all agents
        agents = await agent_store.get_all_agents()
        
        # Convert to graph format
        nodes = []
        edges = []
        
        # Create nodes for each agent
        for agent in agents:
            nodes.append({
                "id": agent.get("id", agent["name"]),
                "label": agent["name"],
                "type": "agent",
                "category": agent.get("type", "agent"),
                "metadata": (lambda m: json.loads(m) if isinstance(m, str) else {
                    "type": agent.get("type"),
                    "description": agent.get("description"),
                    "domain": agent.get("domain"),
                    "created_at": str(agent.get("created_at")),
                    "status": agent.get("status", "active")
                })(agent.get("metadata", "{}"))
            })
            
            # Add coordination edges
            if agent.get("type") == "nova":
                # Nova coordinates all other agents
                for other in agents:
                    if other["name"] != agent["name"]:
                        edges.append({
                            "id": f"coord_{agent['name']}_{other['name']}",
                            "source": agent.get("id", agent["name"]),
                            "target": other.get("id", other["name"]),
                            "type": "coordinates",
                            "label": "coordinates"
                        })
            elif agent.get("type") in ["belief", "desire"]:
                # Add management edges
                concept_name = agent.get("type").capitalize()
                edges.append({
                    "id": f"manages_{agent['name']}_{concept_name}",
                    "source": agent.get("id", agent["name"]),
                    "target": concept_name,
                    "type": "manages",
                    "label": "manages"
                })
        
        # Add concept nodes
        for concept in ["Belief", "Desire", "Emotion"]:
            nodes.append({
                "id": concept,
                "label": concept,
                "type": "concept",
                "category": "concept"
            })
        
        # Add concept relationships
        concept_edges = [
            ("Belief", "Desire", "influences"),
            ("Desire", "Emotion", "affects"),
            ("Emotion", "Belief", "impacts")
        ]
        
        for source, target, rel_type in concept_edges:
            edges.append({
                "id": f"{rel_type}_{source}_{target}",
                "source": source,
                "target": target,
                "type": rel_type,
                "label": rel_type
            })
        
        # Convert to expected format
        formatted_nodes = []
        for node in nodes:
            formatted_node = {
                "id": node["id"],
                "label": node["label"],
                "type": node["type"],
                "status": node.get("metadata", {}).get("status"),
                "domain": node.get("metadata", {}).get("domain"),
                "properties": {
                    "type": node.get("metadata", {}).get("type"),
                    "description": node.get("metadata", {}).get("description"),
                    "created_at": node.get("metadata", {}).get("created_at")
                }
            }
            formatted_nodes.append(formatted_node)

        formatted_edges = []
        for edge in edges:
            formatted_edge = {
                "source": edge["source"],
                "target": edge["target"],
                "type": edge["type"],
                "label": edge["label"],
                "properties": {}
            }
            formatted_edges.append(formatted_edge)

        return {
            "nodes": formatted_nodes,
            "edges": formatted_edges,
            "timestamp": datetime.now().isoformat()
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in add_thread_agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@chat_router.options("/{path:path}")
async def chat_options_handler(request: Request):
    """Handle CORS preflight requests for chat endpoints."""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        },
    )

@chat_router.get("/threads", response_model=ThreadListResponse)
async def list_threads(
    request: Request,
    thread_manager: Any = Depends(get_thread_manager)
) -> ThreadListResponse:
    """List all chat threads with optional filtering."""
    try:
        # API key validation is handled by dependencies
        _: None = Depends(get_permission("read"))
        
        raw_threads = await thread_manager.list_threads(None)
        
        # Convert thread data to match schema
        threads = []
        for thread in raw_threads:
            # Convert created_at/updated_at to createdAt/updatedAt
            thread_data = {
                "id": thread["id"],
                "name": thread.get("title", "Untitled"),  # title -> name
                "domain": thread.get("domain"),
                "messages": thread.get("messages", []),
                "createdAt": thread.get("created_at"),  # created_at -> createdAt
                "updatedAt": thread.get("updated_at"),  # updated_at -> updatedAt
                "workspace": thread.get("workspace", "personal"),
                "participants": thread.get("participants", []),
                "metadata": thread.get("metadata", {})
            }
            threads.append(thread_data)
            
        return ThreadListResponse(
            threads=[ThreadResponse(**thread) for thread in threads],
            total=len(threads),
            page=None,
            page_size=None,
            metadata={}
        )
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in list_threads: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@chat_router.get("/agents", response_model=List[Dict[str, Any]])
async def list_available_agents(
    _: None = Depends(get_permission("read")),
    agent_store: Any = Depends(get_agent_store)
) -> List[Dict[str, Any]]:
    """List all available agents."""
    try:
        # Create core agents if they don't exist
        core_agents = [
            {
                "id": "nova-orchestrator",
                "name": "Nova Orchestrator",
                "type": "orchestrator",
                "workspace": "system",
                "domain": "general",
                "status": "active",
                "metadata_type": "agent",
                "metadata_capabilities": ["orchestration"],
                "metadata_created_at": datetime.now().isoformat()
            },
            {
                "id": "belief-agent",
                "name": "Belief Agent", 
                "type": "belief",
                "workspace": "system",
                "domain": "general",
                "status": "active",
                "metadata_type": "agent",
                "metadata_capabilities": ["belief_management"],
                "metadata_created_at": datetime.now().isoformat()
            },
            {
                "id": "desire-agent",
                "name": "Desire Agent",
                "type": "desire", 
                "workspace": "system",
                "domain": "general",
                "status": "active",
                "metadata_type": "agent",
                "metadata_capabilities": ["desire_management"],
                "metadata_created_at": datetime.now().isoformat()
            }
        ]
        
        # Store core agents
        for agent in core_agents:
            await agent_store.store_agent(agent)
            
        # Get all agents including core agents
        agents = await agent_store.get_all_agents()
        return [
            {
                "id": agent["id"],
                "name": agent["name"],
                "type": agent.get("type"),
                "workspace": agent.get("workspace", "personal"),
                "status": agent.get("status", "active"),
                "metadata": (lambda m: (
                    logger.debug(f"Processing metadata for agent {agent['id']}: {m}"),
                    json.loads(m) if isinstance(m, str) else m
                )[1])(agent.get("metadata", "{}"))
            }
            for agent in agents
        ]
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/threads/{thread_id}/agents", response_model=List[Dict[str, Any]])
async def get_thread_agents(
    thread_id: str,
    _: None = Depends(get_permission("read")),
    thread_manager: Any = Depends(get_thread_manager)
) -> List[Dict[str, Any]]:
    """Get all agents in a thread."""
    try:
        return await thread_manager.get_thread_agents(thread_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_thread_agents: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@chat_router.post("/threads/{thread_id}/agents", response_model=Dict[str, Any])
async def add_thread_agent(
    thread_id: str,
    request: Dict[str, Any],
    _: None = Depends(get_permission("write")),
    thread_manager: Any = Depends(get_thread_manager),
    agent_store: Any = Depends(get_agent_store)
) -> Dict[str, Any]:
    """Add an agent to a thread."""
    try:
        agent = await thread_manager.add_single_agent(
            thread_id=thread_id,
            agent_type=request.get("agentType"),
            workspace=request.get("workspace", "personal"),
            domain=request.get("domain"),
            agent_store=agent_store
        )
        return agent
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in add_thread_agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@chat_router.get("/threads/{thread_id}/messages", response_model=List[Dict[str, Any]])
async def get_thread_messages(
    thread_id: str,
    _: None = Depends(get_permission("read")),
    thread_manager: Any = Depends(get_thread_manager)
) -> List[Dict[str, Any]]:
    """Get messages from a thread."""
    try:
        # Create system threads if they don't exist
        if thread_id in ["nova-team", "nova"]:
            thread = await thread_manager._create_system_thread(thread_id)
        else:
            thread = await thread_manager.get_thread(thread_id)
        return thread.get("messages", [])
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_thread_messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@chat_router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    _: None = Depends(get_permission("read")),
    thread_manager: Any = Depends(get_thread_manager)
) -> ThreadResponse:
    """Get a specific thread."""
    try:
        # Create system threads if they don't exist
        if thread_id in ["nova-team", "nova"]:
            thread = await thread_manager._create_system_thread(thread_id)
        else:
            thread = await thread_manager.get_thread(thread_id)
        return ThreadResponse(**thread)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_thread: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@chat_router.post("/threads/create", response_model=ThreadResponse)
async def create_thread(
    request: ThreadRequest,
    _: None = Depends(get_permission("write")),
    thread_manager: Any = Depends(get_thread_manager)
) -> ThreadResponse:
    """Create a new chat thread with validation."""
    try:
        # Validate request
        if not request.title:
            raise ValidationError("Thread title is required")
            
        # Validate metadata if provided
        if request.metadata:
            if not isinstance(request.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            # Ensure required metadata fields
            required_metadata = ["type", "system", "pinned", "description"]
            for field in required_metadata:
                if field not in request.metadata:
                    logger.warning(f"Missing metadata field {field}, using default")
                    
            # Validate thread type if provided
            if "type" in request.metadata:
                valid_types = ["test", "system", "user", "agent", "chat", "task", "agent-team"]
                if request.metadata["type"] not in valid_types:
                    raise ValidationError(f"Invalid thread type. Must be one of: {valid_types}")
        
        # Create thread with validation
        thread = await thread_manager.create_thread(
            title=request.title,
            domain=request.domain or "general",
            metadata=request.metadata,
            workspace=request.workspace or "personal"
        )
        
        return ThreadResponse(**thread)
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in create_thread: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@chat_router.post("/threads/{thread_id}/messages", response_model=MessageResponse)
async def add_message(
    thread_id: str,
    request: MessageRequest,
    _: None = Depends(get_permission("write")),
    thread_manager: Any = Depends(get_thread_manager)
) -> MessageResponse:
    """Add a message to a thread with validation."""
    try:
        # Validate request
        if not request.content:
            raise ValidationError("Message content is required")
            
        if not request.sender_type:
            raise ValidationError("Sender type is required")
            
        if not request.sender_id:
            raise ValidationError("Sender ID is required")
            
        # Create message with validation
        message = Message(
            id=str(uuid.uuid4()),
            content=request.content,
            sender_type=request.sender_type,
            sender_id=request.sender_id,
            timestamp=datetime.now().isoformat(),
            metadata={
                "type": "message",
                "domain": request.metadata.get("domain", "general") if request.metadata else "general",
                "importance": request.metadata.get("importance", 0.5) if request.metadata else 0.5,
                **(request.metadata if request.metadata else {})
            }
        )
        
        # Add message with verification
        thread = await thread_manager.add_message(thread_id, message.dict())
        
        return MessageResponse(
            id=message.id,
            content=message.content,
            message=message,
            thread_id=thread_id,
            timestamp=datetime.now().isoformat()
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in add_message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@chat_router.post("/threads/{thread_id}/agent-team", response_model=List[Dict[str, Any]])
async def create_agent_team(
    thread_id: str,
    request: Dict[str, Any],
    _: None = Depends(get_permission("write")),
    thread_manager: Any = Depends(get_thread_manager),
    agent_store: Any = Depends(get_agent_store)
) -> List[Dict[str, Any]]:
    """Create a team of agents in a thread."""
    try:
        agents = await thread_manager.add_agent_team(
            thread_id=thread_id,
            agent_specs=request.get("agents", []),
            agent_store=agent_store
        )
        return agents
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in create_agent_team: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@ws_router.websocket("/ws")
async def analytics_websocket(
    websocket: NovaWebSocket,
    analytics_agent: Any = Depends(get_analytics_agent),
    graph_store: Any = Depends(get_graph_store)
):
    """WebSocket endpoint for real-time analytics updates."""
    client_id = str(uuid.uuid4())
    
    try:
        await websocket.accept()
        
        # Wait for auth message
        try:
            data = await websocket.receive_json()
            if data.get('type') != 'auth' or data.get('api_key') not in API_KEYS:
                await websocket.close(code=4000, reason="Invalid API key")
                return
        except Exception as e:
            logger.error(f"Auth error: {e}")
            await websocket.close(code=4000, reason="Auth required")
            return
            
        # Get analytics agent from async generator if needed
        if hasattr(analytics_agent, '__aiter__'):
            try:
                analytics_agent = await anext(analytics_agent.__aiter__())
            except StopAsyncIteration:
                analytics_agent = None
                
        if not analytics_agent:
            await websocket.close(code=4000, reason="Failed to initialize analytics agent")
            return
        
        # Accept connection and add to manager
        await websocket_manager.connect(websocket, client_id)
        
        try:
            while True:
                data = await websocket.receive_json()
                
                try:
                    # Handle different message types
                    if data.get("type") == "ping":
                        await websocket_manager.broadcast_to_client(client_id, {
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        })
                    elif data.get("type") == "graph_subscribe":
                        await handle_graph_subscribe(client_id, graph_store)
                    elif data.get("type") == "swarm_monitor":
                        await handle_swarm_monitor(client_id, data, analytics_agent, websocket)
                    elif data.get("type") == "agent_coordination":
                        await handle_agent_coordination(client_id, data, analytics_agent, websocket)
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await websocket_manager.broadcast_to_client(client_id, {
                        "type": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await websocket_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close()
        except:
            pass

async def handle_graph_subscribe(client_id: str, graph_store: Any):
    """Handle graph subscription request."""
    graph_data = await graph_store.get_graph_data()
    nodes = []
    edges = []
    
    for node in graph_data.get("nodes", []):
        node_data = {
            "id": node["id"],
            "type": node["type"]
        }
        if "label" in node:
            node_data["label"] = node["label"]
        if "category" in node:
            node_data["category"] = node["category"]
        if "domain" in node:
            node_data["domain"] = node["domain"]
        if "metadata" in node:
            try:
                metadata = node["metadata"]
                node_data["metadata"] = json.loads(metadata) if isinstance(metadata, str) else metadata
                logger.debug(f"Processed metadata for node {node['id']}: {node_data['metadata']}")
            except Exception as e:
                logger.warning(f"Failed to process metadata for node {node['id']}: {e}")
                node_data["metadata"] = {}
        
        node_data["color"] = (
            "#4A4AFF" if node.get("category") == "brand" else
            "#FF4A4A" if node.get("category") == "policy" else
            "#4AFF4A"
        )
        
        nodes.append({"data": node_data})
        
    for edge in graph_data.get("edges", []):
        edge_data = {
            "id": edge["id"],
            "source": edge["source"],
            "target": edge["target"],
            "type": edge["type"]
        }
        if "label" in edge:
            edge_data["label"] = edge["label"]
        
        edges.append({"data": edge_data})
    
    await websocket_manager.broadcast_to_client(client_id, {
        "type": "graph_update",
        "data": {
            "added": {
                "nodes": nodes,
                "edges": edges
            }
        },
        "timestamp": datetime.now().isoformat()
    })

async def handle_swarm_monitor(client_id: str, data: Dict, analytics_agent: Any, websocket: WebSocket):
    """Handle swarm monitoring request."""
    task_id = data.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="swarm_monitor requires task_id")
        
    result = await analytics_agent.process_analytics(
        content={
            "type": "swarm_analytics",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        },
        analytics_type="behavioral",
        metadata={"domain": data.get("domain")}
    )
    
    for event in result.analytics.get("events", []):
        await websocket.send_json({
            "type": "swarm_update",
            "event_type": event["type"],
            **event["data"],
            "timestamp": datetime.now().isoformat()
        })

async def handle_agent_coordination(client_id: str, data: Dict, analytics_agent: Any, websocket: WebSocket):
    """Handle agent coordination request."""
    result = await analytics_agent.process_analytics(
        content={
            "type": "coordination",
            "query": data.get("content"),
            "domain": data.get("domain", "general"),
            "llm_config": data.get("llm_config", {}),
            "timestamp": datetime.now().isoformat()
        },
        analytics_type="behavioral",
        metadata={"domain": data.get("domain")}
    )
    
    if isinstance(result.analytics, dict):
        for agent, update in result.analytics.items():
            await websocket_manager.broadcast_to_client(client_id, {
                "type": "agent_update",
                "agent": agent,
                "update": update,
                "timestamp": datetime.now().isoformat()
            })
