"""Memory system type definitions."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Protocol, Union, Literal, runtime_checkable
from datetime import datetime
from enum import Enum, auto
import json

@runtime_checkable
class JSONSerializable(Protocol):
    """Protocol for JSON serializable objects."""
    def to_json(self) -> str:
        """Convert object to JSON string."""
        ...
    
    @classmethod
    def from_json(cls, json_str: str) -> 'JSONSerializable':
        """Create object from JSON string."""
        ...

class RelationshipTypes(Enum):
    """Types of relationships between concepts."""
    IS_A = auto()
    HAS_A = auto()
    PART_OF = auto()
    RELATED_TO = auto()
    DEPENDS_ON = auto()
    CAUSES = auto()
    INFLUENCES = auto()
    CONTRADICTS = auto()
    SUPPORTS = auto()
    PRECEDES = auto()
    FOLLOWS = auto()
    SIMILAR_TO = auto()
    DIFFERENT_FROM = auto()
    INSTANCE_OF = auto()
    MEMBER_OF = auto()
    SUBSET_OF = auto()
    SUPERSET_OF = auto()
    DERIVED_FROM = auto()
    LEADS_TO = auto()
    ENABLES = auto()
    PREVENTS = auto()
    REQUIRES = auto()
    EXCLUDES = auto()
    ALTERNATIVE_TO = auto()
    EQUIVALENT_TO = auto()
    
    def to_json(self) -> str:
        """Convert enum to JSON string."""
        return json.dumps(self.name)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RelationshipTypes':
        """Create enum from JSON string."""
        return cls[json.loads(json_str)]

@dataclass
class Evolution:
    """System evolution record."""
    version: str
    changes: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Convert evolution record to JSON string."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Evolution':
        """Create evolution record from JSON string."""
        data = json.loads(json_str)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class Capability:
    """A system capability."""
    name: str
    description: str
    type: str  # e.g. memory, reasoning, perception
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evolution: Optional[Evolution] = None
    relationships: Dict[RelationshipTypes, List[str]] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Convert capability to JSON string."""
        data = asdict(self)
        if self.evolution:
            data['evolution'] = json.loads(self.evolution.to_json())
        data['relationships'] = {
            rel.name: targets for rel, targets in self.relationships.items()
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Capability':
        """Create capability from JSON string."""
        data = json.loads(json_str)
        if data.get('evolution'):
            data['evolution'] = Evolution.from_json(json.dumps(data['evolution']))
        if data.get('relationships'):
            data['relationships'] = {
                RelationshipTypes[rel]: targets
                for rel, targets in data['relationships'].items()
            }
        return cls(**data)

@dataclass
class AISystem:
    """Configuration for an AI system."""
    name: str
    description: str
    capabilities: List[Capability]
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evolution: Optional[Evolution] = None
    relationships: Dict[RelationshipTypes, List[str]] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Convert system config to JSON string."""
        data = asdict(self)
        data['capabilities'] = [
            json.loads(c.to_json()) for c in self.capabilities
        ]
        if self.evolution:
            data['evolution'] = json.loads(self.evolution.to_json())
        data['relationships'] = {
            rel.name: targets for rel, targets in self.relationships.items()
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AISystem':
        """Create system config from JSON string."""
        data = json.loads(json_str)
        data['capabilities'] = [
            Capability.from_json(json.dumps(c))
            for c in data['capabilities']
        ]
        if data.get('evolution'):
            data['evolution'] = Evolution.from_json(json.dumps(data['evolution']))
        if data.get('relationships'):
            data['relationships'] = {
                RelationshipTypes[rel]: targets
                for rel, targets in data['relationships'].items()
            }
        return cls(**data)

@dataclass
class Memory:
    """A memory entry in the system."""
    content: str
    memory_type: str  # semantic, episodic, procedural
    source: str  # agent or system that created the memory
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    evolution: Optional[Evolution] = None
    relationships: Dict[RelationshipTypes, List[str]] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Convert memory to JSON string."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.evolution:
            data['evolution'] = json.loads(self.evolution.to_json())
        data['relationships'] = {
            rel.name: targets for rel, targets in self.relationships.items()
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Memory':
        """Create memory from JSON string."""
        data = json.loads(json_str)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('evolution'):
            data['evolution'] = Evolution.from_json(json.dumps(data['evolution']))
        if data.get('relationships'):
            data['relationships'] = {
                RelationshipTypes[rel]: targets
                for rel, targets in data['relationships'].items()
            }
        return cls(**data)

@dataclass
class DialogueMessage:
    """A message in a dialogue."""
    agent_type: str
    content: str
    message_type: str  # e.g. question, insight, validation
    references: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evolution: Optional[Evolution] = None
    relationships: Dict[RelationshipTypes, List[str]] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.evolution:
            data['evolution'] = json.loads(self.evolution.to_json())
        data['relationships'] = {
            rel.name: targets for rel, targets in self.relationships.items()
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DialogueMessage':
        """Create message from JSON string."""
        data = json.loads(json_str)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('evolution'):
            data['evolution'] = Evolution.from_json(json.dumps(data['evolution']))
        if data.get('relationships'):
            data['relationships'] = {
                RelationshipTypes[rel]: targets
                for rel, targets in data['relationships'].items()
            }
        return cls(**data)

@dataclass
class DialogueContext:
    """Context for a dialogue session."""
    topic: str
    messages: List[DialogueMessage] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    status: str = "active"  # active, completed, archived
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evolution: Optional[Evolution] = None
    relationships: Dict[RelationshipTypes, List[str]] = field(default_factory=dict)
    
    def add_message(self, message: DialogueMessage):
        """Add a message to the dialogue."""
        self.messages.append(message)
        if message.agent_type not in self.participants:
            self.participants.append(message.agent_type)
    
    def add_participant(self, participant: str):
        """Add a participant to the dialogue."""
        if participant not in self.participants:
            self.participants.append(participant)
    
    def get_messages_by_type(self, message_type: str) -> List[DialogueMessage]:
        """Get all messages of a specific type."""
        return [m for m in self.messages if m.message_type == message_type]
    
    def get_messages_by_agent(self, agent_type: str) -> List[DialogueMessage]:
        """Get all messages from a specific agent."""
        return [m for m in self.messages if m.agent_type == agent_type]
    
    def get_recent_messages(self, count: int = 5) -> List[DialogueMessage]:
        """Get the most recent messages."""
        return self.messages[-count:]
    
    def to_json(self) -> str:
        """Convert context to JSON string."""
        data = asdict(self)
        data['messages'] = [
            json.loads(m.to_json()) for m in self.messages
        ]
        data['created_at'] = self.created_at.isoformat()
        if self.evolution:
            data['evolution'] = json.loads(self.evolution.to_json())
        data['relationships'] = {
            rel.name: targets for rel, targets in self.relationships.items()
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DialogueContext':
        """Create context from JSON string."""
        data = json.loads(json_str)
        data['messages'] = [
            DialogueMessage.from_json(json.dumps(m))
            for m in data['messages']
        ]
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('evolution'):
            data['evolution'] = Evolution.from_json(json.dumps(data['evolution']))
        if data.get('relationships'):
            data['relationships'] = {
                RelationshipTypes[rel]: targets
                for rel, targets in data['relationships'].items()
            }
        return cls(**data)

@dataclass
class AgentResponse:
    """Response from an agent."""
    response: str
    concepts: List[Dict[str, Any]] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    implications: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    reasoning: List[str] = field(default_factory=list)
    dialogue_context: Optional[DialogueContext] = None
    referenced_messages: List[DialogueMessage] = field(default_factory=list)
    perspective: str = ""
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evolution: Optional[Evolution] = None
    relationships: Dict[RelationshipTypes, List[str]] = field(default_factory=dict)
    
    def dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        data = {
            'response': self.response,
            'concepts': self.concepts,
            'key_points': self.key_points,
            'implications': self.implications,
            'uncertainties': self.uncertainties,
            'reasoning': self.reasoning,
            'perspective': self.perspective,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
        
        if self.dialogue_context:
            data['dialogue_context'] = json.loads(self.dialogue_context.to_json())
        
        if self.referenced_messages:
            data['referenced_messages'] = [
                json.loads(m.to_json()) for m in self.referenced_messages
            ]
        
        if self.evolution:
            data['evolution'] = json.loads(self.evolution.to_json())
        
        if self.relationships:
            data['relationships'] = {
                rel.name: targets for rel, targets in self.relationships.items()
            }
        
        return data
    
    def to_json(self) -> str:
        """Convert response to JSON string."""
        return json.dumps(self.dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentResponse':
        """Create response from JSON string."""
        data = json.loads(json_str)
        if data.get('dialogue_context'):
            data['dialogue_context'] = DialogueContext.from_json(
                json.dumps(data['dialogue_context'])
            )
        if data.get('referenced_messages'):
            data['referenced_messages'] = [
                DialogueMessage.from_json(json.dumps(m))
                for m in data['referenced_messages']
            ]
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('evolution'):
            data['evolution'] = Evolution.from_json(json.dumps(data['evolution']))
        if data.get('relationships'):
            data['relationships'] = {
                RelationshipTypes[rel]: targets
                for rel, targets in data['relationships'].items()
            }
        return cls(**data)
