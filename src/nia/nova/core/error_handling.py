"""Error handling for Nova's FastAPI server."""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from functools import wraps
from typing import Any, Callable, Dict, Type, TypeVar, Optional, Union
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

# Custom exception types
class NovaError(Exception):
    """Base exception for Nova errors."""
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dict."""
        return {
            "error": {
                "code": self.code,
                "message": self.message
            },
            "detail": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=get_status_code(self),
            detail=self.to_dict()
        )

class ValidationError(NovaError):
    """Validation error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("VALIDATION_ERROR", message, details)

class AuthenticationError(NovaError):
    """Authentication error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("AUTHENTICATION_ERROR", message, details)

class AuthorizationError(NovaError):
    """Authorization error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("PERMISSION_DENIED", message, details)

class ResourceNotFoundError(NovaError):
    """Resource not found error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("RESOURCE_NOT_FOUND", message, details)

class RateLimitError(NovaError):
    """Rate limit exceeded error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("RATE_LIMIT_EXCEEDED", message, details)

class ServiceError(NovaError):
    """Internal service error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("SERVICE_ERROR", message, details)

class InitializationError(NovaError):
    """Error during initialization."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("INITIALIZATION_ERROR", message, details)

# Error handlers
async def handle_nova_error(request: Request, exc: NovaError) -> JSONResponse:
    """Handle Nova errors."""
    logger.error(f"Error handling request {request.state.request_id}: {exc}")
    return JSONResponse(
        status_code=get_status_code(exc),
        content=exc.to_dict()
    )

async def handle_http_error(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.error(f"Error handling request {request.state.request_id}: {exc.detail}")
    
    # Extract error details
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        code = exc.detail["code"]
        message = exc.detail.get("message", str(exc.detail))
    else:
        code = "HTTP_ERROR"
        message = str(exc.detail)
    
    error_response = {
        "error": {
            "code": code,
            "message": message
        },
        "detail": {
            "code": code,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation errors."""
    logger.error(f"Validation error in request {request.state.request_id}: {exc}")
    error = ValidationError(str(exc))
    return JSONResponse(
        status_code=400,
        content=error.to_dict()
    )

def get_status_code(error: Union[Exception, Type[Exception]]) -> int:
    """Get HTTP status code for error."""
    status_codes = {
        ValidationError: 400,
        AuthenticationError: 401,
        AuthorizationError: 403,
        ResourceNotFoundError: 404,
        RateLimitError: 429,
        InitializationError: 422,
        ServiceError: 500
    }
    error_type = error if isinstance(error, type) else type(error)
    return status_codes.get(error_type, 500)

# Decorators
T = TypeVar("T")

def validate_request(model: Type[T]) -> Callable:
    """Validate request body against Pydantic model."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # If request body is passed as a keyword argument
                if "request" in kwargs:
                    validated = model(**kwargs["request"])
                    kwargs["request"] = validated
                # If request body is the first argument
                elif args and len(args) > 0:
                    validated = model(**args[0])
                    args = (validated,) + args[1:]
                return await func(*args, **kwargs)
            except Exception as e:
                raise ValidationError(str(e))
        return wrapper
    return decorator

def retry_on_error(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """Retry operation on failure with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        retry_delay = delay * (2 ** attempt)
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{max_retries} "
                            f"for {func.__name__} after {retry_delay}s delay"
                        )
                        await asyncio.sleep(retry_delay)
            
            logger.error(
                f"All {max_retries} retry attempts failed for {func.__name__}"
            )
            raise last_error
        return wrapper
    return decorator
