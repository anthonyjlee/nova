"""Pydantic models for structured responses."""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Any
from nia.core.types.memory_types import AgentResponse  # Import AgentResponse instead of redefining it

# Base Models
class Concept(BaseModel):
    statement: str
    type: str
    confidence: float
    description: Optional[str] = None

class KeyPoint(BaseModel):
    statement: str
    type: str
    confidence: float
    importance: float

class ComplexityFactor(BaseModel):
    factor: str
    weight: float

class Structure(BaseModel):
    sections: List[str]
    relationships: List[str]
    domain_factors: Dict[str, Union[str, float]]
    complexity_factors: List[ComplexityFactor]

class AnalysisResponse(BaseModel):
    concepts: List[Concept]
    key_points: List[KeyPoint]
    structure: Structure

class Metric(BaseModel):
    name: str
    value: Union[str, float, int]
    confidence: float

class Trend(BaseModel):
    name: str
    description: str
    confidence: float

class Insight(BaseModel):
    type: str
    description: str
    confidence: float
    recommendations: List[str]

class Analytics(BaseModel):
    key_metrics: List[Metric]
    trends: List[Trend]

class AnalyticsResponse(BaseModel):
    analytics: Dict[str, Any]
    insights: List[Dict[str, Any]]
    confidence: float
    timestamp: str

# Request Models
class AnalyticsRequest(BaseModel):
    type: str = Field(..., description="Type of analytics to perform")
    content: Dict[str, Any] = Field(..., description="Content to analyze")
    domain: Optional[str] = Field(None, description="Domain for analysis")

class TaskRequest(BaseModel):
    task_type: str
    content: Dict[str, Any]
    domain: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CoordinationRequest(BaseModel):
    type: str
    content: str
    domain: Optional[str] = None
    llm_config: Optional[Dict[str, str]] = None

class ResourceAllocationRequest(BaseModel):
    resources: List[Dict[str, Any]]
    constraints: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None

class MemoryRequest(BaseModel):
    content: str
    type: str
    importance: Optional[float] = 0.5
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class FlowOptimizationRequest(BaseModel):
    flow_id: str
    optimization_type: str
    constraints: Optional[Dict[str, Any]] = None

class AgentAssignmentRequest(BaseModel):
    task_id: str
    agent_type: str
    capabilities: List[str]
    domain: Optional[str] = None

class ParseRequest(BaseModel):
    text: str
    domain: Optional[str] = None
    llm_config: Optional[Dict[str, str]] = None

# Response Models
class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    timestamp: str

class CoordinationResponse(BaseModel):
    coordination_id: str
    status: str
    agents: List[str]
    timestamp: str

class ResourceAllocationResponse(BaseModel):
    allocations: List[Dict[str, Any]]
    analytics: Dict[str, Any]
    confidence: float
    timestamp: str

class MemoryResponse(BaseModel):
    memory_id: str
    status: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
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

class ParseResponse(BaseModel):
    parsed_content: Dict[str, Any]
    confidence: float
    metadata: Dict[str, Any]
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
    issues: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    timestamp: str

class GraphOptimizeResponse(BaseModel):
    optimizations_applied: List[str]
    performance_impact: Dict[str, Any]
    timestamp: str

class GraphStatisticsResponse(BaseModel):
    node_count: int
    edge_count: int
    density: float
    clustering_coefficient: float
    timestamp: str

class GraphBackupResponse(BaseModel):
    backup_id: str
    size_bytes: int
    node_count: int
    edge_count: int
    timestamp: str

# LLM Response Models for Outlines JSON Generation
class LLMConcept(BaseModel):
    """A concept identified in LLM analysis."""
    name: str = Field(..., description="Name of the concept")
    type: str = Field(..., description="Type of concept (e.g., scientific, technical, abstract)")
    description: str = Field(..., description="Detailed description of the concept")
    related: List[str] = Field(default_factory=list, description="List of related concepts")

class LLMAnalysisResult(BaseModel):
    """Analysis result from LLM using outlines.generate.json."""
    response: str = Field(..., description="The main analysis response")
    concepts: List[LLMConcept] = Field(..., description="List of identified concepts")
    key_points: List[str] = Field(..., description="List of key points from the analysis")
    implications: List[str] = Field(..., description="List of implications drawn from the analysis")
    uncertainties: List[str] = Field(..., description="List of uncertainties or open questions")
    reasoning: List[str] = Field(..., description="Step-by-step reasoning process")

class LLMAnalyticsResult(BaseModel):
    """Analytics result from LLM using outlines.generate.json."""
    response: str = Field(..., description="The analysis response")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")

from typing import Literal

class LLMErrorResponse(BaseModel):
    """Error response from LLM using outlines.generate.json."""
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    confidence: Literal[0.0] = Field(default=0.0, description="Always 0.0 for errors")
