"""FastAPI endpoints for Nova's analytics and orchestration."""

from fastapi import APIRouter, HTTPException, WebSocket, Depends, Header, Request
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
import logging
import uuid

from nia.nova.core.analytics import AnalyticsAgent, AnalyticsResult
from nia.nova.core.parsing import NovaParser
from nia.nova.core.llm import LMStudioLLM
from nia.agents.specialized.orchestration_agent import OrchestrationAgent
from nia.agents.specialized.parsing_agent import ParsingAgent
from nia.core.types.memory_types import AgentResponse
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

logger = logging.getLogger(__name__)

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

# Create WebSocket router without dependencies
ws_router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"]
)

# LM Studio configuration
CHAT_MODEL = "llama-3.2-3b-instruct"
EMBEDDING_MODEL = "text-embedding-nomic-embed-text-v1.5@q8_0"

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

async def get_world():
    """Get world instance."""
    return NIAWorld()

async def get_parsing_agent(
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system),
    world: NIAWorld = Depends(get_world),
    llm: LMStudioLLM = Depends(get_llm)
):
    """Get parsing agent instance."""
    # Generate unique name for each agent instance
    agent_name = f"nova_parser_{uuid.uuid4().hex[:8]}"
    agent = ParsingAgent(
        name=agent_name,
        memory_system=memory_system,
        world=world,
        domain="professional"
    )
    agent.llm = llm
    return agent

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

async def get_llm_interface():
    """Get LLM interface instance."""
    return LMStudioLLM(
        chat_model=CHAT_MODEL,
        embedding_model=EMBEDDING_MODEL
    )

async def get_tiny_factory(
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
):
    """Get TinyFactory instance."""
    from nia.agents.tinytroupe_agent import TinyFactory
    return TinyFactory(memory_system=memory_system)

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
    analytics_agent: AnalyticsAgent = Depends(get_analytics_agent)
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
    analytics_agent: AnalyticsAgent = Depends(get_analytics_agent)
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

@orchestration_router.post("/agents/create")
@retry_on_error(max_retries=3)
async def create_agent(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    tiny_factory: Any = Depends(get_tiny_factory),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
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

# Task retrieval and update endpoints for hierarchical pattern
@orchestration_router.get("/swarms/hierarchical/{task_id}")
@retry_on_error(max_retries=3)
async def get_hierarchical_task(
    task_id: str,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Get hierarchical swarm task details."""
    try:
        task_result = await orchestration_agent.get_task(
            task_id=task_id,
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        if task_result.swarm_pattern != "hierarchical":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_PATTERN",
                    "message": f"Task {task_id} is not a hierarchical swarm task"
                }
            )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "hierarchical",
            "orchestration": task_result.orchestration,
            "confidence": task_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.put("/swarms/hierarchical/{task_id}")
@retry_on_error(max_retries=3)
@validate_request(TaskRequest)
async def update_hierarchical_task(
    task_id: str,
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Update hierarchical swarm task."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        supervisor_id = request.get("supervisor_id")
        if not supervisor_id:
            raise ValidationError("hierarchical pattern requires supervisor_id")
            
        worker_ids = request.get("worker_ids", [])
        if not worker_ids:
            raise ValidationError("hierarchical pattern requires worker_ids")
        
        # Update task
        task_result = await orchestration_agent.update_task(
            task_id=task_id,
            task_data={
                **request,
                "swarm_pattern": "hierarchical",
                "assigned_agents": [supervisor_id] + worker_ids,
                "supervisor_id": supervisor_id,
                "worker_ids": worker_ids
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "swarm_pattern": "hierarchical",
                "supervisor_id": supervisor_id,
                "worker_ids": worker_ids
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": "updated",
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "hierarchical",
            "orchestration": task_result.orchestration,
            "confidence": task_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.post("/swarms/hierarchical")
@retry_on_error(max_retries=3)
@validate_request(TaskRequest)
async def create_hierarchical_task(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """Create a hierarchical swarm task with supervisor and worker agents."""
    try:
        # Check domain access
        if request.get("domain") and not request.get("cross_domain_approved"):
            # Get agent domains
            agent_domains = []
            supervisor_id = request.get("supervisor_id")
            worker_ids = request.get("worker_ids", [])
            for agent_id in [supervisor_id] + worker_ids:
                agent_data = await memory_system.semantic.search(
                    query=f"id:{agent_id}"
                )
                if agent_data:
                    agent_domains.append(agent_data[0].get("domain"))
            
            # Check if any agent is from a different domain
            task_domain = request.get("domain")
            if any(d != task_domain for d in agent_domains if d):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "DOMAIN_ACCESS_DENIED",
                        "message": "Cross-domain operation requires approval"
                    }
                )
        
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        supervisor_id = request.get("supervisor_id")
        if not supervisor_id:
            raise ValidationError("hierarchical pattern requires supervisor_id")
            
        worker_ids = request.get("worker_ids", [])
        if not worker_ids:
            raise ValidationError("hierarchical pattern requires worker_ids")
        
        # Create task with hierarchical pattern
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task_result = await orchestration_agent.create_task(
            task_id=task_id,
            task_data={
                **request,
                "swarm_pattern": "hierarchical",
                "assigned_agents": [supervisor_id] + worker_ids,
                "supervisor_id": supervisor_id,
                "worker_ids": worker_ids
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "swarm_pattern": "hierarchical",
                "supervisor_id": supervisor_id,
                "worker_ids": worker_ids
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "hierarchical",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

# Task retrieval and update endpoints for voting pattern
@orchestration_router.get("/swarms/voting/{task_id}")
@retry_on_error(max_retries=3)
async def get_voting_task(
    task_id: str,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Get voting swarm task details."""
    try:
        task_result = await orchestration_agent.get_task(
            task_id=task_id,
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        if task_result.swarm_pattern != "MajorityVoting":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_PATTERN",
                    "message": f"Task {task_id} is not a voting swarm task"
                }
            )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "MajorityVoting",
            "orchestration": task_result.orchestration,
            "confidence": task_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.put("/swarms/voting/{task_id}")
@retry_on_error(max_retries=3)
@validate_request(TaskRequest)
async def update_voting_task(
    task_id: str,
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Update voting swarm task."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        voter_ids = request.get("voter_ids", [])
        if not voter_ids:
            raise ValidationError("voting pattern requires voter_ids")
        
        # Update task
        task_result = await orchestration_agent.update_task(
            task_id=task_id,
            task_data={
                **request,
                "swarm_pattern": "MajorityVoting",
                "assigned_agents": voter_ids,
                "voter_ids": voter_ids,
                "decision_threshold": request.get("decision_threshold", 0.5)
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "swarm_pattern": "MajorityVoting",
                "voter_ids": voter_ids,
                "decision_threshold": request.get("decision_threshold", 0.5)
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": "updated",
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "MajorityVoting",
            "orchestration": task_result.orchestration,
            "confidence": task_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.post("/swarms/voting")
@retry_on_error(max_retries=3)
@validate_request(TaskRequest)
async def create_voting_task(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """Create a majority voting swarm task."""
    try:
        # Check domain access
        if request.get("domain") and not request.get("cross_domain_approved"):
            # Get agent domains
            agent_domains = []
            for agent_id in request.get("voter_ids", []):
                agent_data = await memory_system.semantic.search(
                    query=f"id:{agent_id}"
                )
                if agent_data:
                    agent_domains.append(agent_data[0].get("domain"))
            
            # Check if any agent is from a different domain
            task_domain = request.get("domain")
            if any(d != task_domain for d in agent_domains if d):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "DOMAIN_ACCESS_DENIED",
                        "message": "Cross-domain operation requires approval"
                    }
                )
        
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        voter_ids = request.get("voter_ids", [])
        if not voter_ids:
            raise ValidationError("voting pattern requires voter_ids")
        
        # Create task with voting pattern
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task_result = await orchestration_agent.create_task(
            task_id=task_id,
            task_data={
                **request,
                "swarm_pattern": "MajorityVoting",
                "assigned_agents": voter_ids,
                "voter_ids": voter_ids,
                "decision_threshold": request.get("decision_threshold", 0.5)
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "swarm_pattern": "MajorityVoting",
                "voter_ids": voter_ids,
                "decision_threshold": request.get("decision_threshold", 0.5)
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "MajorityVoting",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

# Task retrieval and update endpoints for round-robin pattern
@orchestration_router.get("/swarms/round-robin/{task_id}")
@retry_on_error(max_retries=3)
async def get_round_robin_task(
    task_id: str,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Get round-robin swarm task details."""
    try:
        task_result = await orchestration_agent.get_task(
            task_id=task_id,
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        if task_result.swarm_pattern != "RoundRobin":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_PATTERN",
                    "message": f"Task {task_id} is not a round-robin swarm task"
                }
            )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "RoundRobin",
            "orchestration": task_result.orchestration,
            "confidence": task_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.put("/swarms/round-robin/{task_id}")
@retry_on_error(max_retries=3)
@validate_request(TaskRequest)
async def update_round_robin_task(
    task_id: str,
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Update round-robin swarm task."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        agent_ids = request.get("agent_ids", [])
        if not agent_ids:
            raise ValidationError("round-robin pattern requires agent_ids")
        
        subtasks = request.get("subtasks", [])
        if not subtasks:
            raise ValidationError("round-robin pattern requires subtasks")
        
        # Update task
        task_result = await orchestration_agent.update_task(
            task_id=task_id,
            task_data={
                **request,
                "swarm_pattern": "RoundRobin",
                "assigned_agents": agent_ids,
                "agent_ids": agent_ids,
                "subtasks": subtasks
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "swarm_pattern": "RoundRobin",
                "agent_ids": agent_ids,
                "subtasks": subtasks
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": "updated",
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "RoundRobin",
            "orchestration": task_result.orchestration,
            "confidence": task_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.post("/swarms/round-robin")
@retry_on_error(max_retries=3)
@validate_request(TaskRequest)
async def create_round_robin_task(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """Create a round-robin swarm task with cyclic task distribution."""
    try:
        # Check domain access
        if request.get("domain") and not request.get("cross_domain_approved"):
            # Get agent domains
            agent_domains = []
            for agent_id in request.get("agent_ids", []):
                agent_data = await memory_system.semantic.search(
                    query=f"id:{agent_id}"
                )
                if agent_data:
                    agent_domains.append(agent_data[0].get("domain"))
            
            # Check if any agent is from a different domain
            task_domain = request.get("domain")
            if any(d != task_domain for d in agent_domains if d):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "DOMAIN_ACCESS_DENIED",
                        "message": "Cross-domain operation requires approval"
                    }
                )
        
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        agent_ids = request.get("agent_ids", [])
        if not agent_ids:
            raise ValidationError("round-robin pattern requires agent_ids")
        
        subtasks = request.get("subtasks", [])
        if not subtasks:
            raise ValidationError("round-robin pattern requires subtasks")
        
        # Create task with round-robin pattern
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task_result = await orchestration_agent.create_task(
            task_id=task_id,
            task_data={
                **request,
                "swarm_pattern": "RoundRobin",
                "assigned_agents": agent_ids,
                "agent_ids": agent_ids,
                "subtasks": subtasks
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "swarm_pattern": "RoundRobin",
                "agent_ids": agent_ids,
                "subtasks": subtasks
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "RoundRobin",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

# Task retrieval and update endpoints for mesh pattern
@orchestration_router.get("/swarms/mesh/{task_id}")
@retry_on_error(max_retries=3)
async def get_mesh_task(
    task_id: str,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Get mesh swarm task details."""
    try:
        task_result = await orchestration_agent.get_task(
            task_id=task_id,
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        if task_result.swarm_pattern != "mesh":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_PATTERN",
                    "message": f"Task {task_id} is not a mesh swarm task"
                }
            )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "mesh",
            "orchestration": task_result.orchestration,
            "confidence": task_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.put("/swarms/mesh/{task_id}")
@retry_on_error(max_retries=3)
@validate_request(TaskRequest)
async def update_mesh_task(
    task_id: str,
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Update mesh swarm task."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        agent_ids = request.get("agent_ids", [])
        if not agent_ids:
            raise ValidationError("mesh pattern requires agent_ids")
        
        # Update task
        task_result = await orchestration_agent.update_task(
            task_id=task_id,
            task_data={
                **request,
                "swarm_pattern": "mesh",
                "assigned_agents": agent_ids
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "swarm_pattern": "mesh",
                "assigned_agents": agent_ids,
                "communication_patterns": request.get("communication_patterns", [])
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": "updated",
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "mesh",
            "orchestration": task_result.orchestration,
            "confidence": task_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.post("/swarms/mesh")
@retry_on_error(max_retries=3)
@validate_request(TaskRequest)
async def create_mesh_task(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """Create a mesh swarm task with free-form agent communication."""
    try:
        # Check domain access
        if request.get("domain") and not request.get("cross_domain_approved"):
            # Get agent domains
            agent_domains = []
            for agent_id in request.get("agent_ids", []):
                agent_data = await memory_system.semantic.search(
                    query=f"id:{agent_id}"
                )
                if agent_data:
                    agent_domains.append(agent_data[0].get("domain"))
            
            # Check if any agent is from a different domain
            task_domain = request.get("domain")
            if any(d != task_domain for d in agent_domains if d):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "DOMAIN_ACCESS_DENIED",
                        "message": "Cross-domain operation requires approval"
                    }
                )
        
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        agent_ids = request.get("agent_ids", [])
        if not agent_ids:
            raise ValidationError("mesh pattern requires agent_ids")
        
        # Create task with mesh pattern
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task_result = await orchestration_agent.create_task(
            task_id=task_id,
            task_data={
                **request,
                "swarm_pattern": "mesh",
                "assigned_agents": agent_ids
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "swarm_pattern": "mesh",
                "assigned_agents": agent_ids,
                "communication_patterns": request.get("communication_patterns", [])
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "mesh",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

# Task retrieval and update endpoints for swarm patterns
@orchestration_router.get("/swarms/parallel/{task_id}")
@retry_on_error(max_retries=3)
async def get_parallel_task(
    task_id: str,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Get parallel swarm task details."""
    try:
        task_result = await orchestration_agent.get_task(
            task_id=task_id,
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        if task_result.swarm_pattern != "parallel":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_PATTERN",
                    "message": f"Task {task_id} is not a parallel swarm task"
                }
            )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "parallel",
            "orchestration": task_result.orchestration,
            "confidence": task_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.put("/swarms/parallel/{task_id}")
@retry_on_error(max_retries=3)
@validate_request(TaskRequest)
async def update_parallel_task(
    task_id: str,
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Update parallel swarm task."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        agent_ids = request.get("agent_ids", [])
        if not agent_ids:
            raise ValidationError("parallel pattern requires agent_ids")
        
        subtasks = request.get("subtasks", [])
        if not subtasks:
            raise ValidationError("parallel pattern requires subtasks")
        
        # Update task
        task_result = await orchestration_agent.update_task(
            task_id=task_id,
            task_data={
                **request,
                "swarm_pattern": "parallel",
                "assigned_agents": agent_ids
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "swarm_pattern": "parallel",
                "assigned_agents": agent_ids,
                "subtasks": subtasks
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": "updated",
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "parallel",
            "orchestration": task_result.orchestration,
            "confidence": task_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.post("/swarms/parallel")
@retry_on_error(max_retries=3)
@validate_request(TaskRequest)
async def create_parallel_task(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """Create a parallel swarm task with independent agents."""
    try:
        # Check domain access
        if request.get("domain") and not request.get("cross_domain_approved"):
            # Get agent domains
            agent_domains = []
            for agent_id in request.get("agent_ids", []):
                agent_data = await memory_system.semantic.search(
                    query=f"id:{agent_id}"
                )
                if agent_data:
                    agent_domains.append(agent_data[0].get("domain"))
            
            # Check if any agent is from a different domain
            task_domain = request.get("domain")
            if any(d != task_domain for d in agent_domains if d):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "DOMAIN_ACCESS_DENIED",
                        "message": "Cross-domain operation requires approval"
                    }
                )
        
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        agent_ids = request.get("agent_ids", [])
        if not agent_ids:
            raise ValidationError("parallel pattern requires agent_ids")
        
        subtasks = request.get("subtasks", [])
        if not subtasks:
            raise ValidationError("parallel pattern requires subtasks")
        
        # Create task with parallel pattern
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task_result = await orchestration_agent.create_task(
            task_id=task_id,
            task_data={
                **request,
                "swarm_pattern": "parallel",
                "assigned_agents": agent_ids
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "swarm_pattern": "parallel",
                "assigned_agents": agent_ids,
                "subtasks": subtasks
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "parallel",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

# Task retrieval and update endpoints for sequential pattern
@orchestration_router.get("/swarms/sequential/{task_id}")
@retry_on_error(max_retries=3)
async def get_sequential_task(
    task_id: str,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Get sequential swarm task details."""
    try:
        task_result = await orchestration_agent.get_task(
            task_id=task_id,
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        if task_result.swarm_pattern != "sequential":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_PATTERN",
                    "message": f"Task {task_id} is not a sequential swarm task"
                }
            )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "sequential",
            "orchestration": task_result.orchestration,
            "confidence": task_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.put("/swarms/sequential/{task_id}")
@retry_on_error(max_retries=3)
@validate_request(TaskRequest)
async def update_sequential_task(
    task_id: str,
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Update sequential swarm task."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        agent_sequence = request.get("agent_sequence", [])
        if not agent_sequence:
            raise ValidationError("sequential pattern requires agent_sequence")
        
        # Extract agent IDs and types
        agent_ids = [agent[0] for agent in agent_sequence]
        agent_types = [agent[1] for agent in agent_sequence]
        
        # Update task
        task_result = await orchestration_agent.update_task(
            task_id=task_id,
            task_data={
                **request,
                "swarm_pattern": "sequential",
                "assigned_agents": agent_ids,
                "agent_types": agent_types
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "swarm_pattern": "sequential",
                "assigned_agents": agent_ids,
                "agent_types": agent_types,
                "input_data": request.get("input_data")
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": "updated",
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "sequential",
            "orchestration": task_result.orchestration,
            "confidence": task_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.post("/swarms/sequential")
@retry_on_error(max_retries=3)
@validate_request(TaskRequest)
async def create_sequential_task(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """Create a sequential swarm task with ordered processing."""
    try:
        # Check domain access
        if request.get("domain") and not request.get("cross_domain_approved"):
            # Get agent domains
            agent_domains = []
            agent_sequence = request.get("agent_sequence", [])
            for agent_id, _ in agent_sequence:
                agent_data = await memory_system.semantic.search(
                    query=f"id:{agent_id}"
                )
                if agent_data:
                    agent_domains.append(agent_data[0].get("domain"))
            
            # Check if any agent is from a different domain
            task_domain = request.get("domain")
            if any(d != task_domain for d in agent_domains if d):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "DOMAIN_ACCESS_DENIED",
                        "message": "Cross-domain operation requires approval"
                    }
                )
        
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        agent_sequence = request.get("agent_sequence", [])
        if not agent_sequence:
            raise ValidationError("sequential pattern requires agent_sequence")
        
        # Extract agent IDs and types
        agent_ids = [agent[0] for agent in agent_sequence]
        agent_types = [agent[1] for agent in agent_sequence]
        
        # Create task with sequential pattern
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task_result = await orchestration_agent.create_task(
            task_id=task_id,
            task_data={
                **request,
                "swarm_pattern": "sequential",
                "assigned_agents": agent_ids,
                "agent_types": agent_types
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "swarm_pattern": "sequential",
                "assigned_agents": agent_ids,
                "agent_types": agent_types,
                "input_data": request.get("input_data")
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": "sequential",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.post("/tasks", deprecated=True)
@retry_on_error(max_retries=3)
async def create_task(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """[Deprecated] Create a new task with specified pattern and agents.
    
    This endpoint is deprecated. Please use the pattern-specific endpoints:
    - /swarms/hierarchical for supervisor/worker pattern
    - /swarms/voting for majority voting pattern
    - /swarms/round-robin for cyclic task distribution
    - /swarms/mesh for free-form communication
    - /swarms/parallel for independent task processing
    - /swarms/sequential for ordered task processing
    """
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        # Process task creation with validation
        swarm_pattern = request.get("swarm_pattern") or request.get("swarm_type")
        
        # Handle different agent assignment fields based on pattern
        assigned_agents = []
        if swarm_pattern == "MajorityVoting":
            assigned_agents = request.get("voter_ids", [])
        elif swarm_pattern == "RoundRobin":
            assigned_agents = request.get("agent_ids", [])
        elif swarm_pattern == "hierarchical":
            # For hierarchical pattern, combine supervisor and workers
            supervisor_id = request.get("supervisor_id")
            worker_ids = request.get("worker_ids", [])
            if not supervisor_id:
                raise ValidationError("hierarchical pattern requires supervisor_id")
            if not worker_ids:
                raise ValidationError("hierarchical pattern requires worker_ids")
            assigned_agents = [supervisor_id] + worker_ids
        else:
            assigned_agents = request.get("assigned_agents", [])
            if swarm_pattern and not assigned_agents:
                raise ValidationError("swarm_pattern requires assigned_agents")
            
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task_result = await orchestration_agent.create_task(
            task_id=task_id,
            task_data={
                **request,
                "assigned_agents": assigned_agents,  # Normalize agent assignments
                "supervisor_id": request.get("supervisor_id") if swarm_pattern == "hierarchical" else None,
                "worker_ids": request.get("worker_ids") if swarm_pattern == "hierarchical" else None,
                "voter_ids": request.get("voter_ids") if swarm_pattern == "MajorityVoting" else None,
                "agent_ids": request.get("agent_ids") if swarm_pattern == "RoundRobin" else None
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "swarm_pattern": swarm_pattern,
                "assigned_agents": assigned_agents
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "assigned_agents": task_result.assigned_agents,
            "swarm_pattern": swarm_pattern,  # Use normalized pattern
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@orchestration_router.post("/swarms/decide")
@retry_on_error(max_retries=3)
async def decide_swarm_pattern(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Decide optimal swarm pattern for a given task."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        if "task" not in request:
            raise ValidationError("Request must include 'task' field")
        
        # Generate task ID for decision
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # Get swarm pattern decision
        decision = await orchestration_agent.decide_swarm_pattern(
            task_id=task_id,
            task=request["task"],
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "task_type": request["task"].get("type"),
                "requirements": request["task"].get("requirements", {})
            } if domain else None
        )
        
        return {
            "task_id": decision.task_id,
            "selected_pattern": decision.pattern,
            "reasoning": decision.reasoning,
            "confidence": decision.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@analytics_router.get("/agents", response_model=AnalyticsResponse)
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
        # Validate request format
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        if "parameters" not in request:
            raise ValidationError("Request must include 'parameters' field")
            
        if "constraints" not in request:
            raise ValidationError("Request must include 'constraints' field")
            
        # Get flow analytics
        try:
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
        
        # Use insights to optimize flow
        optimizations = []
        for insight in analytics_result.insights:
            if insight.get("type") == "optimization":
                optimizations.append({
                    "type": insight.get("optimization_type"),
                    "description": insight.get("description"),
                    "confidence": insight.get("confidence", 0.0)
                })
        
        # Process flow optimization
        flow_result = await orchestration_agent.process_flow(
            flow_id=flow_id,
            optimizations=optimizations,
            parameters=request.get("parameters", {}),
            constraints=request.get("constraints", {}),
            metadata={"domain": domain} if domain else None
        )
        
        return {
            "flow_id": flow_id,
            "optimizations": optimizations,
            "analytics": analytics_result.analytics,
            "confidence": analytics_result.confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))
