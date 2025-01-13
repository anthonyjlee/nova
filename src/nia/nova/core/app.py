"""FastAPI application configuration."""

from neo4j import GraphDatabase
from fastapi import FastAPI, APIRouter, Request, HTTPException
from .auth import validate_api_key
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from pathlib import Path
import sys
import traceback
import asyncio

# Configure minimal logging
import logging
from datetime import datetime, time

class RateLimitedLogger:
    def __init__(self, name: str, rate_limit: float = 1.0):  # Increased rate limit to 1 second
        self.logger = logging.getLogger(name)
        self.rate_limit = rate_limit
        self.last_log = {}
        
        # Configure basic logging
        logs_dir = Path("logs/fastapi")
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / f"fastapi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # File handler for all logs
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Configure logger - Set base level to INFO for file logging
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
    
    def _should_log(self, level: int, msg: str) -> bool:
        now = datetime.now().timestamp()
        key = f"{level}:{msg}"
        if key not in self.last_log or (now - self.last_log[key]) >= self.rate_limit:
            self.last_log[key] = now
            return True
        return False
    
    def debug(self, msg: str, *args, **kwargs):
        if self._should_log(logging.DEBUG, msg):
            self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        if self._should_log(logging.INFO, msg):
            self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        if self._should_log(logging.WARNING, msg):
            self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        if self._should_log(logging.ERROR, msg):
            self.logger.error(msg, *args, **kwargs)

logger = RateLimitedLogger("uvicorn")

def log_exception(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = log_exception

from .endpoints import (
    root_router,
    agent_router,
    user_router,
    analytics_router,
    orchestration_router,
    chat_router
)
from .graph_endpoints import graph_router
from .knowledge_endpoints import kg_router
from .nova_endpoints import nova_router
from .tasks_endpoints import tasks_router
from .websocket_endpoints import ws_router
from .dependencies import get_memory_system, get_thread_manager

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

## WebSocket Endpoints (/api/ws)

### Chat WebSocket (/api/ws/chat/{client_id})
Real-time chat updates including:
- New messages
- Thread updates
- Message reactions
- Typing indicators

### Tasks WebSocket (/api/ws/tasks/{client_id})
Real-time task board updates including:
- Task state changes
- Assignment updates
- Comment notifications
- Progress tracking

### Agents WebSocket (/api/ws/agents/{client_id})
Real-time agent status updates including:
- Agent state changes
- Team updates
- Performance metrics
- Capability changes

### Graph WebSocket (/api/ws/graph/{client_id})
Real-time knowledge graph updates including:
- Node updates
- Edge modifications
- Domain changes
- Relationship tracking

Example connection:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/chat/client123');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

Message Format:
```typescript
interface WebSocketMessage {
    type: string;          // Message type (e.g. 'message', 'status', 'update')
    data: any;            // Message payload
    timestamp: string;    // ISO timestamp
    metadata?: {          // Optional metadata
        source?: string;
        domain?: string;
        importance?: number;
    }
}
```
""",
    version="0.1.0"
)

# Configure CORS - must be first middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-API-Key"],
    expose_headers=["*", "Content-Type", "Authorization", "X-API-Key"],
    max_age=3600,
)

# Include routers
app.include_router(root_router)           # Root endpoint (must be first)
app.include_router(nova_router)           # Nova-specific endpoints
app.include_router(chat_router)           # Chat and threads
app.include_router(graph_router)          # Knowledge graph operations
app.include_router(kg_router)             # Knowledge graph data
app.include_router(orchestration_router)  # Task orchestration
app.include_router(agent_router)          # Agent management
app.include_router(analytics_router)      # Analytics and insights
app.include_router(user_router)           # User management
app.include_router(ws_router)             # Real-time updates
app.include_router(tasks_router)          # Task management

# Add root routes directly to app
@app.options("/api/status")
async def status_options():
    """Handle CORS preflight requests for status endpoint."""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*,X-API-Key",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.get("/api/status")
async def get_status(request: Request):
    """Get server status."""
    api_key = request.headers.get("X-API-Key")
    if not api_key or not validate_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return JSONResponse(
        content={
            "status": "running",
            "version": "0.1.0",
            "timestamp": datetime.now().isoformat()
        },
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

async def verify_thread_manager():
    """Verify thread manager is working correctly."""
    try:
        logger.info("Verifying thread manager...")
        thread_manager = await get_thread_manager()
        
        # Create test thread with validation
        test_thread = await thread_manager.create_thread(
            title="Test Thread",
            domain="system",
            metadata={
                "system": True,
                "pinned": False,
                "description": "Startup test thread"
            },
            workspace="system"
        )
        logger.debug(f"Created test thread: {test_thread['id']}")
        
        # Verify thread exists and data is correct
        stored_thread = await thread_manager.get_thread(test_thread['id'])
        if not stored_thread:
            raise RuntimeError("Failed to retrieve test thread")
            
        # Verify metadata
        required_fields = ["type", "system", "pinned", "description"]
        for field in required_fields:
            if field not in stored_thread["metadata"]:
                raise RuntimeError(f"Missing required metadata field: {field}")
                
        # Verify thread type
        if stored_thread["metadata"]["type"] not in ["test", "system", "user", "agent", "chat", "task", "agent-team"]:
            raise RuntimeError("Invalid thread type")
            
        logger.info("Thread manager verification successful")
        
        # Clean up test thread
        await thread_manager.memory_system.semantic.run_query(
            """
            MATCH (t:Thread {id: $id})
            DETACH DELETE t
            """,
            {"id": test_thread["id"]}
        )
        logger.debug("Cleaned up test thread")
        return True
    except Exception as e:
        logger.error(f"Thread manager verification failed: {str(e)}")
        logger.error(traceback.format_exc())
        return False

async def initialize_system_threads():
    """Initialize system threads."""
    try:
        logger.info("Initializing system threads...")
        
        # Get thread manager but skip verification for now
        thread_manager = await get_thread_manager()
        logger.info("Got thread manager")
        
        # Just log status and continue - don't block startup
        try:
            # Try to get nova-team thread
            nova_team = await thread_manager.get_thread(thread_manager.NOVA_TEAM_UUID)
            if nova_team:
                logger.info("Nova team thread exists")
            else:
                logger.warning("Nova team thread not found")
                
            # Try to get nova thread
            nova = await thread_manager.get_thread(thread_manager.NOVA_UUID)
            if nova:
                logger.info("Nova thread exists")
            else:
                logger.warning("Nova thread not found")
                
        except Exception as e:
            logger.warning(f"Non-critical error checking threads: {str(e)}")
            
        logger.info("System threads check complete")
        return True
        
    except Exception as e:
        logger.error(f"Error in initialize_system_threads: {str(e)}")
        logger.error(traceback.format_exc())
        # Don't raise - allow startup to continue
        return False

# Add event handlers
@app.on_event("startup")
async def startup_event():
    """Handle application startup."""
    try:
        logger.info("Application starting up...")
        
        # Initialize services with non-blocking retries
        logger.warning("Initializing services...")
        
        async def initialize_services():
            """Initialize all required services."""
            try:
                # Check Neo4j connection first
                retry_count = 0
                max_retries = 10
                while retry_count < max_retries:
                    try:
                        uri = "bolt://localhost:7687"
                        driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
                        driver.verify_connectivity()
                        logger.info("Neo4j connection verified")
                        driver.close()
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            logger.error(f"Neo4j connection failed after {max_retries} retries")
                            break
                        if retry_count == 1:  # Only log on first attempt
                            logger.warning("Waiting for Neo4j...")
                        await asyncio.sleep(2)
                
                # Initialize memory system with retries
                retry_count = 0
                max_retries = 5
                while retry_count < max_retries:
                    try:
                        memory_system = await get_memory_system()
                        logger.info("Memory system initialized")
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            logger.error("Memory system initialization failed")
                            break
                        if retry_count == 1:  # Only log on first attempt
                            logger.warning("Waiting for memory system...")
                        await asyncio.sleep(2)
                
                # Initialize system threads
                try:
                    await initialize_system_threads()
                    logger.info("System threads initialized")
                except Exception as e:
                    logger.error("System threads initialization failed")
                    
            except Exception as e:
                logger.error("Service initialization error")
                
        # Start initialization in background
        asyncio.create_task(initialize_services())
        logger.info("Service initialization started in background")
        
        logger.info("Startup complete!")
    except Exception as e:
        logger.error("Error during startup:", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Handle application shutdown."""
    logger.info("Application shutting down...")

# Add error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Error: {exc}")
    return {
        "detail": str(exc),
        "type": type(exc).__name__,
        "path": request.url.path
    }
