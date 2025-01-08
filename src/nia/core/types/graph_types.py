"""Graph type definitions."""

from enum import Enum
from typing import Dict, Optional, Any
from pydantic import BaseModel

class GraphNode(BaseModel):
    """Graph node representation."""
    id: str
    label: str
    type: str
    metadata: Optional[Dict[str, Any]] = None

class GraphEdge(BaseModel):
    """Graph edge representation."""
    from_: str
    to: str
    type: str
    metadata: Optional[Dict[str, Any]] = None

class GraphLayout(str, Enum):
    """Graph layout type."""
    HIERARCHICAL = "hierarchical"
    FORCE = "force"
    CIRCULAR = "circular"
    GRID = "grid"
