"""Memory system type definitions."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class AgentResponse:
    """Response from an agent's processing."""
    content: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)
    related: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class DialogueContext:
    """Context for a dialogue interaction."""
    conversation_id: str
    turn_number: int
    speaker: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class MemoryEntry:
    """Base class for memory entries."""
    id: str
    content: str
    type: str
    domain: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class EpisodicMemory(MemoryEntry):
    """Episodic memory entry."""
    vector: Optional[List[float]] = None
    context: Optional[DialogueContext] = None

@dataclass
class SemanticMemory(MemoryEntry):
    """Semantic memory entry."""
    confidence: float = 0.0
    source: Optional[str] = None
    validation: Dict[str, Any] = field(default_factory=dict)
    related: List[str] = field(default_factory=list)

@dataclass
class ConsolidationPattern:
    """Pattern for memory consolidation."""
    type: str
    pattern: str
    confidence_threshold: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationResult:
    """Result of memory validation."""
    is_valid: bool
    confidence: float
    issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MemoryQueryResult:
    """Result of a memory query."""
    entries: List[MemoryEntry]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
