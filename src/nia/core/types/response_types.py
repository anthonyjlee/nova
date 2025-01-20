"""Response type definitions."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel

class AgentResponse(BaseModel):
    """Base model for agent responses."""
    response: str
    concepts: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    timestamp: Optional[datetime] = None
    confidence: float = 0.0
    source: str = ""
    domain: str = "general"
    perspective: Optional[str] = None
    dialogue_context: Optional[Dict[str, Any]] = None
    dialogue: Optional[str] = None
    key_points: Optional[List[str]] = None
    implications: Optional[List[str]] = None
    uncertainties: Optional[List[str]] = None
    reasoning: Optional[str] = None
    message_type: Optional[str] = None
    agent_type: Optional[str] = None
    references: Optional[List[str]] = None
    is_valid: bool = True
    logging: Dict[str, Any] = {}
    logs: List[Dict[str, Any]] = []
    issues: List[Dict[str, Any]] = []
