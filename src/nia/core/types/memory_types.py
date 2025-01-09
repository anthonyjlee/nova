"""Memory type definitions for NIA."""

from enum import Enum
from typing import Dict, Optional, Any, List, Union, TypeVar, Protocol
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from typing import runtime_checkable

@runtime_checkable
class JSONSerializable(Protocol):
    """Protocol for JSON-serializable objects."""
    def dict(self) -> Dict[str, Any]: ...

class BaseDomain(str, Enum):
    """Base domains for memory organization."""
    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    GENERAL = "general"  # For cross-domain or general knowledge

    def __str__(self):
        return self.value

class KnowledgeVertical(str, Enum):
    """Knowledge verticals for specialized domains."""
    RETAIL = "retail"
    BUSINESS = "business"
    PSYCHOLOGY = "psychology"
    TECHNOLOGY = "technology"
    BACKEND = "backend"
    DATABASE = "database"
    GENERAL = "general"  # For general knowledge within a vertical

    def __str__(self):
        return self.value

class DomainTransfer(BaseModel):
    """Model for cross-domain transfer requests."""
    requested: bool = False
    approved: bool = False
    justification: str = ""
    source_domain: Optional[str] = None
    target_domain: Optional[str] = None
    source_vertical: Optional[str] = None
    target_vertical: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    approval_source: Optional[str] = None

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        d = super().dict()
        if self.source_domain:
            d["source_domain"] = str(self.source_domain)
        if self.target_domain:
            d["target_domain"] = str(self.target_domain)
        if self.source_vertical:
            d["source_vertical"] = str(self.source_vertical)
        if self.target_vertical:
            d["target_vertical"] = str(self.target_vertical)
        if self.approval_timestamp:
            d["approval_timestamp"] = self.approval_timestamp.isoformat()
        return d

class MemoryType(str, Enum):
    """Types of memories in the system."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EMOTIONAL = "emotional"

class DomainContext(BaseModel):
    """Domain context for memories and concepts."""
    primary_domain: str
    knowledge_vertical: Optional[str] = None
    cross_domain: Optional[DomainTransfer] = Field(
        default_factory=lambda: DomainTransfer()
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for domain assignment"
    )
    validation: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "last_validated": datetime.now(timezone.utc).isoformat(),
            "validation_source": "system",
            "validation_rules": []
        }
    )
    access_control: Dict[str, Any] = Field(
        default_factory=lambda: {
            "read": ["system"],
            "write": ["system"],
            "execute": ["system"]
        }
    )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        d = super().dict()
        # Convert enums and complex types to strings
        d["primary_domain"] = str(self.primary_domain)
        if self.knowledge_vertical:
            d["knowledge_vertical"] = str(self.knowledge_vertical)
        if self.cross_domain:
            d["cross_domain"] = self.cross_domain.dict()
        return d

    def validate_transfer(
        self,
        target_domain: Optional[str] = None,
        target_vertical: Optional[str] = None
    ) -> bool:
        """Validate if transfer to target domain/vertical is allowed."""
        # Always allow transfers within same domain
        if target_domain == self.primary_domain:
            return True

        # Check if cross-domain operation is approved
        if self.cross_domain and self.cross_domain.approved:
            if target_domain and self.cross_domain.target_domain == target_domain:
                return True
            if target_vertical and self.cross_domain.target_vertical == target_vertical:
                return True

        # Check knowledge vertical compatibility
        if (self.knowledge_vertical and target_vertical and 
            self.knowledge_vertical == target_vertical):
            return True

        return False

    def request_transfer(
        self,
        target_domain: Optional[str] = None,
        target_vertical: Optional[str] = None,
        justification: str = ""
    ) -> None:
        """Request transfer to target domain/vertical."""
        self.cross_domain = DomainTransfer(
            requested=True,
            justification=justification,
            source_domain=self.primary_domain,
            target_domain=target_domain,
            source_vertical=self.knowledge_vertical,
            target_vertical=target_vertical
        )

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

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        d = super().dict()
        if self.domain_context:
            d["domain_context"] = self.domain_context.dict()
        return d

class Relationship(BaseModel):
    """A relationship between concepts."""
    source: str
    target: str
    type: str
    attributes: Dict[str, Any] = {}
    domain_context: DomainContext
    confidence: float = 1.0
    bidirectional: bool = False

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        d = super().dict()
        if self.domain_context:
            d["domain_context"] = self.domain_context.dict()
        return d

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

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        d = super().dict()
        # Convert datetime to ISO format
        if self.timestamp:
            d["timestamp"] = self.timestamp.isoformat()
        # Convert type enum to string
        d["type"] = self.type.value if isinstance(self.type, MemoryType) else str(self.type)
        # Convert domain context if present
        if self.domain_context:
            d["domain_context"] = self.domain_context.dict()
        return d

class EpisodicMemory(Memory):
    """Episodic memory model."""
    type: MemoryType = MemoryType.EPISODIC
    location: Optional[str] = None
    participants: List[str] = Field(default_factory=list)
    emotions: Dict[str, float] = Field(default_factory=dict)
    related_memories: List[str] = Field(default_factory=list)
    concepts: List[Concept] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        d = super().dict()
        # Convert concepts and relationships
        if self.concepts:
            d["concepts"] = [c.dict() for c in self.concepts]
        if self.relationships:
            d["relationships"] = [r.dict() for r in self.relationships]
        return d

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

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        d = super().dict()
        if self.timestamp:
            d["timestamp"] = self.timestamp.isoformat()
        return d

class DialogueContext(BaseModel):
    """Context for a dialogue."""
    messages: List[DialogueMessage] = []
    participants: List[str] = []
    metadata: Dict[str, Any] = {}

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        d = super().dict()
        if self.messages:
            d["messages"] = [m.dict() for m in self.messages]
        return d

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

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        d = super().dict()
        if self.domain_context:
            d["domain_context"] = self.domain_context.dict()
        if self.created_at:
            d["created_at"] = self.created_at.isoformat()
        if self.last_updated:
            d["last_updated"] = self.last_updated.isoformat()
        return d

class MemoryQuery(BaseModel):
    """Query for searching memories."""
    content: Optional[str] = None
    type: Optional[MemoryType] = None
    time_range: Optional[tuple[datetime, datetime]] = None
    filter: Dict[str, Any] = {}
    limit: int = 10

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        d = super().dict()
        if self.type:
            d["type"] = str(self.type)
        if self.time_range:
            d["time_range"] = [t.isoformat() if t else None for t in self.time_range]
        return d

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

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        d = super().dict()
        if self.domain_context:
            d["domain_context"] = self.domain_context.dict()
        return d

class MemoryBatch(BaseModel):
    """Batch of memories for processing."""
    memories: List[Memory]
    metadata: Dict[str, Any] = {}
    batch_id: Optional[str] = None

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        d = super().dict()
        if self.memories:
            d["memories"] = [m.dict() for m in self.memories]
        return d
