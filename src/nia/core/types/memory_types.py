"""Memory type definitions for NIA."""

from enum import Enum
from typing import Dict, Optional, Any, List, Union, TypeVar, Protocol
from pydantic import BaseModel, Field, validator
from datetime import datetime, timezone

from typing import runtime_checkable

@runtime_checkable
class JSONSerializable(Protocol):
    """Protocol for JSON-serializable objects."""
    def dict(self, minimal: bool = False) -> Dict[str, Any]: ...

class OutputType(str, Enum):
    """Types of outputs in the system."""
    TEXT = "text"
    JSON = "json"
    BINARY = "binary"
    ERROR = "error"

class Domain(str, Enum):
    """Domain types in the system."""
    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"
    TASK = "task"

class TaskStatus(str, Enum):
    """Task status types."""
    SUCCESS = "success"
    FAILURE = "failure"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"

class GraphNode(BaseModel):
    """A node in the knowledge graph."""
    id: Optional[str] = None
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "id": self.id,
                "label": self.label
            }
        return super().dict()

class GraphEdge(BaseModel):
    """An edge in the knowledge graph."""
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "source": self.source,
                "target": self.target,
                "type": self.type
            }
        return super().dict()

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

class CrossDomainSchema(BaseModel):
    """Schema for cross-domain validation."""
    approved: bool = Field(default=False)
    requested: bool = Field(default=False)
    source_domain: Optional[str] = Field(default="general")
    target_domain: Optional[str] = Field(default="general")
    justification: Optional[str] = Field(default="")
    approval_timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    approval_source: Optional[str] = Field(default="system")

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "approved": self.approved,
                "source_domain": str(self.source_domain) if self.source_domain else "general",
                "target_domain": str(self.target_domain) if self.target_domain else "general"
            }
        d = super().dict()
        if self.source_domain:
            d["source_domain"] = str(self.source_domain)
        if self.target_domain:
            d["target_domain"] = str(self.target_domain)
        if self.approval_timestamp:
            d["approval_timestamp"] = self.approval_timestamp.isoformat()
        return d

    @validator("source_domain", "target_domain", pre=True)
    def validate_domain(cls, v):
        """Validate domain values."""
        if v is None:
            return "general"
        try:
            return str(BaseDomain(str(v).lower()))
        except ValueError:
            return str(v)

class ValidationSchema(BaseModel):
    """Schema for validation data."""
    cross_domain: CrossDomainSchema = Field(default_factory=CrossDomainSchema)
    domain: str = Field(default="professional")
    access_domain: str = Field(default="professional")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    source: str = Field(default="system")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    supported_by: List[str] = Field(default_factory=list)
    contradicted_by: List[str] = Field(default_factory=list)
    needs_verification: List[str] = Field(default_factory=list)

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "domain": str(self.domain),
                "access_domain": str(self.access_domain),
                "confidence": self.confidence
            }
        d = super().dict()
        if self.cross_domain:
            d["cross_domain"] = self.cross_domain.dict(minimal=minimal)
        return d

    @validator("domain", "access_domain", pre=True)
    def validate_domain_fields(cls, v):
        """Validate domain and access_domain values."""
        if v is None:
            return "professional"
        try:
            return str(BaseDomain(str(v).lower()))
        except ValueError:
            return str(v)

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

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "approved": self.approved,
                "source_domain": str(self.source_domain) if self.source_domain else None,
                "target_domain": str(self.target_domain) if self.target_domain else None
            }
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

class TaskState(str, Enum):
    """Task states in the system."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"

class MemoryType(str, Enum):
    """Types of memories in the system."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EMOTIONAL = "emotional"
    TASK_UPDATE = "task_update"  # For task state changes and updates

class TaskValidation(BaseModel):
    """Validation schema for task-related data."""
    state: TaskState
    domain: str
    team_id: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    blocked_by: List[str] = Field(default_factory=list)
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    last_transition: Optional[datetime] = None
    transition_history: List[Dict[str, Any]] = Field(default_factory=list)

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "state": str(self.state),
                "domain": str(self.domain),
                "team_id": self.team_id
            }
        d = super().dict()
        d["state"] = str(self.state)
        if self.last_transition:
            d["last_transition"] = self.last_transition.isoformat()
        return d

    @validator("state", pre=True)
    def validate_state(cls, v):
        """Validate task state."""
        if isinstance(v, str):
            return TaskState(v)
        return v

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
    validation: ValidationSchema = Field(default_factory=ValidationSchema)
    access_control: Dict[str, Any] = Field(
        default_factory=lambda: {
            "read": ["system"],
            "write": ["system"],
            "execute": ["system"]
        }
    )

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "primary_domain": str(self.primary_domain),
                "knowledge_vertical": str(self.knowledge_vertical) if self.knowledge_vertical else None,
                "confidence": self.confidence
            }
        d = super().dict()
        d["primary_domain"] = str(self.primary_domain)
        if self.knowledge_vertical:
            d["knowledge_vertical"] = str(self.knowledge_vertical)
        if self.cross_domain:
            d["cross_domain"] = self.cross_domain.dict(minimal=minimal)
        if self.validation:
            d["validation"] = self.validation.dict(minimal=minimal)
        return d

    @validator("validation", pre=True)
    def validate_validation_data(cls, v):
        """Ensure validation data is properly structured."""
        if isinstance(v, dict):
            return ValidationSchema(**v)
        elif isinstance(v, ValidationSchema):
            return v
        else:
            return ValidationSchema()

    def validate_transfer(
        self,
        target_domain: Optional[str] = None,
        target_vertical: Optional[str] = None
    ) -> bool:
        """Validate if transfer to target domain/vertical is allowed."""
        if target_domain == self.primary_domain:
            return True
        if self.cross_domain and self.cross_domain.approved:
            if target_domain and self.cross_domain.target_domain == target_domain:
                return True
            if target_vertical and self.cross_domain.target_vertical == target_vertical:
                return True
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
    validation: ValidationSchema = Field(default_factory=ValidationSchema)

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "name": self.name,
                "type": self.type,
                "domain_context": self.domain_context.dict(minimal=True)
            }
        d = super().dict()
        if self.domain_context:
            d["domain_context"] = self.domain_context.dict(minimal=minimal)
        if self.validation:
            d["validation"] = self.validation.dict(minimal=minimal)
        return d

    @validator("validation", pre=True)
    def validate_validation_data(cls, v):
        """Ensure validation data is properly structured."""
        if isinstance(v, dict):
            return ValidationSchema(**v)
        elif isinstance(v, ValidationSchema):
            return v
        else:
            return ValidationSchema()

class Relationship(BaseModel):
    """A relationship between concepts."""
    source: str
    target: str
    type: str
    attributes: Dict[str, Any] = {}
    domain_context: DomainContext
    confidence: float = 1.0
    bidirectional: bool = False
    validation: ValidationSchema = Field(default_factory=ValidationSchema)

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "source": self.source,
                "target": self.target,
                "type": self.type,
                "bidirectional": self.bidirectional
            }
        d = super().dict()
        if self.domain_context:
            d["domain_context"] = self.domain_context.dict(minimal=minimal)
        if self.validation:
            d["validation"] = self.validation.dict(minimal=minimal)
        return d

    @validator("validation", pre=True)
    def validate_validation_data(cls, v):
        """Ensure validation data is properly structured."""
        if isinstance(v, dict):
            return ValidationSchema(**v)
        elif isinstance(v, ValidationSchema):
            return v
        else:
            return ValidationSchema()

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

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "id": self.id,
                "type": self.type.value if isinstance(self.type, MemoryType) else str(self.type),
                "timestamp": self.timestamp.isoformat() if self.timestamp else None,
                "content": self.content if isinstance(self.content, str) else {
                    k: v for k, v in self.content.items()
                    if k in ["thread_id", "task_id", "message_id", "status"]
                }
            }
        d = super().dict()
        if self.timestamp:
            d["timestamp"] = self.timestamp.isoformat()
        d["type"] = self.type.value if isinstance(self.type, MemoryType) else str(self.type)
        if self.domain_context:
            d["domain_context"] = self.domain_context.dict(minimal=minimal)
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

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            base = super().dict(minimal=True)
            return {
                **base,
                "location": self.location,
                "participants": self.participants[:5] if self.participants else [],  # Limit participants
                "related_memories": self.related_memories[:5] if self.related_memories else []  # Limit related
            }
        d = super().dict()
        if self.concepts:
            d["concepts"] = [c.dict(minimal=minimal) for c in self.concepts]
        if self.relationships:
            d["relationships"] = [r.dict(minimal=minimal) for r in self.relationships]
        return d

class SemanticMemory(Memory):
    """Semantic memory model."""
    type: MemoryType = MemoryType.SEMANTIC
    concepts: List[Concept] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    confidence: float = 1.0
    validation: ValidationSchema = Field(default_factory=ValidationSchema)

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            base = super().dict(minimal=True)
            return {
                **base,
                "confidence": self.confidence
            }
        d = super().dict()
        if self.concepts:
            d["concepts"] = [c.dict(minimal=minimal) for c in self.concepts]
        if self.relationships:
            d["relationships"] = [r.dict(minimal=minimal) for r in self.relationships]
        if self.validation:
            d["validation"] = self.validation.dict(minimal=minimal)
        return d

    @validator("validation", pre=True)
    def validate_validation_data(cls, v):
        """Ensure validation data is properly structured."""
        if isinstance(v, dict):
            return ValidationSchema(**v)
        elif isinstance(v, ValidationSchema):
            return v
        else:
            return ValidationSchema()

class ProceduralMemory(Memory):
    """Procedural memory model."""
    type: MemoryType = MemoryType.PROCEDURAL
    steps: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    validation: ValidationSchema = Field(default_factory=ValidationSchema)

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            base = super().dict(minimal=True)
            return {
                **base,
                "steps": self.steps[:3] if self.steps else []  # Limit steps
            }
        d = super().dict()
        if self.validation:
            d["validation"] = self.validation.dict(minimal=minimal)
        return d

    @validator("validation", pre=True)
    def validate_validation_data(cls, v):
        """Ensure validation data is properly structured."""
        if isinstance(v, dict):
            return ValidationSchema(**v)
        elif isinstance(v, ValidationSchema):
            return v
        else:
            return ValidationSchema()

class TaskOutput(BaseModel):
    """Output from a task execution."""
    task_id: str
    status: TaskState
    content: Union[str, Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "task_id": self.task_id,
                "status": str(self.status),
                "timestamp": self.timestamp.isoformat() if self.timestamp else None
            }
        d = super().dict()
        d["status"] = str(self.status)
        if self.timestamp:
            d["timestamp"] = self.timestamp.isoformat()
        return d

    @validator("status", pre=True)
    def validate_status(cls, v):
        """Validate task status."""
        if isinstance(v, str):
            return TaskState(v)
        return v

class TaskMemory(Memory):
    """Task-specific memory model."""
    type: MemoryType = MemoryType.TASK_UPDATE
    task_id: str
    previous_state: Optional[TaskState] = None
    new_state: TaskState
    validation: TaskValidation
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            base = super().dict(minimal=True)
            return {
                **base,
                "task_id": self.task_id,
                "new_state": str(self.new_state)
            }
        d = super().dict()
        if self.previous_state:
            d["previous_state"] = str(self.previous_state)
        d["new_state"] = str(self.new_state)
        if self.validation:
            d["validation"] = self.validation.dict(minimal=minimal)
        return d

    @validator("previous_state", "new_state", pre=True)
    def validate_states(cls, v):
        """Validate task states."""
        if isinstance(v, str):
            return TaskState(v)
        return v

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

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "content": self.content,
                "sender": self.sender,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None
            }
        d = super().dict()
        if self.timestamp:
            d["timestamp"] = self.timestamp.isoformat()
        return d

class DialogueContext(BaseModel):
    """Context for a dialogue."""
    messages: List[DialogueMessage] = []
    participants: List[str] = []
    metadata: Dict[str, Any] = {}

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "participants": self.participants[:5] if self.participants else [],  # Limit participants
                "messages": [m.dict(minimal=True) for m in self.messages[-5:]] if self.messages else []  # Last 5 messages
            }
        d = super().dict()
        if self.messages:
            d["messages"] = [m.dict(minimal=minimal) for m in self.messages]
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

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "subject": self.subject,
                "predicate": self.predicate,
                "object": self.object,
                "confidence": self.confidence
            }
        d = super().dict()
        if self.domain_context:
            d["domain_context"] = self.domain_context.dict(minimal=minimal)
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

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "type": str(self.type) if self.type else None,
                "limit": self.limit
            }
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
    cross_domain_rules: ValidationSchema = Field(default_factory=ValidationSchema)

    @validator("cross_domain_rules", pre=True)
    def validate_cross_domain_rules(cls, v):
        """Ensure cross domain rules are properly structured."""
        if isinstance(v, dict):
            return ValidationSchema(**v)
        elif isinstance(v, ValidationSchema):
            return v
        else:
            return ValidationSchema()

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "pattern": self.pattern,
                "priority": self.priority
            }
        d = super().dict()
        if self.domain_context:
            d["domain_context"] = self.domain_context.dict(minimal=minimal)
        return d

class MemoryBatch(BaseModel):
    """Batch of memories for processing."""
    memories: List[Memory]
    metadata: Dict[str, Any] = {}
    batch_id: Optional[str] = None

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            return {
                "batch_id": self.batch_id,
                "memories": [m.dict(minimal=True) for m in self.memories] if self.memories else []
            }
        d = super().dict()
        if self.memories:
            d["memories"] = [m.dict(minimal=minimal) for m in self.memories]
        return d

class MockMemory(EpisodicMemory):
    """Mock memory for testing."""
    content: str
    importance: float = 0.8
    knowledge: Dict[str, Any] = Field(default_factory=dict)
    type: MemoryType = MemoryType.EPISODIC
    context: Dict[str, Any] = Field(default_factory=lambda: {
        "domain": "professional",
        "source": "professional",
        "access_domain": "professional",
        "cross_domain": {
            "approved": True,
            "requested": True,
            "source_domain": "professional",
            "target_domain": "general",
            "justification": "Test justification"
        }
    })
    validation: ValidationSchema = Field(default_factory=ValidationSchema)
    validation_data: Dict[str, Any] = Field(default_factory=lambda: {
        "domain": "professional",
        "access_domain": "professional",
        "confidence": 0.9,
        "source": "professional",
        "supported_by": [],
        "contradicted_by": [],
        "needs_verification": [],
        "cross_domain": {
            "approved": True,
            "requested": True,
            "source_domain": "professional",
            "target_domain": "general",
            "justification": "Test justification"
        }
    })

    def dict(self, minimal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        if minimal:
            base = super().dict(minimal=True)
            return {
                **base,
                "content": self.content,
                "importance": self.importance
            }
        d = super().dict()
        if self.validation:
            d["validation"] = self.validation.dict(minimal=minimal)
        return d

    @validator("validation", pre=True)
    def validate_validation_data(cls, v):
        """Ensure validation data is properly structured."""
        if isinstance(v, dict):
            return ValidationSchema(**v)
        elif isinstance(v, ValidationSchema):
            return v
        else:
            return ValidationSchema()

    @validator("knowledge")
    def validate_knowledge(cls, v, values):
        """Validate knowledge field and map to concepts/relationships."""
        from nia.core.types.concept_utils.validation import validate_concept_structure
        
        if not isinstance(v, dict):
            raise ValueError("Knowledge must be a dictionary")
            
        # Handle concepts
        if "concepts" in v:
            if not isinstance(v["concepts"], list):
                raise ValueError("Concepts must be a list")
                
            validated_concepts = []
            for concept in v["concepts"]:
                try:
                    # Create domain context from validation data
                    domain_context = DomainContext(
                        primary_domain=concept.get("validation", {}).get("domain", "professional"),
                        knowledge_vertical=concept.get("validation", {}).get("knowledge_vertical", "general"),
                        validation=ValidationSchema(**concept.get("validation", {}))
                    )
                    
                    # Validate concept structure
                    validated_concept = validate_concept_structure(concept)
                    validated_concept["domain_context"] = domain_context.dict(minimal=True)
                    validated_concepts.append(validated_concept)
                except ValueError as e:
                    raise ValueError(str(e))
                    
            v["concepts"] = validated_concepts
            values["concepts"] = [Concept(**c) for c in validated_concepts]
            
        # Handle relationships
        if "relationships" in v:
            if not isinstance(v["relationships"], list):
                raise ValueError("Relationships must be a list")
                
            validated_relationships = []
            for rel in v["relationships"]:
                if not isinstance(rel, dict):
                    raise ValueError("Each relationship must be a dictionary")
                    
                # Create domain context from validation data
                domain_context = DomainContext(
                    primary_domain=rel.get("validation", {}).get("domain", "professional"),
                    knowledge_vertical=rel.get("validation", {}).get("knowledge_vertical", "general"),
                    validation=ValidationSchema(**rel.get("validation", {}))
                )
                
                # Add domain context to relationship
                rel["domain_context"] = domain_context.dict(minimal=True)
                validated_relationships.append(rel)
                
            v["relationships"] = validated_relationships
            values["relationships"] = [Relationship(**r) for r in validated_relationships]
            
        return v
