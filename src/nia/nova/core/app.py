"""FastAPI application configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .endpoints import (
    graph_router,
    agent_router,
    user_router,
    analytics_router,
    orchestration_router,
    ws_router
)

app = FastAPI(
    title="Nova API",
    description="Nova's analytics and orchestration API",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(graph_router)
app.include_router(agent_router)
app.include_router(user_router)
app.include_router(analytics_router)
app.include_router(orchestration_router)
app.include_router(ws_router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Nova API",
        "version": "0.1.0",
        "status": "running"
    }
