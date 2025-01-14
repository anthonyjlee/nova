"""Task-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .dependencies import get_memory_system
from .auth import get_permission
from .error_handling import ServiceError
from .models import (
    TaskNode, TaskEdge, TaskUpdate, TaskDetails, TaskState, TaskStateTransition,
    SubTask, Comment, TaskPriority
)
from nia.core.types.memory_types import Memory, MemoryType

# Valid state transitions
VALID_TRANSITIONS = {
    TaskState.PENDING: [TaskState.IN_PROGRESS],  # Can only start from pending
    TaskState.IN_PROGRESS: [TaskState.BLOCKED, TaskState.COMPLETED],  # Can block or complete from in progress
    TaskState.BLOCKED: [TaskState.IN_PROGRESS],  # Can only resume to in progress from blocked
    TaskState.COMPLETED: []  # No transitions from completed
}

async def validate_state_transition(
    current_state: TaskState,
    new_state: TaskState,
    task_id: str,
    memory_system: Any
) -> bool:
    """Validate if a state transition is allowed."""
    if new_state not in VALID_TRANSITIONS.get(current_state, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state transition from {current_state} to {new_state}"
        )
    
    # Additional validation for BLOCKED state
    if new_state == TaskState.BLOCKED:
        # Check if task has dependencies
        dependencies = await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $task_id})<-[:DEPENDS_ON]-(d:Concept)
            RETURN count(d) as dep_count
            """,
            {"task_id": task_id}
        )
        if dependencies[0]["dep_count"] == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot block task without dependencies"
            )
    
    return True

async def validate_domain_access(
    domain: str,
    memory_system: Any
) -> bool:
    """Validate domain access permissions."""
    try:
        await memory_system.validate_domain_access(domain)
        return True
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Domain access denied: {str(e)}"
        )

tasks_router = APIRouter(
    prefix="/api/tasks",
    tags=["Tasks"],
    dependencies=[Depends(get_permission("write"))]
)

@tasks_router.get("/search", response_model=Dict[str, Any])
async def search_tasks(
    q: Optional[str] = Query(None, description="Text search query"),
    status: Optional[str] = Query(None, description="Comma-separated task states"),
    priority: Optional[str] = Query(None, description="Comma-separated priorities"),
    assignee: Optional[str] = Query(None, description="Comma-separated assignees"),
    from_date: Optional[str] = Query(None, description="Start date for date range filter"),
    to_date: Optional[str] = Query(None, description="End date for date range filter"),
    sort: Optional[str] = Query("updated_at", description="Field to sort by"),
    order: Optional[str] = Query("desc", description="Sort direction (asc/desc)"),
    page: Optional[int] = Query(1, description="Page number", ge=1),
    size: Optional[int] = Query(20, description="Page size", ge=1, le=100),
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Search tasks with filtering, sorting, and pagination."""
    try:
        # Build Cypher query
        query_parts = ["MATCH (t:Concept) WHERE t.type = 'task'"]
        params: Dict[str, Any] = {}

        # Text search
        if q:
            query_parts.append("AND (t.description CONTAINS $search OR t.name CONTAINS $search)")
            params["search"] = q

        # Status filter
        if status:
            statuses = status.split(",")
            query_parts.append("AND t.status IN $statuses")
            params["statuses"] = statuses

        # Priority filter
        if priority:
            priorities = priority.split(",")
            query_parts.append("AND t.priority IN $priorities")
            params["priorities"] = priorities

        # Assignee filter
        if assignee:
            assignees = assignee.split(",")
            query_parts.append("AND t.assignee IN $assignees")
            params["assignees"] = assignees

        # Date range filter
        if from_date:
            query_parts.append("AND t.created_at >= $from_date")
            params["from_date"] = from_date
        if to_date:
            query_parts.append("AND t.created_at <= $to_date")
            params["to_date"] = to_date

        # Calculate pagination
        skip = (page - 1) * size
        
        # Build count query
        count_query = " ".join(query_parts + ["RETURN count(t) as total"])
        
        # Get total count
        count_result = await memory_system.semantic.run_query(count_query, params)
        total_items = count_result[0]["total"]
        total_pages = (total_items + size - 1) // size

        # Build final query with sorting and pagination
        sort_direction = "DESC" if order.lower() == "desc" else "ASC"
        query = f"""
        {" ".join(query_parts)}
        RETURN t.name as id, t.description as label, 
               t.status as status, t.domain as domain,
               t.team_id as team_id, t.created_at as created_at,
               t.updated_at as updated_at, t.priority as priority,
               t.assignee as assignee, t.title as title,
               t.dueDate as dueDate, t.tags as tags,
               t.time_active as time_active, t.dependencies as dependencies,
               t.blocked_by as blocked_by, t.sub_tasks as sub_tasks,
               t.completed as completed, t.metadata as metadata,
               t.type as type
        ORDER BY t.{sort} {sort_direction}
        SKIP {skip} LIMIT {size}
        """

        # Execute query
        tasks = await memory_system.semantic.run_query(query, params)

        # Format results as TaskNode objects
        return {
            "tasks": [TaskNode(
                id=task["id"],
                label=task["label"],
                type=task["type"] or "task",
                status=TaskState(task["status"] or TaskState.PENDING),
                description=task["description"],
                team_id=task["team_id"],
                domain=task["domain"],
                created_at=task["created_at"],
                updated_at=task["updated_at"],
                metadata=task["metadata"] or {},
                title=task["title"],
                priority=task["priority"],
                assignee=task["assignee"],
                dueDate=task["dueDate"],
                tags=task["tags"],
                time_active=task["time_active"],
                dependencies=task["dependencies"],
                blocked_by=task["blocked_by"],
                sub_tasks=[SubTask(**st) for st in (task["sub_tasks"] or [])],
                completed=task["completed"]
            ).dict() for task in tasks],
            "totalItems": total_items,
            "totalPages": total_pages
        }
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.get("/board", response_model=Dict[str, Any])
async def get_task_board(
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Get tasks organized by state for Kanban board view."""
    try:
        tasks = await memory_system.semantic.run_query(
            """
            MATCH (t:Concept)
            WHERE t.type = 'task'
            RETURN t.name as id, t.description as label, 
                   t.status as status, t.domain as domain,
                   t.team_id as team_id, t.created_at as created_at,
                   t.updated_at as updated_at, t.priority as priority,
                   t.assignee as assignee, t.title as title,
                   t.dueDate as dueDate, t.tags as tags,
                   t.time_active as time_active, t.dependencies as dependencies,
                   t.blocked_by as blocked_by, t.sub_tasks as sub_tasks,
                   t.completed as completed, t.metadata as metadata,
                   t.type as type
            """
        )
        
        # Organize tasks by state
        board = {
            TaskState.PENDING: [],
            TaskState.IN_PROGRESS: [],
            TaskState.BLOCKED: [],
            TaskState.COMPLETED: []
        }
        
        for task in tasks:
            status = TaskState(task["status"] or TaskState.PENDING)
            board[status].append(TaskNode(
                id=task["id"],
                label=task["label"],
                type=task["type"] or "task",
                status=status,
                description=task["description"],
                team_id=task["team_id"],
                domain=task["domain"],
                created_at=task["created_at"],
                updated_at=task["updated_at"],
                metadata=task["metadata"] or {},
                title=task["title"],
                priority=task["priority"],
                assignee=task["assignee"],
                dueDate=task["dueDate"],
                tags=task["tags"],
                time_active=task["time_active"],
                dependencies=task["dependencies"],
                blocked_by=task["blocked_by"],
                sub_tasks=[SubTask(**st) for st in (task["sub_tasks"] or [])],
                completed=task["completed"]
            ).dict())
            
        return {
            "board": board,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.get("/{task_id}/details", response_model=TaskDetails)
async def get_task_details(
    task_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> TaskDetails:
    """Get detailed information about a task."""
    try:
        # Get task node
        task = await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $task_id})
            RETURN t
            """,
            {"task_id": task_id}
        )
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
            
        # Get dependencies
        dependencies = await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $task_id})-[:DEPENDS_ON]->(d:Concept)
            RETURN d.name as id
            """,
            {"task_id": task_id}
        )
        
        # Get blocking tasks
        blocking = await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $task_id})<-[:DEPENDS_ON]-(b:Concept)
            RETURN b.name as id
            """,
            {"task_id": task_id}
        )
        
        # Get sub-tasks and comments from episodic memory
        episodic_data = await memory_system.episodic.search(
            filter={"task_id": task_id},
            limit=100
        )
        
        return TaskDetails(
            task=TaskNode(**task[0]),
            dependencies=[d["id"] for d in dependencies],
            blocked_by=[b["id"] for b in blocking],
            sub_tasks=[SubTask(**m) for m in episodic_data if m["type"] == "sub_task"],
            comments=[Comment(**m) for m in episodic_data if m["type"] == "comment"],
            time_active=str(datetime.now() - datetime.fromisoformat(task[0]["created_at"])),
            domain_access=[task[0].get("domain", "general")]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.get("/graph", response_model=Dict[str, Any], dependencies=[Depends(get_permission("read"))])
async def get_task_graph(
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Get the current task graph."""
    try:
        # Query semantic layer for task nodes and edges
        tasks = await memory_system.semantic.query_knowledge({
            "type": "task",
            "context": {
                "access_domain": "tasks"
            }
        })
        
        # Format response
        return {
            "analytics": {
                "nodes": [
                    {
                        "id": task["name"],
                        "type": "task",
                        "label": task.get("description", task["name"]),
                        "status": task.get("status", TaskState.PENDING),
                        "metadata": {
                            "domain": task.get("domain", "general"),
                            "timestamp": task.get("created_at", datetime.now().isoformat()),
                            "importance": task.get("importance", 0.5)
                        }
                    }
                    for task in tasks
                ],
                "edges": [
                    {
                        "source": rel["source"],
                        "target": rel["target"],
                        "type": rel["type"],
                        "label": rel.get("label", rel["type"])
                    }
                    for task in tasks
                    for rel in task.get("relationships", [])
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.post("", response_model=Dict[str, Any])
async def create_task(
    task: TaskNode,
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Create a new task."""
    try:
        # Validate domain access
        if task.domain:
            await validate_domain_access(task.domain, memory_system)
            
        # Store task in semantic layer
        await memory_system.semantic.store_knowledge({
            "concepts": [{
                "name": task.id,
                "type": "task",
                "description": task.label,
                "validation": {
                    "domain": "tasks",
                    "access_domain": "tasks",
                    "confidence": 1.0,
                    "source": "system"
                }
            }]
        })
        
        # Store task metadata and all fields
        await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $name})
            SET t.status = $status,
                t.created_at = $created_at,
                t.updated_at = $updated_at,
                t.metadata = $metadata,
                t.title = $title,
                t.priority = $priority,
                t.assignee = $assignee,
                t.dueDate = $dueDate,
                t.tags = $tags,
                t.time_active = $time_active,
                t.dependencies = $dependencies,
                t.blocked_by = $blocked_by,
                t.sub_tasks = $sub_tasks,
                t.completed = $completed
            """,
            task.dict()
        )
        
        return {"success": True, "taskId": task.id}
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.post("/graph/addNode", response_model=Dict[str, Any])
async def add_task_node(
    task: TaskNode,
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Add a new task node to the graph (deprecated: use POST /api/tasks instead)."""
    try:
        # Validate domain access
        if task.domain:
            await validate_domain_access(task.domain, memory_system)
            
        # Store task in semantic layer
        await memory_system.semantic.store_knowledge({
            "concepts": [{
                "name": task.id,
                "type": "task",
                "description": task.label,
                "validation": {
                    "domain": "tasks",
                    "access_domain": "tasks",
                    "confidence": 1.0,
                    "source": "system"
                }
            }]
        })
        
        # Store task metadata and all fields
        await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $name})
            SET t.status = $status,
                t.created_at = $created_at,
                t.updated_at = $updated_at,
                t.metadata = $metadata,
                t.title = $title,
                t.priority = $priority,
                t.assignee = $assignee,
                t.dueDate = $dueDate,
                t.tags = $tags,
                t.time_active = $time_active,
                t.dependencies = $dependencies,
                t.blocked_by = $blocked_by,
                t.sub_tasks = $sub_tasks,
                t.completed = $completed
            """,
            task.dict()
        )
        
        return {"success": True, "taskId": task.id}
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.post("/graph/updateNode", response_model=Dict[str, Any])
async def update_task_node(
    task_id: str,
    update: TaskUpdate,
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Update a task node in the graph."""
    try:
        # Get current task state
        current_task = await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $name})
            RETURN t.status as status, t.domain as domain
            """,
            {"name": task_id}
        )
        
        if not current_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
            
        # Validate state transition if status is being updated
        if update.status:
            await validate_state_transition(
                TaskState(current_task[0]["status"]),
                update.status,
                task_id,
                memory_system
            )
            
        # Validate domain access if domain is being updated
        if update.domain:
            await validate_domain_access(update.domain, memory_system)
            
        # Build update query dynamically based on provided fields
        update_parts = []
        params = {"name": task_id}
        
        for field, value in update.dict(exclude_unset=True).items():
            if value is not None:
                update_parts.append(f"t.{field} = ${field}")
                params[field] = value
        
        if update_parts:
            update_parts.append("t.updated_at = datetime()")
            query = f"""
            MATCH (t:Concept {{name: $name}})
            SET {', '.join(update_parts)}
            """
            await memory_system.semantic.run_query(query, params)
        
        return {"success": True, "taskId": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.post("/groups", response_model=Dict[str, Any])
async def create_task_group(
    group: TaskNode,
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Create a new task group."""
    try:
        if group.type != "group":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task type must be 'group'"
            )
            
        # Create group using task creation logic
        return await create_task(group, memory_system)
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.post("/groups/{group_id}/tasks/{task_id}", response_model=Dict[str, Any])
async def add_task_to_group(
    group_id: str,
    task_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Add a task to a group."""
    try:
        # Verify group exists and is a group type
        group = await memory_system.semantic.run_query(
            """
            MATCH (g:Concept {name: $group_id})
            RETURN g
            """,
            {"group_id": group_id}
        )
        
        if not group or group[0]["type"] != "group":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group {group_id} not found"
            )
            
        # Update task metadata
        await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $task_id})
            SET t.metadata = CASE
                WHEN t.metadata IS NULL THEN {group_id: $group_id}
                ELSE t.metadata + {group_id: $group_id}
            END
            """,
            {"task_id": task_id, "group_id": group_id}
        )
        
        return {
            "success": True,
            "groupId": group_id,
            "taskId": task_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.get("/groups/{group_id}/tasks", response_model=Dict[str, Any])
async def get_group_tasks(
    group_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Get all tasks in a group."""
    try:
        tasks = await memory_system.semantic.run_query(
            """
            MATCH (t:Concept)
            WHERE t.type = 'task' AND t.metadata.group_id = $group_id
            RETURN t
            """,
            {"group_id": group_id}
        )
        
        return {
            "tasks": [TaskNode(**task).dict() for task in tasks],
            "groupId": group_id
        }
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.post("/graph/addDependency", response_model=Dict[str, Any])
async def add_task_dependency(
    edge: TaskEdge,
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Add a dependency between tasks."""
    try:
        # Validate both tasks exist and check domain access
        tasks = await memory_system.semantic.run_query(
            """
            MATCH (s:Concept {name: $source})
            MATCH (t:Concept {name: $target})
            RETURN s.domain as source_domain, t.domain as target_domain
            """,
            {
                "source": edge.source,
                "target": edge.target
            }
        )
        
        if not tasks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source or target task not found"
            )
            
        # Validate domain access for both tasks
        for domain in [tasks[0]["source_domain"], tasks[0]["target_domain"]]:
            if domain:
                await validate_domain_access(domain, memory_system)
                
        # Add relationship in semantic layer
        await memory_system.semantic.store_knowledge({
            "relationships": [{
                "from": edge.source,
                "to": edge.target,
                "type": edge.type,
                "label": edge.label,
                "domains": ["tasks"],
                "confidence": 1.0,
                "bidirectional": False
            }]
        })
        
        return {
            "success": True,
            "edgeId": f"{edge.source}-{edge.target}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.post("/{task_id}/subtasks", response_model=Dict[str, Any])
async def add_subtask(
    task_id: str,
    subtask: SubTask,
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Add a subtask to a task."""
    try:
        # Store subtask in episodic memory
        memory = Memory(
            content=subtask.dict(),
            type=MemoryType.TASK_UPDATE,
            metadata={
                "task_id": task_id,
                "type": "sub_task",
                "timestamp": datetime.now().isoformat()
            }
        )
        await memory_system.episodic.store(memory)
        
        return {
            "success": True,
            "taskId": task_id,
            "subtaskId": subtask.id
        }
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.patch("/{task_id}/sub-tasks/{subtask_id}", response_model=Dict[str, Any])
async def update_subtask(
    task_id: str,
    subtask_id: str,
    update: Dict[str, Any],
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Update a subtask's completion status."""
    try:
        # Get current task
        task = await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $task_id})
            RETURN t
            """,
            {"task_id": task_id}
        )
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
            
        # Update subtask in episodic memory
        memory = Memory(
            content={
                "id": subtask_id,
                "completed": update.get("completed", False),
                "updated_at": datetime.now().isoformat()
            },
            type=MemoryType.TASK_UPDATE,
            metadata={
                "task_id": task_id,
                "subtask_id": subtask_id,
                "type": "sub_task_update",
                "timestamp": datetime.now().isoformat()
            }
        )
        await memory_system.episodic.store(memory)
        
        return {
            "success": True,
            "taskId": task_id,
            "subtaskId": subtask_id,
            "completed": update.get("completed", False)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.post("/{task_id}/comments", response_model=Dict[str, Any])
async def add_comment(
    task_id: str,
    comment: Comment,
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Add a comment to a task."""
    try:
        # Store comment in episodic memory
        memory = Memory(
            content=comment.dict(),
            type=MemoryType.TASK_UPDATE,
            metadata={
                "task_id": task_id,
                "type": "comment",
                "timestamp": datetime.now().isoformat()
            }
        )
        await memory_system.episodic.store(memory)
        
        return {
            "success": True,
            "taskId": task_id,
            "commentId": comment.id
        }
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.get("/{task_id}/history", response_model=Dict[str, Any])
async def get_task_history(
    task_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Get task history including state changes, updates, comments, and assignments."""
    try:
        # Get task
        task = await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $task_id})
            RETURN t
            """,
            {"task_id": task_id}
        )
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
            
        # Get history from metadata
        metadata = task[0].get("metadata", {})
        
        return {
            "taskId": task_id,
            "stateHistory": metadata.get("state_history", []),
            "updateHistory": metadata.get("update_history", []),
            "comments": metadata.get("comments", []),
            "assignmentHistory": metadata.get("assignment_history", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@tasks_router.post("/{task_id}/transition", response_model=Dict[str, Any])
async def transition_task_state(
    task_id: str,
    new_state: TaskState,
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Transition a task to a new state."""
    try:
        # Get current task state
        current_task = await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $name})
            RETURN t.status as status, t.domain as domain
            """,
            {"name": task_id}
        )
        
        if not current_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
            
        # Validate state transition
        await validate_state_transition(
            TaskState(current_task[0]["status"]),
            new_state,
            task_id,
            memory_system
        )
        
        # Validate domain access
        if current_task[0]["domain"]:
            await validate_domain_access(current_task[0]["domain"], memory_system)
            
        # Update task state
        await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $name})
            SET t.status = $status,
                t.updated_at = datetime()
            """,
            {
                "name": task_id,
                "status": new_state
            }
        )
        
        # Store transition in episodic memory
        await memory_system.episodic.store(Memory(
            content=f"Task {task_id} transitioned from {current_task[0]['status']} to {new_state}",
            type=MemoryType.TASK_UPDATE,
            metadata={
                "task_id": task_id,
                "from_state": current_task[0]["status"],
                "to_state": new_state,
                "timestamp": datetime.now().isoformat()
            }
        ))
        
        return {
            "success": True,
            "taskId": task_id,
            "newState": new_state
        }
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))
