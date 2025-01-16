"""Nova-specific endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

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
    get_memory_agent,
    get_planning_agent,
    get_reasoning_agent,
    get_learning_agent,
    # Support agents
    get_parsing_agent,
    get_orchestration_agent,
    get_dialogue_agent,
    get_context_agent,
    get_validation_agent,
    get_synthesis_agent,
    get_alerting_agent,
    get_monitoring_agent,
    get_debugging_agent,
    get_schema_agent
)
from .auth import get_permission
from .error_handling import ServiceError
from .models import (
    Message, MessageResponse, AgentInfo, AgentResponse, 
    AgentTeam, AgentMetrics, AgentSearchResponse
)
from nia.core.types.memory_types import Memory, MemoryType
from nia.core.neo4j.agent_store import AgentStore

# Message Models
class AgentAction(BaseModel):
    """Record of an agent's action in a conversation."""
    agent_id: str
    action_type: str = Field(..., description="Type of action performed")
    timestamp: datetime
    details: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]]

class MessageMetadata(BaseModel):
    """Enhanced message metadata to track agent activities."""
    agent_actions: List[AgentAction] = Field(default_factory=list)
    cognitive_state: Optional[Dict[str, Any]]
    task_context: Optional[Dict[str, Any]]
    debug_info: Optional[Dict[str, Any]]

class Message(BaseModel):
    """Enhanced message model with agent tracking."""
    id: str
    content: str
    sender_type: str
    sender_id: str
    timestamp: datetime
    metadata: MessageMetadata

# Request/Response Models
class NovaRequest(BaseModel):
    """Request model for Nova's ask endpoint."""
    content: str
    workspace: str = Field(default="personal", pattern="^(personal|professional)$")
    debug_flags: Optional[Dict[str, bool]] = None

class NovaResponse(BaseModel):
    """Response model for Nova's ask endpoint."""
    threadId: str
    message: Message
    agent_actions: List[AgentAction]

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

@nova_router.post("/ask", response_model=NovaResponse)
async def ask_nova(
    request: NovaRequest,
    _: None = Depends(get_permission("write")),
    memory_system: Any = Depends(get_memory_system),
    llm: Any = Depends(get_llm_interface),
    agent_store: AgentStore = Depends(get_agent_store),
    # Core cognitive agents
    belief_agent: Any = Depends(get_belief_agent),
    desire_agent: Any = Depends(get_desire_agent),
    emotion_agent: Any = Depends(get_emotion_agent),
    reflection_agent: Any = Depends(get_reflection_agent),
    meta_agent: Any = Depends(get_meta_agent),
    self_model_agent: Any = Depends(get_self_model_agent),
    analysis_agent: Any = Depends(get_analysis_agent),
    research_agent: Any = Depends(get_research_agent),
    integration_agent: Any = Depends(get_integration_agent),
    memory_agent: Any = Depends(get_memory_agent),
    planning_agent: Any = Depends(get_planning_agent),
    reasoning_agent: Any = Depends(get_reasoning_agent),
    learning_agent: Any = Depends(get_learning_agent),
    # Support agents
    parsing_agent: Any = Depends(get_parsing_agent),
    orchestration_agent: Any = Depends(get_orchestration_agent),
    dialogue_agent: Any = Depends(get_dialogue_agent),
    context_agent: Any = Depends(get_context_agent),
    validation_agent: Any = Depends(get_validation_agent),
    synthesis_agent: Any = Depends(get_synthesis_agent),
    alerting_agent: Any = Depends(get_alerting_agent),
    monitoring_agent: Any = Depends(get_monitoring_agent),
    debugging_agent: Any = Depends(get_debugging_agent),
    schema_agent: Any = Depends(get_schema_agent)
) -> NovaResponse:
    """Ask Nova a question through its complete cognitive architecture."""
    try:
        # Get debug flags
        debug_flags = request.debug_flags or {}
        
        # 1. Initial Processing with Validation and Schema
        schema_result = await schema_agent.validate_schema(
            content=request.content,
            schema_type="user_input",
            metadata={"debug_flags": debug_flags}
        )
        
        if not schema_result.is_valid:
            if debug_flags.get("strict_mode"):
                raise ValueError(f"Schema validation failed: {schema_result.issues}")
            await alerting_agent.send_alert(
                type="validation_warning",
                message=f"Schema validation warning: {schema_result.issues}",
                severity="medium"
            )

        parsed_input = await parsing_agent.parse_text(
            request.content,
            metadata={
                "debug_flags": debug_flags,
                "schema_result": schema_result.dict()
            }
        )

        # Start monitoring
        monitor_task = await monitoring_agent.start_monitoring(
            task_type="user_query",
            metadata={
                "query": parsed_input.response,
                "debug_flags": debug_flags
            }
        )

        # Get context with memory integration
        context = await context_agent.get_context({
            "query": parsed_input.response,
            "workspace": request.workspace,
            "domain": "general",
            "debug_flags": debug_flags
        })

        memory_context = await memory_agent.retrieve_relevant_memories({
            "query": parsed_input.response,
            "context": context,
            "debug_flags": debug_flags
        })

        context.update({"memories": memory_context})
        
        # 2. Task Detection & Agent Assembly
        task_detection = await analysis_agent.detect_task({
            "content": parsed_input.response,
            "context": context,
            "workspace": request.workspace
        })

        if task_detection.is_task:
            # Log to #NovaTeam for debugging
            await debugging_agent.log_to_channel(
                channel="nova-team",
                message=f"Task detected: {task_detection.task_type}",
                metadata=task_detection.dict()
            )

            # Spawn specialized agents if needed
            if task_detection.requires_agents:
                for agent_spec in task_detection.required_agents:
                    agent_data = {
                        "id": str(uuid.uuid4()),
                        "name": agent_spec.name,
                        "type": "spawned",
                        "status": "active",
                        "workspace": request.workspace,
                        "metadata": {
                            "task_id": task_detection.task_id,
                            "capabilities": agent_spec.capabilities,
                            "specialization": agent_spec.specialization
                        }
                    }
                    await agent_store.store_agent(agent_data)

                # Log agent spawning to #NovaSupport
                await debugging_agent.log_to_channel(
                    channel="nova-support",
                    message=f"Spawned {len(task_detection.required_agents)} agents for task",
                    metadata={"agents": [a.dict() for a in task_detection.required_agents]}
                )

        # 3. Planning, Research and Analysis
        plan = await planning_agent.create_plan({
            "query": parsed_input.response,
            "context": context,
            "debug_flags": debug_flags,
            "task_detection": task_detection.dict() if task_detection.is_task else None
        })

        if debug_flags.get("log_validation"):
            await debugging_agent.log_plan(plan, "Query processing plan created")

        # Store in ephemeral memory if task-related
        if task_detection.is_task:
            await memory_system.store_ephemeral({
                "type": "task_context",
                "content": {
                    "task_detection": task_detection.dict(),
                    "plan": plan.dict(),
                    "context": context
                },
                "metadata": {
                    "workspace": request.workspace,
                    "task_id": task_detection.task_id
                }
            })

        research_response = await research_agent.gather_information(
            query=parsed_input.response,
            context=context,
            plan=plan,
            metadata={"debug_flags": debug_flags}
        )

        reasoning_context = await reasoning_agent.analyze_logic({
            "query": parsed_input.response,
            "research": research_response,
            "context": context,
            "debug_flags": debug_flags
        })

        analysis_response = await analysis_agent.analyze({
            "query": parsed_input.response,
            "research": research_response,
            "reasoning": reasoning_context,
            "context": context,
            "debug_flags": debug_flags
        })
        
        # 3. Meta-Cognitive Processing with Validation
        meta_response = await meta_agent.process_interaction(
            content=parsed_input.response,
            metadata={
                "type": "user_query",
                "workspace": request.workspace,
                "domain": "general",
                "context": context,
                "debug_flags": debug_flags,
                "agents": {
                    "research": {
                        "agent": research_agent,
                        "validation_result": research_response.validation if hasattr(research_response, "validation") else None
                    },
                    "analysis": {
                        "agent": analysis_agent,
                        "validation_result": analysis_response.validation if hasattr(analysis_response, "validation") else None
                    },
                    "belief": {
                        "agent": belief_agent
                    },
                    "desire": {
                        "agent": desire_agent
                    },
                    "emotion": {
                        "agent": emotion_agent
                    },
                    "reflection": {
                        "agent": reflection_agent
                    },
                    "integration": {
                        "agent": integration_agent
                    }
                }
            }
        )
        
        # Record meta synthesis with validation
        await meta_agent.record_synthesis(
            meta_response,
            importance=0.8,
            metadata={
                "debug_flags": debug_flags,
                "validation_result": meta_response.validation if hasattr(meta_response, "validation") else None
            }
        )
        
        # Update Nova's system state with validation
        await self_model_agent.update_state(
            state="processing",
            metadata={
                "current_input": parsed_input.response,
                "workspace": request.workspace,
                "domain": "general",
                "context": context,
                "meta_understanding": meta_response.dict(),
                "debug_flags": debug_flags,
                "validation_result": meta_response.validation if hasattr(meta_response, "validation") else None
            }
        )

        # Record self-reflection about meta understanding
        await self_model_agent.record_reflection(
            content=f"Processing user query with meta understanding: {meta_response.key_points}",
            domain="general"
        )

        # Get current capabilities
        capabilities = await self_model_agent.get_capabilities()
        
        # Update self model
        self_model_response = await self_model_agent.update_model({
            "current_input": parsed_input.response,
            "meta_understanding": meta_response,
            "context": context,
            "capabilities": capabilities
        })

        # Record final reflection
        await self_model_agent.record_reflection(
            content=f"Updated self model based on interaction. Current state: {self_model_response.dict()}",
            domain="general"
        )
        
        # 4. Core Cognitive Processing
        # Analyze beliefs with evidence
        belief_response = await belief_agent.analyze_beliefs({
            "content": parsed_input.response,
            "type": "user_query",
            "source": "chat",
            "context": context,
            "evidence": {
                "sources": [
                    research_response.dict(),
                    analysis_response.dict()
                ],
                "supporting_facts": analysis_response.key_points,
                "context": str(context),
                "domain_factors": {
                    "workspace": request.workspace,
                    "domain": "general",
                    "analysis_confidence": analysis_response.confidence,
                    "research_confidence": research_response.confidence
                }
            }
        })
        
        # Analyze desires with motivations
        desire_response = await desire_agent.analyze_desires({
            "content": parsed_input.response,
            "type": "user_query",
            "source": "chat",
            "context": context,
            "motivations": {
                "reasons": belief_response.beliefs,
                "drivers": [
                    "User query understanding",
                    "Task completion",
                    "Knowledge integration"
                ],
                "constraints": [
                    {"type": "domain", "value": "general"},
                    {"type": "workspace", "value": request.workspace}
                ],
                "domain_factors": {
                    "workspace": request.workspace,
                    "domain": "general",
                    "belief_confidence": belief_response.confidence,
                    "analysis_confidence": analysis_response.confidence
                },
                "priority_factors": [
                    {
                        "factor": "belief_alignment",
                        "weight": belief_response.confidence
                    },
                    {
                        "factor": "analysis_support",
                        "weight": analysis_response.confidence
                    }
                ]
            }
        })
        
        # Analyze emotional content
        emotion_response = await emotion_agent.analyze_emotion({
            "content": parsed_input.response,
            "type": "user_query",
            "source": "chat",
            "context": {
                "beliefs": belief_response.dict(),
                "desires": desire_response.dict(),
                "background": context,
                "domain_factors": {
                    "workspace": request.workspace,
                    "domain": "general"
                },
                "relationships": [
                    {
                        "type": "belief_influence",
                        "target": "emotional_state",
                        "strength": belief_response.confidence
                    },
                    {
                        "type": "desire_influence",
                        "target": "emotional_state",
                        "strength": desire_response.confidence
                    }
                ]
            }
        })
        
        reflection_response = await reflection_agent.analyze_reflection({
            "content": parsed_input.response,
            "beliefs": belief_response,
            "desires": desire_response,
            "emotions": emotion_response,
            "analysis": analysis_response
        })
        
        # 4. Integration
        integrated_response = await integration_agent.integrate({
            "parsed_input": parsed_input,
            "research": research_response,
            "analysis": analysis_response,
            "beliefs": belief_response,
            "desires": desire_response,
            "emotions": emotion_response,
            "reflections": reflection_response,
            "context": context
        })
        
        # 5. Validation
        validated_response = await validation_agent.validate({
            "integrated_response": integrated_response,
            "context": context,
            "beliefs": belief_response
        })
        
        # 6. Response Generation
        orchestrated_response = await orchestration_agent.process_request({
            "validated_response": validated_response,
            "context": context
        })
        
        dialogue_response = await dialogue_agent.generate_response({
            "orchestrated_response": orchestrated_response,
            "emotions": emotion_response,
            "context": context
        })
        
        # 7. Final Synthesis and Learning
        final_response = await synthesis_agent.synthesize({
            "parsed_input": parsed_input,
            "research": research_response,
            "analysis": analysis_response,
            "beliefs": belief_response,
            "desires": desire_response,
            "emotions": emotion_response,
            "reflections": reflection_response,
            "integrated": integrated_response,
            "validated": validated_response,
            "orchestrated": orchestrated_response,
            "dialogue": dialogue_response,
            "context": context,
            "reasoning": reasoning_context
        })

        # Learn from interaction
        await learning_agent.learn_from_interaction({
            "query": parsed_input.response,
            "response": final_response,
            "context": context,
            "research": research_response,
            "analysis": analysis_response,
            "debug_flags": debug_flags
        })

        # Store in two-layer memory system
        
        # 1. Ephemeral storage for session context
        await memory_system.store_ephemeral({
            "type": "interaction_context",
            "content": {
                "query": parsed_input.response,
                "response": final_response.dict(),
                "context": context,
                "cognitive_state": {
                    "beliefs": belief_response.dict(),
                    "desires": desire_response.dict(),
                    "emotions": emotion_response.dict()
                }
            },
            "metadata": {
                "workspace": request.workspace,
                "importance": 0.8
            }
        })

        # 2. Permanent storage for learned knowledge
        if learning_agent.has_learned_knowledge():
            learned_knowledge = learning_agent.get_learned_knowledge()
            
            # Log learning to #NovaTeam
            await debugging_agent.log_to_channel(
                channel="nova-team",
                message="New knowledge learned",
                metadata={"knowledge": learned_knowledge}
            )
            
            # Store in permanent memory
            await memory_system.store_permanent({
                "type": "learned_knowledge",
                "content": {
                    "knowledge": learned_knowledge,
                    "source": {
                        "type": "interaction",
                        "query": parsed_input.response,
                        "response": final_response.key_points
                    },
                    "validation": {
                        "confidence": final_response.confidence,
                        "supporting_evidence": final_response.reasoning
                    }
                },
                "metadata": {
                    "workspace": request.workspace,
                    "domain": "general",
                    "importance": 0.9
                }
            })

        # Stop monitoring
        await monitoring_agent.stop_monitoring(
            task_id=monitor_task["id"],
            metadata={
                "success": True,
                "response": final_response.dict()
            }
        )

        # 8. Create message from synthesized response
        message = Message(
            id=str(uuid.uuid4()),
            content=final_response.response,
            sender_type="agent",
            sender_id="nova",
            timestamp=datetime.now().isoformat(),
            metadata={
                "concepts": final_response.concepts,
                "key_points": final_response.key_points,
                "implications": final_response.implications,
                "uncertainties": final_response.uncertainties,
                "reasoning": final_response.reasoning,
                "confidence": final_response.confidence,
                "context": context,
                "cognitive_state": {
                    "beliefs": belief_response.dict(),
                    "desires": desire_response.dict(),
                    "emotions": emotion_response.dict(),
                    "reflections": reflection_response.dict(),
                    "meta": meta_response.dict(),
                    "self_model": self_model_response.dict()
                },
                "processing": {
                    "research": research_response.dict(),
                    "analysis": analysis_response.dict(),
                    "integration": integrated_response.dict(),
                    "validation": validated_response.dict(),
                    "orchestration": orchestrated_response.dict(),
                    "dialogue": dialogue_response.dict()
                }
            }
        )

        # Store in thread
        thread = await memory_system.query_episodic({
            "content": {},
            "filter": {
                "metadata.thread_id": "nova",
                "metadata.type": "thread"
            },
            "layer": "episodic"
        })

        if not thread:
            # Create Nova thread if it doesn't exist
            now = datetime.now().isoformat()
            thread_data = {
                "id": "nova",
                "title": "Nova Chat",
                "domain": "general",
                "messages": [],
                "created_at": now,
                "updated_at": now,
                "workspace": request.workspace,
                "metadata": {
                    "type": "agent-team",
                    "system": True,
                    "pinned": True,
                    "description": "Chat with Nova"
                }
            }
            
            # Enhanced thread memory with agent tracking
            memory = Memory(
                content={
                    "data": thread_data,
                    "metadata": {
                        "type": "thread",
                        "domain": "general",
                        "thread_id": "nova",
                        "timestamp": now,
                        "id": "nova",
                        "agent_summary": {
                            "active_agents": [
                                "schema_agent",
                                "analysis_agent", 
                                "planning_agent",
                                "meta_agent",
                                "learning_agent"
                            ],
                            "task_type": task_detection.task_type if task_detection.is_task else "conversation",
                            "workspace": request.workspace
                        }
                    }
                },
                type=MemoryType.EPISODIC,
                importance=0.8,
                context={
                    "domain": "general",
                    "thread_id": "nova",
                    "source": "nova",
                    "agent_context": {
                        "task_detection": task_detection.dict() if task_detection.is_task else None,
                        "plan": plan.dict() if hasattr(plan, "dict") else None
                    }
                }
            )
            await memory_system.episodic.store_memory(memory)
            thread_data = thread_data
        else:
            thread_data = thread[0].content.get("data")

        # Add message to thread
        thread_data["messages"].append(message.dict())
        thread_data["updated_at"] = datetime.now().isoformat()

        # Update thread
        memory = Memory(
            content={
                "data": thread_data,
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

        # Collect agent actions from the processing
        agent_actions = [
            AgentAction(
                agent_id="schema_agent",
                action_type="validation",
                timestamp=datetime.now(),
                details={"schema_type": "user_input"},
                result=schema_result.dict() if hasattr(schema_result, "dict") else None
            ),
            AgentAction(
                agent_id="analysis_agent",
                action_type="task_detection",
                timestamp=datetime.now(),
                details={"workspace": request.workspace},
                result=task_detection.dict() if hasattr(task_detection, "dict") else None
            ),
            AgentAction(
                agent_id="planning_agent",
                action_type="plan_creation",
                timestamp=datetime.now(),
                details={"context": str(context)},
                result=plan.dict() if hasattr(plan, "dict") else None
            ),
            AgentAction(
                agent_id="meta_agent",
                action_type="meta_processing",
                timestamp=datetime.now(),
                details={"workspace": request.workspace},
                result=meta_response.dict() if hasattr(meta_response, "dict") else None
            ),
            AgentAction(
                agent_id="learning_agent",
                action_type="knowledge_acquisition",
                timestamp=datetime.now(),
                details={"source": "interaction"},
                result={"learned": learning_agent.has_learned_knowledge()}
            )
        ]

        # Update message metadata with agent actions
        message.metadata.agent_actions = agent_actions

        return NovaResponse(
            threadId="nova",
            message=message,
            agent_actions=agent_actions
        )
    except Exception as e:
        raise ServiceError(str(e))
