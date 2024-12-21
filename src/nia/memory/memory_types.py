"""Memory system types."""

from typing import Dict, List, Any, Optional, Protocol, runtime_checkable
from datetime import datetime
from dataclasses import dataclass, field

@runtime_checkable
class JSONSerializable(Protocol):
    """Protocol for JSON serializable objects."""
    def dict(self) -> Dict[str, Any]:
        """Convert object to dictionary."""
        ...

@dataclass
class AISystem(JSONSerializable):
    """AI system configuration."""
    name: str
    version: str
    capabilities: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities,
            "metadata": self.metadata
        }

@dataclass
class Memory(JSONSerializable):
    """Memory object."""
    content: str
    timestamp: datetime
    memory_type: str
    metadata: Optional[Dict] = None
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "memory_type": self.memory_type,
            "metadata": self.metadata
        }

@dataclass
class Concept(JSONSerializable):
    """Concept object."""
    name: str
    type: str
    description: str
    related: List[str] = field(default_factory=list)
    validation: Dict[str, Any] = field(default_factory=lambda: {
        "confidence": 0.5,
        "supported_by": [],
        "contradicted_by": [],
        "needs_verification": []
    })
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "related": self.related,
            "validation": self.validation
        }

@dataclass
class DialogueMessage(JSONSerializable):
    """Dialogue message."""
    content: str
    agent_type: str
    message_type: str
    references: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "agent_type": self.agent_type,
            "message_type": self.message_type,
            "references": self.references,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class DialogueContext(JSONSerializable):
    """Dialogue context."""
    topic: str
    status: str = "active"
    messages: List[DialogueMessage] = field(default_factory=list)
    metadata: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.now)
    participants: List[str] = field(default_factory=list)  # Changed from set to list
    
    def add_message(self, message: DialogueMessage) -> None:
        """Add message to dialogue."""
        self.messages.append(message)
        if message.agent_type not in self.participants:
            self.participants.append(message.agent_type)
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "topic": self.topic,
            "status": self.status,
            "messages": [m.dict() for m in self.messages],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "participants": self.participants
        }

@dataclass
class AgentResponse(JSONSerializable):
    """Agent response."""
    response: str
    concepts: List[Dict[str, Any]] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    implications: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    reasoning: List[str] = field(default_factory=list)
    dialogue_context: Optional[DialogueContext] = None
    referenced_messages: List[DialogueMessage] = field(default_factory=list)
    perspective: str = "raw"
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evolution: Optional[Dict[str, Any]] = None
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "response": self.response,
            "concepts": self.concepts,
            "key_points": self.key_points,
            "implications": self.implications,
            "uncertainties": self.uncertainties,
            "reasoning": self.reasoning,
            "dialogue_context": self.dialogue_context.dict() if self.dialogue_context else None,
            "referenced_messages": [m.dict() for m in self.referenced_messages],
            "perspective": self.perspective,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "evolution": self.evolution,
            "relationships": self.relationships
        }
    
    def add_concept(
        self,
        name: str,
        type: str,
        description: str,
        related: Optional[List[str]] = None
    ) -> None:
        """Add concept to response."""
        self.concepts.append({
            "name": name,
            "type": type,
            "description": description,
            "related": related or [],
            "validation": {
                "confidence": 0.5,
                "supported_by": [],
                "contradicted_by": [],
                "needs_verification": []
            }
        })
    
    def add_key_point(self, point: str) -> None:
        """Add key point to response."""
        self.key_points.append(point)
    
    def add_implication(self, implication: str) -> None:
        """Add implication to response."""
        self.implications.append(implication)
    
    def add_uncertainty(self, uncertainty: str) -> None:
        """Add uncertainty to response."""
        self.uncertainties.append(uncertainty)
    
    def add_reasoning(self, reasoning: str) -> None:
        """Add reasoning step to response."""
        self.reasoning.append(reasoning)
    
    def add_relationship(self, type: str, target: str) -> None:
        """Add relationship to response."""
        if type not in self.relationships:
            self.relationships[type] = []
        self.relationships[type].append(target)
    
    def merge(self, other: 'AgentResponse') -> None:
        """Merge another response into this one."""
        self.concepts.extend(other.concepts)
        self.key_points.extend(other.key_points)
        self.implications.extend(other.implications)
        self.uncertainties.extend(other.uncertainties)
        self.reasoning.extend(other.reasoning)
        
        # Merge relationships
        for type, targets in other.relationships.items():
            if type not in self.relationships:
                self.relationships[type] = []
            self.relationships[type].extend(targets)
        
        # Update confidence
        self.confidence = (self.confidence + other.confidence) / 2
        
        # Update metadata
        self.metadata.update(other.metadata)
        
        # Update evolution if present
        if other.evolution:
            if not self.evolution:
                self.evolution = {}
            self.evolution.update(other.evolution)
