"""Task-related endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .dependencies import get_memory_system, get_feature_flags
from .auth import get_permission
from .error_handling import ServiceError
from .validation import ValidationResult, ValidationPattern
from .models import (
    TaskNode, TaskEdge, TaskUpdate, TaskDetails, TaskState, TaskStateTransition,
    SubTask, Comment, TaskPriority
)
from nia.core.types.memory_types import Memory, MemoryType
from nia.core.feature_flags import FeatureFlags

logger = logging.getLogger(__name__)

# Valid state transitions
VALID_TRANSITIONS = {
    TaskState.PENDING: [TaskState.IN_PROGRESS],  # Can only start from pending
    TaskState.IN_PROGRESS: [TaskState.BLOCKED, TaskState.COMPLETED],  # Can block or complete from in progress
    TaskState.BLOCKED: [TaskState.IN_PROGRESS],  # Can only resume to in progress from blocked
    TaskState.COMPLETED: []  # No transitions from completed
}

class TaskValidationPattern(ValidationPattern):
    """Task-specific validation pattern."""
    task_id: str
    state_from: Optional[str] = None
    state_to: Optional[str] = None
    domain: Optional[str] = None

    model_config = {
        "populate_by_name": True
    }

async def validate_state_transition(
    current_state: TaskState,
    new_state: TaskState,
    task_id: str,
    memory_system: Any,
    debug_flags = None
) -> ValidationResult:
    """Validate if a state transition is allowed with debug logging."""
    try:
        if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
            logger.debug(f"Validating state transition - from: {current_state}, to: {new_state}, task: {task_id}")
            
        validation_issues = []
        
        # Check valid transitions
        if new_state not in VALID_TRANSITIONS.get(current_state, []):
            issue = {
                "type": "invalid_transition",
                "severity": "high",
                "description": f"Invalid state transition from {current_state} to {new_state}",
                "task_id": task_id
            }
            validation_issues.append(issue)
            
            if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                logger.warning(f"Invalid state transition detected: {issue}")
                
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
                issue = {
                    "type": "invalid_block",
                    "severity": "high",
                    "description": "Cannot block task without dependencies",
                    "task_id": task_id
                }
                validation_issues.append(issue)
                
                if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                    logger.warning(f"Invalid block attempt detected: {issue}")
                    
        # Create validation result
        result = ValidationResult(
            is_valid=len(validation_issues) == 0,
            issues=validation_issues,
            metadata={
                "task_id": task_id,
                "from_state": current_state,
                "to_state": new_state,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        if debug_flags:
            if await debug_flags.is_debug_enabled('log_validation'):
                logger.debug(f"State transition validation result: {result.dict()}")
                
            if not result.is_valid and await debug_flags.is_debug_enabled('strict_mode'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=validation_issues[0]["description"]
                )
                
        return result
        
    except Exception as e:
        error_msg = f"Error validating state transition: {str(e)}"
        logger.error(error_msg)
        
        if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
            logger.error(error_msg)
            
        raise

async def validate_domain_access(
    domain: str,
    memory_system: Any,
    debug_flags = None
) -> ValidationResult:
    """Validate domain access permissions with debug logging."""
    try:
        if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
            logger.debug(f"Validating domain access - domain: {domain}")
            
        validation_issues = []
        
        try:
            await memory_system.validate_domain_access(domain)
        except Exception as e:
            issue = {
                "type": "domain_access",
                "severity": "high",
                "description": f"Domain access denied: {str(e)}",
                "domain": domain
            }
            validation_issues.append(issue)
            
            if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                logger.warning(f"Domain access validation failed: {issue}")
                
        # Create validation result
        result = ValidationResult(
            is_valid=len(validation_issues) == 0,
            issues=validation_issues,
            metadata={
                "domain": domain,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        if debug_flags:
            if await debug_flags.is_debug_enabled('log_validation'):
                logger.debug(f"Domain access validation result: {result.dict()}")
                
            if not result.is_valid and await debug_flags.is_debug_enabled('strict_mode'):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=validation_issues[0]["description"]
                )
                
        return result
        
    except Exception as e:
        error_msg = f"Error validating domain access: {str(e)}"
        logger.error(error_msg)
        
        if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
            logger.error(error_msg)
            
        raise

async def validate_task(
    task: TaskNode,
    memory_system: Any,
    debug_flags = None
) -> ValidationResult:
    """Validate task data with debug logging."""
    try:
        if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
            logger.debug(f"Validating task data: {task.dict()}")
            
        validation_issues = []
        
        # Validate required fields
        if not task.id:
            validation_issues.append({
                "type": "missing_field",
                "severity": "high",
                "description": "Task ID is required"
            })
            
        if not task.label:
            validation_issues.append({
                "type": "missing_field",
                "severity": "high",
                "description": "Task label is required"
            })
            
        # Validate field formats
        if task.dueDate:
            try:
                datetime.fromisoformat(task.dueDate)
            except ValueError:
                validation_issues.append({
                    "type": "invalid_format",
                    "severity": "medium",
                    "description": "Due date must be in ISO format"
                })
                
        # Validate dependencies
        if task.dependencies:
            for dep in task.dependencies:
                # Check if dependency exists
                dep_exists = await memory_system.semantic.run_query(
                    """
                    MATCH (t:Concept {name: $dep_id})
                    RETURN count(t) as exists
                    """,
                    {"dep_id": dep}
                )
                if dep_exists[0]["exists"] == 0:
                    validation_issues.append({
                        "type": "invalid_dependency",
                        "severity": "medium",
                        "description": f"Dependency {dep} does not exist"
                    })
                    
        # Create validation result
        result = ValidationResult(
            is_valid=len(validation_issues) == 0,
            issues=validation_issues,
            metadata={
                "task_id": task.id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        if debug_flags:
            if await debug_flags.is_debug_enabled('log_validation'):
                logger.debug(f"Task validation result: {result.dict()}")
                
            if not result.is_valid and await debug_flags.is_debug_enabled('strict_mode'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=validation_issues[0]["description"]
                )
                
        return result
        
    except Exception as e:
        error_msg = f"Error validating task: {str(e)}"
        logger.error(error_msg)
        
        if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
            logger.error(error_msg)
            
        raise

tasks_router = APIRouter(
    prefix="/api/tasks",
    tags=["Tasks"],
    dependencies=[Depends(get_permission("write"))]
)

@tasks_router.post("", response_model=None)
async def create_task(
    task: TaskNode,
    memory_system: Any = Depends(get_memory_system),
    debug_flags = Depends(get_feature_flags, use_cache=True)
) -> Dict[str, Any]:
    """Create a new task with validation."""
    try:
        # Validate task data
        validation_result = await validate_task(task, memory_system, debug_flags)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result.issues[0]["description"]
            )
            
        # Validate domain access
        if task.domain:
            domain_result = await validate_domain_access(
                task.domain,
                memory_system,
                debug_flags
            )
            if not domain_result.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=domain_result.issues[0]["description"]
                )
                
        # Store task in semantic layer with validation metadata
        await memory_system.semantic.store_knowledge({
            "concepts": [{
                "name": task.id,
                "type": "task",
                "description": task.label,
                "validation": {
                    "domain": "tasks",
                    "access_domain": "tasks",
                    "confidence": 1.0,
                    "source": "system",
                    "validation_result": validation_result.dict()
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
                t.completed = $completed,
                t.validation = $validation
            """,
            {
                **task.dict(),
                "validation": validation_result.dict()
            }
        )
        
        return {
            "success": True,
            "taskId": task.id,
            "validation": validation_result.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error creating task: {str(e)}"
        logger.error(error_msg)
        
        if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
            logger.error(error_msg)
            
        raise ServiceError(error_msg)

@tasks_router.post("/{task_id}/transition", response_model=None)
async def transition_task_state(
    task_id: str,
    new_state: TaskState,
    memory_system: Any = Depends(get_memory_system),
    debug_flags = Depends(get_feature_flags, use_cache=True)
) -> Dict[str, Any]:
    """Transition a task to a new state with validation."""
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
            
        # Validate state transition with debug flags
        validation_result = await validate_state_transition(
            TaskState(current_task[0]["status"]),
            new_state,
            task_id,
            memory_system,
            debug_flags
        )
        
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result.issues[0]["description"]
            )
        
        # Validate domain access with debug flags
        if current_task[0]["domain"]:
            domain_result = await validate_domain_access(
                current_task[0]["domain"],
                memory_system,
                debug_flags
            )
            
            if not domain_result.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=domain_result.issues[0]["description"]
                )
                
        # Update task state with validation metadata
        await memory_system.semantic.run_query(
            """
            MATCH (t:Concept {name: $name})
            SET t.status = $status,
                t.updated_at = datetime(),
                t.validation = $validation
            """,
            {
                "name": task_id,
                "status": new_state,
                "validation": validation_result.dict()
            }
        )
        
        # Store transition in episodic memory with validation
        await memory_system.episodic.store(Memory(
            content=f"Task {task_id} transitioned from {current_task[0]['status']} to {new_state}",
            type=MemoryType.TASK_UPDATE,
            metadata={
                "task_id": task_id,
                "from_state": current_task[0]["status"],
                "to_state": new_state,
                "timestamp": datetime.now().isoformat(),
                "validation": validation_result.dict()
            }
        ))
        
        return {
            "success": True,
            "taskId": task_id,
            "newState": new_state,
            "validation": validation_result.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error transitioning task state: {str(e)}"
        logger.error(error_msg)
        
        if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
            logger.error(error_msg)
            
        raise ServiceError(error_msg)
