"""Nova-specific endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .dependencies import get_memory_system, get_agent_store
from .auth import get_permission
from .error_handling import ServiceError
from .models import (
    Message, MessageResponse, AgentInfo, AgentResponse, 
    AgentTeam, AgentMetrics, AgentSearchResponse
)
from nia.core.types.memory_types import Memory, MemoryType
from nia.core.neo4j.agent_store import AgentStore

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
                type=agent["type"],
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
            type=agent["type"],
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
            type=stored_agent["type"],
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
            type=updated_agent["type"],
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

@nova_router.post("/ask", response_model=Dict[str, Any])
async def ask_nova(
    request: Dict[str, str],
    _: None = Depends(get_permission("write")),
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Ask Nova a question."""
    try:
        # Check if Nova thread exists
        result = await memory_system.query_episodic({
            "content": {},
            "filter": {
                "metadata.thread_id": "nova",
                "metadata.type": "thread"
            },
            "layer": "episodic"
        })
        
        if not result:
            # Create Nova thread if it doesn't exist
            now = datetime.now().isoformat()
            thread = {
                "id": "nova",
                "title": "Nova Chat",
                "domain": "general",
                "messages": [],
                "created_at": now,
                "updated_at": now,
                "workspace": "personal",
                "metadata": {
                    "type": "agent-team",
                    "system": True,
                    "pinned": True,
                    "description": "Chat with Nova"
                }
            }
            
            # Store thread in memory system
            memory = Memory(
                content={
                    "data": thread,
                    "metadata": {
                        "type": "thread",
                        "domain": "general",
                        "thread_id": "nova",
                        "timestamp": now,
                        "id": "nova"
                    }
                },
                type=MemoryType.EPISODIC,
                importance=0.8,
                context={
                    "domain": "general",
                    "thread_id": "nova",
                    "source": "nova"
                }
            )
            await memory_system.episodic.store_memory(memory)
            
            # Verify thread was stored
            result = await memory_system.query_episodic({
                "content": {},
                "filter": {
                    "metadata.thread_id": "nova",
                    "metadata.type": "thread"
                },
                "layer": "episodic"
            })
            
            if not result:
                raise ServiceError("Failed to store Nova thread")
        
        thread = result[0]["content"]["data"] if result else thread
        
        # Create Nova's response
        message = Message(
            id=str(uuid.uuid4()),
            content=f"I understand you're asking about: {request['content']}. Let me help with that.",
            sender_type="agent",
            sender_id="nova",
            timestamp=datetime.now().isoformat(),
            metadata={}
        )
        
        # Add message to thread
        thread["messages"].append(message.dict())
        thread["updated_at"] = datetime.now().isoformat()
        
        # Update thread in memory system
        memory = Memory(
            content={
                "data": thread,
                "metadata": {
                    "type": "thread",
                    "domain": "general",
                    "thread_id": "nova",
                    "timestamp": datetime.now().isoformat(),
                    "id": "nova"
                }
            },
            type=MemoryType.EPISODIC,
            importance=0.8,
            context={
                "domain": "general",
                "thread_id": "nova",
                "source": "nova"
            }
        )
        await memory_system.episodic.store_memory(memory)
        
        return {
            "threadId": "nova",
            "message": message
        }
    except Exception as e:
        raise ServiceError(str(e))
