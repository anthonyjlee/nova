"""Nova-specific endpoints."""

import uuid
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator, model_validator
from fastapi import APIRouter, Depends, HTTPException
from .dependencies import (
    get_memory_system,
    get_agent_store,
    get_llm_interface,
    # Core cognitive agents
    get_belief_agent,
    get_desire_agent,
    get_emotion_agent,
    get_reflection_agent,
    get_meta_agent,
    get_self_model_agent,
    get_analysis_agent,
    get_research_agent,
    get_integration_agent,
    get_task_agent,
    get_response_agent,
    # Support agents
    get_parsing_agent,
    get_orchestration_agent,
    get_dialogue_agent,
    get_context_agent,
    get_validation_agent,
    get_synthesis_agent,
    get_alerting_agent,
    get_monitoring_agent,
    get_schema_agent
)
from .auth import get_permission
from .error_handling import ServiceError, InitializationError
from nia.core.types import (
    Memory, MemoryType, DomainContext, ValidationSchema
)
from nia.core.types.memory_types import TaskState, DomainTransfer
from nia.core.neo4j.agent_store import AgentStore

logger = logging.getLogger(__name__)

class AgentMetrics(BaseModel):
    """Model for agent performance metrics."""
    response_time: float = Field(..., description="Average response time in seconds")
    tasks_completed: int = Field(..., description="Number of completed tasks")
    success_rate: float = Field(..., description="Success rate as a percentage")
    uptime: float = Field(..., description="Uptime percentage")
    last_active: datetime = Field(..., description="Last active timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metrics metadata")

    model_config = {
        "populate_by_name": True
    }

class AgentResponse(BaseModel):
    """Response model for agent operations."""
    agent_id: str = Field(..., description="Unique agent ID")
    name: str = Field(..., description="Agent name")
    type: str = Field(..., description="Agent type (usually 'agent')")
    agentType: str = Field(..., description="Specific agent type (e.g., 'test', 'meta', etc.)")
    status: str = Field(..., description="Agent status")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Agent metadata")
    timestamp: str = Field(..., description="ISO format timestamp")

    model_config = {
        "populate_by_name": True
    }

class AgentInfo(BaseModel):
    """Request model for agent creation/update."""
    name: str = Field(..., description="Agent name")
    type: str = Field(..., description="Agent type")
    status: str = Field(..., description="Agent status")
    team_id: Optional[str] = Field(None, description="Team ID")
    channel_id: Optional[str] = Field(None, description="Channel ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Agent metadata")

    model_config = {
        "populate_by_name": True
    }

    @validator("status")
    def validate_status(cls, v):
        """Validate status is valid."""
        valid_statuses = ["active", "inactive", "error"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v

    @validator("metadata")
    def validate_metadata(cls, v):
        """Validate metadata has required fields."""
        if "capabilities" not in v:
            v["capabilities"] = []
        return v

# Message Models
class AgentAction(BaseModel):
    """Record of an agent's action in a conversation."""
    agent_id: str
    action_type: str = Field(..., description="Type of action performed")
    timestamp: datetime
    details: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]]

    model_config = {
        "populate_by_name": True
    }

class MessageMetadata(BaseModel):
    """Enhanced message metadata to track agent activities."""
    agent_actions: List[AgentAction] = Field(default_factory=list)
    cognitive_state: Optional[Dict[str, Any]]
    task_context: Optional[Dict[str, Any]]
    debug_info: Optional[Dict[str, Any]]

    model_config = {
        "populate_by_name": True
    }

class Message(BaseModel):
    """Enhanced message model with agent tracking."""
    id: str
    content: str
    sender_type: str
    sender_id: str
    timestamp: datetime
    metadata: MessageMetadata

    model_config = {
        "populate_by_name": True
    }

# Request/Response Models
class DebugFlags(BaseModel):
    """Debug flags for testing and development."""
    trace_initialization: bool = Field(default=False, description="Enable initialization tracing")
    trace_dependencies: bool = Field(default=False, description="Enable dependency tracing")
    simulate_errors: Optional[Dict[str, bool]] = Field(default=None, description="Simulate initialization errors")

    model_config = {
        "populate_by_name": True
    }

class NovaRequest(BaseModel):
    """Request model for Nova's ask endpoint."""
    content: str
    workspace: str = Field(default="personal", pattern="^(personal|professional)$")
    debug_flags: Optional[DebugFlags] = None

    model_config = {
        "populate_by_name": True
    }

    @validator("content")
    def validate_content(cls, v):
        """Validate content is not empty."""
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()

    @validator("workspace")
    def validate_workspace(cls, v):
        """Validate workspace is valid."""
        if v not in ["personal", "professional"]:
            raise ValueError("Workspace must be 'personal' or 'professional'")
        return v

    @model_validator(mode='after')
    def validate_debug_flags(self) -> 'NovaRequest':
        """Validate debug flags are only used in test environment."""
        if self.debug_flags:
            # Allow debug flags in test environment and during testing
            if not (logger.getEffectiveLevel() == logging.DEBUG or "pytest" in sys.modules):
                raise ValueError("Debug flags can only be used in test environment")
        return self


class NovaResponse(BaseModel):
    """Response model for Nova's ask endpoint."""
    threadId: str
    message: Message
    agent_actions: List[AgentAction]

    model_config = {
        "populate_by_name": True
    }

nova_router = APIRouter(
    prefix="/api/nova",
    tags=["Nova"],
    dependencies=[Depends(get_permission("write"))]
)

# Agent endpoints
@nova_router.get("/agents", response_model=List[AgentResponse])
async def list_agents(
    agent_type: Optional[str] = None,
    workspace: Optional[str] = None,
    domain: Optional[str] = None,
    agent_store: AgentStore = Depends(get_agent_store)
) -> List[AgentResponse]:
    """List all agents with optional filters."""
    try:
        agents = await agent_store.search_agents(
            agent_type=agent_type,
            workspace=workspace,
            domain=domain
        )
        processed_agents = []
        for agent in agents:
            # Extract content from payload if needed
            if isinstance(agent, dict) and "payload" in agent:
                agent = agent["payload"].get("content", agent)
                
            processed_agents.append(AgentResponse(
                agent_id=agent["id"],
                name=agent["name"],
                type="agent",
                agentType=agent["type"],
                status=agent["status"],
                capabilities=agent["metadata"].get("capabilities", []),
                metadata=agent["metadata"],
                timestamp=datetime.now().isoformat()
            ))
        return processed_agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@nova_router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    agent_store: AgentStore = Depends(get_agent_store)
) -> AgentResponse:
    """Get a specific agent by ID."""
    try:
        agent = await agent_store.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Extract content from payload if needed
        if isinstance(agent, dict) and "payload" in agent:
            agent = agent["payload"].get("content", agent)
            
        return AgentResponse(
            agent_id=agent["id"],
            name=agent["name"],
            type="agent",
            agentType=agent["type"],
            status=agent["status"],
            capabilities=agent["metadata"].get("capabilities", []),
            metadata=agent["metadata"],
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@nova_router.post("/agents", response_model=AgentResponse)
async def create_agent(
    agent: AgentInfo,
    thread_id: Optional[str] = None,
    agent_store: AgentStore = Depends(get_agent_store)
) -> AgentResponse:
    """Create a new agent."""
    try:
        agent_data = {
            "id": str(uuid.uuid4()),
            "name": agent.name,
            "type": agent.type,
            "status": agent.status,
            "team_id": agent.team_id,
            "channel_id": agent.channel_id,
            "metadata": agent.metadata
        }
        
        agent_id = await agent_store.store_agent(agent_data, thread_id)
        stored_agent = await agent_store.get_agent(agent_id)
        
        if not stored_agent:
            raise HTTPException(status_code=500, detail="Failed to create agent")
            
        # Extract content from payload if needed
        if isinstance(stored_agent, dict) and "payload" in stored_agent:
            stored_agent = stored_agent["payload"].get("content", stored_agent)
            
        return AgentResponse(
            agent_id=stored_agent["id"],
            name=stored_agent["name"],
            type="agent",
            agentType=stored_agent["type"],
            status=stored_agent["status"],
            capabilities=stored_agent["metadata"].get("capabilities", []),
            metadata=stored_agent["metadata"],
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@nova_router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent: AgentInfo,
    agent_store: AgentStore = Depends(get_agent_store)
) -> AgentResponse:
    """Update an existing agent."""
    try:
        # Verify agent exists
        existing_agent = await agent_store.get_agent(agent_id)
        if not existing_agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Update agent
        await agent_store.update_agent(agent_id, {
            "name": agent.name,
            "type": agent.type,
            "status": agent.status,
            "team_id": agent.team_id,
            "channel_id": agent.channel_id,
            "metadata": agent.metadata
        })
        
        updated_agent = await agent_store.get_agent(agent_id)
        
        # Extract content from payload if needed
        if isinstance(updated_agent, dict) and "payload" in updated_agent:
            updated_agent = updated_agent["payload"].get("content", updated_agent)
            
        return AgentResponse(
            agent_id=updated_agent["id"],
            name=updated_agent["name"],
            type="agent",
            agentType=updated_agent["type"],
            status=updated_agent["status"],
            capabilities=updated_agent["metadata"].get("capabilities", []),
            metadata=updated_agent["metadata"],
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@nova_router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    thread_id: Optional[str] = None,
    agent_store: AgentStore = Depends(get_agent_store)
):
    """Delete an agent or remove from thread."""
    try:
        await agent_store.delete_agent(agent_id, thread_id)
        return {"message": "Agent deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@nova_router.get("/agents/{agent_id}/metrics", response_model=AgentMetrics)
async def get_agent_metrics(
    agent_id: str,
    agent_store: AgentStore = Depends(get_agent_store)
) -> AgentMetrics:
    """Get performance metrics for an agent."""
    try:
        agent = await agent_store.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # For now, return mock metrics
        return AgentMetrics(
            response_time=0.5,
            tasks_completed=10,
            success_rate=0.95,
            uptime=99.9,
            last_active=datetime.now(),
            metadata={}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@nova_router.post("/ask", response_model=None)
async def ask_nova(
    request: NovaRequest,
    _: None = Depends(get_permission("write")),
    meta_agent = Depends(get_meta_agent),  # Remove Any type to use MetaAgent's type
    memory_system = Depends(get_memory_system)  # Remove Any type to use TwoLayerMemorySystem's type
) -> NovaResponse:
    """Ask Nova a question through the meta agent's cognitive architecture."""
    try:
        # Handle debug flags
        debug_metadata = {}
        if request.debug_flags:
            debug_metadata = {
                "trace_initialization": request.debug_flags.trace_initialization,
                "trace_dependencies": request.debug_flags.trace_dependencies
            }
            
            # Handle simulated errors
            if request.debug_flags.simulate_errors:
                for component, should_error in request.debug_flags.simulate_errors.items():
                    if should_error:
                        if component == "memory_system" and memory_system:
                            # Simulate initialization error
                            raise InitializationError("Failed to initialize memory system")
                        elif hasattr(meta_agent, f"_simulate_{component}_error"):
                            setattr(meta_agent, f"_simulate_{component}_error", True)
        
        # Store user message in memory system
        if memory_system:
            await memory_system.store(
                content=request.content,
                metadata={
                    'source': 'user',
                    'workspace': request.workspace
                }
            )

        # Let meta_agent handle the complete cognitive flow
        agent_response = await meta_agent.process_interaction(
            content=request.content,
            metadata={
                "type": "user_query",
                "workspace": request.workspace,
                "debug_flags": debug_metadata
            }
        )
        
        # Collect initialization data if tracing
        if request.debug_flags and request.debug_flags.trace_initialization:
            init_sequence = getattr(meta_agent, 'initialization_sequence', [])
            debug_metadata["initialization_sequence"] = init_sequence
            if "MetaAgent" not in init_sequence:
                init_sequence.append("MetaAgent")
            
        # Collect dependency data if tracing
        if request.debug_flags and request.debug_flags.trace_dependencies:
            dependencies = getattr(meta_agent, 'agent_dependencies', {})
            debug_metadata["agent_dependencies"] = dependencies
        
        # Create message from agent response dictionary
        if not agent_response or not isinstance(agent_response, dict):
            raise InitializationError("Failed to get response from meta agent")
            
        message = Message(
            id=str(uuid.uuid4()),
            content=agent_response.get("content", ""),
            sender_type="agent",
            sender_id="nova",
            timestamp=datetime.now(),  # Use datetime object directly
            metadata=MessageMetadata(
                agent_actions=agent_response.get("agent_actions", []),
                cognitive_state=agent_response.get("cognitive_state", {}),
                task_context=agent_response.get("task_context", {}),
                debug_info={
                    **(agent_response.get("debug_info", {}) or {}),
                    **debug_metadata
                }
            )
        )

        # Return NovaResponse with the properly constructed message
        return NovaResponse(
            threadId="nova",
            message=message,
            agent_actions=agent_response.get("agent_actions", [])  # Use agent_response instead of response
        )
    except InitializationError as e:
        # Format error as validation error list
        error_data = [{
            "loc": ["meta_agent"],
            "msg": "Failed to initialize MetaAgent",
            "type": "initialization_error",
            "ctx": {
                "error": str(e),
                "initialization_errors": getattr(meta_agent, 'initialization_errors', {})
            }
        }]
        raise HTTPException(status_code=422, detail=error_data)
    except Exception as e:
        # Handle simulated errors with 422
        if request.debug_flags and request.debug_flags.simulate_errors:
            error_data = [{
                "loc": ["meta_agent"],
                "msg": "Failed to initialize MetaAgent",
                "type": "initialization_error",
                "ctx": {
                    "error": str(e),
                    "initialization_errors": getattr(meta_agent, 'initialization_errors', {})
                }
            }]
            raise HTTPException(status_code=422, detail=error_data)
        # Handle other errors with 500
        raise ServiceError(str(e))
