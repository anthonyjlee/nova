"""
Task node representation for DAG system.
"""

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import uuid

from .types import TaskStatus, TaskType, AgentType, TaskResult, TaskContext

logger = logging.getLogger(__name__)

class TaskNode:
    """Represents a task node in the DAG."""
    
    def __init__(
        self,
        task_id: Optional[str] = None,
        task_type: TaskType = TaskType.CUSTOM,
        agent_type: AgentType = AgentType.CUSTOM,
        description: str = "",
        inputs: Dict[str, Any] = None,
        parameters: Dict[str, Any] = None,
        required_memory: List[str] = None,
        timeout_seconds: Optional[int] = None
    ):
        """Initialize task node."""
        # Core attributes
        self.task_id = task_id or str(uuid.uuid4())
        self.task_type = task_type
        self.agent_type = agent_type
        self.description = description
        
        # Task configuration
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.required_memory = required_memory or []
        self.timeout_seconds = timeout_seconds
        
        # State management
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[TaskResult] = None
        
        # Dependencies
        self.dependencies: Set[str] = set()  # task_ids this node depends on
        self.dependents: Set[str] = set()    # task_ids that depend on this node
        self.parent_id: Optional[str] = None
        self.children: Set[str] = set()
        
        # Execution context
        self.context: Optional[TaskContext] = None
        self.retries = 0
        self.max_retries = 3
        self.error_history: List[str] = []
    
    def add_dependency(self, task_id: str) -> None:
        """Add a dependency for this task."""
        if task_id != self.task_id:  # Prevent self-dependency
            self.dependencies.add(task_id)
    
    def remove_dependency(self, task_id: str) -> None:
        """Remove a dependency from this task."""
        self.dependencies.discard(task_id)
    
    def add_dependent(self, task_id: str) -> None:
        """Add a dependent task."""
        if task_id != self.task_id:  # Prevent self-dependency
            self.dependents.add(task_id)
    
    def remove_dependent(self, task_id: str) -> None:
        """Remove a dependent task."""
        self.dependents.discard(task_id)
    
    def add_child(self, task_id: str) -> None:
        """Add a child task."""
        if task_id != self.task_id:  # Prevent self-reference
            self.children.add(task_id)
    
    def set_parent(self, task_id: str) -> None:
        """Set the parent task."""
        if task_id != self.task_id:  # Prevent self-reference
            self.parent_id = task_id
    
    def is_ready(self) -> bool:
        """Check if task is ready to execute."""
        return (
            self.status == TaskStatus.PENDING and
            len(self.dependencies) == 0
        )
    
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return (
            self.status == TaskStatus.FAILED and
            self.retries < self.max_retries
        )
    
    def start(self, context: TaskContext) -> None:
        """Start task execution."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        self.context = context
        logger.info(f"Started task {self.task_id} ({self.task_type})")
    
    def complete(self, result: TaskResult) -> None:
        """Complete task execution."""
        self.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.result = result
        
        if not result.success:
            self.error_history.append(result.error or "Unknown error")
            self.retries += 1
            if self.can_retry():
                self.status = TaskStatus.PENDING
                logger.warning(f"Task {self.task_id} failed, will retry ({self.retries}/{self.max_retries})")
            else:
                logger.error(f"Task {self.task_id} failed permanently after {self.retries} retries")
        else:
            logger.info(f"Completed task {self.task_id} successfully")
    
    def cancel(self) -> None:
        """Cancel task execution."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
        logger.info(f"Cancelled task {self.task_id}")
    
    def reset(self) -> None:
        """Reset task state."""
        self.status = TaskStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.context = None
        self.retries = 0
        self.error_history = []
        logger.info(f"Reset task {self.task_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type.name,
            'agent_type': self.agent_type.name,
            'description': self.description,
            'status': self.status.name,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'dependencies': list(self.dependencies),
            'dependents': list(self.dependents),
            'parent_id': self.parent_id,
            'children': list(self.children),
            'inputs': self.inputs,
            'parameters': self.parameters,
            'required_memory': self.required_memory,
            'timeout_seconds': self.timeout_seconds,
            'retries': self.retries,
            'max_retries': self.max_retries,
            'error_history': self.error_history,
            'result': {
                'success': self.result.success,
                'output': self.result.output,
                'error': self.result.error,
                'metadata': self.result.metadata,
                'timestamp': self.result.timestamp.isoformat()
            } if self.result else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskNode':
        """Create task from dictionary."""
        task = cls(
            task_id=data['task_id'],
            task_type=TaskType[data['task_type']],
            agent_type=AgentType[data['agent_type']],
            description=data['description'],
            inputs=data['inputs'],
            parameters=data['parameters'],
            required_memory=data['required_memory'],
            timeout_seconds=data['timeout_seconds']
        )
        
        task.status = TaskStatus[data['status']]
        task.created_at = datetime.fromisoformat(data['created_at'])
        task.started_at = datetime.fromisoformat(data['started_at']) if data['started_at'] else None
        task.completed_at = datetime.fromisoformat(data['completed_at']) if data['completed_at'] else None
        task.dependencies = set(data['dependencies'])
        task.dependents = set(data['dependents'])
        task.parent_id = data['parent_id']
        task.children = set(data['children'])
        task.retries = data['retries']
        task.max_retries = data['max_retries']
        task.error_history = data['error_history']
        
        if data['result']:
            task.result = TaskResult(
                success=data['result']['success'],
                output=data['result']['output'],
                error=data['result']['error'],
                metadata=data['result']['metadata'],
                timestamp=datetime.fromisoformat(data['result']['timestamp'])
            )
        
        return task
