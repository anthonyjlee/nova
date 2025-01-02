"""FastAPI application for Nova's server."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uuid
import logging
from datetime import datetime

from .endpoints import analytics_router, orchestration_router
from .error_handling import NovaError, handle_nova_error

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

# Add error handlers
app.add_exception_handler(NovaError, handle_nova_error)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to each request."""
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
