"""FastAPI endpoints for Nova's analytics and orchestration."""

from fastapi import APIRouter, HTTPException, WebSocket, Depends, Header, Request, Response, Query, File, UploadFile
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
import logging
import uuid

from nia.core.types.memory_types import AgentResponse
from nia.nova.core.analytics import AnalyticsResult
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.nova.core.llm import LMStudioLLM

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
    GraphBackupResponse
)

logger = logging.getLogger(__name__)

# Create routers with dependencies
graph_router = APIRouter(
    prefix="/api/graph",
    tags=["graph"],
    dependencies=[Depends(check_rate_limit)]
)

agent_router = APIRouter(
    prefix="/api/agents",
    tags=["agents"],
    dependencies=[Depends(check_rate_limit)]
)

user_router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    dependencies=[Depends(check_rate_limit)]
)

analytics_router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"],
    dependencies=[Depends(check_rate_limit)]
)

orchestration_router = APIRouter(
    prefix="/api/orchestration",
    tags=["orchestration"],
    dependencies=[Depends(check_rate_limit)]
)

# Create WebSocket router without dependencies
ws_router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"]
)

@analytics_router.post("/parse", response_model=ParseResponse)
@retry_on_error(max_retries=3)
async def parse_query(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    parsing_agent: Any = Depends(get_parsing_agent)
) -> Dict:
    """Parse user query."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
            
        if "text" not in request:
            raise ValidationError("Request must include 'text' field")
            
        # Initialize agent
        await parsing_agent.initialize()
        
        try:
            # Parse query
            result = await parsing_agent.parse_and_store(
                text=request["text"],
                context={
                    "domain": domain or request.get("domain", "professional"),
                    "source": "api"
                }
            )
        finally:
            # Clean up agent
            await parsing_agent.cleanup()
        
        return {
            "parsed_content": {
                "concepts": result.concepts,
                "key_points": result.key_points,
                "structure": result.structure
            },
            "confidence": result.confidence,
            "metadata": result.metadata,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@ws_router.websocket("/ws")
async def analytics_websocket(
    websocket: WebSocket,
    analytics_agent: Any = Depends(get_analytics_agent)
):
    """WebSocket endpoint for real-time analytics updates."""
    try:
        # Validate API key using dependency
        api_key = await get_ws_api_key(websocket)
        if not api_key:
            await websocket.close(code=4001, reason="Invalid API key")
            return
        
        try:
            await websocket.accept()
        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {str(e)}")
            return
        
        while True:
            try:
                data = await websocket.receive_json()
                
                try:
                    # Handle different message types
                    if data.get("type") == "swarm_monitor":
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
                    else:
                        # Handle regular analytics requests
                        request = AnalyticsRequest(**data)
                        result = await analytics_agent.process_analytics(
                            content=data,
                            analytics_type=request.type,
                            metadata={"domain": request.domain} if request.domain else None
                        )
                        
                        # Send analytics update
                        await websocket.send_json({
                            "type": "analytics_update",
                            "analytics": result.analytics if hasattr(result, 'analytics') else {},
                            "insights": result.insights if hasattr(result, 'insights') else [],
                            "confidence": result.confidence if hasattr(result, 'confidence') else 1.0,
                            "timestamp": datetime.now().isoformat()
                        })
                except ValidationError as e:
                    await websocket.send_json({
                        "type": "error",
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": str(e)
                        }
                    })
                except ResourceNotFoundError as e:
                    await websocket.send_json({
                        "type": "error",
                        "error": {
                            "code": "NOT_FOUND",
                            "message": str(e)
                        }
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "error": {
                            "code": "PROCESSING_ERROR",
                            "message": str(e)
                        }
                    })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "error": {
                        "code": "PROCESSING_ERROR",
                        "message": str(e)
                    }
                })
    except Exception as e:
        if websocket.client_state.value != 3:  # Not closed
            await websocket.send_json({
                "type": "error",
                "error": {
                    "code": "ERROR",
                    "message": str(e)
                }
            })
    finally:
        if websocket.client_state.value != 3:  # Not closed
            await websocket.close()

@orchestration_router.post("/memory/store", response_model=MemoryResponse)
@retry_on_error(max_retries=3)
async def store_memory(
    request: Dict[str, Any],
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system),
    llm_interface: LMStudioLLM = Depends(get_llm_interface)
) -> Dict:
    """Store memory in the system."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
            
        required_fields = ["content", "type"]
        for field in required_fields:
            if field not in request:
                raise ValidationError(f"Request must include '{field}' field")
        
        # Initialize memory system
        await memory_system.initialize()
        
        # Store memory
        content_dict = {"text": request["content"]}  # Wrap content in dict
        memory_id = await memory_system.store(
            content=content_dict,
            memory_type=request["type"],
            importance=request.get("importance", 0.5),
            context=request.get("context", {}),
            metadata=request.get("metadata", {})
        )
        
        # Format response as dictionary
        response = {
            "memory_id": str(memory_id),
            "status": "stored",
            "content": content_dict,
            "metadata": request.get("metadata", {}),
            "timestamp": datetime.now().isoformat()
        }
        return response
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.post("/memory/query", response_model=Dict[str, Any])
@retry_on_error(max_retries=3)
async def query_memory(
    request: Dict[str, Any],
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """Query memories from the system."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
            
        if "query" not in request:
            raise ValidationError("Request must include 'query' field")
        
        # Initialize memory system
        await memory_system.initialize()
        
        # Query memories
        query_dict = {
            "text": request["query"],
            "type": request.get("type", "episodic")  # Use specified type or default to episodic
        }
        memories = await memory_system.query_episodic(query_dict)
        
        return {
            "memories": memories,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.post("/memory/consolidate", response_model=Dict[str, Any])
@retry_on_error(max_retries=3)
async def consolidate_memory(
    request: Dict[str, Any],
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """Consolidate memories in the system."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        # Initialize memory system
        await memory_system.initialize()
        
        # Consolidate memories
        await memory_system.consolidate_memories()
        return {
            "consolidated_count": 1,  # Placeholder since we don't get a count back
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.post("/resources/allocate", response_model=ResourceAllocationResponse)
@validate_request(ResourceAllocationRequest)
@retry_on_error(max_retries=3)
async def allocate_resources(
    allocation_request: ResourceAllocationRequest,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    analytics_agent: Any = Depends(get_analytics_agent),
    orchestration_agent: Any = Depends(get_orchestration_agent)
) -> Dict:
    """Allocate resources based on analytics predictions."""
    try:
        # Perform resource allocation first
        allocation_result = await orchestration_agent.allocate_resources(
            resources=allocation_request.resources,
            constraints=allocation_request.constraints,
            priority=allocation_request.priority,
            metadata={"domain": domain} if domain else None
        )
        
        # Get analytics for the allocation
        analytics_result = await analytics_agent.process_analytics(
            content={
                "type": "resource_analytics",
                "request": allocation_request.dict(),
                "timestamp": datetime.now().isoformat()
            },
            analytics_type="predictive",
            metadata={"domain": domain} if domain else None
        )
        
        return {
            "allocations": allocation_result.get("allocations", []),
            "analytics": analytics_result.analytics,
            "confidence": analytics_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@analytics_router.get("/flows", response_model=AnalyticsResponse)
@retry_on_error(max_retries=3)
async def get_flow_analytics(
    flow_id: Optional[str] = None,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    analytics_agent: Any = Depends(get_analytics_agent)
) -> Dict:
    """Get analytics for active flows."""
    try:
        content = {
            "type": "flow_analytics",
            "flow_id": flow_id,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            result = await analytics_agent.process_analytics(
                content=content,
                analytics_type="behavioral",
                metadata={"domain": domain} if domain else None
            )
        except ResourceNotFoundError as e:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": str(e)
                }
            )
        except Exception as e:
            raise ServiceError(str(e))
        
        return {
            "analytics": result.analytics,
            "insights": result.insights,
            "confidence": result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@analytics_router.get("/resources", response_model=AnalyticsResponse)
@retry_on_error(max_retries=3)
async def get_resource_analytics(
    resource_id: Optional[str] = None,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    analytics_agent: Any = Depends(get_analytics_agent)
) -> Dict:
    """Get analytics for resource utilization."""
    try:
        content = {
            "type": "resource_analytics",
            "resource_id": resource_id,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            result = await analytics_agent.process_analytics(
                content=content,
                analytics_type="predictive",
                metadata={"domain": domain} if domain else None
            )
        except ResourceNotFoundError as e:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": str(e)
                }
            )
        except Exception as e:
            raise ServiceError(str(e))
        
        return {
            "analytics": result.analytics,
            "insights": result.insights,
            "confidence": result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.post("/agents/create", response_model=AgentResponse)
@retry_on_error(max_retries=3)
async def create_agent(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    tiny_factory: Any = Depends(get_tiny_factory),
    memory_system: Any = Depends(get_memory_system)
) -> Dict:
    """Create a new agent with specified type and capabilities."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        required_fields = ["agent_type", "capabilities"]
        for field in required_fields:
            if field not in request:
                raise ValidationError(f"Request must include '{field}' field")
        
        # Create agent using TinyFactory with unique name
        agent_name = f"{request['agent_type']}_{uuid.uuid4().hex[:8]}"
        agent = await tiny_factory.create_agent(
            name=agent_name,
            agent_type=request["agent_type"],
            capabilities=request["capabilities"],
            domain=domain or request.get("domain", "professional"),
            supervisor_id=request.get("supervisor_id"),
            metadata={"domain": domain} if domain else None
        )
        
        return {
            "agent_id": agent.name,
            "agent_type": request["agent_type"],
            "capabilities": request["capabilities"],
            "domain": agent.domain,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@user_router.post("/profile/questionnaire", response_model=ProfileResponse)
@retry_on_error(max_retries=3)
async def submit_questionnaire(
    request: Dict[str, Any],
    _: None = Depends(get_permission("write")),
    profile_store: Any = Depends(get_profile_store)
) -> Dict:
    """Submit user psychometric questionnaire."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        required_sections = ["personality", "learning_style", "communication_preferences"]
        for section in required_sections:
            if section not in request:
                raise ValidationError(f"Request must include '{section}' section")
        
        # Store profile data
        profile_id = f"profile_{uuid.uuid4().hex[:8]}"
        await profile_store.store_profile(
            profile_id=profile_id,
            profile_data={
                **request,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        )
        
        return {
            "profile_id": profile_id,
            "status": "created",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@user_router.get("/profile", response_model=Dict[str, Any])
@retry_on_error(max_retries=3)
async def get_profile(
    _: None = Depends(get_permission("read")),
    profile_store: Any = Depends(get_profile_store)
) -> Dict:
    """Get user profile data."""
    try:
        profile_data = await profile_store.get_profile()
        if not profile_data:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": "Profile not found"
                }
            )
        
        return {
            **profile_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@user_router.put("/profile/preferences", response_model=PreferenceResponse)
@retry_on_error(max_retries=3)
async def update_preferences(
    request: Dict[str, Any],
    _: None = Depends(get_permission("write")),
    profile_store: Any = Depends(get_profile_store)
) -> Dict:
    """Update user preferences."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        # Update preferences
        await profile_store.update_preferences(
            preferences=request,
            updated_at=datetime.now().isoformat()
        )
        
        return {
            "status": "updated",
            "preferences": request,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@user_router.get("/profile/learning-style", response_model=Dict[str, Any])
@retry_on_error(max_retries=3)
async def get_learning_style(
    _: None = Depends(get_permission("read")),
    profile_store: Any = Depends(get_profile_store)
) -> Dict:
    """Get user learning style."""
    try:
        profile_data = await profile_store.get_profile()
        if not profile_data or "learning_style" not in profile_data:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": "Learning style not found"
                }
            )
        
        return {
            **profile_data["learning_style"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@user_router.put("/profile/auto-approval", response_model=PreferenceResponse)
@retry_on_error(max_retries=3)
async def update_auto_approval(
    request: Dict[str, Any],
    _: None = Depends(get_permission("write")),
    profile_store: Any = Depends(get_profile_store)
) -> Dict:
    """Update auto-approval settings."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        # Update auto-approval settings
        await profile_store.update_preferences(
            preferences={
                "auto_approval": request
            },
            updated_at=datetime.now().isoformat()
        )
        
        return {
            "status": "updated",
            "auto_approval": request,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/capabilities", response_model=AgentCapabilitiesResponse)
@retry_on_error(max_retries=3)
async def get_agent_capabilities(
    agent_id: str,
    _: None = Depends(get_permission("read")),
    agent_store: Any = Depends(get_agent_store)
) -> Dict:
    """Get agent capabilities."""
    try:
        capabilities = await agent_store.get_capabilities(agent_id)
        if not capabilities:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": f"Agent {agent_id} not found"
                }
            )
        
        return {
            "agent_id": agent_id,
            "capabilities": capabilities,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@agent_router.get("/types", response_model=AgentTypesResponse)
@retry_on_error(max_retries=3)
async def get_agent_types(
    _: None = Depends(get_permission("read")),
    agent_store: Any = Depends(get_agent_store)
) -> Dict:
    """Get available agent types."""
    try:
        types = await agent_store.get_types()
        return {
            "agent_types": types,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/search", response_model=AgentSearchResponse)
@retry_on_error(max_retries=3)
async def search_agents(
    capability: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    _: None = Depends(get_permission("read")),
    agent_store: Any = Depends(get_agent_store)
) -> Dict:
    """Search for agents by capability and domain."""
    try:
        agents = await agent_store.search_agents(
            capability=capability,
            domain=domain
        )
        return {
            "agents": agents,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/history", response_model=AgentHistoryResponse)
@retry_on_error(max_retries=3)
async def get_agent_history(
    agent_id: str,
    _: None = Depends(get_permission("read")),
    agent_store: Any = Depends(get_agent_store)
) -> Dict:
    """Get agent interaction history."""
    try:
        history = await agent_store.get_history(agent_id)
        if not history:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": f"Agent {agent_id} not found"
                }
            )
        
        return {
            "agent_id": agent_id,
            "interactions": history,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/metrics", response_model=AgentMetricsResponse)
@retry_on_error(max_retries=3)
async def get_agent_metrics(
    agent_id: str,
    _: None = Depends(get_permission("read")),
    agent_store: Any = Depends(get_agent_store)
) -> Dict:
    """Get agent performance metrics."""
    try:
        metrics = await agent_store.get_metrics(agent_id)
        if not metrics:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": f"Agent {agent_id} not found"
                }
            )
        
        return {
            "agent_id": agent_id,
            "performance_metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@agent_router.post("/{agent_id}/activate", response_model=AgentStatusResponse)
@retry_on_error(max_retries=3)
async def activate_agent(
    agent_id: str,
    _: None = Depends(get_permission("write")),
    agent_store: Any = Depends(get_agent_store)
) -> Dict:
    """Activate an agent."""
    try:
        await agent_store.set_status(agent_id, "active")
        return {
            "agent_id": agent_id,
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.post("/{agent_id}/deactivate", response_model=AgentStatusResponse)
@retry_on_error(max_retries=3)
async def deactivate_agent(
    agent_id: str,
    _: None = Depends(get_permission("write")),
    agent_store: Any = Depends(get_agent_store)
) -> Dict:
    """Deactivate an agent."""
    try:
        await agent_store.set_status(agent_id, "inactive")
        return {
            "agent_id": agent_id,
            "status": "inactive",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/status", response_model=AgentStatusResponse)
@retry_on_error(max_retries=3)
async def get_agent_status(
    agent_id: str,
    _: None = Depends(get_permission("read")),
    agent_store: Any = Depends(get_agent_store)
) -> Dict:
    """Get agent status."""
    try:
        status = await agent_store.get_status(agent_id)
        if status is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": f"Agent {agent_id} not found"
                }
            )
        
        return {
            "agent_id": agent_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@graph_router.post("/prune", response_model=GraphPruneResponse)
@retry_on_error(max_retries=3)
async def prune_graph(
    request: Dict[str, Any],
    _: None = Depends(get_permission("write")),
    graph_store: Any = Depends(get_graph_store)
) -> Dict:
    """Prune knowledge graph based on criteria."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        min_relevance = request.get("min_relevance_score", 0.5)
        max_age_days = request.get("max_age_days", 30)
        exclude_domains = request.get("exclude_domains", [])
        
        # Perform pruning
        result = await graph_store.prune_graph(
            min_relevance=min_relevance,
            max_age_days=max_age_days,
            exclude_domains=exclude_domains
        )
        
        return {
            "nodes_removed": result["nodes_removed"],
            "edges_removed": result["edges_removed"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@graph_router.get("/health", response_model=GraphHealthResponse)
@retry_on_error(max_retries=3)
async def check_graph_health(
    _: None = Depends(get_permission("read")),
    graph_store: Any = Depends(get_graph_store)
) -> Dict:
    """Check knowledge graph health."""
    try:
        health_data = await graph_store.check_health()
        return {
            **health_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@graph_router.post("/optimize", response_model=GraphOptimizeResponse)
@retry_on_error(max_retries=3)
async def optimize_graph(
    request: Dict[str, Any],
    _: None = Depends(get_permission("write")),
    graph_store: Any = Depends(get_graph_store)
) -> Dict:
    """Optimize graph structure."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        target_metrics = request.get("target_metrics", ["query_performance"])
        optimization_level = request.get("optimization_level", "moderate")
        
        # Perform optimization
        result = await graph_store.optimize_structure(
            target_metrics=target_metrics,
            optimization_level=optimization_level
        )
        
        return {
            **result,
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

@graph_router.post("/backup", response_model=GraphBackupResponse)
@retry_on_error(max_retries=3)
async def create_graph_backup(
    request: Dict[str, Any],
    _: None = Depends(get_permission("write")),
    graph_store: Any = Depends(get_graph_store)
) -> Dict:
    """Create graph backup."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        include_domains = request.get("include_domains", ["all"])
        backup_format = request.get("backup_format", "cypher")
        compression = request.get("compression", True)
        
        # Create backup
        result = await graph_store.create_backup(
            include_domains=include_domains,
            backup_format=backup_format,
            compression=compression
        )
        
        return {
            **result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))
