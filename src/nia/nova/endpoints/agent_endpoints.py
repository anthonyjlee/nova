"""Agent-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from datetime import datetime
import uuid

from ..core.auth import get_permission
from ..core.error_handling import ServiceError
from ..core.models import (
    AgentMetrics, AgentInteraction, AgentInfo, AgentResponse
)
from ..core.neo4j.base_store import Neo4jBaseStore

agent_router = APIRouter(
    prefix="/api/agents",
    tags=["Agents"],
    dependencies=[Depends(get_permission("write"))]
)

@agent_router.get("", response_model=Dict[str, List[AgentResponse]])
async def get_agents() -> Dict[str, List[AgentResponse]]:
    """Get list of all agents."""
    try:
        # Query agents directly from Neo4j
        store = Neo4jBaseStore(uri="bolt://localhost:7687", user="neo4j", password="password")
        await store.connect()
        
        try:
            # Query agents with consistent label
            agents = await store.run_query(
                """
                MATCH (a:Agent)
                WHERE a.type = 'system'
                RETURN {
                    id: a.id,
                    name: a.name,
                    type: 'agent',
                    agentType: coalesce(a.agentType, a.type),
                    status: coalesce(a.status, 'active'),
                    capabilities: coalesce(a.capabilities, []),
                    workspace: coalesce(a.workspace, 'personal'),
                    metadata: coalesce(a.metadata, {})
                } as n
                """
            )
        finally:
            await store.close()
        
        # Convert query results to agent list
        agent_list = []
        for agent in agents:
            agent_data = agent['n']
            agent_data['timestamp'] = datetime.utcnow().isoformat()
            agent_list.append(AgentResponse(**agent_data))
        
        return {"agents": agent_list}
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/details", response_model=AgentInfo)
async def get_agent_details(agent_id: str) -> AgentInfo:
    """Get detailed information about an agent."""
    try:
        # Query agent directly from Neo4j
        store = Neo4jBaseStore(uri="bolt://localhost:7687", user="neo4j", password="password")
        await store.connect()
        
        try:
            agent = await store.run_query(
            """
            MERGE (a:Agent {id: $agent_id})
            ON CREATE SET 
                a.type = 'system',
                a.name = 'Unknown Agent',
                a.agentType = 'system',
                a.status = 'active',
                a.capabilities = [],
                a.workspace = 'personal',
                a.metadata = {},
                a.description = '',
                a.confidence = 0.8,
                a.specialization = 'system',
                a.domain = 'general',
                a.created_at = datetime(),
                a.last_active = datetime()
            ON MATCH SET
                a.last_active = datetime()
            RETURN {
                id: a.id,
                name: a.name,
                type: 'agent',
                agentType: a.agentType,
                status: a.status,
                capabilities: a.capabilities,
                workspace: a.workspace,
                metadata: a.metadata,
                description: a.description,
                confidence: a.confidence,
                specialization: a.specialization,
                domain: a.domain,
                created_at: a.created_at,
                last_active: a.last_active
            } as n
            """,
                {"agent_id": agent_id}
            )
        finally:
            await store.close()
        
        if not agent or not agent[0].get('n'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        return AgentInfo(**agent[0]['n'])
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/metrics", response_model=AgentMetrics)
async def get_agent_metrics(agent_id: str) -> AgentMetrics:
    """Get performance metrics for an agent."""
    try:
        # Query metrics directly from Neo4j
        store = Neo4jBaseStore(uri="bolt://localhost:7687", user="neo4j", password="password")
        await store.connect()
        
        try:
            metrics = await store.run_query(
                """
                MERGE (m:Metric {agent_id: $agent_id})
                ON CREATE SET
                    m.response_time = 0,
                    m.tasks_completed = 0,
                    m.success_rate = 0,
                    m.uptime = 0,
                    m.last_active = datetime(),
                    m.metadata = {}
                RETURN {
                    response_time: m.response_time,
                    tasks_completed: m.tasks_completed,
                    success_rate: m.success_rate,
                    uptime: m.uptime,
                    last_active: m.last_active,
                    metadata: m.metadata
                } as metrics
                """,
                {"agent_id": agent_id}
            )
        finally:
            await store.close()
        
        if not metrics or not metrics[0].get('metrics'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No metrics found for agent {agent_id}"
            )
            
        return AgentMetrics(**metrics[0]['metrics'])
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@agent_router.get("/{agent_id}/interactions", response_model=List[AgentInteraction])
async def get_agent_interactions(agent_id: str) -> List[AgentInteraction]:
    """Get recent interactions for an agent."""
    try:
        # Query interactions directly from Neo4j
        store = Neo4jBaseStore(uri="bolt://localhost:7687", user="neo4j", password="password")
        await store.connect()
        
        try:
            interactions = await store.run_query(
                """
                MATCH (i:Interaction)
                WHERE i.agent_id = $agent_id
                WITH i ORDER BY i.timestamp DESC LIMIT 100
                RETURN {
                    id: i.id,
                    type: i.type,
                    content: i.content,
                    context: coalesce(i.context, {}),
                    timestamp: i.timestamp,
                    metadata: coalesce(i.metadata, {})
                } as interaction
                """,
                {"agent_id": agent_id}
            )
        finally:
            await store.close()
            
        return [AgentInteraction(**interaction['interaction']) for interaction in interactions]
    except Exception as e:
        raise ServiceError(str(e))
