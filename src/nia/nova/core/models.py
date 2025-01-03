"""Pydantic models for Nova's API."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class ParseRequest(BaseModel):
    """Request model for text parsing."""
    text: str = Field(..., description="Text to parse")
    llm_config: Optional[Dict[str, Any]] = Field(
        None,
        description="LLM configuration for parsing"
    )
    domain: Optional[str] = Field(None, description="Domain for parsing context")

class AnalyticsRequest(BaseModel):
    """Request model for analytics endpoints."""
    type: str = Field(..., description="Type of analytics to perform")
    flow_id: Optional[str] = Field(None, description="Flow ID for flow analytics")
    domain: Optional[str] = Field(None, description="Domain for analytics context")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional parameters for analytics"
    )

class AnalyticsResponse(BaseModel):
    """Response model for analytics endpoints."""
    analytics: Dict[str, Any] = Field(..., description="Analytics results")
    insights: List[Dict[str, Any]] = Field(..., description="Insights derived from analytics")
    confidence: float = Field(..., description="Confidence score for analytics")
    timestamp: str = Field(..., description="Timestamp of analytics generation")

class TaskRequest(BaseModel):
    """Request model for task endpoints."""
    type: str = Field(..., description="Type of task")
    parameters: Dict[str, Any] = Field(..., description="Task parameters")
    priority: int = Field(1, description="Task priority (1-5)")
    deadline: Optional[str] = Field(None, description="Task deadline")
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of task IDs this task depends on"
    )

class TaskResponse(BaseModel):
    """Response model for task endpoints."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status")
    orchestration: Dict[str, Any] = Field(..., description="Orchestration details")
    confidence: float = Field(..., description="Confidence score for orchestration")
    timestamp: str = Field(..., description="Timestamp of response")

class CoordinationRequest(BaseModel):
    """Request model for agent coordination."""
    agents: List[str] = Field(..., description="List of agent IDs to coordinate")
    task: TaskRequest = Field(..., description="Task to coordinate")
    strategy: Optional[Dict[str, Any]] = Field(None, description="Coordination strategy")
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Coordination constraints"
    )

class CoordinationResponse(BaseModel):
    """Response model for agent coordination."""
    coordination_id: str = Field(..., description="Unique coordination identifier")
    status: str = Field(..., description="Coordination status")
    orchestration: Dict[str, Any] = Field(..., description="Orchestration details")
    confidence: float = Field(..., description="Confidence score for coordination")
    timestamp: str = Field(..., description="Timestamp of response")

class AgentAssignmentRequest(BaseModel):
    """Request model for agent assignment."""
    agent_id: str = Field(..., description="Agent ID to assign task to")
    task: TaskRequest = Field(..., description="Task to assign")
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Assignment constraints"
    )

class AgentAssignmentResponse(BaseModel):
    """Response model for agent assignment."""
    agent_id: str = Field(..., description="Agent ID task was assigned to")
    status: str = Field(..., description="Assignment status")
    orchestration: Dict[str, Any] = Field(..., description="Orchestration details")
    confidence: float = Field(..., description="Confidence score for assignment")
    timestamp: str = Field(..., description="Timestamp of response")

class ResourceAllocationRequest(BaseModel):
    """Request model for resource allocation."""
    resources: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Resource requirements (resource_id -> {capacity, etc})"
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Allocation constraints"
    )
    priority: int = Field(1, description="Allocation priority (1-5)")

class ResourceAllocationResponse(BaseModel):
    """Response model for resource allocation."""
    allocations: List[Dict[str, Any]] = Field(..., description="Resource allocations")
    analytics: Dict[str, Any] = Field(..., description="Analytics used for allocation")
    confidence: float = Field(..., description="Confidence score for allocation")
    timestamp: str = Field(..., description="Timestamp of response")

class FlowOptimizationRequest(BaseModel):
    """Request model for flow optimization."""
    flow_id: str = Field(..., description="Flow ID to optimize")
    parameters: Dict[str, Any] = Field(..., description="Optimization parameters")
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optimization constraints"
    )

class FlowOptimizationResponse(BaseModel):
    """Response model for flow optimization."""
    flow_id: str = Field(..., description="Flow ID that was optimized")
    optimizations: List[Dict[str, Any]] = Field(..., description="Optimization results")
    analytics: Dict[str, Any] = Field(..., description="Analytics used for optimization")
    confidence: float = Field(..., description="Confidence score for optimization")
    timestamp: str = Field(..., description="Timestamp of response")

class MemoryRequest(BaseModel):
    """Request model for memory operations."""
    type: str = Field(..., description="Type of memory operation")
    content: Dict[str, Any] = Field(..., description="Memory content")
    importance: float = Field(0.5, description="Memory importance (0-1)")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Memory context"
    )
    llm_config: Optional[Dict[str, Any]] = Field(
        None,
        description="LLM configuration for memory operations"
    )

class MemoryResponse(BaseModel):
    """Response model for memory operations."""
    memory_id: Optional[str] = Field(None, description="Memory identifier")
    content: Optional[Dict[str, Any]] = Field(None, description="Memory content")
    matches: Optional[List[Dict[str, Any]]] = Field(None, description="Search matches")
    orchestration: Dict[str, Any] = Field(
        ...,
        description="Orchestration details",
        example={
            "status": "success",
            "details": {
                "operation": "store",
                "type": "memory",
                "memory_id": "123"
            }
        }
    )
    confidence: float = Field(
        ...,
        description="Confidence score for operation",
        ge=0.0,
        le=1.0
    )
    timestamp: str = Field(
        ...,
        description="Timestamp of response",
        example=datetime.now().isoformat()
    )

    class Config:
        """Model configuration."""
        schema_extra = {
            "example": {
                "memory_id": "123",
                "content": {"data": "Memory content"},
                "orchestration": {
                    "status": "success",
                    "details": {
                        "operation": "store",
                        "type": "memory",
                        "memory_id": "123"
                    }
                },
                "confidence": 0.95,
                "timestamp": datetime.now().isoformat()
            }
        }
