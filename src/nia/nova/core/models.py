"""Models for Nova endpoints."""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List, Union, Literal
from datetime import datetime
from enum import Enum

class TaskState(str, Enum):
    """Task states for Kanban-style interface."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"

TaskPriority = Literal["high", "medium", "low"]

class TaskStateTransition(BaseModel):
    """Valid task state transitions."""
    from_state: TaskState
    to_state: TaskState
    requires_validation: bool = False
    validation_rules: Optional[Dict[str, Any]] = None

class Message(BaseModel):
    """Message model."""
    id: str
    content: str
    sender_type: str
    sender_id: str
    timestamp: str
    metadata: Dict[str, Any] = {}

class MessageResponse(BaseModel):
    """Response model for messages."""
    id: str
    content: str
    timestamp: str

class SubTask(BaseModel):
    """SubTask model."""
    id: str
    description: str
    completed: bool = False
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class TaskNode(BaseModel):
    """Task node model matching frontend Task interface."""
    id: str
    label: str
    type: str = "task"
    status: TaskState = TaskState.PENDING
    description: Optional[str] = None
    team_id: Optional[str] = None
    domain: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Backward compatibility fields
    title: Optional[str] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    dueDate: Optional[str] = None
    tags: Optional[List[str]] = None
    time_active: Optional[int] = None
    dependencies: Optional[List[str]] = None
    blocked_by: Optional[List[str]] = None
    sub_tasks: Optional[List[SubTask]] = None
    completed: Optional[bool] = None

    @validator('status')
    def validate_status(cls, v):
        if isinstance(v, str):
            return TaskState(v)
        return v

    @validator('created_at', 'updated_at')
    def validate_dates(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

class TaskEdge(BaseModel):
    """Task edge model."""
    source: str
    target: str
    type: str
    label: Optional[str] = None

class Comment(BaseModel):
    """Comment model."""
    id: str
    content: str
    author: str
    timestamp: str
    edited: Optional[bool] = None

class TaskDetails(BaseModel):
    """Extended task details model."""
    task: TaskNode
    dependencies: List[str] = Field(default_factory=list)
    blocked_by: List[str] = Field(default_factory=list)
    sub_tasks: List[SubTask] = Field(default_factory=list)
    comments: List[Comment] = Field(default_factory=list)
    time_active: Optional[str] = None
    domain_access: List[str] = Field(default_factory=list)

class TaskUpdate(BaseModel):
    """Task update model."""
    label: Optional[str] = None
    status: Optional[TaskState] = None
    description: Optional[str] = None
    team_id: Optional[str] = None
    domain: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    # Backward compatibility fields
    title: Optional[str] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    dueDate: Optional[str] = None
    tags: Optional[List[str]] = None
    completed: Optional[bool] = None

    @validator('status')
    def validate_status(cls, v):
        if isinstance(v, str):
            return TaskState(v)
        return v

class ChannelDetails(BaseModel):
    """Channel information model."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_public: bool = True
    workspace: str
    domain: Optional[str] = None
    type: str = "channel"  # channel, dm, team
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChannelMember(BaseModel):
    """Channel member model."""
    id: str
    name: str
    type: str  # user or agent
    role: str  # admin, member
    status: str  # active, inactive
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PinnedItem(BaseModel):
    """Pinned item model."""
    id: str
    type: str  # message, file, link
    content: Dict[str, Any]
    pinned_by: str
    pinned_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChannelSettings(BaseModel):
    """Channel settings model."""
    notifications: bool = True
    privacy: str = "public"  # public, private
    retention_days: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentMetrics(BaseModel):
    """Agent performance metrics model."""
    response_time: float  # Average response time in seconds
    tasks_completed: int
    success_rate: float
    uptime: float  # Percentage
    last_active: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentInteraction(BaseModel):
    """Agent interaction history model."""
    id: str
    type: str  # message, task, action
    content: str
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentType(str, Enum):
    """Agent types matching frontend."""
    AGENT = "agent"
    TEAM = "team"
    SYSTEM = "system"

class AgentStatus(str, Enum):
    """Agent statuses matching frontend."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class AgentWorkspace(str, Enum):
    """Agent workspaces matching frontend."""
    PERSONAL = "personal"
    SHARED = "shared"
    SYSTEM = "system"

class AgentDomain(str, Enum):
    """Agent domains matching frontend."""
    GENERAL = "general"
    TASKS = "tasks"
    CHAT = "chat"
    ANALYSIS = "analysis"

class AgentRelationType(str, Enum):
    """Agent relationship types matching frontend."""
    COORDINATES = "COORDINATES"
    MANAGES = "MANAGES"
    ASSISTS = "ASSISTS"
    COLLABORATES_WITH = "COLLABORATES_WITH"
    REPORTS_TO = "REPORTS_TO"
    DELEGATES_TO = "DELEGATES_TO"
    DEPENDS_ON = "DEPENDS_ON"

class AgentMetadata(BaseModel):
    """Agent metadata matching frontend."""
    type: str
    capabilities: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    thread_id: Optional[str] = None

class AgentRelationship(BaseModel):
    """Agent relationship matching frontend."""
    target_id: str
    type: AgentRelationType
    properties: Dict[str, Any] = Field(default_factory=dict)

class AgentInfo(BaseModel):
    """Agent information model matching frontend interface."""
    id: str
    name: str
    type: AgentType
    workspace: AgentWorkspace = AgentWorkspace.PERSONAL
    domain: AgentDomain = AgentDomain.GENERAL
    status: AgentStatus = AgentStatus.ACTIVE
    metadata: AgentMetadata
    relationships: Optional[List[AgentRelationship]] = None

class AgentTeam(BaseModel):
    """Agent team model."""
    id: str
    name: str
    agents: List[AgentInfo]
    status: str
    channel_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Concept(BaseModel):
    """Concept model for analysis."""
    name: str
    type: str
    description: str
    confidence: float
    relationships: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KeyPoint(BaseModel):
    statement: str
    type: str
    confidence: float
    importance: float

class ComplexityFactor(BaseModel):
    factor: str
    weight: float

class Structure(BaseModel):
    sections: List[str]
    relationships: List[str]
    domain_factors: Dict[str, Union[str, float]]
    complexity_factors: List[ComplexityFactor]

class AnalysisResponse(BaseModel):
    concepts: List[Concept]
    key_points: List[KeyPoint]
    structure: Structure

class Metric(BaseModel):
    name: str
    value: Union[str, float, int]
    confidence: float

class Trend(BaseModel):
    name: str
    description: str
    confidence: float

class Insight(BaseModel):
    type: str
    description: str
    confidence: float
    recommendations: List[str]

class Analytics(BaseModel):
    key_metrics: List[Metric]
    trends: List[Trend]

class AnalyticsResponse(BaseModel):
    analytics: Dict[str, Any]
    insights: List[Dict[str, Any]]
    confidence: float
    timestamp: str

# Request Models
class AnalyticsRequest(BaseModel):
    type: str = Field(..., description="Type of analytics to perform")
    content: Dict[str, Any] = Field(..., description="Content to analyze")
    domain: Optional[str] = Field(None, description="Domain for analysis")

class TaskRequest(BaseModel):
    task_type: str
    content: Dict[str, Any]
    domain: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CoordinationRequest(BaseModel):
    type: str
    content: str
    domain: Optional[str] = None
    llm_config: Optional[Dict[str, str]] = None

class ResourceAllocationRequest(BaseModel):
    resources: List[Dict[str, Any]]
    constraints: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None

class MemoryRequest(BaseModel):
    content: str
    type: str
    importance: Optional[float] = 0.5
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class FlowOptimizationRequest(BaseModel):
    flow_id: str
    optimization_type: str
    constraints: Optional[Dict[str, Any]] = None

class AgentAssignmentRequest(BaseModel):
    task_id: str
    agent_type: str
    capabilities: List[str]
    domain: Optional[str] = None

class ParseRequest(BaseModel):
    text: str
    domain: Optional[str] = None
    llm_config: Optional[Dict[str, str]] = None

# Response Models
class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    timestamp: str

class CoordinationResponse(BaseModel):
    coordination_id: str
    status: str
    agents: List[str]
    timestamp: str

class ResourceAllocationResponse(BaseModel):
    allocations: List[Dict[str, Any]]
    analytics: Dict[str, Any]
    confidence: float
    timestamp: str

class MemoryResponse(BaseModel):
    memory_id: str
    status: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: str

class FlowOptimizationResponse(BaseModel):
    flow_id: str
    optimizations: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    timestamp: str

class AgentAssignmentResponse(BaseModel):
    task_id: str
    agent_id: str
    status: str
    timestamp: str

class ParseResponse(BaseModel):
    parsed_content: Dict[str, Any]
    confidence: float
    metadata: Dict[str, Any]
    timestamp: str

class ProfileResponse(BaseModel):
    profile_id: str
    status: str
    timestamp: str

class PreferenceResponse(BaseModel):
    status: str
    preferences: Dict[str, Any]
    timestamp: str

class AgentCapabilitiesResponse(BaseModel):
    agent_id: str
    capabilities: List[str]
    timestamp: str

class AgentTypesResponse(BaseModel):
    agent_types: List[str]
    timestamp: str

class AgentSearchResponse(BaseModel):
    agents: List[Dict[str, Any]]
    timestamp: str

class AgentHistoryResponse(BaseModel):
    agent_id: str
    interactions: List[Dict[str, Any]]
    timestamp: str

class AgentMetricsResponse(BaseModel):
    agent_id: str
    performance_metrics: Dict[str, Any]
    timestamp: str

class AgentStatusResponse(BaseModel):
    agent_id: str
    status: str
    timestamp: str

class AgentResponse(BaseModel):
    """Response model for agent operations matching frontend schema."""
    agent_id: str = Field(alias="id")
    name: str
    type: Literal["agent"] = Field(default="agent")
    agentType: str
    status: str = Field(default="active")
    capabilities: List[str] = Field(default_factory=list)
    workspace: str = Field(default="personal")  # Allow any workspace value
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @validator('workspace')
    def validate_workspace(cls, v):
        """Convert system workspace to personal for frontend compatibility."""
        return "personal" if v == "system" else v

    class Config:
        allow_population_by_field_name = True

class GraphPruneResponse(BaseModel):
    nodes_removed: int
    edges_removed: int
    timestamp: str

class GraphHealthResponse(BaseModel):
    status: str
    issues: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    timestamp: str

class GraphOptimizeResponse(BaseModel):
    optimizations_applied: List[str]
    performance_impact: Dict[str, Any]
    timestamp: str

class GraphStatisticsResponse(BaseModel):
    node_count: int
    edge_count: int
    density: float
    clustering_coefficient: float
    timestamp: str

class GraphBackupResponse(BaseModel):
    backup_id: str
    size_bytes: int
    node_count: int
    edge_count: int
    timestamp: str

# LLM Response Models for Outlines JSON Generation
class LLMConcept(BaseModel):
    """A concept identified in LLM analysis."""
    name: str = Field(..., description="Name of the concept")
    type: str = Field(..., description="Type of concept (e.g., scientific, technical, abstract)")
    description: str = Field(..., description="Detailed description of the concept")
    related: List[str] = Field(default_factory=list, description="List of related concepts")

class LLMAnalysisResult(BaseModel):
    """Analysis result from LLM using outlines.generate.json."""
    response: str = Field(..., description="The main analysis response")
    concepts: List[LLMConcept] = Field(..., description="List of identified concepts")
    key_points: List[str] = Field(..., description="List of key points from the analysis")
    implications: List[str] = Field(..., description="List of implications drawn from the analysis")
    uncertainties: List[str] = Field(..., description="List of uncertainties or open questions")
    reasoning: List[str] = Field(..., description="Step-by-step reasoning process")

class LLMAnalyticsResult(BaseModel):
    """Analytics result from LLM using outlines.generate.json."""
    response: str = Field(..., description="The analysis response")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")

class LLMErrorResponse(BaseModel):
    """Error response from LLM using outlines.generate.json."""
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    confidence: Literal[0.0] = Field(default=0.0, description="Always 0.0 for errors")

class ThreadRequest(BaseModel):
    """Request model for thread operations."""
    title: str
    workspace: str
    domain: Optional[str] = None
    participants: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ThreadParticipant(BaseModel):
    """Thread participant model."""
    id: str
    name: str
    type: Literal["user", "agent"]
    agentType: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    workspace: str = "personal"
    domain: Optional[str] = None
    threadId: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ThreadMessage(BaseModel):
    """Thread message model."""
    id: str
    threadId: str
    content: str
    sender: Dict[str, Any]
    timestamp: str
    workspace: str = "personal"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ThreadValidation(BaseModel):
    """Thread validation model."""
    domain: str
    access_domain: str
    confidence: float
    source: str
    timestamp: str
    supported_by: List[str] = Field(default_factory=list)
    contradicted_by: List[str] = Field(default_factory=list)
    needs_verification: List[str] = Field(default_factory=list)
    cross_domain: Dict[str, Any] = Field(
        default_factory=lambda: {
            "approved": False,
            "requested": False,
            "source_domain": "",
            "target_domain": ""
        }
    )

class ThreadResponse(BaseModel):
    """Response model for thread operations."""
    id: str
    title: str  # Changed from name to title
    domain: str = "general"  # Made required with default
    status: str = "active"  # Added status field
    created_at: str  # Changed from createdAt
    updated_at: str  # Changed from updatedAt
    workspace: str = "personal"
    participants: List[ThreadParticipant] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "chat",
            "system": False,
            "pinned": False,
            "description": ""
        }
    )
    validation: ThreadValidation = Field(
        default_factory=lambda: ThreadValidation(
            domain="general",
            access_domain="general",
            confidence=1.0,
            source="system",
            timestamp=datetime.utcnow().isoformat()
        )
    )

class MessageRequest(BaseModel):
    """Request model for message operations."""
    content: str
    thread_id: str
    sender_type: str = "user"
    sender_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ThreadListResponse(BaseModel):
    """Response model for listing threads."""
    threads: List[ThreadResponse]
    total: int
    page: Optional[int] = None
    page_size: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
