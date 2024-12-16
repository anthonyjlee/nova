"""
Memory type definitions and structures.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional, List

class JSONSerializable:
    """Mixin to make dataclasses JSON serializable."""
    def to_dict(self):
        """Convert to dictionary."""
        return {k: (v.isoformat() if isinstance(v, datetime) else v)
                for k, v in asdict(self).items()}

    def to_json(self):
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

@dataclass
class MemoryBase(JSONSerializable):
    """Base memory fields."""
    agent_name: str
    memory_type: str
    content: Dict[str, Any]
    timestamp: datetime
    metadata: Optional[Dict] = None

@dataclass
class EmotionalState(JSONSerializable):
    """Structure for tracking emotional states."""
    primary_emotion: str  # The dominant emotion being experienced
    intensity: float  # Intensity level from 0.0 to 1.0
    triggers: List[str]  # What caused this emotional state
    context: Dict[str, Any]  # Relevant contextual information
    timestamp: datetime
    duration: Optional[float] = None  # How long this state lasted
    related_memories: Optional[List[str]] = None  # IDs of related memories
    previous_state: Optional[str] = None  # ID of previous emotional state

@dataclass
class EmotionalMemoryContent(JSONSerializable):
    """Content for emotional memories."""
    emotional_state: EmotionalState
    reflection: Optional[str] = None
    impact: Optional[Dict[str, Any]] = None

@dataclass
class InteractionMemoryContent(JSONSerializable):
    """Content for interaction memories."""
    input: str
    responses: Dict[str, str]
    synthesis: str
    emotional_impact: Optional[Dict[str, Any]] = None

@dataclass
class ReflectionMemoryContent(JSONSerializable):
    """Content for reflection memories."""
    insights: List[str]
    patterns: List[str]
    implications: List[str]
    emotional_context: Optional[Dict[str, Any]] = None

@dataclass
class CapabilityMemoryContent(JSONSerializable):
    """Content for capability memories."""
    capability_type: str
    proficiency_level: float
    usage_examples: List[str]
    development_history: List[Dict[str, Any]]
    emotional_associations: Optional[Dict[str, Any]] = None

@dataclass
class RelationshipMemoryContent(JSONSerializable):
    """Content for relationship memories."""
    entity_id: str
    interaction_history: List[Dict[str, Any]]
    trust_level: float
    emotional_dynamics: Dict[str, Any]
    shared_experiences: List[str]

@dataclass
class GoalMemoryContent(JSONSerializable):
    """Content for goal memories."""
    goal_type: str
    description: str
    progress: float
    milestones: List[Dict[str, Any]]
    related_capabilities: List[str]
    emotional_investment: Optional[Dict[str, Any]] = None

class Memory:
    """Memory factory class."""
    
    @staticmethod
    def create_emotional(agent_name: str, emotional_state: EmotionalState,
                        reflection: Optional[str] = None,
                        impact: Optional[Dict[str, Any]] = None,
                        metadata: Optional[Dict] = None) -> MemoryBase:
        """Create an emotional memory."""
        content = EmotionalMemoryContent(
            emotional_state=emotional_state,
            reflection=reflection,
            impact=impact
        )
        return MemoryBase(
            agent_name=agent_name,
            memory_type="emotional",
            content=asdict(content),
            timestamp=datetime.now(),
            metadata=metadata
        )
    
    @staticmethod
    def create_interaction(agent_name: str, input_text: str,
                         responses: Dict[str, str], synthesis: str,
                         emotional_impact: Optional[Dict[str, Any]] = None,
                         metadata: Optional[Dict] = None) -> MemoryBase:
        """Create an interaction memory."""
        content = InteractionMemoryContent(
            input=input_text,
            responses=responses,
            synthesis=synthesis,
            emotional_impact=emotional_impact
        )
        return MemoryBase(
            agent_name=agent_name,
            memory_type="interaction",
            content=asdict(content),
            timestamp=datetime.now(),
            metadata=metadata
        )
    
    @staticmethod
    def create_reflection(agent_name: str, insights: List[str],
                         patterns: List[str], implications: List[str],
                         emotional_context: Optional[Dict[str, Any]] = None,
                         metadata: Optional[Dict] = None) -> MemoryBase:
        """Create a reflection memory."""
        content = ReflectionMemoryContent(
            insights=insights,
            patterns=patterns,
            implications=implications,
            emotional_context=emotional_context
        )
        return MemoryBase(
            agent_name=agent_name,
            memory_type="reflection",
            content=asdict(content),
            timestamp=datetime.now(),
            metadata=metadata
        )
    
    @staticmethod
    def create_capability(agent_name: str, capability_type: str,
                         proficiency_level: float, usage_examples: List[str],
                         development_history: List[Dict[str, Any]],
                         emotional_associations: Optional[Dict[str, Any]] = None,
                         metadata: Optional[Dict] = None) -> MemoryBase:
        """Create a capability memory."""
        content = CapabilityMemoryContent(
            capability_type=capability_type,
            proficiency_level=proficiency_level,
            usage_examples=usage_examples,
            development_history=development_history,
            emotional_associations=emotional_associations
        )
        return MemoryBase(
            agent_name=agent_name,
            memory_type="capability",
            content=asdict(content),
            timestamp=datetime.now(),
            metadata=metadata
        )
    
    @staticmethod
    def create_relationship(agent_name: str, entity_id: str,
                          interaction_history: List[Dict[str, Any]],
                          trust_level: float,
                          emotional_dynamics: Dict[str, Any],
                          shared_experiences: List[str],
                          metadata: Optional[Dict] = None) -> MemoryBase:
        """Create a relationship memory."""
        content = RelationshipMemoryContent(
            entity_id=entity_id,
            interaction_history=interaction_history,
            trust_level=trust_level,
            emotional_dynamics=emotional_dynamics,
            shared_experiences=shared_experiences
        )
        return MemoryBase(
            agent_name=agent_name,
            memory_type="relationship",
            content=asdict(content),
            timestamp=datetime.now(),
            metadata=metadata
        )
    
    @staticmethod
    def create_goal(agent_name: str, goal_type: str,
                    description: str, progress: float,
                    milestones: List[Dict[str, Any]],
                    related_capabilities: List[str],
                    emotional_investment: Optional[Dict[str, Any]] = None,
                    metadata: Optional[Dict] = None) -> MemoryBase:
        """Create a goal memory."""
        content = GoalMemoryContent(
            goal_type=goal_type,
            description=description,
            progress=progress,
            milestones=milestones,
            related_capabilities=related_capabilities,
            emotional_investment=emotional_investment
        )
        return MemoryBase(
            agent_name=agent_name,
            memory_type="goal",
            content=asdict(content),
            timestamp=datetime.now(),
            metadata=metadata
        )
