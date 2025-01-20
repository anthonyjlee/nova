"""Agent types and models for Nova."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from nia.core.types.agent_types import AgentResponse as CoreAgentResponse

class AgentState(str, Enum):
    """Agent state enum."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    TERMINATED = "terminated"

class AgentRole(str, Enum):
    """Agent role enum."""
    COORDINATOR = "coordinator"
    WORKER = "worker"
    MONITOR = "monitor"
    ANALYZER = "analyzer"
    VALIDATOR = "validator"
    EXECUTOR = "executor"

class AgentCapability(BaseModel):
    """Agent capability model."""
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None
    requires_auth: bool = False
    metadata: Optional[Dict[str, Any]] = None

class AgentMetrics(BaseModel):
    """Agent metrics model."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_response_time: float = 0.0
    uptime: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

class AgentInteraction(BaseModel):
    """Agent interaction model."""
    from_agent: str
    to_agent: str
    interaction_type: str
    content: Any
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class AgentInfo(BaseModel):
    """Agent information model."""
    id: str
    name: str
    type: str
    version: str
    state: AgentState
    role: AgentRole
    capabilities: List[AgentCapability] = []
    metadata: Optional[Dict[str, Any]] = None

class AgentConfig(BaseModel):
    """Agent configuration model."""
    name: str
    type: str
    role: AgentRole
    capabilities: List[str] = []
    max_concurrent_tasks: int = 1
    timeout: int = 30
    retry_limit: int = 3
    metadata: Optional[Dict[str, Any]] = None

class AgentResponse(CoreAgentResponse):
    """Agent response model extending core AgentResponse."""
    agent_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class AgentError(BaseModel):
    """Agent error model."""
    agent_id: str
    error_type: str
    message: str
    stack_trace: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class AgentLog(BaseModel):
    """Agent log model."""
    agent_id: str
    level: str
    message: str
    context: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

class AgentStatus(BaseModel):
    """Agent status model."""
    agent_id: str
    state: AgentState
    health: float = 1.0
    last_heartbeat: str = Field(default_factory=lambda: datetime.now().isoformat())
    current_tasks: List[str] = []
    metadata: Optional[Dict[str, Any]] = None

class AgentResource(BaseModel):
    """Agent resource model."""
    agent_id: str
    resource_type: str
    resource_id: str
    permissions: List[str] = []
    metadata: Optional[Dict[str, Any]] = None

class AgentValidation(BaseModel):
    """Agent validation model."""
    agent_id: str
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    metadata: Optional[Dict[str, Any]] = None

class AgentProfile(BaseModel):
    """Agent profile model."""
    agent_id: str
    name: str
    description: str
    capabilities: List[AgentCapability] = []
    preferences: Dict[str, Any] = {}
    metadata: Optional[Dict[str, Any]] = None

class AgentGroup(BaseModel):
    """Agent group model."""
    id: str
    name: str
    description: str
    members: List[str] = []
    leader_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentPermission(BaseModel):
    """Agent permission model."""
    agent_id: str
    resource_type: str
    actions: List[str] = []
    constraints: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentHistory(BaseModel):
    """Agent history model."""
    agent_id: str
    events: List[Dict[str, Any]] = []
    metrics: AgentMetrics
    metadata: Optional[Dict[str, Any]] = None

class AgentRequest(BaseModel):
    """Agent request model."""
    agent_id: str
    action: str
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentContext(BaseModel):
    """Agent context model."""
    agent_id: str
    environment: Dict[str, Any] = {}
    state: Dict[str, Any] = {}
    metadata: Optional[Dict[str, Any]] = None
