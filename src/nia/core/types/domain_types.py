"""Domain and knowledge vertical type definitions."""

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class KnowledgeVertical(str, Enum):
    """Knowledge verticals in the system."""
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

class BaseDomain(str, Enum):
    """Base domain types."""
    GENERAL = "general"
    PROFESSIONAL = "professional"
    PERSONAL = "personal"
    SYSTEM = "system"

class DomainContext(BaseModel):
    """Context for domain operations."""
    domain: str
    confidence: float = 0.5
    source: str
    timestamp: str
    metadata: Dict[str, Any] = {}
    primary_domain: Optional[str] = None
    knowledge_vertical: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None
    access_domain: Optional[str] = None
    cross_domain: Optional[Dict[str, Any]] = None
    approved: bool = False
    requested: bool = False
    source_domain: Optional[str] = None
    target_domain: Optional[str] = None
    justification: Optional[str] = None

    def validate_transfer(self, target_domain: str, target_vertical: Optional[str] = None) -> bool:
        """Validate knowledge transfer between domains."""
        if not self.approved:
            return False
        if self.confidence < 0.5:
            return False
        return True

class DomainTransfer(BaseModel):
    """Model for cross-domain transfers."""
    from_domain: str
    to_domain: str
    operation: str
    data: Dict[str, Any]
    approved: bool = False
    requested: bool = False
    source_domain: Optional[str] = None
    target_domain: Optional[str] = None
    justification: Optional[str] = None
