"""Agent type definitions."""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel

class AgentResponse(BaseModel):
    """Base model for agent responses."""
    response: str
    concepts: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    timestamp: Optional[datetime] = None
    confidence: float = 0.0
    source: str = ""
    domain: str = "general"
    perspective: Optional[str] = None
    dialogue_context: Optional[Dict[str, Any]] = None
    dialogue: Optional[str] = None
    key_points: Optional[List[str]] = None
    implications: Optional[List[str]] = None
    uncertainties: Optional[List[str]] = None
    reasoning: Optional[str] = None
    message_type: Optional[str] = None
    agent_type: Optional[str] = None
    references: Optional[List[str]] = None
    is_valid: bool = True
    logging: Dict[str, Any] = {}
    logs: List[Dict[str, Any]] = []
    issues: List[Dict[str, Any]] = []

class DialogueMessage(BaseModel):
    """Model for dialogue messages."""
    content: str
    sender: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}
    message_type: Optional[str] = None
    agent_type: Optional[str] = None
    references: Optional[List[str]] = None

class DialogueContext(BaseModel):
    """Context for dialogue operations."""
    conversation_id: str
    participants: List[str]
    domain: str = "general"
    metadata: Dict[str, Any] = {}

class SemanticMemory(BaseModel):
    """Model for semantic memories."""
    concepts: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}

class ProceduralMemory(BaseModel):
    """Model for procedural memories."""
    steps: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}

class Concept(BaseModel):
    """Model for knowledge concepts."""
    name: str
    type: str
    description: str
    related: List[str] = []
    metadata: Dict[str, Any] = {}
    validation: Optional[Dict[str, Any]] = None

class Relationship(BaseModel):
    """Model for concept relationships."""
    from_concept: str
    to_concept: str
    type: str
    metadata: Dict[str, Any] = {}

class Belief(BaseModel):
    """Model for agent beliefs."""
    content: str
    confidence: float = 0.5
    source: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class TaskState(str, Enum):
    """States for task execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MemoryQuery(BaseModel):
    """Model for memory queries."""
    content: Dict[str, Any]
    filter: Dict[str, Any] = {}
    limit: int = 100
    score_threshold: float = 0.7

class ConsolidationRule(BaseModel):
    """Model for memory consolidation rules."""
    pattern: Dict[str, Any]
    action: str
    metadata: Dict[str, Any] = {}

class MemoryBatch(BaseModel):
    """Model for batched memory operations."""
    memories: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}

class MockMemory(BaseModel):
    """Mock memory model for testing."""
    id: str
    content: Any
    type: str
    metadata: Dict[str, Any] = {}
