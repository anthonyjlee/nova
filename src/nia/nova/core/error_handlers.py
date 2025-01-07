"""FastAPI error handlers and middleware for Nova's API."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

from .error_handling import (
    NovaError,
    ValidationError,
    ResourceNotFoundError,
    ServiceError
)

logger = logging.getLogger(__name__)

class ErrorLogger:
    """Log and format error responses."""
    
    @staticmethod
    def log_error(
        error: Exception,
        request: Request,
        status_code: int,
        error_code: str,
        error_type: Optional[str] = None
    ) -> None:
        """Log error details."""
        logger.error(
            f"Error processing request: {request.method} {request.url}\n"
            f"Status Code: {status_code}\n"
            f"Error Code: {error_code}\n"
            f"Error Type: {error_type or error.__class__.__name__}\n"
            f"Error Message: {str(error)}\n"
            f"Stack Trace:\n{traceback.format_exc()}"
        )
    
    @staticmethod
    def format_error_response(
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format error response."""
        return {
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {},
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
        }

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    error_details = []
    for error in exc.errors():
        error_details.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        })
    
    ErrorLogger.log_error(
        error=exc,
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        error_type="RequestValidationError"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorLogger.format_error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"validation_errors": error_details},
            request_id=request.state.request_id if hasattr(request.state, "request_id") else None
        )
    )

async def nova_exception_handler(
    request: Request,
    exc: NovaError
) -> JSONResponse:
    """Handle Nova-specific errors."""
    status_codes = {
        ValidationError: status.HTTP_400_BAD_REQUEST,
        ResourceNotFoundError: status.HTTP_404_NOT_FOUND,
        ServiceError: status.HTTP_500_INTERNAL_SERVER_ERROR
    }
    
    error_code = exc.__class__.__name__.upper()
    status_code = status_codes.get(exc.__class__, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    ErrorLogger.log_error(
        error=exc,
        request=request,
        status_code=status_code,
        error_code=error_code
    )
    
    return JSONResponse(
        status_code=status_code,
        content=ErrorLogger.format_error_response(
            error_code=error_code,
            message=str(exc),
            request_id=request.state.request_id if hasattr(request.state, "request_id") else None
        )
    )

async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    ErrorLogger.log_error(
        error=exc,
        request=request,
        status_code=exc.status_code,
        error_code="HTTP_ERROR"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorLogger.format_error_response(
            error_code="HTTP_ERROR",
            message=str(exc.detail),
            request_id=request.state.request_id if hasattr(request.state, "request_id") else None
        )
    )

async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle all other exceptions."""
    ErrorLogger.log_error(
        error=exc,
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_ERROR"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorLogger.format_error_response(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details={"error_type": exc.__class__.__name__},
            request_id=request.state.request_id if hasattr(request.state, "request_id") else None
        )
    )

class RequestContextMiddleware:
    """Add request context like request ID."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Process request context."""
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        # Add request ID
        from uuid import uuid4
        scope["state"] = {"request_id": str(uuid4())}
        
        # Add timing information
        scope["state"]["start_time"] = datetime.now()
        
        return await self.app(scope, receive, send)

class ResponseHeaderMiddleware:
    """Add custom response headers."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Process response headers."""
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        async def send_wrapper(message):
            """Wrap send to modify headers."""
            if message["type"] == "http.response.start":
                # Add custom headers
                headers = dict(message.get("headers", []))
                
                # Add request ID
                if hasattr(scope.get("state", {}), "request_id"):
                    headers[b"x-request-id"] = scope["state"]["request_id"].encode()
                
                # Add timing information
                if hasattr(scope.get("state", {}), "start_time"):
                    process_time = (datetime.now() - scope["state"]["start_time"]).total_seconds()
                    headers[b"x-process-time"] = str(process_time).encode()
                
                # Update headers in message
                message["headers"] = [(k, v) for k, v in headers.items()]
            
            await send(message)
        
        return await self.app(scope, receive, send_wrapper)

def configure_error_handlers(app):
    """Configure FastAPI error handlers."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(NovaError, nova_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    # Add middleware
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(ResponseHeaderMiddleware)
