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

class Domain(str, Enum):
    """Base domains and knowledge verticals."""
    # Base domains
    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    
    # Knowledge verticals
    RETAIL = "retail"
    BUSINESS = "business"
    PSYCHOLOGY = "psychology"
    TECHNOLOGY = "technology"
    BACKEND = "backend"
    DATABASE = "database"
    GENERAL = "general"  # For cross-domain or general knowledge

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

class DomainContext(BaseModel):
    """Domain context for memories and concepts."""
    primary_domain: Domain
    knowledge_vertical: Optional[Domain] = None
    cross_domain: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "requested": False,
            "approved": False,
            "justification": "",
            "source_domain": None,
            "target_domain": None
        }
    )
    confidence: float = 1.0
    validation: Optional[Dict[str, Any]] = None

class Memory(BaseModel):
    """Base memory model."""
    id: Optional[str] = None
    content: Union[str, Dict[str, Any]]  # Allow both string and dict content
    type: MemoryType
    importance: float = 1.0
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Dict[str, Any] = {}
    consolidated: bool = False
    domain_context: Optional[DomainContext] = None

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
    domain_context: DomainContext
    validation: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "confidence": 1.0,
            "supported_by": [],
            "contradicted_by": [],
            "needs_verification": []
        }
    )

class Relationship(BaseModel):
    """A relationship between concepts."""
    source: str
    target: str
    type: str
    attributes: Dict[str, Any] = {}
    domain_context: DomainContext
    confidence: float = 1.0
    bidirectional: bool = False

class Belief(BaseModel):
    """A belief about concepts."""
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    evidence: List[str] = []
    domain_context: DomainContext
    source: str = "system"
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

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
    domain_context: DomainContext
    cross_domain_rules: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "allowed_verticals": [],
            "requires_approval": True,
            "validation_rules": {}
        }
    )

class MemoryBatch(BaseModel):
    """Batch of memories for processing."""
    memories: List[Memory]
    metadata: Dict[str, Any] = {}
    batch_id: Optional[str] = None
