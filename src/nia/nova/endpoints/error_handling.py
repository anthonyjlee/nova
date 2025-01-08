"""Error handling utilities for endpoints."""

from typing import Optional, Dict, Any
from fastapi import HTTPException

class ServiceError(Exception):
    """Base class for service errors."""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        """Initialize error."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dict."""
        return {
            "error": self.message,
            "status_code": self.status_code,
            "details": self.details
        }
        
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict()
        )

class ValidationError(ServiceError):
    """Validation error."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize validation error."""
        super().__init__(message, status_code=422, details=details)
