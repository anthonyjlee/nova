"""Memory type definitions for NIA."""

from enum import Enum
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, ConfigDict

from .json_utils import validate_json_structure

class JSONSerializable(BaseModel):
    """Base class for JSON serializable objects."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

class MemoryType(str, Enum):
    """Types of memories in the system."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

class Concept(JSONSerializable):
    """Representation of a concept in memory."""
    name: str
    type: str = "Concept"
    category: Optional[str] = None
    description: str
    attributes: Dict = Field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('attributes')
    def validate_attributes(cls, v):
        """Validate concept attributes."""
        # Only validate JSON serialization
        validate_json_structure(v)
        return v

    def dict(self, *args, **kwargs):
        """Convert to dictionary with proper structure."""
        d = super().dict(*args, **kwargs)
        # Ensure description is in both places for backward compatibility
        if 'description' in d:
            if 'attributes' not in d:
                d['attributes'] = {}
            d['attributes']['description'] = d['description']
        return d

class Relationship(JSONSerializable):
    """Representation of a relationship between concepts."""
    from_concept: str
    to_concept: str
    type: str = "RELATED_TO"
    properties: Dict = Field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Belief(JSONSerializable):
    """Representation of a belief about concepts."""
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    evidence: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Memory(JSONSerializable):
    """Base memory representation."""
    id: Optional[str] = None
    type: MemoryType
    content: Union[str, Dict]
    source: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    importance: float = 0.5
    concepts: List[Concept] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    beliefs: List[Belief] = Field(default_factory=list)
    metadata: Dict = Field(default_factory=dict)
    consolidated: bool = False

    @validator('content')
    def validate_content(cls, v):
        """Validate memory content."""
        if isinstance(v, dict):
            validate_json_structure(v)
        return v

    @validator('metadata')
    def validate_metadata(cls, v):
        """Validate memory metadata."""
        validate_json_structure(v)
        return v

class EpisodicMemory(Memory):
    """Episodic memory specific fields."""
    type: MemoryType = MemoryType.EPISODIC
    context: Dict = Field(default_factory=dict)
    emotions: Dict = Field(default_factory=dict)
    participants: List[str] = Field(default_factory=list)

    @validator('context', 'emotions')
    def validate_dicts(cls, v):
        """Validate dictionary fields."""
        validate_json_structure(v)
        return v

    def dict(self, *args, **kwargs):
        """Convert to dictionary with proper structure."""
        d = super().dict(*args, **kwargs)
        # Include context in metadata for querying
        if 'metadata' not in d:
            d['metadata'] = {}
        d['metadata']['context'] = self.context
        return d

class SemanticMemory(Memory):
    """Semantic memory specific fields."""
    type: MemoryType = MemoryType.SEMANTIC
    category: Optional[str] = None
    confidence: float = 1.0
    sources: List[str] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)

class ProceduralMemory(Memory):
    """Procedural memory for storing action sequences."""
    type: MemoryType = MemoryType.PROCEDURAL
    steps: List[Dict] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    success_rate: float = 1.0
    last_executed: Optional[datetime] = None

class MemoryQuery(JSONSerializable):
    """Query structure for memory retrieval."""
    content: Optional[str] = None
    type: Optional[MemoryType] = None
    time_range: Optional[Dict] = None
    filter: Dict = Field(default_factory=dict)
    limit: int = 10
    include_consolidated: bool = False

class ConsolidationRule(JSONSerializable):
    """Rule for memory consolidation."""
    enabled: bool = True
    threshold: float = 0.7
    interval: Optional[int] = None  # in seconds
    conditions: Dict = Field(default_factory=dict)

class MemoryBatch(JSONSerializable):
    """Batch of memories for processing."""
    memories: List[Memory]
    batch_type: str = "consolidation"
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict = Field(default_factory=dict)

class DialogueMessage(JSONSerializable):
    """Message in a dialogue context."""
    content: str
    agent_type: str
    message_type: str = "message"
    references: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict = Field(default_factory=dict)

class DialogueContext(JSONSerializable):
    """Context for a dialogue interaction."""
    topic: str
    status: str = "active"
    messages: List[DialogueMessage] = Field(default_factory=list)
    participants: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict = Field(default_factory=dict)

    def add_message(self, message: DialogueMessage) -> None:
        """Add a message to the dialogue context."""
        self.messages.append(message)
        if message.agent_type not in self.participants:
            self.participants.append(message.agent_type)
        self.updated_at = datetime.now()

class AgentResponse(JSONSerializable):
    """Response from an agent."""
    response: str
    dialogue: Optional[str] = None
    concepts: List[Dict] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)
    implications: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    reasoning: List[str] = Field(default_factory=list)
    whispers: List[str] = Field(default_factory=list)
    perspective: str = "default"
    confidence: float = 1.0
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict = Field(default_factory=dict)
    dialogue_context: Optional[DialogueContext] = None
    orchestration: Optional[Dict] = Field(default_factory=dict)

    def dict(self) -> Dict:
        """Convert to dictionary."""
        d = super().dict()
        if self.dialogue_context:
            d['dialogue_context'] = self.dialogue_context.dict()
        return d
