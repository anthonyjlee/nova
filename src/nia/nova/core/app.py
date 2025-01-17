"""Nova FastAPI application."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from ..endpoints.nova_endpoints import nova_router
from ..endpoints.thread_endpoints import thread_router, task_router
from ..endpoints.graph_endpoints import graph_router
from ..endpoints.user_endpoints import user_router
from ..endpoints.memory_endpoints import memory_router
from ..endpoints.knowledge_endpoints import kg_router
from ..endpoints.websocket_endpoints import ws_router
from ..endpoints.tasks_endpoints import tasks_router
from ..endpoints.channel_endpoints import channel_router
from ..endpoints.agent_endpoints import agent_router
from ..endpoints.auth import validate_api_key

# Create FastAPI app
app = FastAPI(
    title="Nova API",
    description="Nova API for agent orchestration and real-time communication",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers
app.include_router(nova_router)
app.include_router(thread_router, prefix="/api/threads", tags=["Chat & Threads"])
app.include_router(task_router, prefix="/api/tasks", tags=["Task Orchestration"])
app.include_router(graph_router, prefix="/api/graph", tags=["Knowledge Graph"])
app.include_router(user_router, prefix="/api/users", tags=["User Management"])
app.include_router(memory_router, prefix="/api/memory", tags=["System"])
app.include_router(kg_router, prefix="/api/knowledge", tags=["Knowledge Graph"])
app.include_router(ws_router, prefix="/api/ws", tags=["Real-time Updates"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["Task Orchestration"])
app.include_router(channel_router, prefix="/api/channels", tags=["Chat & Threads"])
app.include_router(agent_router, prefix="/api/agents", tags=["Agent Management"])

# Add OpenAPI tags metadata
app.openapi_tags = [
    {
        "name": "System",
        "description": "System-wide operations and health checks"
    },
    {
        "name": "Knowledge Graph",
        "description": "Knowledge graph operations and queries"
    },
    {
        "name": "Agent Management",
        "description": "Agent lifecycle and coordination"
    },
    {
        "name": "User Management",
        "description": "User account and profile management"
    },
    {
        "name": "Analytics & Insights",
        "description": "Data analytics and insights generation"
    },
    {
        "name": "Task Orchestration",
        "description": "Task management and orchestration"
    },
    {
        "name": "Chat & Threads",
        "description": "Chat and thread management"
    },
    {
        "name": "Real-time Updates",
        "description": "WebSocket endpoints for real-time updates"
    }
]

# Health check endpoint
@app.get("/api/status", tags=["System"])
async def health_check(key: str = Depends(validate_api_key)):
    """Health check endpoint."""
    return {"status": "ok"}
