"""Nova FastAPI application."""

from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response as FastAPIResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import base64
import hashlib

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

import logging

logger = logging.getLogger(__name__)

class WebSocketUpgradeMiddleware(BaseHTTPMiddleware):
    """Middleware to handle WebSocket upgrade requests."""
    async def dispatch(self, request: Request, call_next):
        logger.debug(f"Request path: {request.url.path}")
        logger.debug(f"Request headers: {request.headers}")
        
        if (
            request.headers.get("upgrade", "").lower() == "websocket" and
            request.headers.get("connection", "").lower() == "upgrade"
        ):
            logger.debug("WebSocket upgrade request detected")
            # Check if this is a WebSocket route
            if request.url.path.startswith("/debug/"):
                logger.debug("WebSocket route detected")
                # Get the WebSocket key from headers
                ws_key = request.headers.get("sec-websocket-key")
                if ws_key:
                    logger.debug(f"WebSocket key found: {ws_key}")
                    # Calculate accept key
                    ws_accept = base64.b64encode(
                        hashlib.sha1(
                            f"{ws_key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11".encode()
                        ).digest()
                    ).decode()
                    logger.debug(f"Calculated accept key: {ws_accept}")
                    
                    # Extract client_id from path
                    path_parts = request.url.path.split("/")
                    if len(path_parts) >= 4 and path_parts[-2] == "client":
                        client_id = path_parts[-1]
                        
                        # Add CORS headers for WebSocket upgrade
                        if request.headers.get("origin") == "http://localhost:5173":
                            # Pass control to FastAPI's WebSocket handler
                            return await call_next(request)
                        else:
                            logger.error(f"Invalid origin: {request.headers.get('origin')}")
                            return Response(status_code=403)
                else:
                    logger.error("No WebSocket key found in headers")
            else:
                logger.debug("Not a WebSocket route")
        # Handle preflight requests
        elif request.method == "OPTIONS" and request.url.path.startswith("/debug/"):
            logger.debug("Handling WebSocket preflight request")
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-Key",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        else:
            logger.debug("Not a WebSocket upgrade request")
            return await call_next(request)

# Create FastAPI app
app = FastAPI(
    title="Nova API",
    description="Nova API for agent orchestration and real-time communication",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add WebSocket upgrade middleware first
app.add_middleware(WebSocketUpgradeMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "CONNECT", "TRACE", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Encoding",
        "Authorization",
        "Content-Type",
        "Origin",
        "X-API-Key",
        "key",
        "Upgrade",
        "Connection",
        "Sec-WebSocket-Key",
        "Sec-WebSocket-Version",
        "Sec-WebSocket-Extensions",
        "Sec-WebSocket-Protocol"
    ],
    expose_headers=[
        "Upgrade",
        "Connection",
        "Sec-WebSocket-Accept",
        "Sec-WebSocket-Protocol"
    ]
)

# Add WebSocket router first without prefix
app.include_router(ws_router, tags=["Real-time Updates"])

# Add other routers
app.include_router(nova_router)
app.include_router(thread_router, prefix="/api/threads", tags=["Chat & Threads"])
app.include_router(task_router, prefix="/api/tasks", tags=["Task Orchestration"])
app.include_router(graph_router, prefix="/api/graph", tags=["Knowledge Graph"])
app.include_router(user_router, prefix="/api", tags=["User Management"])
app.include_router(memory_router, prefix="/api/memory", tags=["System"])
app.include_router(kg_router, prefix="/api/knowledge", tags=["Knowledge Graph"])
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

# Initialize WebSocket server on startup
@app.on_event("startup")
async def startup_event():
    """Initialize WebSocket server on startup."""
    from ..endpoints.websocket_endpoints import initialize_websocket_server
    await initialize_websocket_server()

# Health check endpoint
@app.get("/api/status", tags=["System"])
async def health_check(key: str = Depends(validate_api_key)):
    """Health check endpoint."""
    return {"status": "ok"}
