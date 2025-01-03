"""FastAPI application for Nova's server."""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import logging
from datetime import datetime

from .endpoints import analytics_router, orchestration_router, ws_router
from .error_handling import (
    NovaError,
    handle_nova_error,
    handle_http_error,
    handle_validation_error
)
from .auth import reset_rate_limits

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Nova API",
    description="API for Nova's agent orchestration and analytics",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Add routers
app.include_router(analytics_router)
app.include_router(orchestration_router)
app.include_router(ws_router)

# Add error handlers
app.add_exception_handler(NovaError, handle_nova_error)
app.add_exception_handler(HTTPException, handle_http_error)
app.add_exception_handler(Exception, handle_validation_error)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to each request."""
    # Skip WebSocket connections
    if "upgrade" in request.headers and request.headers["upgrade"].lower() == "websocket":
        return await call_next(request)
        
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Start request timing
    start_time = datetime.now()
    
    # Add request logging
    logger.info(
        f"Request started",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "start_time": start_time.isoformat()
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # End request timing
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Add response headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = str(duration)
    
    # Add response logging
    logger.info(
        f"Request completed",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration": duration,
            "end_time": end_time.isoformat()
        }
    )
    
    return response

@app.middleware("http")
async def format_error_responses(request: Request, call_next):
    """Format error responses to match expected structure."""
    # Skip WebSocket connections
    if "upgrade" in request.headers and request.headers["upgrade"].lower() == "websocket":
        return await call_next(request)
        
    response = await call_next(request)
    
    if response.status_code >= 400:
        # Get response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Parse response body
        try:
            import json
            data = json.loads(body)
            error = None
            
            # Extract error details while preserving original error codes
            if isinstance(data, dict):
                if "detail" in data and isinstance(data["detail"], dict):
                    # Use existing error structure if it has the expected format
                    if "code" in data["detail"]:
                        error = data["detail"]
                    # Extract error from nested structure
                    elif "error" in data["detail"] and isinstance(data["detail"]["error"], dict):
                        error = data["detail"]["error"]
                    else:
                        error = {
                            "code": data["detail"].get("code", "ERROR"),
                            "message": str(data["detail"])
                        }
                # Handle direct error object
                elif "error" in data and isinstance(data["error"], dict):
                    error = data["error"]
                # Handle direct code and message
                elif "code" in data:
                    error = {
                        "code": data["code"],
                        "message": str(data.get("message", "An error occurred"))
                    }
                else:
                    error = {
                        "code": "ERROR",
                        "message": str(data.get("message", "An error occurred"))
                    }
            else:
                error = {
                    "code": "ERROR",
                    "message": str(data)
                }
            
            # Preserve original status code and headers
            return JSONResponse(
                status_code=response.status_code,
                content={
                    "error": error,
                    "detail": {
                        "code": error["code"],
                        "message": error["message"],
                        "timestamp": datetime.now().isoformat()
                    }
                },
                headers=dict(response.headers)
            )
        except:
            # If we can't parse the response, return a generic error
            return JSONResponse(
                status_code=response.status_code,
                content={
                    "error": {
                        "code": "ERROR",
                        "message": "An error occurred"
                    },
                    "detail": {
                        "code": "ERROR",
                        "message": "An error occurred"
                    }
                },
                headers=dict(response.headers)
            )
    
    return response

@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    # Reset rate limits on startup
    reset_rate_limits()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": app.version
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Nova API",
        "version": app.version,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
