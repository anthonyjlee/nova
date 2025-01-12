"""Memory system type definitions."""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class CrossDomainSchema(BaseModel):
    """Cross-domain validation schema."""
    approved: bool = False
    requested: bool = False
    source_domain: Optional[str] = None
    target_domain: Optional[str] = None
    approval_date: Optional[str] = None
    approval_source: Optional[str] = None

class ValidationSchema(BaseModel):
    """Validation schema for concepts and relationships."""
    domain: str
    confidence: float
    source: str
    timestamp: str
    cross_domain: Optional[CrossDomainSchema] = None

class MemoryType(str, Enum):
    """Type of memory."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

class OutputType(str, Enum):
    """Type of task output."""
    CODE = "code"
    DOCUMENT = "document"
    MEDIA = "media"
    API = "api"

class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Domain(str, Enum):
    """Domain of knowledge/expertise."""
    GENERAL = "general"
    RETAIL = "retail"
    ECOMMERCE = "ecommerce"
    PHILOSOPHY = "philosophy"
    PSYCHOLOGY = "psychology"
    BUSINESS = "business"
    SCIENCE = "science"
    TECHNOLOGY = "technology"
    ARTS = "arts"
    EDUCATION = "education"

class Concept(BaseModel):
    """Semantic concept representation."""
    name: str
    type: str
    category: Optional[str] = None
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None

class Relationship(BaseModel):
    """Relationship between concepts."""
    from_: str
    to: str
    type: str
    attributes: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None

class Memory(BaseModel):
    """Base memory representation."""
    id: Optional[str] = None
    content: str
    type: MemoryType
    timestamp: str
    context: Optional[Dict[str, Any]] = None
    concepts: Optional[List[Concept]] = None
    relationships: Optional[List[Relationship]] = None
    participants: Optional[List[str]] = None
    importance: Optional[float] = 0.0
    metadata: Optional[Dict[str, Any]] = None

class EpisodicMemory(Memory):
    """Episodic memory representation."""
    consolidated: Optional[bool] = False

class TaskOutput(BaseModel):
    """Task output representation."""
    task_id: str
    type: OutputType
    content: str
    metadata: Optional[Dict[str, Any]] = None
