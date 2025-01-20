"""FastAPI endpoints for thread management."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ..memory.two_layer import TwoLayerMemorySystem
from ...agents.specialized.orchestration_agent import OrchestrationAgent
from ...agents.specialized.coordination_agent import CoordinationAgent

from ...core.auth import (
    check_rate_limit,
    get_permission
)
from ..core.error_handling import (
    NovaError,
    ValidationError,
    ResourceNotFoundError,
    ServiceError,
    retry_on_error,
    validate_request
)
from ..core.dependencies import (
    get_memory_system,
    get_orchestration_agent,
    get_coordination_agent,
    get_thread_manager
)

# Create router with dependencies
thread_router = APIRouter(
    tags=["threads"],
    dependencies=[Depends(check_rate_limit)]
)

task_router = APIRouter(
    prefix="",
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
            "task_id": task_id,
            "status": "pending_approval",
            "type": request.get("type"),
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
    thread_manager: Any = Depends(get_thread_manager)
) -> Dict:
    """Approve a pending task and trigger execution."""
    try:
        # Get task details
        task_result = await orchestration_agent.get_task(
            task_id=task_id,
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        if not task_result or not isinstance(task_result, dict):
            raise ResourceNotFoundError(f"Task {task_id} not found")
            
        if task_result.get("status") != "pending_approval":
            raise ValidationError(f"Task {task_id} is not pending approval")
        
        # Update task status
        updated_task = await orchestration_agent.update_task(
            task_id=task_id,
            task_data={
                **task_result,
                "status": "approved",
                "approved_at": datetime.now().isoformat()
            },
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        # Create thread for task
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        thread_result = await thread_manager.create_thread(
            title=f"Task {task_id}",
            domain=domain or "general",
            metadata={
                "type": "task",
                "task_id": task_id,
                "task_type": updated_task.get("type"),
                "system": False,
                "pinned": False,
                "description": ""
            },
            workspace="personal"
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

@thread_router.post("")
@retry_on_error(max_retries=3)
async def create_thread(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    thread_manager: Any = Depends(get_thread_manager)
) -> Dict:
    """Create a new thread."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        # Generate thread ID
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        
        # Create thread
        thread_result = await thread_manager.create_thread(
            title=request.get("title", "Untitled"),
            domain=domain or "general",
            metadata=request.get("metadata", {}),
            workspace=request.get("workspace", "personal")
        )
        
        return {
            "thread_id": thread_result["id"],
            "task_id": request.get("task_id"),
            "type": request.get("type", "chat"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@thread_router.get("")
@retry_on_error(max_retries=3)
async def list_threads(
    domain: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    thread_manager: Any = Depends(get_thread_manager)
) -> Dict:
    """List all threads."""
    try:
        threads = await thread_manager.list_threads(domain)
        return threads
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
    thread_manager: Any = Depends(get_thread_manager)
) -> Dict:
    """Get messages from a thread with pagination."""
    try:
        thread = await thread_manager.get_thread(thread_id)
        return thread
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
    thread_manager: Any = Depends(get_thread_manager)
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
        
        # Add message
        message_result = await thread_manager.add_message(
            thread_id,
            {
                "content": request["content"],
                "sender": request.get("sender", "user"),
                "message_type": request.get("type", "text"),
                "metadata": request.get("metadata", {})
            }
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
        if not memory_system or not memory_system.semantic:
            raise ServiceError("Memory system not available")
            
        # Get project nodes
        nodes_result = await memory_system.semantic.run_query(
            """
            MATCH (n)
            WHERE n.project_id = $project_id
            RETURN n
            """,
            {"project_id": project_id}
        ) or []
        
        nodes = [record["n"] for record in nodes_result]
        
        # Get relationships if nodes exist
        relationships = []
        if nodes:
            rel_result = await memory_system.semantic.run_query(
                """
                MATCH (n)-[r]-(m)
                WHERE n.project_id = $project_id
                RETURN type(r) as type, startNode(r) as source, endNode(r) as target
                """,
                {"project_id": project_id}
            ) or []
            
            relationships = [{
                "type": record["type"],
                "source": record["source"]["id"],
                "target": record["target"]["id"]
            } for record in rel_result]
        
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
