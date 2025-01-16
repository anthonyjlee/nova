"""Memory system type definitions."""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
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
    type: Union[MemoryType, str]  # Allow both enum and string types
    timestamp: str
    context: Optional[Dict[str, Any]] = None
    concepts: Optional[List[Concept]] = None
    relationships: Optional[List[Relationship]] = None
    participants: Optional[List[str]] = None
    importance: Optional[float] = 0.0
    metadata: Optional[Dict[str, Any]] = None
    
    def dict(self, *args, minimal: bool = False, **kwargs):
        """Override dict serialization to handle custom types."""
        d = super().dict(*args, **kwargs)
        # Keep custom type as string
        if isinstance(self.type, str):
            d["type"] = self.type
            if minimal and self.metadata and "type" in self.metadata:
                self.metadata["type"] = self.type
        return d

    
    def __init__(self, **data):
        """Initialize with validation logging."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.debug(f"Validating memory data: {data}")
            super().__init__(**data)
            
            # Validate required fields
            if not self.content:
                raise ValueError("Memory content cannot be empty")
                
            if not isinstance(self.type, (MemoryType, str)):
                raise ValueError(f"Invalid memory type: {self.type}")
                
            # Handle memory type conversion
            if isinstance(self.type, str):
                # Keep original string if it's a custom type
                if self.type not in [t.value for t in MemoryType]:
                    logger.debug(f"Using custom memory type: {self.type}")
                else:
                    # Convert to enum if it matches a standard type
                    try:
                        self.type = MemoryType(self.type)
                        logger.debug(f"Converted to enum type: {self.type}")
                    except ValueError:
                        logger.warning(f"Invalid memory type string: {self.type}")
            
            # Validate timestamp format
            try:
                datetime.fromisoformat(self.timestamp)
                logger.debug(f"Valid timestamp: {self.timestamp}")
            except ValueError:
                logger.error(f"Invalid timestamp format: {self.timestamp}")
                raise ValueError(f"Invalid timestamp format: {self.timestamp}")
                
            # Validate concepts if present
            if self.concepts:
                for i, concept in enumerate(self.concepts):
                    logger.debug(f"Validating concept {i+1}: {concept}")
                    if not concept.name or not concept.type:
                        logger.error(f"Invalid concept {i+1}: missing name or type")
                        raise ValueError(f"Invalid concept {i+1}: missing name or type")
                    logger.debug(f"Concept {i+1} valid")
                        
            # Validate relationships if present
            if self.relationships:
                for i, rel in enumerate(self.relationships):
                    logger.debug(f"Validating relationship {i+1}: {rel}")
                    if not rel.from_ or not rel.to or not rel.type:
                        logger.error(f"Invalid relationship {i+1}: missing from/to/type")
                        raise ValueError(f"Invalid relationship {i+1}: missing from/to/type")
                    logger.debug(f"Relationship {i+1} valid")
                        
            # Validate importance range
            if self.importance is not None:
                if not (0.0 <= self.importance <= 1.0):
                    logger.error(f"Invalid importance value: {self.importance}")
                    raise ValueError(f"Importance must be between 0 and 1: {self.importance}")
                logger.debug(f"Valid importance: {self.importance}")
                
            logger.debug("Memory validation successful")
            
        except Exception as e:
            logger.error(f"Memory validation failed: {str(e)}")
            raise

class EpisodicMemory(Memory):
    """Episodic memory representation."""
    consolidated: Optional[bool] = False
    
    def dict(self, *args, minimal: bool = False, **kwargs):
        """Override dict serialization to handle custom types."""
        d = super().dict(*args, minimal=minimal, **kwargs)
        # Keep custom type as string
        if isinstance(self.type, str):
            d["type"] = self.type
            if minimal and self.metadata and "type" in self.metadata:
                self.metadata["type"] = self.type
        return d
    
    def __init__(self, **data):
        """Initialize with validation logging."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.debug(f"Validating episodic memory data: {data}")
            super().__init__(**data)
            
            # Allow custom types
            if isinstance(self.type, MemoryType):
                # Only validate if it's a MemoryType enum
                if self.type != MemoryType.EPISODIC:
                    logger.error(f"Invalid type for episodic memory: {self.type}")
                    raise ValueError(f"Invalid type for episodic memory: {self.type}")
            logger.debug(f"Using memory type: {self.type}")
                
            # Validate consolidated flag
            if self.consolidated is not None and not isinstance(self.consolidated, bool):
                raise ValueError(f"Invalid consolidated flag: {self.consolidated}")
                
            logger.debug("Episodic memory validation successful")
            
        except Exception as e:
            logger.error(f"Episodic memory validation failed: {str(e)}")
            raise

class TaskOutput(BaseModel):
    """Task output representation."""
    task_id: str
    type: OutputType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    
    def __init__(self, **data):
        """Initialize with validation logging."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.debug(f"Validating task output data: {data}")
            super().__init__(**data)
            
            # Validate required fields
            if not self.task_id:
                raise ValueError("Task ID cannot be empty")
                
            if not isinstance(self.type, (OutputType, str)):
                raise ValueError(f"Invalid output type: {self.type}")
                
            # Convert string type to enum if needed
            if isinstance(self.type, str):
                try:
                    self.type = OutputType(self.type)
                except ValueError:
                    raise ValueError(f"Invalid output type string: {self.type}")
            
            # Validate content
            if not self.content:
                raise ValueError("Task output content cannot be empty")
                
            # Validate metadata if present
            if self.metadata:
                logger.debug(f"Validating task metadata: {self.metadata}")
                # Add any specific metadata validation here
                
            logger.debug("Task output validation successful")
            
        except Exception as e:
            logger.error(f"Task output validation failed: {str(e)}")
            raise
