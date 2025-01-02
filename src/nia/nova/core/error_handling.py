"""Error handling utilities for Nova's FastAPI server."""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, Type, List
import time
from functools import wraps
import asyncio
import logging

logger = logging.getLogger(__name__)

class NovaError(Exception):
    """Base exception for Nova errors."""
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(NovaError):
    """Raised when request validation fails."""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )

class AuthenticationError(NovaError):
    """Raised when authentication fails."""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )

class AuthorizationError(NovaError):
    """Raised when authorization fails."""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details
        )

class ResourceNotFoundError(NovaError):
    """Raised when a requested resource is not found."""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=details
        )

class RateLimitError(NovaError):
    """Raised when rate limit is exceeded."""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )

class ServiceError(NovaError):
    """Raised when an internal service error occurs."""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="SERVICE_ERROR",
            status_code=500,
            details=details
        )

async def handle_nova_error(
    request: Request,
    exc: NovaError
) -> JSONResponse:
    """Handle Nova-specific errors."""
    error_response = {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "request_id": request.state.request_id,
            "timestamp": time.time()
        }
    }
    
    # Log error with context
    logger.error(
        f"Error handling request {request.state.request_id}: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "request_id": request.state.request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

def retry_on_error(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    exceptions: List[Type[Exception]] = None,
    exponential_backoff: bool = True
):
    """Decorator to retry operations on failure."""
    if exceptions is None:
        exceptions = (ServiceError,)
        
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except tuple(exceptions) as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        delay = (
                            retry_delay * (2 ** attempt)
                            if exponential_backoff
                            else retry_delay
                        )
                        
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{max_retries} "
                            f"for {func.__name__} after {delay}s delay"
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries} retry attempts failed "
                            f"for {func.__name__}"
                        )
                        
            raise last_exception
            
        return wrapper
    return decorator

def validate_request(request_model: Type[Any]):
    """Decorator to validate request data against a Pydantic model."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Extract request data from kwargs
                request_data = next(
                    (v for k, v in kwargs.items() if isinstance(v, dict)),
                    None
                )
                
                if request_data:
                    # Validate against model
                    validated_data = request_model(**request_data)
                    # Replace original data with validated data
                    for k, v in kwargs.items():
                        if isinstance(v, dict):
                            kwargs[k] = validated_data.dict()
                            break
                            
                return await func(*args, **kwargs)
            except Exception as e:
                raise ValidationError(
                    message="Request validation failed",
                    details={"error": str(e)}
                )
                
        return wrapper
    return decorator
