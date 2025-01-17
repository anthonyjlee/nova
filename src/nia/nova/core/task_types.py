"""Task types and models for Nova."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

class TaskState(str, Enum):
    """Task state enum."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    """Task priority enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskType(str, Enum):
    """Task type enum."""
    ANALYSIS = "analysis"
    PROCESSING = "processing"
    COORDINATION = "coordination"
    MONITORING = "monitoring"
    MAINTENANCE = "maintenance"
    SYSTEM = "system"

class TaskStateTransition(BaseModel):
    """Task state transition model."""
    from_state: TaskState
    to_state: TaskState
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskDependency(BaseModel):
    """Task dependency model."""
    task_id: str
    dependency_type: str
    required: bool = True
    metadata: Optional[Dict[str, Any]] = None

class TaskConstraint(BaseModel):
    """Task constraint model."""
    type: str
    value: Any
    operator: str
    metadata: Optional[Dict[str, Any]] = None

class TaskResource(BaseModel):
    """Task resource model."""
    type: str
    amount: float
    unit: str
    metadata: Optional[Dict[str, Any]] = None

class TaskSchedule(BaseModel):
    """Task schedule model."""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[float] = None
    repeat: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskProgress(BaseModel):
    """Task progress model."""
    percent_complete: float = 0.0
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskError(BaseModel):
    """Task error model."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class TaskResult(BaseModel):
    """Task result model."""
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[TaskError] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskMetrics(BaseModel):
    """Task metrics model."""
    duration: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    io_operations: int = 0
    metadata: Optional[Dict[str, Any]] = None

class SubTask(BaseModel):
    """Subtask model."""
    id: str
    parent_id: str
    name: str
    state: TaskState
    priority: TaskPriority
    progress: TaskProgress
    metadata: Optional[Dict[str, Any]] = None

class Comment(BaseModel):
    """Task comment model."""
    id: str
    task_id: str
    user_id: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    edited: bool = False
    edited_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskNode(BaseModel):
    """Task node model."""
    id: str
    name: str
    type: TaskType
    state: TaskState
    priority: TaskPriority
    dependencies: List[TaskDependency] = []
    constraints: List[TaskConstraint] = []
    resources: List[TaskResource] = []
    schedule: Optional[TaskSchedule] = None
    progress: TaskProgress = Field(default_factory=lambda: TaskProgress())
    result: Optional[TaskResult] = None
    metrics: TaskMetrics = Field(default_factory=lambda: TaskMetrics())
    metadata: Optional[Dict[str, Any]] = None

class TaskEdge(BaseModel):
    """Task edge model."""
    from_id: str
    to_id: str
    type: str
    weight: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

class TaskUpdate(BaseModel):
    """Task update model."""
    task_id: str
    field: str
    value: Any
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class TaskDetails(BaseModel):
    """Task details model."""
    id: str
    name: str
    description: Optional[str] = None
    type: TaskType
    state: TaskState
    priority: TaskPriority
    owner: str
    assignee: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    dependencies: List[TaskDependency] = []
    constraints: List[TaskConstraint] = []
    resources: List[TaskResource] = []
    schedule: Optional[TaskSchedule] = None
    progress: TaskProgress = Field(default_factory=lambda: TaskProgress())
    result: Optional[TaskResult] = None
    metrics: TaskMetrics = Field(default_factory=lambda: TaskMetrics())
    subtasks: List[SubTask] = []
    comments: List[Comment] = []
    metadata: Optional[Dict[str, Any]] = None

class TaskRequest(BaseModel):
    """Task request model."""
    name: str
    description: Optional[str] = None
    type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[TaskDependency] = []
    constraints: List[TaskConstraint] = []
    resources: List[TaskResource] = []
    schedule: Optional[TaskSchedule] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskResponse(BaseModel):
    """Task response model."""
    task: TaskDetails
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskValidation(BaseModel):
    """Task validation model."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    metadata: Optional[Dict[str, Any]] = None

class TaskSearch(BaseModel):
    """Task search model."""
    query: str
    filters: Optional[Dict[str, Any]] = None
    sort: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskStats(BaseModel):
    """Task statistics model."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_duration: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
