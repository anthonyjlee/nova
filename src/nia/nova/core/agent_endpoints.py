"""Agent-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from datetime import datetime
import uuid

from .dependencies import get_memory_system
from .auth import get_permission
from .error_handling import ServiceError
from .models import (
    AgentMetrics, AgentInteraction, AgentInfo, AgentResponse
)

agent_router = APIRouter(
    prefix="/api/nova/agents",
    tags=["Agents"],
    dependencies=[Depends(get_permission("write"))]
)

@agent_router.get("/", response_model=List[AgentResponse])
async def get_agents(
    memory_system: Any = Depends(get_memory_system)
) -> List[AgentResponse]:
    """Get list of all agents."""
    try:
        # Query all agents from semantic layer
        agents = await memory_system.semantic.run_query(
            """
            MATCH (a:Concept {type: 'agent'})
            RETURN a {
                .id,
                .name,
                .type,
                .status,
                .capabilities,
                .workspace,
                .metadata,
                agent_id: coalesce(a.id, randomUUID()),
                name: coalesce(a.name, 'Unknown Agent'),
                type: coalesce(a.type, 'agent'),
                status: coalesce(a.status, 'active'),
                capabilities: coalesce(a.capabilities, []),
                workspace: case when a.workspace in ['personal', 'professional'] then a.workspace else 'personal' end,
                metadata: {
                    capabilities: coalesce(a.capabilities, []),
                    confidence: coalesce(a.confidence, 0.8),
                    specialization: coalesce(a.specialization, a.type)
                }
            } as agent
            """,
            {}
        )
        
        agent_list = []
        for record in agents:
            agent = record['agent']
            # Ensure required fields
            if 'agent_id' not in agent:
                agent['agent_id'] = str(uuid.uuid4())
            if 'name' not in agent:
                agent['name'] = 'Unknown Agent'
            if 'type' not in agent:
                agent['type'] = 'agent'
            if 'status' not in agent:
                agent['status'] = 'active'
            if 'capabilities' not in agent:
                agent['capabilities'] = []
            if 'workspace' not in agent:
                agent['workspace'] = 'personal'
            if 'metadata' not in agent:
                agent['metadata'] = {}
            
            agent_list.append(AgentResponse(
                id=agent['agent_id'],
                name=agent['name'],
                type="agent",
                agentType=agent['type'],
                status=agent['status'],
                capabilities=agent['capabilities'],
                workspace=agent['workspace'],
                metadata=agent['metadata'],
                timestamp=datetime.utcnow().isoformat()
            ))
        
        return agent_list
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/details", response_model=AgentInfo)
async def get_agent_details(
    agent_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> AgentInfo:
    """Get detailed information about an agent."""
    try:
        # Query agent from semantic layer
        agent = await memory_system.semantic.run_query(
            """
            MATCH (a:Concept {id: $agent_id, type: 'agent'})
            RETURN a
            """,
            {"agent_id": agent_id}
        )
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
            
        return AgentInfo(**agent[0])
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/metrics", response_model=AgentMetrics)
async def get_agent_metrics(
    agent_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> AgentMetrics:
    """Get performance metrics for an agent."""
    try:
        # Get metrics from episodic memory
        metrics = await memory_system.episodic.search(
            filter={
                "type": "agent_metrics",
                "agent_id": agent_id
            },
            limit=1,
            sort=[("timestamp", "desc")]
        )
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No metrics found for agent {agent_id}"
            )
            
        return AgentMetrics(**metrics[0])
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/interactions", response_model=List[AgentInteraction])
async def get_agent_interactions(
    agent_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> List[AgentInteraction]:
    """Get recent interactions for an agent."""
    try:
        # Get interactions from episodic memory
        interactions = await memory_system.episodic.search(
            filter={
                "type": "agent_interaction",
                "agent_id": agent_id
            },
            limit=100,
            sort=[("timestamp", "desc")]
        )
        
        return [AgentInteraction(**interaction) for interaction in interactions]
    except Exception as e:
        raise ServiceError(str(e))
