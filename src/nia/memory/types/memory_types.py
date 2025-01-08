"""Memory system type definitions."""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel

class MemoryType(str, Enum):
    """Types of memory entries."""
    EPHEMERAL = "ephemeral"  # Short-term, chunk-based storage
    SEMANTIC = "semantic"    # Long-term, graph-based storage
    EPISODIC = "episodic"   # Experience-based storage

class OutputType(str, Enum):
    """Types of task outputs."""
    CODE = "code"
    MEDIA = "media"
    NEW_SKILL = "new_skill"
    DOCUMENT = "document"
    API_CALL = "api_call"

class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Domain(str, Enum):
    """Domain labels for data."""
    PROFESSIONAL = "professional"
    PERSONAL = "personal"

class MemoryEntry(BaseModel):
    """Base memory entry model."""
    id: str
    content: str
    created_at: datetime
    updated_at: datetime
    memory_type: MemoryType
    domain: Domain
    metadata: Dict[str, Any] = {}

class TaskOutput(BaseModel):
    """Task output model."""
    task_id: str
    output_type: OutputType
    content: Any
    status: TaskStatus
    domain: Domain
    created_at: datetime
    updated_at: datetime
    references: Dict[str, str] = {}  # Store references to Neo4j, Qdrant, or external
    metadata: Dict[str, Any] = {}

class GraphNode(BaseModel):
    """Graph node model."""
    id: str
    label: str
    properties: Dict[str, Any]
    domain: Domain
    created_at: datetime
    updated_at: datetime

class GraphRelationship(BaseModel):
    """Graph relationship model."""
    from_id: str
    to_id: str
    type: str
    properties: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

class MemoryQuery(BaseModel):
    """Memory query model."""
    query: str
    memory_type: Optional[MemoryType] = None
    domain: Optional[Domain] = None
    limit: int = 10
    metadata_filters: Dict[str, Any] = {}

class MemoryResult(BaseModel):
    """Memory query result model."""
    entries: List[Union[MemoryEntry, GraphNode]]
    total_count: int
    query_time: float
    metadata: Dict[str, Any] = {}

class Concept(BaseModel):
    """Concept model."""
    name: str
    type: str
    category: str
    description: str
    attributes: Dict[str, Any] = {}
    confidence: float = 0.0

class Relationship(BaseModel):
    """Relationship between concepts."""
    from_concept: str
    to_concept: str
    type: str
    properties: Dict[str, Any] = {}

class EpisodicMemory(BaseModel):
    """Episodic memory model."""
    content: Any
    type: MemoryType = MemoryType.EPHEMERAL
    timestamp: str
    concepts: List[Concept] = []
    relationships: List[Relationship] = []
    context: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    importance: float = 0.0
    participants: List[str] = []

    def get(self, key: str, default: Any = None) -> Any:
        """Get attribute value by key."""
        return getattr(self, key, default)
