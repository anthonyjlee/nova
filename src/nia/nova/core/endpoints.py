"""FastAPI endpoints for Nova's analytics and orchestration."""

from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, Depends, Header, Request, Response, Query, File, UploadFile
from starlette.websockets import WebSocketDisconnect
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
import json
import logging
import uuid

from nia.core.types.memory_types import AgentResponse, Memory, MemoryType
from nia.nova.core.analytics import AnalyticsResult
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.nova.core.llm import LMStudioLLM
from .websocket import manager

from .dependencies import (
    get_memory_system,
    get_world,
    get_llm,
    get_parsing_agent,
    get_coordination_agent,
    get_llm_interface,
    get_tiny_factory,
    get_analytics_agent,
    get_orchestration_agent,
    get_graph_store,
    get_agent_store,
    get_profile_store,
    get_thread_manager,
    CHAT_MODEL,
    EMBEDDING_MODEL
)

from .auth import (
    check_rate_limit,
    check_domain_access,
    get_permission,
    get_api_key,
    get_ws_api_key,
    ws_auth,
    API_KEYS
)
from .error_handling import (
    NovaError,
    ValidationError,
    ResourceNotFoundError,
    ServiceError,
    retry_on_error,
    validate_request
)
from .models import (
    AnalyticsRequest,
    AnalyticsResponse,
    TaskRequest,
    TaskResponse,
    CoordinationRequest,
    CoordinationResponse,
    ResourceAllocationRequest,
    ResourceAllocationResponse,
    MemoryRequest,
    MemoryResponse,
    FlowOptimizationRequest,
    FlowOptimizationResponse,
    AgentAssignmentRequest,
    AgentAssignmentResponse,
    ParseRequest,
    ParseResponse,
    AgentResponse,
    ProfileResponse,
    PreferenceResponse,
    AgentCapabilitiesResponse,
    AgentTypesResponse,
    AgentSearchResponse,
    AgentHistoryResponse,
    AgentMetricsResponse,
    AgentStatusResponse,
    GraphPruneResponse,
    GraphHealthResponse,
    GraphOptimizeResponse,
    GraphStatisticsResponse,
    GraphBackupResponse,
    ThreadRequest,
    ThreadResponse,
    MessageRequest,
    Message,  # Added Message model
    MessageResponse,
    ThreadListResponse
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG to see metadata processing logs

# Create root router for status endpoint
root_router = APIRouter(
    prefix="/api",
    tags=["System"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "Not found"}}
)

@root_router.get("/status")
async def get_status() -> Dict[str, str]:
    """Get server status."""
    return {
        "status": "running",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat()
    }

# Create routers with dependencies
graph_router = APIRouter(
    prefix="/api/graph",
    tags=["Knowledge Graph"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "Not found"}}
)

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

agent_router = APIRouter(
    prefix="/api/agents",
    tags=["Agent Management"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "Not found"}}
)

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
async def list_available_agents(
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

user_router = APIRouter(
    prefix="/api/users",
    tags=["User Management"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "Not found"}}
)

analytics_router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics & Insights"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "Not found"}}
)

orchestration_router = APIRouter(
    prefix="/api/orchestration",
    tags=["Task Orchestration"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "Not found"}}
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request

chat_router = APIRouter(
    prefix="/api/chat",
    tags=["Chat & Threads"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "Not found"}}
)

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
    _: None = Depends(get_permission("read")),
    thread_manager: Any = Depends(get_thread_manager),
    filter_params: Optional[Dict[str, Any]] = None
) -> ThreadListResponse:
    """List all chat threads with optional filtering."""
    try:
        threads = await thread_manager.list_threads(filter_params)
        response = ThreadListResponse(
            threads=[ThreadResponse(**thread) for thread in threads],
            total=len(threads),
            timestamp=datetime.now().isoformat()
        )
        return JSONResponse(
            content=response.dict(),
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
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
        
        response = ThreadResponse(**thread)
        return JSONResponse(
            content=response.dict(),
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "*", 
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
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
                **request.metadata if request.metadata else {}
            }
        )
        
        # Add message with verification
        thread = await thread_manager.add_message(thread_id, message.dict())
        
        response = MessageResponse(
            message=message,
            thread_id=thread_id,
            timestamp=datetime.now().isoformat()
        )
        
        return JSONResponse(
            content=response.dict(),
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
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

# Create WebSocket router without dependencies
ws_router = APIRouter(
    prefix="/api/ws",
    tags=["Real-time Updates"]
)

@ws_router.websocket("/ws")
async def analytics_websocket(
    websocket: WebSocket,
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
        await manager.connect(websocket, client_id)
        
        try:
            while True:
                data = await websocket.receive_json()
                
                try:
                    # Handle different message types
                    if data.get("type") == "ping":
                        await manager.send_json(client_id, {
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
                    await manager.send_json(client_id, {
                        "type": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await manager.disconnect(client_id)
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
    
    await manager.send_json(client_id, {
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
            await manager.send_json(client_id, {
                "type": "agent_update",
                "agent": agent,
                "update": update,
                "timestamp": datetime.now().isoformat()
            })
