"""Memory type definitions for NIA."""

from enum import Enum
from typing import Dict, Optional, Any, List, Union, TypeVar, Protocol
from pydantic import BaseModel, Field
from datetime import datetime

from typing import runtime_checkable

@runtime_checkable
class JSONSerializable(Protocol):
    """Protocol for JSON-serializable objects."""
    def dict(self) -> Dict[str, Any]: ...

class MemoryType(str, Enum):
    """Types of memories in the system."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EMOTIONAL = "emotional"

class AgentResponse(BaseModel):
    """Response from an agent."""
    content: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = {}

class DialogueMessage(BaseModel):
    """A message in a dialogue."""
    content: str
    sender: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}

class DialogueContext(BaseModel):
    """Context for a dialogue."""
    messages: List[DialogueMessage] = []
    participants: List[str] = []
    metadata: Dict[str, Any] = {}

class Memory(BaseModel):
    """Base memory model."""
    id: Optional[str] = None
    content: str
    type: MemoryType
    importance: float = 1.0
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Dict[str, Any] = {}
    consolidated: bool = False

class EpisodicMemory(Memory):
    """Episodic memory model."""
    type: MemoryType = MemoryType.EPISODIC
    location: Optional[str] = None
    participants: Optional[List[str]] = None
    emotions: Optional[Dict[str, float]] = None
    related_memories: Optional[List[str]] = None

class SemanticMemory(Memory):
    """Semantic memory model."""
    type: MemoryType = MemoryType.SEMANTIC
    concepts: List[str] = []
    relationships: List[Dict[str, str]] = []
    confidence: float = 1.0

class ProceduralMemory(Memory):
    """Procedural memory model."""
    type: MemoryType = MemoryType.PROCEDURAL
    steps: List[str] = []
    prerequisites: List[str] = []
    success_criteria: List[str] = []

class Concept(BaseModel):
    """A concept in the knowledge graph."""
    name: str
    type: str
    description: str
    attributes: Dict[str, Any] = {}
    validation: Optional[Dict[str, Any]] = None

class Relationship(BaseModel):
    """A relationship between concepts."""
    source: str
    target: str
    type: str
    attributes: Dict[str, Any] = {}
    confidence: float = 1.0

class Belief(BaseModel):
    """A belief about concepts."""
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    evidence: List[str] = []

class MemoryQuery(BaseModel):
    """Query for searching memories."""
    content: Optional[str] = None
    type: Optional[MemoryType] = None
    time_range: Optional[tuple[datetime, datetime]] = None
    filter: Dict[str, Any] = {}
    limit: int = 10

class ConsolidationRule(BaseModel):
    """Rule for memory consolidation."""
    pattern: str
    conditions: Dict[str, Any] = {}
    actions: List[str] = []
    priority: int = 0

class MemoryBatch(BaseModel):
    """Batch of memories for processing."""
    memories: List[Memory]
    metadata: Dict[str, Any] = {}
    batch_id: Optional[str] = None
