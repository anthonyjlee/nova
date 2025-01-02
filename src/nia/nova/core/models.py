"""Pydantic models for Nova's FastAPI server."""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model."""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ErrorResponse(BaseResponse):
    """Error response model."""
    error: Dict[str, Any]

class AnalyticsRequest(BaseModel):
    """Base analytics request model."""
    type: str = Field(..., description="Type of analytics to perform")
    domain: Optional[str] = Field(None, description="Domain for analytics")
    
    @validator("type")
    def validate_type(cls, v):
        allowed_types = ["behavioral", "predictive", "performance"]
        if v not in allowed_types:
            raise ValueError(f"Type must be one of {allowed_types}")
        return v

class AnalyticsResponse(BaseResponse):
    """Base analytics response model."""
    analytics: Dict[str, Any]
    insights: List[Dict[str, Any]]
    confidence: float = Field(..., ge=0.0, le=1.0)

class TaskRequest(BaseModel):
    """Task creation/update request model."""
    type: str = Field(..., description="Type of task")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=1, le=5)
    deadline: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)

class TaskResponse(BaseResponse):
    """Task response model."""
    task_id: str
    status: str
    orchestration: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)

class CoordinationRequest(BaseModel):
    """Agent coordination request model."""
    agents: List[str] = Field(..., min_items=1)
    task: TaskRequest
    strategy: Optional[str] = None
    constraints: Dict[str, Any] = Field(default_factory=dict)

class CoordinationResponse(BaseResponse):
    """Agent coordination response model."""
    coordination_id: str
    status: str
    orchestration: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)

class ResourceAllocationRequest(BaseModel):
    """Resource allocation request model."""
    resources: Dict[str, Dict[str, Any]] = Field(..., description="Resources to allocate")
    constraints: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=1, le=5)

class ResourceAllocationResponse(BaseResponse):
    """Resource allocation response model."""
    allocations: List[Dict[str, Any]]
    analytics: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)

class MemoryRequest(BaseModel):
    """Memory operation request model."""
    type: str = Field(..., description="Type of memory operation")
    content: Dict[str, Any] = Field(..., description="Memory content")
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("type")
    def validate_type(cls, v):
        allowed_types = ["store", "retrieve", "search", "update", "delete"]
        if v not in allowed_types:
            raise ValueError(f"Type must be one of {allowed_types}")
        return v

class MemoryResponse(BaseResponse):
    """Memory operation response model."""
    memory_id: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    matches: Optional[List[Dict[str, Any]]] = None
    orchestration: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)

class FlowOptimizationRequest(BaseModel):
    """Flow optimization request model."""
    flow_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)

class FlowOptimizationResponse(BaseResponse):
    """Flow optimization response model."""
    flow_id: str
    optimizations: List[Dict[str, Any]]
    analytics: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)

class AgentAssignmentRequest(BaseModel):
    """Agent assignment request model."""
    agent_id: str
    task: TaskRequest
    constraints: Dict[str, Any] = Field(default_factory=dict)

class AgentAssignmentResponse(BaseResponse):
    """Agent assignment response model."""
    agent_id: str
    status: str
    orchestration: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)
