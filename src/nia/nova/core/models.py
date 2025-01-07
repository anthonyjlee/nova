"""Pydantic models for API responses."""

from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

# Request Models
class AnalyticsRequest(BaseModel):
    type: str
    domain: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class ParseRequest(BaseModel):
    text: str
    domain: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ResourceAllocationRequest(BaseModel):
    resources: List[Dict[str, Any]]
    constraints: Dict[str, Any]
    priority: Optional[int] = None

class MemoryRequest(BaseModel):
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class TaskRequest(BaseModel):
    task_type: str
    parameters: Dict[str, Any]
    priority: Optional[int] = None

class CoordinationRequest(BaseModel):
    action: str
    parameters: Dict[str, Any]

class FlowOptimizationRequest(BaseModel):
    flow_id: str
    target_metrics: List[str]
    constraints: Dict[str, Any]

class AgentAssignmentRequest(BaseModel):
    task_id: str
    agent_type: str
    capabilities: List[str]

# Response Models
class ParsedContent(BaseModel):
    concepts: List[str]
    key_points: List[str]
    structure: Dict[str, Any]

class ParseResponse(BaseModel):
    parsed_content: ParsedContent
    confidence: float
    metadata: Dict[str, Any]
    timestamp: str

class AnalyticsResult(BaseModel):
    analytics: Dict[str, Any]
    insights: List[str]
    confidence: float
    timestamp: str

# Alias for backward compatibility
AnalyticsResponse = AnalyticsResult

class ResourceAllocationResult(BaseModel):
    allocations: List[Dict[str, Any]]
    analytics: Dict[str, Any]
    confidence: float
    timestamp: str

# Alias for backward compatibility
ResourceAllocationResponse = ResourceAllocationResult

class AgentResponse(BaseModel):
    agent_id: str
    agent_type: str
    capabilities: List[str]
    domain: str
    timestamp: str

class ProfileResponse(BaseModel):
    profile_id: str
    status: str
    timestamp: str

class PreferenceResponse(BaseModel):
    status: str
    preferences: Dict[str, Any]
    timestamp: str

class AgentCapabilitiesResponse(BaseModel):
    agent_id: str
    capabilities: List[str]
    timestamp: str

class AgentTypesResponse(BaseModel):
    agent_types: List[str]
    timestamp: str

class AgentSearchResponse(BaseModel):
    agents: List[Dict[str, Any]]
    timestamp: str

class AgentHistoryResponse(BaseModel):
    agent_id: str
    interactions: List[Dict[str, Any]]
    timestamp: str

class AgentMetricsResponse(BaseModel):
    agent_id: str
    performance_metrics: Dict[str, Any]
    timestamp: str

class AgentStatusResponse(BaseModel):
    agent_id: str
    status: str
    timestamp: str

class GraphPruneResponse(BaseModel):
    nodes_removed: int
    edges_removed: int
    timestamp: str

class GraphHealthResponse(BaseModel):
    status: str
    details: Dict[str, Any]
    timestamp: str

class GraphOptimizeResponse(BaseModel):
    optimizations: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    timestamp: str

class GraphStatisticsResponse(BaseModel):
    node_count: int
    edge_count: int
    metrics: Dict[str, Any]
    timestamp: str

class GraphBackupResponse(BaseModel):
    backup_id: str
    size: int
    format: str
    timestamp: str

class MemoryResponse(BaseModel):
    memory_id: str
    status: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: str

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    timestamp: str

class CoordinationResponse(BaseModel):
    success: bool
    message: str
    result: Optional[Dict[str, Any]] = None
    timestamp: str

class FlowOptimizationResponse(BaseModel):
    flow_id: str
    optimizations: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    timestamp: str

class AgentAssignmentResponse(BaseModel):
    task_id: str
    agent_id: str
    status: str
    timestamp: str
