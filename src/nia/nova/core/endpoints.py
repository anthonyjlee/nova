"""FastAPI endpoints for Nova's analytics and orchestration."""

from fastapi import APIRouter, HTTPException, WebSocket, Depends, Header
from typing import Dict, List, Optional
from datetime import datetime

from nia.nova.core.analytics import AnalyticsAgent, AnalyticsResult
from nia.agents.specialized.orchestration_agent import OrchestrationAgent
from nia.memory.types.memory_types import AgentResponse

from .auth import check_rate_limit, check_domain_access, get_permission
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
    AgentAssignmentResponse
)

# Create routers with dependencies
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

# Initialize agents
analytics_agent = AnalyticsAgent(domain="professional")  # Default to professional domain
orchestration_agent = OrchestrationAgent(name="nova_orchestrator", domain="professional")

@analytics_router.get("/flows", response_model=AnalyticsResponse)
@retry_on_error(max_retries=3)
async def get_flow_analytics(
    flow_id: Optional[str] = None,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read"))
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
        
        return {
            "analytics": result.analytics,
            "insights": result.insights,
            "confidence": result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@analytics_router.get("/resources", response_model=AnalyticsResponse)
@retry_on_error(max_retries=3)
async def get_resource_analytics(
    resource_id: Optional[str] = None,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read"))
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

@analytics_router.get("/agents", response_model=AnalyticsResponse)
@retry_on_error(max_retries=3)
async def get_agent_analytics(
    agent_id: Optional[str] = None,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read"))
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

@analytics_router.websocket("/ws")
async def analytics_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time analytics updates."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            
            # Validate request
            request = AnalyticsRequest(**data)
            
            # Process analytics based on data type
            result = await analytics_agent.process_analytics(
                content=data,
                analytics_type=request.type,
                metadata={"domain": request.domain} if request.domain else None
            )
            
            # Send analytics update
            await websocket.send_json({
                "type": "analytics_update",
                "analytics": result.analytics,
                "insights": result.insights,
                "confidence": result.confidence,
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "detail": str(e)
        })
    finally:
        await websocket.close()

# Task Management Endpoints
@orchestration_router.post("/tasks", response_model=TaskResponse)
@validate_request(TaskRequest)
@retry_on_error(max_retries=3)
async def create_task(
    task: TaskRequest,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write"))
) -> Dict:
    """Create a new task for orchestration."""
    try:
        result = await orchestration_agent.orchestrate_and_store(
            content=task.dict(),
            orchestration_type="task_creation",
            target_domain=domain
        )
        
        return {
            "task_id": result.orchestration.get("task_id"),
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
    _: None = Depends(get_permission("read"))
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
            "status": result.orchestration.get("status"),
            "orchestration": result.orchestration,
            "confidence": result.confidence,
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
    _: None = Depends(get_permission("write"))
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
@orchestration_router.post("/agents/coordinate", response_model=CoordinationResponse)
@validate_request(CoordinationRequest)
@retry_on_error(max_retries=3)
async def coordinate_agents(
    coordination_request: CoordinationRequest,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write"))
) -> Dict:
    """Coordinate multiple agents for a task."""
    try:
        result = await orchestration_agent.orchestrate_and_store(
            content=coordination_request.dict(),
            orchestration_type="agent_coordination",
            target_domain=domain
        )
        
        return {
            "coordination_id": result.orchestration.get("coordination_id"),
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
    _: None = Depends(get_permission("write"))
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
@validate_request(FlowOptimizationRequest)
@retry_on_error(max_retries=3)
async def optimize_flow(
    flow_id: str,
    request: FlowOptimizationRequest,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write"))
) -> Dict:
    """Optimize flow based on analytics insights."""
    try:
        # Get flow analytics
        analytics_result = await analytics_agent.process_analytics(
            content={
                "type": "flow_analytics",
                "flow_id": flow_id,
                "parameters": request.parameters,
                "constraints": request.constraints,
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
    _: None = Depends(get_permission("write"))
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
    _: None = Depends(get_permission("write"))
) -> Dict:
    """Store a new memory."""
    try:
        result = await orchestration_agent.process(
            content={
                "type": "memory_store",
                "memory": memory.dict()
            },
            metadata={"domain": domain} if domain else None
        )
        
        return {
            "memory_id": result.orchestration.get("memory_id"),
            "status": "stored",
            "orchestration": result.orchestration,
            "confidence": result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@orchestration_router.get("/memory/{memory_id}", response_model=MemoryResponse)
@retry_on_error(max_retries=3)
async def retrieve_memory(
    memory_id: str,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read"))
) -> Dict:
    """Retrieve a stored memory."""
    try:
        result = await orchestration_agent.process(
            content={
                "type": "memory_retrieve",
                "memory_id": memory_id
            },
            metadata={"domain": domain} if domain else None
        )
        
        if not result:
            raise ResourceNotFoundError(f"Memory {memory_id} not found")
            
        return {
            "memory_id": memory_id,
            "content": result.orchestration.get("memory"),
            "orchestration": result.orchestration,
            "confidence": result.confidence,
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
    _: None = Depends(get_permission("read"))
) -> Dict:
    """Search through stored memories."""
    try:
        result = await orchestration_agent.process(
            content={
                "type": "memory_search",
                "query": query.dict()
            },
            metadata={"domain": domain} if domain else None
        )
        
        return {
            "matches": result.orchestration.get("matches", []),
            "orchestration": result.orchestration,
            "confidence": result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))
