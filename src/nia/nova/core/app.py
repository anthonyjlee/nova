"""FastAPI application configuration."""

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# Create root router
root_router = APIRouter(prefix="/api")

@root_router.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Nova API",
        "version": "0.1.0",
        "status": "running"
    }

from .endpoints import (
    graph_router,
    agent_router,
    user_router,
    analytics_router,
    orchestration_router,
    chat_router,
    ws_router
)
from .nova_endpoints import nova_router

# Create FastAPI app
app = FastAPI(
    title="Nova API",
    description="""
Nova's analytics and orchestration API

## Chat & Thread Endpoints

### Thread Management (/api/chat/threads)
- POST /threads/create - Create new thread
- GET /threads/{thread_id} - Get thread details
- POST /threads/{thread_id}/messages - Add message
- GET /threads - List all threads

## WebSocket Endpoints

### Real-time Analytics (/api/ws/ws)
Connect to receive real-time analytics updates. Supports:
- Ping/pong heartbeat
- Swarm monitoring
- Agent coordination
- Analytics updates

Example connection:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

Message Types:
1. Ping: `{"type": "ping"}`
2. Swarm Monitor: `{"type": "swarm_monitor", "task_id": "..."}`
3. Agent Coordination: `{"type": "agent_coordination", "content": "..."}`
4. Analytics Request: `{"type": "analytics", ...}`
""",
    version="0.1.0"
)

# Configure CORS - must be first middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "x-api-key", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Type", "Authorization"],
    max_age=3600,
)

# Enable detailed error logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)

# Include routers
app.include_router(root_router)           # Root endpoint (must be first)
app.include_router(nova_router)           # Nova-specific endpoints
app.include_router(chat_router)           # Chat and threads
app.include_router(graph_router)          # Knowledge graph operations
app.include_router(orchestration_router)  # Task orchestration
app.include_router(agent_router)          # Agent management
app.include_router(analytics_router)      # Analytics and insights
app.include_router(user_router)           # User management
app.include_router(ws_router)             # Real-time updates

# Add error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error handler caught: {exc}", exc_info=True)
    return {
        "detail": str(exc),
        "type": type(exc).__name__,
        "path": request.url.path
    }
