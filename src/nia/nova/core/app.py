"""FastAPI application configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .endpoints import analytics_router, orchestration_router, ws_router
from .thread_endpoints import thread_router, task_router
from .memory_endpoints import memory_router

# Create FastAPI app
app = FastAPI(
    title="Nova Intelligence Architecture",
    description="API for Nova's analytics and orchestration capabilities",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routers
app.include_router(analytics_router)
app.include_router(orchestration_router)
app.include_router(ws_router)
app.include_router(thread_router)
app.include_router(task_router)
app.include_router(memory_router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Nova Intelligence Architecture",
        "version": "0.1.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "api": "operational",
            "websocket": "operational",
            "memory": "operational",
            "orchestration": "operational"
        }
    }
