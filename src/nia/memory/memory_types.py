"""
Memory system types and schemas.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

@dataclass
class Analysis:
    """Analysis of content."""
    key_points: List[str]
    confidence: float
    state_update: str

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key_points": self.key_points,
            "confidence": self.confidence,
            "state_update": self.state_update
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Analysis':
        """Create from dictionary."""
        return cls(
            key_points=data.get("key_points", []),
            confidence=float(data.get("confidence", 0.0)),
            state_update=str(data.get("state_update", ""))
        )

@dataclass
class AgentResponse:
    """Response from an agent."""
    response: str
    analysis: Analysis

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "response": self.response,
            "analysis": self.analysis.dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentResponse':
        """Create from dictionary."""
        return cls(
            response=str(data.get("response", "")),
            analysis=Analysis.from_dict(data.get("analysis", {}))
        )

@dataclass
class Memory:
    """Memory node."""
    id: str
    type: str
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "content": json.dumps(self.content, default=str),
            "metadata": json.dumps(self.metadata or {}, default=str),
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """Create from dictionary."""
        return cls(
            id=str(data.get("id", "")),
            type=str(data.get("type", "")),
            content=json.loads(data.get("content", "{}")),
            metadata=json.loads(data.get("metadata", "{}")),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        )

@dataclass
class Capability:
    """System capability."""
    id: str
    type: str
    description: str
    confidence: float = 1.0

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "confidence": self.confidence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Capability':
        """Create from dictionary."""
        return cls(
            id=str(data.get("id", "")),
            type=str(data.get("type", "")),
            description=str(data.get("description", "")),
            confidence=float(data.get("confidence", 1.0))
        )

@dataclass
class AISystem:
    """AI system node."""
    id: str
    name: str
    type: str
    capabilities: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "capabilities": self.capabilities,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AISystem':
        """Create from dictionary."""
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            type=str(data.get("type", "")),
            capabilities=list(data.get("capabilities", [])),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        )

@dataclass
class Evolution:
    """System evolution node."""
    id: str
    from_system: str
    to_system: str
    changes: List[str]
    created_at: datetime = field(default_factory=datetime.now)

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "from_system": self.from_system,
            "to_system": self.to_system,
            "changes": self.changes,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Evolution':
        """Create from dictionary."""
        return cls(
            id=str(data.get("id", "")),
            from_system=str(data.get("from_system", "")),
            to_system=str(data.get("to_system", "")),
            changes=list(data.get("changes", [])),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        )

class RelationshipTypes:
    """Neo4j relationship types."""
    CREATED_BY = "CREATED_BY"
    SIMILAR_TO = "SIMILAR_TO"
    HAS_CAPABILITY = "HAS_CAPABILITY"
    PREDECESSOR_OF = "PREDECESSOR_OF"
    EVOLVED_TO = "EVOLVED_TO"
    RELATED_TO = "RELATED_TO"
    HAS_CONCEPT = "HAS_CONCEPT"

# Default capabilities
DEFAULT_CAPABILITIES = [
    Capability(
        id="function_calls",
        type="system",
        description="Function call capabilities"
    ),
    Capability(
        id="image_generation",
        type="generation",
        description="Image generation capabilities"
    ),
    Capability(
        id="audio_generation",
        type="generation",
        description="Audio generation capabilities"
    ),
    Capability(
        id="webcam_access",
        type="hardware",
        description="Webcam access capabilities"
    ),
    Capability(
        id="computer_vision",
        type="vision",
        description="Computer vision capabilities"
    )
]

# Default systems
NOVA = AISystem(
    id="nova",
    name="Nova",
    type="current",
    created_at=datetime.now()
)

NIA = AISystem(
    id="nia",
    name="Nia",
    type="predecessor",
    capabilities=[c.id for c in DEFAULT_CAPABILITIES],
    created_at=datetime.now()
)

ECHO = AISystem(
    id="echo",
    name="Echo",
    type="initial",
    created_at=datetime.now()
)

# Neo4j schema
Neo4jSchema = Dict[str, Dict[str, str]]
Neo4jQuery = Dict[str, Any]
Neo4jQuerySet = Dict[str, Neo4jQuery]

DEFAULT_SCHEMA: Neo4jSchema = {
    "Memory": {
        "id": "string",
        "type": "string",
        "content": "string",
        "metadata": "string",
        "created_at": "datetime"
    },
    "Capability": {
        "id": "string",
        "type": "string",
        "description": "string",
        "confidence": "float"
    },
    "AISystem": {
        "id": "string",
        "name": "string",
        "type": "string",
        "capabilities": "list",
        "created_at": "datetime"
    },
    "Evolution": {
        "id": "string",
        "from_system": "string",
        "to_system": "string",
        "changes": "list",
        "created_at": "datetime"
    }
}
