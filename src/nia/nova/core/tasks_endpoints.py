"""Task-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .dependencies import get_memory_system
from .auth import get_permission
from .error_handling import ServiceError
from .models import (
    TaskNode, TaskEdge, TaskUpdate, TaskDetails, 
    TaskState, TaskStateTransition
)
from nia.core.types.memory_types import Memory, MemoryType

# Valid state transitions
VALID_TRANSITIONS = {
    TaskState.PENDING: [TaskState.IN_PROGRESS, TaskState.COMPLETED],
    TaskState.IN_PROGRESS: [TaskState.BLOCKED, TaskState.COMPLETED],
    TaskState.BLOCKED: [TaskState.IN_PROGRESS, TaskState.COMPLETED],
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
                   t.updated_at as updated_at
            """
        )
        
        # Organize tasks by state
        board = {
            "pending": [],
            "in_progress": [],
            "blocked": [],
            "completed": []
        }
        
        for task in tasks:
            status = task["status"] or TaskState.PENDING
            board[status].append({
                "id": task["id"],
                "label": task["label"],
                "domain": task["domain"],
                "team_id": task["team_id"],
                "created_at": task["created_at"],
                "updated_at": task["updated_at"]
            })
            
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
            sub_tasks=[m for m in episodic_data if m["type"] == "sub_task"],
            comments=[m for m in episodic_data if m["type"] == "comment"],
            time_active=str(datetime.now() - task[0]["created_at"]),
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
                        "status": task.get("status", "pending"),
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

@tasks_router.post("/graph/addNode", response_model=Dict[str, Any])
async def add_task_node(
    task: TaskNode,
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Add a new task node to the graph."""
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
        
        # Store task metadata
        await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $name})
            SET t.status = $status,
                t.created_at = datetime(),
                t.importance = $importance
            """,
            {
                "name": task.id,
                "status": task.status,
                "importance": task.metadata.get("importance", 0.5)
            }
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
            
        # Update task in semantic layer
        await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $name})
            SET t.status = $status,
                t.description = $description,
                t.updated_at = datetime()
            """,
            {
                "name": task_id,
                "status": update.status,
                "description": update.label
            }
        )
        
        return {"success": True, "taskId": task_id}
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
