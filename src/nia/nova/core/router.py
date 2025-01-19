"""FastAPI router configuration."""

from fastapi import APIRouter, WebSocket
from ..endpoints.thread_endpoints import thread_router, task_router
from ..endpoints.user_endpoints import user_router
from ..endpoints.agent_websocket import agent_websocket_endpoint

# Create main router
api_router = APIRouter()

# Add routes
api_router.include_router(thread_router, prefix="/threads", tags=["threads"])
api_router.include_router(task_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(user_router, prefix="/user", tags=["user"])

# Add WebSocket endpoint
@api_router.websocket("/ws/agent/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    await agent_websocket_endpoint(websocket, agent_id)
