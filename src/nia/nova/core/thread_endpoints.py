"""FastAPI endpoints for thread management."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from nia.memory.two_layer import TwoLayerMemorySystem
from nia.agents.specialized.orchestration_agent import OrchestrationAgent
from nia.agents.specialized.coordination_agent import CoordinationAgent

from .auth import (
    check_rate_limit,
    check_domain_access,
    get_permission
)
from .error_handling import (
    NovaError,
    ValidationError,
    ResourceNotFoundError,
    ServiceError,
    retry_on_error,
    validate_request
)
from .endpoints import (
    get_memory_system,
    get_orchestration_agent,
    get_coordination_agent
)

# Create router with dependencies
thread_router = APIRouter(
    prefix="/api/threads",
    tags=["threads"],
    dependencies=[Depends(check_rate_limit)]
)

task_router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"],
    dependencies=[Depends(check_rate_limit)]
)

@task_router.post("/propose")
@retry_on_error(max_retries=3)
async def propose_task(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Propose a new task for approval."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        required_fields = ["type", "content"]
        for field in required_fields:
            if field not in request:
                raise ValidationError(f"Request must include '{field}' field")
        
        # Generate task ID
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # Create task in pending state
        task_result = await orchestration_agent.create_task(
            task_id=task_id,
            task_data={
                **request,
                "status": "pending_approval",
                "created_at": datetime.now().isoformat()
            },
            domain=domain or request.get("domain", "professional"),
            metadata={
                "domain": domain,
                "task_type": request["type"],
                "requires_approval": True
            } if domain else None
        )
        
        return {
            "task_id": task_result.task_id,
            "status": "pending_approval",
            "type": request["type"],
            "content": request["content"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@task_router.post("/{task_id}/approve")
@retry_on_error(max_retries=3)
async def approve_task(
    task_id: str,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent),
    coordination_agent: CoordinationAgent = Depends(get_coordination_agent)
) -> Dict:
    """Approve a pending task and trigger execution."""
    try:
        # Get task details
        task_result = await orchestration_agent.get_task(
            task_id=task_id,
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        if task_result.status != "pending_approval":
            raise ValidationError(f"Task {task_id} is not pending approval")
        
        # Update task status
        updated_task = await orchestration_agent.update_task(
            task_id=task_id,
            task_data={
                **task_result.dict(),
                "status": "approved",
                "approved_at": datetime.now().isoformat()
            },
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        # Create thread for task
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        thread_result = await coordination_agent.create_thread(
            thread_id=thread_id,
            task_id=task_id,
            domain=domain,
            metadata={
                "domain": domain,
                "task_type": updated_task.type,
                "parent_thread_id": None
            } if domain else None
        )
        
        return {
            "task_id": task_id,
            "thread_id": thread_id,
            "status": "approved",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@thread_router.get("/{thread_id}")
@retry_on_error(max_retries=3)
async def get_thread_messages(
    thread_id: str,
    start: Optional[int] = 0,
    limit: Optional[int] = 100,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    coordination_agent: CoordinationAgent = Depends(get_coordination_agent)
) -> Dict:
    """Get messages from a thread with pagination."""
    try:
        # Get thread details and messages
        thread_result = await coordination_agent.get_thread(
            thread_id=thread_id,
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        messages = await coordination_agent.get_messages(
            thread_id=thread_id,
            start=start,
            limit=limit,
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        # Get sub-threads if any
        sub_threads = await coordination_agent.get_sub_threads(
            thread_id=thread_id,
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        # Get aggregator summary if available
        summary = await coordination_agent.get_thread_summary(
            thread_id=thread_id,
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        return {
            "thread_id": thread_id,
            "task_id": thread_result.task_id,
            "messages": messages,
            "sub_threads": sub_threads,
            "summary": summary,
            "total_messages": thread_result.message_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@thread_router.post("/{thread_id}/message")
@retry_on_error(max_retries=3)
async def post_thread_message(
    thread_id: str,
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    coordination_agent: CoordinationAgent = Depends(get_coordination_agent)
) -> Dict:
    """Post a message to a thread."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        if "content" not in request:
            raise ValidationError("Request must include 'content' field")
        
        # Generate message ID
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        
        # Post message
        message_result = await coordination_agent.post_message(
            thread_id=thread_id,
            message_id=message_id,
            content=request["content"],
            domain=domain,
            metadata={
                "domain": domain,
                "agent_id": request.get("agent_id"),
                "message_type": request.get("type", "text")
            } if domain else None
        )
        
        return {
            "message_id": message_id,
            "thread_id": thread_id,
            "content": request["content"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@thread_router.get("/graph/projects/{project_id}")
@retry_on_error(max_retries=3)
async def get_project_graph(
    project_id: str,
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """Get graph visualization data for a project."""
    try:
        # Get project nodes and relationships
        nodes = await memory_system.semantic.search(
            query=f"project_id:{project_id}",
            domain=domain
        )
        
        # Get relationships
        relationships = await memory_system.semantic.get_relationships(
            node_ids=[node["id"] for node in nodes],
            domain=domain
        )
        
        return {
            "project_id": project_id,
            "nodes": nodes,
            "relationships": relationships,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))
