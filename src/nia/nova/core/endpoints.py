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
                    # First validate the request
                    request = AnalyticsRequest(**data)
                    
                    # Then process analytics
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
