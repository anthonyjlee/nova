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

chat_router = APIRouter(
    prefix="/api/chat",
    tags=["Chat & Threads"],
    dependencies=[Depends(check_rate_limit)],
    responses={404: {"description": "Not found"}}
)

@chat_router.post("/threads/create", response_model=ThreadResponse)
async def create_thread(
    request: ThreadRequest,
    _: None = Depends(get_permission("write")),
    memory_system: Any = Depends(get_memory_system)
) -> ThreadResponse:
    """Create a new chat thread."""
    try:
        thread_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        thread = {
            "id": thread_id,
            "title": request.title,
            "domain": request.domain,
            "messages": [],
            "created_at": now,
            "updated_at": now,
            "metadata": request.metadata or {}
        }
        
        # Store thread in memory system
        await memory_system.store_experience({
            "type": "thread",
            "content": thread,
            "importance": 0.8,
            "metadata": {
                "domain": request.domain,
                "thread_id": thread_id
            }
        })
        
        return ThreadResponse(**thread)
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    _: None = Depends(get_permission("read")),
    memory_system: Any = Depends(get_memory_system)
) -> ThreadResponse:
    """Get thread details and messages."""
    try:
        # Retrieve thread from memory system
        result = await memory_system.search_experiences({
            "type": "thread",
            "metadata.thread_id": thread_id
        })
        
        if not result:
            raise ResourceNotFoundError(f"Thread {thread_id} not found")
            
        thread = result[0]["content"]
        return ThreadResponse(**thread)
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.post("/threads/{thread_id}/messages", response_model=MessageResponse)
async def add_message(
    thread_id: str,
    message: MessageRequest,
    _: None = Depends(get_permission("write")),
    memory_system: Any = Depends(get_memory_system)
) -> MessageResponse:
    """Add a message to a thread."""
    try:
        # Get existing thread
        result = await memory_system.search_experiences({
            "type": "thread",
            "metadata.thread_id": thread_id
        })
        
        if not result:
            raise ResourceNotFoundError(f"Thread {thread_id} not found")
            
        thread = result[0]["content"]
        now = datetime.now().isoformat()
        
        # Create new message
        new_message = Message(
            id=str(uuid.uuid4()),
            content=message.content,
            sender_type=message.sender_type,
            sender_id=message.sender_id,
            timestamp=now,
            metadata=message.metadata
        )
        
        # Update thread
        thread["messages"].append(new_message.dict())
        thread["updated_at"] = now
        
        # Store updated thread
        await memory_system.store_experience({
            "type": "thread",
            "content": thread,
            "importance": 0.8,
            "metadata": {
                "domain": thread.get("domain"),
                "thread_id": thread_id
            }
        })
        
        return MessageResponse(
            message=new_message,
            thread_id=thread_id,
            timestamp=now
        )
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.get("/threads", response_model=ThreadListResponse)
async def list_threads(
    _: None = Depends(get_permission("read")),
    memory_system: Any = Depends(get_memory_system)
) -> ThreadListResponse:
    """List all chat threads."""
    try:
        # Retrieve all threads from memory system
        results = await memory_system.search_experiences({
            "type": "thread"
        })
        
        threads = [ThreadResponse(**result["content"]) for result in results]
        
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
        
        # Get API key from query parameters or headers
        api_key = websocket.query_params.get("api_key")
        if not api_key:
            headers = dict(websocket.headers)
            api_key = headers.get("x-api-key")
            
        if not api_key or api_key not in API_KEYS:
            await websocket.close(code=4000, reason="Invalid API key")
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
        
        while True:
            try:
                data = await websocket.receive_json()
                
                try:
                    # Handle different message types
                    if data.get("type") == "ping":
                        # Handle ping message
                        await manager.send_json(client_id, {
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        })
                    elif data.get("type") == "graph_subscribe":
                        # Send initial graph data
                        graph_data = await graph_store.get_graph_data()
                        
                        # Format nodes and edges for Cytoscape
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
                            
                            # Set color based on category
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
                    elif data.get("type") == "swarm_monitor":
                        # Monitor swarm activity for specific task
                        task_id = data.get("task_id")
                        if not task_id:
                            raise ValidationError("swarm_monitor requires task_id")
                            
                        # Get swarm analytics
                        result = await analytics_agent.process_analytics(
                            content={
                                "type": "swarm_analytics",
                                "task_id": task_id,
                                "timestamp": datetime.now().isoformat()
                            },
                            analytics_type="behavioral",
                            metadata={"domain": data.get("domain")}
                        )
                        
                        # Send swarm updates based on analytics
                        for event in result.analytics.get("events", []):
                            await websocket.send_json({
                                "type": "swarm_update",
                                "event_type": event["type"],
                                **event["data"],
                                "timestamp": datetime.now().isoformat()
                            })
                    elif data.get("type") == "agent_coordination":
                        # Handle agent coordination request
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
                        
                        # Send agent updates
                        if isinstance(result.analytics, dict):
                            for agent, update in result.analytics.items():
                                await websocket.send_json({
                                    "type": "analytics_update",
                                    "analytics": {agent: update},
                                    "timestamp": datetime.now().isoformat()
                                })
                        
                        # Send final response
                        if result.insights:
                            insight = result.insights[0] if isinstance(result.insights, list) else result.insights
                            content = insight.get("description", str(insight)) if isinstance(insight, dict) else str(insight)
                            await websocket.send_json({
                                "type": "response",
                                "content": content,
                                "confidence": result.confidence,
                                "timestamp": datetime.now().isoformat()
                            })
                    else:
                        # Handle regular analytics requests
                        request = AnalyticsRequest(**data)
                        result = await analytics_agent.process_analytics(
                            content=data,
                            analytics_type=request.type,
                            metadata={"domain": request.domain} if request.domain else None
                        )
                        
                    # Send analytics update
                    if hasattr(result, 'analytics') and isinstance(result.analytics, dict):
                        # Format nodes and edges if present
                        if 'nodes' in result.analytics or 'edges' in result.analytics:
                            formatted_nodes = []
                            formatted_edges = []
                            
                            for node in result.analytics.get('nodes', []):
                                node_data = {
                                    "id": node["id"],
                                    "type": node.get("type", "default")
                                }
                                if "label" in node:
                                    node_data["label"] = node["label"]
                                if "category" in node:
                                    node_data["category"] = node["category"]
                                if "domain" in node:
                                    node_data["domain"] = node["domain"]
                                if "metadata" in node:
                                    node_data["metadata"] = node["metadata"]
                                if "status" in node:
                                    node_data["status"] = node["status"]
                                    node_data["color"] = "#4AFF4A" if node["status"] == "active" else "#FF4A4A"
                                elif "category" in node:
                                    node_data["color"] = (
                                        "#4A4AFF" if node["category"] == "brand" else
                                        "#FF4A4A" if node["category"] == "policy" else
                                        "#4AFF4A"
                                    )
                                else:
                                    node_data["color"] = "#4AFF4A"
                                
                                formatted_nodes.append({"data": node_data})
                            
                            for edge in result.analytics.get('edges', []):
                                edge_data = {
                                    "id": edge.get("id") or f"{edge['source']}-{edge['target']}",
                                    "source": edge["source"],
                                    "target": edge["target"],
                                    "type": edge.get("type", "default")
                                }
                                if "label" in edge:
                                    edge_data["label"] = edge["label"]
                                
                                formatted_edges.append({"data": edge_data})
                            
                            await manager.send_json(client_id, {
                                "type": "graph_update",
                                "data": {
                                    "added": {
                                        "nodes": formatted_nodes,
                                        "edges": formatted_edges
                                    }
                                },
                                "insights": result.insights if hasattr(result, 'insights') else [],
                                "confidence": result.confidence if hasattr(result, 'confidence') else 1.0,
                                "timestamp": datetime.now().isoformat()
                            })
                        else:
                            # Regular analytics update without graph data
                            await manager.send_json(client_id, {
                                "type": "analytics_update",
                                "analytics": result.analytics,
                                "insights": result.insights if hasattr(result, 'insights') else [],
                                "confidence": result.confidence if hasattr(result, 'confidence') else 1.0,
                                "timestamp": datetime.now().isoformat()
                            })
                except ValidationError as e:
                    await manager.send_json(client_id, {
                        "type": "error",
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": str(e)
                        }
                    })
                except ResourceNotFoundError as e:
                    await manager.send_json(client_id, {
                        "type": "error",
                        "error": {
                            "code": "NOT_FOUND",
                            "message": str(e)
                        }
                    })
                except Exception as e:
                    await manager.send_json(client_id, {
                        "type": "error",
                        "error": {
                            "code": "PROCESSING_ERROR",
                            "message": str(e)
                        }
                    })
            except WebSocketDisconnect:
                # Client disconnected
                break
            except Exception as e:
                logger.error(f"Error in websocket: {str(e)}")
                try:
                    await manager.send_json(client_id, {
                        "type": "error",
                        "error": {
                            "code": "PROCESSING_ERROR",
                            "message": str(e)
                        }
                    })
                except:
                    break
    except Exception as e:
        logger.error(f"Error in websocket: {str(e)}")
    finally:
        manager.disconnect(client_id)
        try:
            await websocket.close()
        except:
            pass

@graph_router.get("/data", response_model=Dict[str, Any])
@retry_on_error(max_retries=3)
async def get_graph_data(
    _: None = Depends(get_permission("read")),
    graph_store: Any = Depends(get_graph_store)
) -> Dict:
    """Get complete knowledge graph data."""
    try:
        data = await graph_store.get_graph_data()
        return {
            **data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@graph_router.get("/statistics", response_model=GraphStatisticsResponse)
@retry_on_error(max_retries=3)
async def get_graph_statistics(
    _: None = Depends(get_permission("read")),
    graph_store: Any = Depends(get_graph_store)
) -> Dict:
    """Get knowledge graph statistics."""
    try:
        stats = await graph_store.get_statistics()
        return {
            **stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@orchestration_router.get("/tasks/flow", response_model=Dict[str, Any])
@retry_on_error(max_retries=3)
async def get_task_flow(
    _: None = Depends(get_permission("read")),
    orchestration_agent: Any = Depends(get_orchestration_agent)
) -> Dict:
    """Get task flow DAG data."""
    try:
        tasks = await orchestration_agent.get_active_tasks()
        nodes = []
        edges = []
        
        # Add task nodes
        for task in tasks:
            nodes.append({
                "id": task["id"],
                "type": "task",
                "label": task["description"],
                "status": task["status"],
                "metadata": {
                    "domain": task.get("domain"),
                    "timestamp": task.get("created_at"),
                    "importance": task.get("importance", 0.5)
                }
            })
            
            # Add dependency edges
            for dep in task.get("dependencies", []):
                edges.append({
                    "source": task["id"],
                    "target": dep,
                    "type": "DEPENDS_ON",
                    "label": "depends on"
                })
        
        return {
            "analytics": {
                "nodes": nodes,
                "edges": edges
            },
            "insights": [],
            "confidence": 1.0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/graph", response_model=Dict[str, Any])
@retry_on_error(max_retries=3)
async def get_agent_graph(
    _: None = Depends(get_permission("read")),
    agent_store: Any = Depends(get_agent_store)
) -> Dict:
    """Get agent graph data."""
    try:
        agents = await agent_store.get_all_agents()
        nodes = []
        edges = []
        
        # Add agent nodes
        for agent in agents:
            nodes.append({
                "id": agent["id"],
                "type": "agent",
                "label": agent["name"],
                "status": agent["status"],
                "domain": agent.get("domain"),
                "properties": {
                    "capabilities": agent.get("capabilities", []),
                    "created_at": agent.get("created_at"),
                    "supervisor_id": agent.get("supervisor_id")
                }
            })
            
            # Add supervision edges
            if agent.get("supervisor_id"):
                edges.append({
                    "source": agent["supervisor_id"],
                    "target": agent["id"],
                    "type": "SUPERVISES",
                    "label": "supervises",
                    "properties": {}
                })
            
            # Add task assignment edges
            for task_id in agent.get("assigned_tasks", []):
                edges.append({
                    "source": agent["id"],
                    "target": task_id,
                    "type": "ASSIGNED",
                    "label": "assigned to",
                    "properties": {}
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

# Export routers for app.py to include
__all__ = [
    'graph_router',
    'agent_router',
    'user_router',
    'analytics_router',
    'orchestration_router',
    'chat_router',
    'ws_router'
]
