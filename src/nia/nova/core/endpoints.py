"""F astAPI endpoints for Nova's analytics and orchestration."""

from fastapi import APIRouter, HTTPException, WebSocket, Depends, Header, Request
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp

from nia.nova.core.analytics import AnalyticsAgent, AnalyticsResult
from nia.nova.core.parsing import NovaParser
from nia.nova.core.llm import LMStudioLLM
from nia.agents.specialized.orchestration_agent import OrchestrationAgent
from nia.agents.specialized.parsing_agent import ParsingAgent
from nia.memory.types.memory_types import AgentResponse
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.world.environment import NIAWorld

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
# LM Studio configuration
CHAT_MODEL = "llama-3.2-3b-instruct"
EMBEDDING_MODEL = "text-embedding-nomic-embed-text-v1.5@q8_0"

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
    ParseRequest
)

# Create routers with dependencies
analytics_router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"],
    dependencies=[Depends(check_rate_limit)]
)

# Create WebSocket router without dependencies
ws_router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"]
)

# Service dependencies
async def get_memory_system():
    """Get memory system instance."""
    memory_system = TwoLayerMemorySystem(
        neo4j_uri="bolt://localhost:7687"
    )
    try:
        # Initialize Neo4j connection
        await memory_system.semantic.connect()
        # Initialize vector store if needed
        if hasattr(memory_system.episodic.store, 'connect'):
            await memory_system.episodic.store.connect()
        yield memory_system
    finally:
        # Cleanup connections
        if hasattr(memory_system.semantic, 'close'):
            await memory_system.semantic.close()
        if hasattr(memory_system.episodic.store, 'close'):
            await memory_system.episodic.store.close()

async def get_llm():
    """Get LLM instance."""
    llm = LMStudioLLM(
        chat_model=CHAT_MODEL,
        embedding_model=EMBEDDING_MODEL
    )
    return llm

async def get_llm_interface():
    """Get LLM interface instance."""
    return LMStudioLLM(
        chat_model=CHAT_MODEL,
        embedding_model=EMBEDDING_MODEL
    )

async def get_coordination_agent(
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system),
    world: NIAWorld = Depends(get_world),
    llm: LMStudioLLM = Depends(get_llm)
):
    """Get coordination agent instance."""
    from nia.agents.specialized.coordination_agent import CoordinationAgent
    
    agent = CoordinationAgent(
        name="nova_coordinator",
        memory_system=memory_system,
        world=world,
        domain="professional"
    )
    agent.llm = llm
    return agent

async def get_world():
    """Get world instance."""
    return NIAWorld()

async def get_parsing_agent(
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system),
    world: NIAWorld = Depends(get_world),
    llm: LMStudioLLM = Depends(get_llm)
):
    """Get parsing agent instance."""
    agent = ParsingAgent(
        name="nova_parser",
        memory_system=memory_system,
        world=world,
        domain="professional"
    )
    agent.llm = llm
    return agent

async def get_analytics_agent(
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system),
    llm: LMStudioLLM = Depends(get_llm)
):
    """Get analytics agent instance."""
    # Get memory system from async generator
    if hasattr(memory_system, '__aiter__'):
        try:
            memory_system = await anext(memory_system.__aiter__())
        except StopAsyncIteration:
            memory_system = None
    
    return AnalyticsAgent(
        domain="professional",
        llm=llm,
        store=memory_system.semantic.store if memory_system else None,
        vector_store=memory_system.episodic.store if memory_system else None
    )

import uuid

async def get_orchestration_agent(
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system),
    llm: LMStudioLLM = Depends(get_llm)
):
    """Get orchestration agent instance."""
    # Get memory system from async generator
    if hasattr(memory_system, '__aiter__'):
        try:
            memory_system = await anext(memory_system.__aiter__())
        except StopAsyncIteration:
            memory_system = None
    
    # Generate unique name for each agent instance
    agent_name = f"nova_orchestrator_{uuid.uuid4().hex[:8]}"
    agent = OrchestrationAgent(
        name=agent_name,
        memory_system=memory_system,
        domain="professional"
    )
    agent.llm = llm
    return agent

@analytics_router.post("/parse", dependencies=[Depends(check_rate_limit)])
@retry_on_error(max_retries=3)
async def parse_text(
    request: Dict,
    _: None = Depends(get_permission("write")),
    parsing_agent: ParsingAgent = Depends(get_parsing_agent)
) -> Dict:
    """Parse text using LM Studio integration."""
    try:
        # Parse and validate request
        try:
            parse_request = ParseRequest(**request)
        except Exception as e:
            raise ValidationError(f"Invalid request format: {str(e)}")
        
        # Validate LLM config
        if parse_request.llm_config:
            chat_model = parse_request.llm_config.get("chat_model")
            embedding_model = parse_request.llm_config.get("embedding_model")
            
            if not chat_model or not embedding_model:
                raise ValidationError("LLM config must include both chat_model and embedding_model")
            
            # Check if models are available
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:1234/v1/models") as response:
                        if response.status != 200:
                            raise ValidationError("LM Studio API not available")
                        
                        models = (await response.json()).get("data", [])
                        available_models = [model["id"] for model in models]
                        
                        if chat_model not in available_models:
                            raise ValidationError(f"Chat model '{chat_model}' not available")
                        if embedding_model not in available_models:
                            raise ValidationError(f"Embedding model '{embedding_model}' not available")
            except aiohttp.ClientError:
                raise ValidationError("Could not connect to LM Studio")
            
            # Configure LLM if provided
            if parse_request.llm_config:
                from .llm import LMStudioLLM
                # Configure both the parsing agent and its NovaParser base class
                llm = LMStudioLLM(
                    chat_model=parse_request.llm_config["chat_model"],
                    embedding_model=parse_request.llm_config["embedding_model"]
                )
                parsing_agent.llm = llm
                # Also set the LLM for the NovaParser base class
                NovaParser.__init__(
                    parsing_agent,
                    llm=llm,
                    store=parsing_agent.store,
                    vector_store=parsing_agent.vector_store,
                    domain=parsing_agent.domain
                )
            
        # Process the request
        result = await parsing_agent.parse_text(
            parse_request.text,
            metadata={
                "domain": parse_request.domain,
                "llm_config": parse_request.llm_config
            }
        )
        
        return {
            "concepts": result.concepts,
            "key_points": result.key_points,
            "confidence": result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except ValidationError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise ServiceError(str(e))

orchestration_router = APIRouter(
    prefix="/api/orchestration",
    tags=["orchestration"],
    dependencies=[Depends(check_rate_limit)]
)


@ws_router.websocket("/ws")
async def analytics_websocket(
    websocket: WebSocket,
    analytics_agent: AnalyticsAgent = Depends(get_analytics_agent)
):
    """WebSocket endpoint for real-time analytics updates."""
    try:
        # Validate API key using dependency
        api_key = await get_ws_api_key(websocket)
        if not api_key:
            return  # WebSocket already closed by get_ws_api_key
        
        await websocket.accept()
        
        while True:
            try:
                data = await websocket.receive_json()
                
                # Validate request
                try:
                    request = AnalyticsRequest(**data)
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": str(e)
                        }
                    })
                    continue
                
                # Process analytics based on data type
                try:
                    # Handle both sync and async process_analytics
                    if hasattr(analytics_agent.process_analytics, '__call__'):
                        result = analytics_agent.process_analytics(
                            content=data,
                            analytics_type=request.type,
                            metadata={"domain": request.domain} if request.domain else None
                        )
                    else:
                        result = await analytics_agent.process_analytics(
                            content=data,
                            analytics_type=request.type,
                            metadata={"domain": request.domain} if request.domain else None
                        )
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "error": {
                            "code": "PROCESSING_ERROR",
                            "message": str(e)
                        }
                    })
                    continue
                
                # Ensure we have valid analytics data
                analytics = result.analytics if hasattr(result, 'analytics') else {}
                insights = result.insights if hasattr(result, 'insights') else []
                confidence = result.confidence if hasattr(result, 'confidence') else 1.0
                
                # Send analytics update
                await websocket.send_json({
                    "type": "analytics_update",
                    "analytics": analytics,
                    "insights": insights,
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat()
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

@analytics_router.get("/flows", response_model=AnalyticsResponse, dependencies=[Depends(check_rate_limit)])
@retry_on_error(max_retries=3)
async def get_flow_analytics(
    flow_id: Optional[str] = None,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    analytics_agent: AnalyticsAgent = Depends(get_analytics_agent)
) -> Dict:
    """Get analytics for active flows."""
    try:
        content = {
            "type": "flow_analytics",
            "flow_id": flow_id,
            "timestamp": datetime.now().isoformat()
        }
        
        result = await analytics_agent.process_analytics(
            content=content,
            analytics_type="behavioral",
            metadata={"domain": domain} if domain else None
        )
        
        # Extract analytics from LM Studio response
        analytics = {}
        insights = []
        confidence = 0.8

        if hasattr(result, 'analytics') and isinstance(result.analytics, dict):
            analytics = result.analytics.get("analytics", {})
            insights = result.analytics.get("insights", [])
            confidence = result.analytics.get("confidence", 0.8)

        return {
            "analytics": analytics,
            "insights": insights,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@analytics_router.get("/resources", response_model=AnalyticsResponse, dependencies=[Depends(check_rate_limit)])
@retry_on_error(max_retries=3)
async def get_resource_analytics(
    resource_id: Optional[str] = None,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    analytics_agent: AnalyticsAgent = Depends(get_analytics_agent)
) -> Dict:
    """Get analytics for resource utilization."""
    try:
        content = {
            "type": "resource_analytics",
            "resource_id": resource_id,
            "timestamp": datetime.now().isoformat()
        }
        
        result = await analytics_agent.process_analytics(
            content=content,
            analytics_type="predictive",
            metadata={"domain": domain} if domain else None
        )
        
        return {
            "analytics": result.analytics,
            "insights": result.insights,
            "confidence": result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@analytics_router.get("/agents", response_model=AnalyticsResponse, dependencies=[Depends(check_rate_limit)])
@retry_on_error(max_retries=3)
async def get_agent_analytics(
    agent_id: Optional[str] = None,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    analytics_agent: AnalyticsAgent = Depends(get_analytics_agent)
) -> Dict:
    """Get analytics for agent performance."""
    try:
        content = {
            "type": "agent_analytics",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        result = await analytics_agent.process_analytics(
            content=content,
            analytics_type="behavioral",
            metadata={"domain": domain} if domain else None
        )
        
        return {
            "analytics": result.analytics,
            "insights": result.insights,
            "confidence": result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

# Task Management Endpoints
@orchestration_router.get("/tasks")
async def list_tasks(
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """List all tasks."""
    try:
        result = await orchestration_agent.process(
            content={
                "type": "task_list",
                "timestamp": datetime.now().isoformat()
            },
            metadata={"domain": domain} if domain else None
        )
        
        return {
            "tasks": result.orchestration.get("tasks", []),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@orchestration_router.post("/tasks", response_model=TaskResponse)
@validate_request(TaskRequest)
@retry_on_error(max_retries=3)
async def create_task(
    task: TaskRequest,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Create a new task for orchestration."""
    try:
        result = await orchestration_agent.orchestrate_and_store(
            content=task.dict(),
            orchestration_type="task_creation",
            target_domain=domain
        )
        
        # Generate task ID if not provided by orchestration
        task_id = result.orchestration.get("task_id") or str(datetime.now().timestamp())
        
        return {
            "task_id": task_id,
            "status": "created",
            "orchestration": result.orchestration,
            "confidence": result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@orchestration_router.get("/tasks/{task_id}", response_model=TaskResponse)
@retry_on_error(max_retries=3)
async def get_task(
    task_id: str,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Get task status and details."""
    try:
        result = await orchestration_agent.process(
            content={
                "type": "task_query",
                "task_id": task_id
            },
            metadata={"domain": domain} if domain else None
        )
        
        if not result:
            raise ResourceNotFoundError(f"Task {task_id} not found")
            
        return {
            "task_id": task_id,
            "status": result.orchestration.get("status") if hasattr(result, "orchestration") else "success",
            "orchestration": result.orchestration if hasattr(result, "orchestration") else {},
            "confidence": result.confidence if hasattr(result, "confidence") else 1.0,
            "timestamp": datetime.now().isoformat()
        }
    except ResourceNotFoundError:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@orchestration_router.put("/tasks/{task_id}", response_model=TaskResponse)
@validate_request(TaskRequest)
@retry_on_error(max_retries=3)
async def update_task(
    task_id: str,
    updates: TaskRequest,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Update task status or configuration."""
    try:
        result = await orchestration_agent.orchestrate_and_store(
            content={
                "type": "task_update",
                "task_id": task_id,
                "updates": updates.dict()
            },
            orchestration_type="task_update",
            target_domain=domain
        )
        
        return {
            "task_id": task_id,
            "status": "updated",
            "orchestration": result.orchestration,
            "confidence": result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

# Agent Coordination Endpoints
@orchestration_router.get("/agents/coordinate")
async def get_coordination_status(
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read"))
) -> Dict:
    """Get coordination status."""
    raise HTTPException(
        status_code=405,
        detail={
            "code": "METHOD_NOT_ALLOWED",
            "message": "Method not allowed. Use POST to coordinate agents."
        }
    )

@orchestration_router.post("/agents/coordinate", response_model=CoordinationResponse)
@validate_request(CoordinationRequest)
@retry_on_error(max_retries=3)
async def coordinate_agents(
    coordination_request: CoordinationRequest,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Coordinate multiple agents for a task."""
    try:
        # Validate request format
        if not isinstance(coordination_request.dict(), dict):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request format"
                }
            )
            
        result = await orchestration_agent.orchestrate_and_store(
            content=coordination_request.dict(),
            orchestration_type="agent_coordination",
            target_domain=domain
        )
        
        # Generate coordination ID if not provided by orchestration
        coordination_id = result.orchestration.get("coordination_id") or str(datetime.now().timestamp())
        
        return {
            "coordination_id": coordination_id,
            "status": "coordinated",
            "orchestration": result.orchestration,
            "confidence": result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@orchestration_router.post("/agents/{agent_id}/assign", response_model=AgentAssignmentResponse)
@validate_request(AgentAssignmentRequest)
@retry_on_error(max_retries=3)
async def assign_agent(
    agent_id: str,
    assignment: AgentAssignmentRequest,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Assign a task to a specific agent."""
    try:
        result = await orchestration_agent.orchestrate_and_store(
            content={
                "type": "agent_assignment",
                "agent_id": agent_id,
                "assignment": assignment.dict()
            },
            orchestration_type="agent_assignment",
            target_domain=domain
        )
        
        return {
            "agent_id": agent_id,
            "status": "assigned",
            "orchestration": result.orchestration,
            "confidence": result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

# Flow Optimization Endpoints
@orchestration_router.post("/flows/{flow_id}/optimize", response_model=FlowOptimizationResponse)
@retry_on_error(max_retries=3)
async def optimize_flow(
    flow_id: str,
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    analytics_agent: AnalyticsAgent = Depends(get_analytics_agent),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Optimize flow based on analytics insights."""
    try:
        # Get flow analytics
        analytics_result = await analytics_agent.process_analytics(
            content={
                "type": "flow_analytics",
                "flow_id": flow_id,
                "parameters": request.get("parameters", {}),
                "constraints": request.get("constraints", {}),
                "timestamp": datetime.now().isoformat()
            },
            analytics_type="predictive",
            metadata={"domain": domain} if domain else None
        )
        
        # Use insights to optimize flow
        optimizations = []
        for insight in analytics_result.insights:
            if insight.get("type") == "optimization":
                optimizations.append({
                    "type": insight.get("optimization_type"),
                    "description": insight.get("description"),
                    "confidence": insight.get("confidence", 0.0)
                })
        
        return {
            "flow_id": flow_id,
            "optimizations": optimizations,
            "analytics": analytics_result.analytics,
            "confidence": analytics_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

# Resource Management Endpoints
@orchestration_router.post("/resources/allocate", response_model=ResourceAllocationResponse)
@validate_request(ResourceAllocationRequest)
@retry_on_error(max_retries=3)
async def allocate_resources(
    allocation_request: ResourceAllocationRequest,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    analytics_agent: AnalyticsAgent = Depends(get_analytics_agent),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Allocate resources based on analytics predictions."""
    try:
        # Get resource analytics
        analytics_result = await analytics_agent.process_analytics(
            content={
                "type": "resource_analytics",
                "request": allocation_request.dict(),
                "timestamp": datetime.now().isoformat()
            },
            analytics_type="predictive",
            metadata={"domain": domain} if domain else None
        )
        
        # Use predictions to allocate resources
        allocations = []
        for analytic in analytics_result.analytics.get("analytics", {}).values():
            if analytic.get("type") == "resource_prediction":
                allocations.append({
                    "resource_id": analytic.get("resource_id"),
                    "allocation": analytic.get("value", 0.0),
                    "confidence": analytic.get("confidence", 0.0)
                })
        
        return {
            "allocations": allocations,
            "analytics": analytics_result.analytics,
            "confidence": analytics_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

# Memory Operation Endpoints
@orchestration_router.post("/memory/store", response_model=MemoryResponse)
@validate_request(MemoryRequest)
@retry_on_error(max_retries=3)
async def store_memory(
    memory: MemoryRequest,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Store a new memory."""
    try:
        # Configure LLM if provided
        if memory.llm_config:
            llm = LMStudioLLM(
                chat_model=memory.llm_config["chat_model"],
                embedding_model=memory.llm_config.get("embedding_model", EMBEDDING_MODEL)
            )
            orchestration_agent.llm = llm

        result = await orchestration_agent.process(
            content={
                "type": "memory_store",
                "content": memory.content,
                "importance": memory.importance,
                "metadata": {
                    "domain": domain,
                    "llm_config": memory.llm_config,
                    "context": memory.context
                }
            }
        )
        
        # Ensure orchestration details are included
        orchestration_details = result.orchestration if hasattr(result, "orchestration") else {}
        if not orchestration_details:
            orchestration_details = {
                "status": "success",
                "details": {"operation": "store", "type": memory.type}
            }
            
        return {
            "memory_id": result.orchestration.get("memory_id") if hasattr(result, "orchestration") else str(datetime.now().timestamp()),
            "content": memory.content,
            "orchestration": orchestration_details,
            "confidence": getattr(result, "confidence", 1.0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@orchestration_router.get("/memory/{memory_id}", response_model=MemoryResponse)
@retry_on_error(max_retries=3)
async def retrieve_memory(
    memory_id: str,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Retrieve a stored memory."""
    try:
        result = await orchestration_agent.process(
            content={
                "type": "memory_retrieve",
                "memory_id": memory_id,
                "metadata": {
                    "domain": domain
                }
            }
        )
        
        if not result:
            raise ResourceNotFoundError(f"Memory {memory_id} not found")
            
        # Ensure orchestration details are included
        orchestration_details = result.orchestration if hasattr(result, "orchestration") else {}
        if not orchestration_details:
            orchestration_details = {
                "status": "success",
                "details": {"operation": "retrieve", "memory_id": memory_id}
            }
            
        return {
            "memory_id": memory_id,
            "content": {"data": result.orchestration.get("memory")} if hasattr(result, "orchestration") else None,
            "orchestration": orchestration_details,
            "confidence": getattr(result, "confidence", 1.0),
            "timestamp": datetime.now().isoformat()
        }
    except ResourceNotFoundError:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@orchestration_router.post("/memory/search", response_model=MemoryResponse)
@validate_request(MemoryRequest)
@retry_on_error(max_retries=3)
async def search_memories(
    query: MemoryRequest,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Search through stored memories."""
    try:
        # Configure LLM if provided
        if query.llm_config:
            llm = LMStudioLLM(
                chat_model=query.llm_config["chat_model"],
                embedding_model=query.llm_config.get("embedding_model", EMBEDDING_MODEL)
            )
            orchestration_agent.llm = llm

        result = await orchestration_agent.process(
            content={
                "type": "memory_search",
                "query": query.content,
                "importance": query.importance,
                "metadata": {
                    "domain": domain,
                    "llm_config": query.llm_config,
                    "context": query.context
                }
            }
        )
        
        # Ensure orchestration details are included
        orchestration_details = result.orchestration if hasattr(result, "orchestration") else {}
        if not orchestration_details:
            orchestration_details = {
                "status": "success",
                "details": {"operation": "search", "query": query.dict()}
            }
            
        return {
            "matches": result.orchestration.get("matches", []) if hasattr(result, "orchestration") else [],
            "orchestration": orchestration_details,
            "confidence": getattr(result, "confidence", 1.0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))
