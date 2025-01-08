"""Memory system type definitions."""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

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
    """Domain of knowledge."""
    GENERAL = "general"
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATABASE = "database"
    TESTING = "testing"
    DEPLOYMENT = "deployment"

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
