"""FastAPI application configuration."""

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from pathlib import Path
import sys
import traceback
import asyncio

# Enable detailed error logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)

# Add file handler for persistent logging
logs_dir = Path("logs/fastapi")
logs_dir.mkdir(parents=True, exist_ok=True)
log_file = logs_dir / f"fastapi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

def log_exception(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = log_exception

from .endpoints import (
    root_router,
    graph_router,
    agent_router,
    user_router,
    analytics_router,
    orchestration_router,
    chat_router
)
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
    allow_headers=["*"],
    expose_headers=["*", "Content-Type", "Authorization"],
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
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.get("/api/status")
async def get_status():
    """Get server status."""
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
                "type": "test",
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
            nova_team = await thread_manager.get_thread("nova-team")
            if nova_team:
                logger.info("Nova team thread exists")
            else:
                logger.warning("Nova team thread not found")
                
            # Try to get nova thread
            nova = await thread_manager.get_thread("nova")
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
        logger.info("Initializing services...")
        
        async def initialize_services():
            """Initialize all required services."""
            try:
                # Check Neo4j connection first
                logger.debug("Checking Neo4j connection...")
                from neo4j import GraphDatabase
                from neo4j.exceptions import ServiceUnavailable
                
                retry_count = 0
                max_retries = 10
                while retry_count < max_retries:
                    try:
                        uri = "bolt://neo4j:7687"  # Use Docker service name
                        driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
                        driver.verify_connectivity()
                        logger.debug("Neo4j connection verified")
                        driver.close()
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            logger.warning(f"Neo4j connection failed after {max_retries} retries: {str(e)}")
                            # Continue without Neo4j
                            break
                        logger.warning(f"Neo4j connection attempt {retry_count} failed: {str(e)}")
                        await asyncio.sleep(2)
                
                # Initialize memory system with retries
                logger.debug("Initializing memory system...")
                retry_count = 0
                max_retries = 5
                while retry_count < max_retries:
                    try:
                        memory_system = await get_memory_system()
                        logger.debug("Memory system initialization complete")
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            logger.warning(f"Memory system initialization failed after {max_retries} retries: {str(e)}")
                            # Continue without full initialization
                            break
                        logger.warning(f"Memory system initialization attempt {retry_count} failed: {str(e)}")
                        await asyncio.sleep(1)
                
                # Initialize system threads without blocking
                logger.debug("Initializing system threads...")
                try:
                    await initialize_system_threads()
                    logger.debug("System threads initialized")
                except Exception as e:
                    logger.warning(f"System threads initialization failed: {str(e)}")
                    # Continue without system threads
                    
            except Exception as e:
                logger.error(f"Service initialization error: {str(e)}")
                # Don't raise - allow startup to continue
                
        # Start initialization in background
        asyncio.create_task(initialize_services())
        logger.info("Service initialization started in background")
        
        # Log router status
        logger.info("Checking router status...")
        for router in [
            root_router, nova_router, chat_router, graph_router,
            orchestration_router, agent_router, analytics_router,
            user_router, ws_router, tasks_router
        ]:
            logger.info(f"Router {router.prefix} initialized with {len(router.routes)} routes")
        
        # Log middleware status
        logger.info("Checking middleware status...")
        for middleware in app.user_middleware:
            logger.info(f"Middleware {middleware.cls.__name__} initialized")
        
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
    logger.error(f"Global error handler caught: {exc}", exc_info=True)
    return {
        "detail": str(exc),
        "type": type(exc).__name__,
        "path": request.url.path
    }
