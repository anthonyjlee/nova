"""Nova-specific endpoints."""

import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator, root_validator
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
    get_schema_agent,
    get_feature_flags
)
from .auth import get_permission
from .error_handling import ServiceError
from .models import (
    Message, MessageResponse, AgentInfo, AgentResponse, 
    AgentTeam, AgentMetrics, AgentSearchResponse
)
from nia.core.types import (
    Memory, MemoryType, DomainContext, ValidationSchema, AgentResponse
)
from nia.core.types.memory_types import TaskState, DomainTransfer
from nia.core.neo4j.agent_store import AgentStore

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
class NovaRequest(BaseModel):
    """Request model for Nova's ask endpoint."""
    content: str
    workspace: str = Field(default="personal", pattern="^(personal|professional)$")
    debug_flags: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Debug flags for validation and logging",
        example={
            "log_validation": True,
            "log_websocket": True,
            "log_storage": True,
            "strict_mode": False
        }
    )

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

    @validator("debug_flags")
    def validate_debug_flags(cls, v):
        """Validate debug flags."""
        if v is None:
            return {}
        valid_flags = {
            "log_validation", "log_websocket",
            "log_storage", "strict_mode"
        }
        invalid_flags = set(v.keys()) - valid_flags
        if invalid_flags:
            raise ValueError(f"Invalid debug flags: {invalid_flags}")
        return v

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
        return [
            AgentResponse(
                agent_id=agent["id"],
                name=agent["name"],
                type="agent",
                agentType=agent["type"],
                status=agent["status"],
                capabilities=agent["metadata"].get("capabilities", []),
                metadata=agent["metadata"],
                timestamp=datetime.now().isoformat()
            )
            for agent in agents
        ]
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
    meta_agent: Any = Depends(get_meta_agent),
    feature_flags = Depends(get_feature_flags, use_cache=True)
) -> NovaResponse:
    """Ask Nova a question through the meta agent's cognitive architecture."""
    try:
        # Enable debug flags if requested
        debug_flags = request.debug_flags or {}
        for flag, enabled in debug_flags.items():
            if enabled:
                await feature_flags.enable_debug(flag)

        # Log validation if enabled
        if await feature_flags.is_debug_enabled('log_validation'):
            logger.debug(f"Validating request: {request.dict()}")

        # Let meta_agent handle the complete cognitive flow
        response = await meta_agent.process_interaction(
            content=request.content,
            metadata={
                "type": "user_query",
                "workspace": request.workspace,
                "debug_flags": debug_flags
            }
        )

        # Log response if validation logging enabled
        if await feature_flags.is_debug_enabled('log_validation'):
            logger.debug(f"Meta agent response: {response.dict()}")
        
        # Create message from response
        message = Message(
            id=str(uuid.uuid4()),
            content=response.response,
            sender_type="agent",
            sender_id="nova",
            timestamp=datetime.now().isoformat(),
            metadata=MessageMetadata(
                agent_actions=response.agent_actions,
                cognitive_state=response.cognitive_state,
                task_context=response.task_context,
                debug_info=response.debug_info
            )
        )

        # Log final message if validation logging enabled
        if await feature_flags.is_debug_enabled('log_validation'):
            logger.debug(f"Final message: {message.dict()}")

        return NovaResponse(
            threadId="nova",
            message=message,
            agent_actions=response.agent_actions
        )
    except Exception as e:
        raise ServiceError(str(e))
