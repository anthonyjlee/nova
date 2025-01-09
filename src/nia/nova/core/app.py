"""FastAPI application configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .endpoints import (
    graph_router,
    agent_router,
    user_router,
    analytics_router,
    orchestration_router,
    chat_router,
    ws_router
)

app = FastAPI(
    title="Nova API",
    description="""
Nova's analytics and orchestration API

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
app.include_router(chat_router)
app.include_router(ws_router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Nova API",
        "version": "0.1.0",
        "status": "running"
    }
