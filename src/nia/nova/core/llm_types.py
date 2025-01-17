"""LLM types and models for Nova."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

class LLMProvider(str, Enum):
    """LLM provider enum."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LMSTUDIO = "lmstudio"
    CUSTOM = "custom"

class LLMModel(str, Enum):
    """LLM model enum."""
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"
    CLAUDE = "claude"
    CLAUDE2 = "claude-2"
    CUSTOM = "custom"

class LLMRole(str, Enum):
    """LLM role enum."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"

class LLMMessage(BaseModel):
    """LLM message model."""
    role: LLMRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class LLMFunction(BaseModel):
    """LLM function model."""
    name: str
    description: str
    parameters: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class LLMConfig(BaseModel):
    """LLM configuration model."""
    provider: LLMProvider
    model: LLMModel
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class LLMRequest(BaseModel):
    """LLM request model."""
    messages: List[LLMMessage]
    functions: Optional[List[LLMFunction]] = None
    config: LLMConfig
    metadata: Optional[Dict[str, Any]] = None

class LLMResponse(BaseModel):
    """LLM response model."""
    message: LLMMessage
    usage: Dict[str, int]
    latency: float
    metadata: Optional[Dict[str, Any]] = None

class LLMErrorDetail(BaseModel):
    """LLM error detail model."""
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

class LLMError(Exception):
    """LLM error exception."""
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
        
    def to_model(self) -> LLMErrorDetail:
        """Convert to Pydantic model."""
        return LLMErrorDetail(
            code=self.code,
            message=self.message,
            details=self.details
        )

class LLMErrorResponse(BaseModel):
    """LLM error response model."""
    error: LLMErrorDetail
    request: LLMRequest
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_error(cls, error: LLMError, request: LLMRequest, metadata: Optional[Dict[str, Any]] = None) -> 'LLMErrorResponse':
        """Create error response from LLMError instance."""
        return cls(
            error=error.to_model(),
            request=request,
            metadata=metadata
        )

class LLMConcept(BaseModel):
    """LLM concept model."""
    name: str
    type: str
    description: str
    related: List[str] = []
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

class LLMAnalysisResult(BaseModel):
    """LLM analysis result model."""
    response: str
    concepts: List[LLMConcept] = []
    key_points: List[str] = []
    implications: List[str] = []
    uncertainties: List[str] = []
    reasoning: List[str] = []
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

class LLMAnalyticsResult(BaseModel):
    """LLM analytics result model."""
    response: str
    metrics: Dict[str, float] = {}
    insights: List[str] = []
    recommendations: List[str] = []
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

class LLMValidation(BaseModel):
    """LLM validation model."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    metadata: Optional[Dict[str, Any]] = None

class LLMMetrics(BaseModel):
    """LLM metrics model."""
    total_requests: int = 0
    total_tokens: int = 0
    average_latency: float = 0.0
    error_rate: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

class LLMCache(BaseModel):
    """LLM cache model."""
    key: str
    response: LLMResponse
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class LLMRateLimit(BaseModel):
    """LLM rate limit model."""
    requests_per_minute: int
    tokens_per_minute: int
    concurrent_requests: int
    metadata: Optional[Dict[str, Any]] = None

class LLMUsage(BaseModel):
    """LLM usage model."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    metadata: Optional[Dict[str, Any]] = None

class LLMStreamChunk(BaseModel):
    """LLM stream chunk model."""
    text: str
    index: int
    total: int
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = None

class LLMLog(BaseModel):
    """LLM log model."""
    model_config = {
        "arbitrary_types_allowed": True
    }
    request: LLMRequest
    response: Optional[LLMResponse] = None
    error: Optional[LLMErrorDetail] = None
    usage: Optional[LLMUsage] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_error(cls, error: LLMError, request: LLMRequest, usage: Optional[LLMUsage] = None, metadata: Optional[Dict[str, Any]] = None) -> 'LLMLog':
        """Create log from LLMError instance."""
        return cls(
            request=request,
            error=error.to_model(),
            usage=usage,
            metadata=metadata
        )
