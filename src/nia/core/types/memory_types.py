"""Memory type definitions for NIA."""

import json
from enum import Enum
from typing import Dict, Any, Optional, List, Union, TypeVar

# Type for JSON-serializable values
JSONSerializable = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, ConfigDict

from .domain_types import DomainContext, DomainTransfer, BaseDomain
from .agent_types import Concept, Relationship
from .response_types import AgentResponse

__all__ = [
    'MemoryType', 'Memory', 'EpisodicMemory', 'SemanticMemory',
    'ValidationSchema', 'CrossDomainSchema', 'MockMemory', 'KnowledgeVertical'
]

class KnowledgeVertical(str, Enum):
    """Knowledge vertical types."""
    GENERAL = "general"
    TECHNICAL = "technical"
    BUSINESS = "business"
    CREATIVE = "creative"
    SCIENTIFIC = "scientific"
    EDUCATIONAL = "educational"
    RETAIL = "retail"
    PSYCHOLOGY = "psychology"
    TECHNOLOGY = "technology"
    BACKEND = "backend"
    DATABASE = "database"

class MemoryState(str, Enum):
    """Memory state enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class MemoryValidation(BaseModel):
    """Memory validation schema."""
    is_valid: bool = True
    validation_type: str
    validation_score: float = 1.0
    validation_message: Optional[str] = None

class MemoryType(str, Enum):
    """Types of memories in the system."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EMOTIONAL = "emotional"
    SENSORY = "sensory"
    THREAD = "thread"
    TASK_UPDATE = "task_update"
    CROSS_DOMAIN_REQUEST = "cross_domain_request"

class ValidationSchema(BaseModel):
    """Schema for memory validation."""
    domain: str
    confidence: float
    source: str
    timestamp: str

class CrossDomainSchema(BaseModel):
    """Schema for cross-domain memory operations."""
    from_domain: str
    to_domain: str
    operation: str
    data: Dict[str, Any]


class Memory(BaseModel):
    """Base memory model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: Any = Field(default_factory=dict)
    type: str = Field(default=MemoryType.EPISODIC.value)
    importance: float = 0.5
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    domain_context: Optional[DomainContext] = None
    validation: Optional[ValidationSchema] = None
    concepts: List[Concept] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    knowledge: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra='allow',
        json_encoders={
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else None,
            UUID: str
        }
    )

    @field_validator('id', mode='before')
    def validate_id(cls, v, info):
        """Validate ID field."""
        if v is None:
            return str(uuid4())
        if isinstance(v, UUID):
            return str(v)
        if isinstance(v, str):
            try:
                # Validate it's a proper UUID string
                UUID(v)
                return v
            except ValueError:
                return str(uuid4())
        return str(uuid4())

    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        """Override model_json_schema to handle serialization."""
        schema = super().model_json_schema(*args, **kwargs)
        schema.update({"type": "object"})
        return schema

    def model_dump(self, *args, **kwargs):
        """Override model_dump method to handle serialization."""
        d = super().model_dump(*args, **kwargs)
        # Ensure ID is always a string
        if 'id' in d:
            d['id'] = str(d['id'])
        if self.domain_context:
            d['domain_context'] = self.domain_context.model_dump()
        if self.validation:
            d['validation'] = self.validation.model_dump()
        d['concepts'] = [c.model_dump() if hasattr(c, 'model_dump') else c for c in self.concepts]
        d['relationships'] = [r.model_dump() if hasattr(r, 'model_dump') else r for r in self.relationships]
        return d

    @field_validator('type', mode='before')
    def validate_type(cls, v, info):
        """Validate type field."""
        if v is None:
            return MemoryType.EPISODIC.value
        if isinstance(v, MemoryType):
            return v.value
        try:
            if isinstance(v, str) and v in MemoryType.__members__:
                return MemoryType[v].value
            return str(v)
        except:
            return MemoryType.EPISODIC.value

    @field_validator('content', mode='before')
    def validate_content(cls, v, info):
        """Validate content field."""
        if v is None:
            return {}
            
        # Handle primitive types directly
        if isinstance(v, (str, bool, int, float)):
            return v
            
        # Handle dict type
        if isinstance(v, dict):
            try:
                # Recursively convert all values to JSON-serializable format
                def convert_value(val):
                    if isinstance(val, (dict, list, str, int, float, bool, type(None))):
                        return val
                    if hasattr(val, 'model_dump'):
                        return val.model_dump()
                    if hasattr(val, 'dict'):
                        return val.dict()
                    if hasattr(val, 'json'):
                        try:
                            json_val = val.json()
                            return json.loads(json_val) if isinstance(json_val, str) else json_val
                        except:
                            pass
                    if hasattr(val, '__dict__'):
                        return val.__dict__
                    return str(val)
                    
                result = {}
                for k, val in v.items():
                    if isinstance(val, dict):
                        result[k] = {k2: convert_value(v2) for k2, v2 in val.items()}
                    elif isinstance(val, (list, tuple, set)):
                        result[k] = [convert_value(item) for item in val]
                    else:
                        result[k] = convert_value(val)
                        
                # Verify JSON serializability
                json.dumps(result)
                return result
            except:
                return str(v)
                
        # Handle list/tuple/set types
        if isinstance(v, (list, tuple, set)):
            try:
                # Recursively convert all items to JSON-serializable format
                def convert_item(item):
                    if isinstance(item, (dict, list, str, int, float, bool, type(None))):
                        return item
                    if hasattr(item, 'model_dump'):
                        return item.model_dump()
                    if hasattr(item, 'dict'):
                        return item.dict()
                    if hasattr(item, 'json'):
                        try:
                            json_val = item.json()
                            return json.loads(json_val) if isinstance(json_val, str) else json_val
                        except:
                            pass
                    if hasattr(item, '__dict__'):
                        return item.__dict__
                    return str(item)
                    
                result = []
                for item in v:
                    if isinstance(item, dict):
                        result.append({k: convert_item(v) for k, v in item.items()})
                    elif isinstance(item, (list, tuple, set)):
                        result.append([convert_item(i) for i in item])
                    else:
                        result.append(convert_item(item))
                        
                # Verify JSON serializability
                json.dumps(result)
                return result
            except:
                return str(v)
                
        # Handle Pydantic models and other objects
        if hasattr(v, 'model_dump'):
            try:
                result = v.model_dump()
                json.dumps(result)  # Verify JSON serializability
                return result
            except:
                return str(v)
                
        if hasattr(v, 'dict'):
            try:
                result = v.dict()
                json.dumps(result)  # Verify JSON serializability
                return result
            except:
                return str(v)
                
        if hasattr(v, 'json'):
            try:
                result = v.json()
                if isinstance(result, str):
                    # If json() returns a string, try to parse it
                    return json.loads(result)
                return result
            except:
                return str(v)
                
        if hasattr(v, '__dict__'):
            try:
                result = v.__dict__
                json.dumps(result)  # Verify JSON serializability
                return result
            except:
                return str(v)
                
        # Default to string representation
        return str(v)

    @field_validator('concepts', 'relationships', mode='before')
    def validate_lists(cls, v, info):
        """Validate list fields."""
        if v is None:
            return []
        if isinstance(v, list):
            try:
                if info.field_name == 'concepts':
                    return [Concept(**item) if isinstance(item, dict) else item for item in v]
                if info.field_name == 'relationships':
                    return [Relationship(**item) if isinstance(item, dict) else item for item in v]
                return v
            except:
                return []
        try:
            if hasattr(v, 'dict'):
                return [v.dict()]
            if hasattr(v, 'model_dump'):
                return [v.model_dump()]
            if hasattr(v, 'json'):
                return [v.json()]
            return list(v)
        except:
            return []

    @field_validator('context', 'metadata', 'knowledge', mode='before')
    def validate_dicts(cls, v, info):
        """Validate dictionary fields."""
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        try:
            if hasattr(v, 'dict'):
                return v.dict()
            if hasattr(v, 'model_dump'):
                return v.model_dump()
            if hasattr(v, 'json'):
                return v.json()
            return dict(v)
        except:
            return {}

    @field_validator('timestamp', mode='before')
    def validate_timestamp(cls, v, info):
        """Validate timestamp field."""
        if v is None:
            return datetime.now()
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except:
                try:
                    return datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
                except:
                    try:
                        return datetime.strptime(v, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except:
                        return datetime.now()
        if isinstance(v, (int, float)):
            try:
                return datetime.fromtimestamp(v)
            except:
                return datetime.now()
        return datetime.now()

    @field_validator('importance', mode='before')
    def validate_importance(cls, v, info):
        """Validate importance field."""
        if v is None:
            return 0.5
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except:
            return 0.5

    @field_validator('domain_context', mode='before')
    def validate_domain_context(cls, v, info):
        """Validate domain context."""
        if v is None:
            return None
        if isinstance(v, DomainContext):
            return v
        if isinstance(v, dict):
            try:
                if 'cross_domain' in v and isinstance(v['cross_domain'], dict):
                    v['cross_domain'] = CrossDomainSchema(**v['cross_domain'])
                return DomainContext(**v)
            except:
                return None
        return None

    @field_validator('validation', mode='before')
    def validate_validation(cls, v, info):
        """Validate validation schema."""
        if v is None:
            return None
        if isinstance(v, ValidationSchema):
            return v
        if isinstance(v, dict):
            try:
                return ValidationSchema(**v)
            except:
                return None
        return None


class EpisodicMemory(Memory):
    """Model for episodic memories."""
    pass

class SemanticMemory(Memory):
    """Model for semantic memories."""
    concepts: List[Concept] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    domain_context: Optional[DomainContext] = None
    validation: Optional[ValidationSchema] = None

class MockMemory(Memory):
    """Mock memory model for testing."""
    # Additional fields specific to MockMemory
    consolidated: bool = Field(default=False)
    participants: List[str] = Field(default_factory=list)

    def model_dump(self, *args, **kwargs):
        """Override model_dump method to handle serialization."""
        d = super().model_dump(*args, **kwargs)
        d.update({
            'consolidated': self.consolidated,
            'participants': self.participants
        })
        return d
