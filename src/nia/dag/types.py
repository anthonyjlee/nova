"""
Type definitions and enums for DAG system.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

class TaskStatus(Enum):
    """Status of a task in the DAG."""
    PENDING = auto()      # Task not yet started
    READY = auto()        # Dependencies met, ready to execute
    RUNNING = auto()      # Currently executing
    COMPLETED = auto()    # Successfully completed
    FAILED = auto()       # Failed to complete
    BLOCKED = auto()      # Dependencies not met
    CANCELLED = auto()    # Task cancelled

class TaskType(Enum):
    """Types of tasks that can be executed."""
    ANALYSIS = auto()     # Analyze input or situation
    PLANNING = auto()     # Plan next steps
    EXECUTION = auto()    # Execute an action
    REFLECTION = auto()   # Reflect on results
    RESEARCH = auto()     # Research or gather information
    MEMORY = auto()       # Memory operations
    COORDINATION = auto() # Coordinate between agents
    SYNTHESIS = auto()    # Synthesize information
    CUSTOM = auto()       # Custom task type

class AgentType(Enum):
    """Types of agents that can handle tasks."""
    META = auto()         # Meta agent for coordination
    BELIEF = auto()       # Belief management
    DESIRE = auto()       # Desire management
    EMOTION = auto()      # Emotion processing
    REFLECTION = auto()   # Reflection processing
    RESEARCH = auto()     # Research and information gathering
    MEMORY = auto()       # Memory management
    CUSTOM = auto()       # Custom agent type

@dataclass
class TaskResult:
    """Result of a task execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TaskContext:
    """Context for task execution."""
    inputs: Dict[str, Any]
    parameters: Dict[str, Any]
    memory_context: Optional[Dict[str, Any]] = None
    agent_state: Optional[Dict[str, Any]] = None
    parent_context: Optional['TaskContext'] = None

    def __post_init__(self):
        """Initialize optional fields."""
        if self.memory_context is None:
            self.memory_context = {}
        if self.agent_state is None:
            self.agent_state = {}
