"""FastAPI endpoints for Nova's analytics and orchestration."""

from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, Depends, Header, Request, Response, Query, File, UploadFile
from starlette.websockets import WebSocketDisconnect
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
import logging
import uuid

from nia.core.types.memory_types import AgentResponse
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
    except Exception as e:
        raise ServiceError(str(e))

agent_router = APIRouter(
    prefix="/api/agents",
    tags=["Agent Management"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "Not found"}}
)

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
        },
    )

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
                "metadata": agent.get("metadata", {})
            }
            for agent in agents
        ]
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.get("/threads/{thread_id}/agents", response_model=List[Dict[str, Any]])
async def get_thread_agents(
    thread_id: str,
    _: None = Depends(get_permission("read")),
    memory_system: Any = Depends(get_memory_system)
) -> List[Dict[str, Any]]:
    """Get all agents in a thread."""
    try:
        # Get thread
        result = await memory_system.query_episodic({
            "content": {},
            "filter": {
                "metadata.thread_id": thread_id,
                "metadata.type": "thread"
            },
            "layer": "episodic"
        })
        
        if not result:
            raise ResourceNotFoundError(f"Thread {thread_id} not found")
            
        thread = result[0]["content"]["data"]
        
        # Return participants that are agents
        return [
            p for p in thread.get("metadata", {}).get("participants", [])
            if p.get("type") == "agent"
        ]
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.post("/threads/{thread_id}/agents", response_model=List[Dict[str, Any]])
async def get_thread_agents_post(
    thread_id: str,
    _: None = Depends(get_permission("read")),
    memory_system: Any = Depends(get_memory_system)
) -> List[Dict[str, Any]]:
    """Get all agents in a thread (POST method)."""
    return await get_thread_agents(thread_id, _, memory_system)

@chat_router.get("/threads", response_model=ThreadListResponse)
async def list_threads(
    _: None = Depends(get_permission("read")),
    memory_system: Any = Depends(get_memory_system)
) -> ThreadListResponse:
    """List all chat threads."""
    try:
        # Retrieve all threads from memory system
        results = await memory_system.query_episodic({
            "content": {},
            "filter": {"metadata.type": "thread"},
            "layer": "episodic"
        })
        
        threads = [ThreadResponse(**result["content"]["data"]) for result in results]
        
        return ThreadListResponse(
            threads=threads,
            total=len(threads),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise ServiceError(str(e))

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
            node_data["metadata"] = node["metadata"]
        
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
        raise ValidationError("swarm_monitor requires task_id")
        
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
