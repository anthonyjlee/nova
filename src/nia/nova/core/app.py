"""FastAPI application configuration."""

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
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
file_handler = logging.FileHandler('fastapi.log')
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
        
        # Verify thread manager first
        if not await verify_thread_manager():
            raise RuntimeError("Thread manager verification failed")
            
        thread_manager = await get_thread_manager()
        
        # Initialize nova-team thread
        nova_team = await thread_manager.get_thread("nova-team")
        logger.info(f"Nova team thread initialized: {nova_team['id']}")
        
        # Initialize nova thread
        nova = await thread_manager.get_thread("nova")
        logger.info(f"Nova thread initialized: {nova['id']}")
        
        # Verify both threads exist and have correct metadata
        threads = await thread_manager.list_threads({
            "system": True,
            "type": "agent-team"
        })
        
        if len(threads) < 2:
            raise RuntimeError("System threads not properly initialized")
            
        for thread in threads:
            if not thread["metadata"].get("system"):
                raise RuntimeError(f"Thread {thread['id']} missing system flag")
            if thread["metadata"].get("type") != "agent-team":
                raise RuntimeError(f"Thread {thread['id']} has incorrect type")
                
        logger.info("System threads initialized and verified successfully")
    except Exception as e:
        logger.error(f"Error initializing system threads: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Add event handlers
@app.on_event("startup")
async def startup_event():
    """Handle application startup."""
    try:
        logger.info("Application starting up...")
        
        # Initialize and verify memory system
        logger.info("Initializing memory system...")
        
        # Set longer timeout for startup
        timeout = 30
        start_time = datetime.now()
        
        # Check Neo4j connection first
        logger.debug("Checking Neo4j connection...")
        from neo4j import GraphDatabase
        from neo4j.exceptions import ServiceUnavailable
        try:
            uri = "bolt://localhost:7687"
            driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
            driver.verify_connectivity()
            logger.debug("Neo4j connection verified")
        except ServiceUnavailable as e:
            logger.error(f"Neo4j is not available: {str(e)}")
            logger.error("Make sure Neo4j is running and accessible")
            raise RuntimeError("Neo4j connection failed") from e
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise RuntimeError("Neo4j connection failed") from e
        finally:
            if 'driver' in locals():
                driver.close()
        
        # Initialize memory system with retries
        while True:
            try:
                # Initialize memory system
                memory_system = await get_memory_system()
                logger.debug("Got memory system instance")
                
                await memory_system.initialize()
                logger.debug("Memory system initialization completed")
                
                # Test memory system
                test_result = await memory_system.query_episodic({
                    "content": {},
                    "filter": {"must": []},
                    "limit": 1
                })
                logger.debug("Memory system test query successful")
                break
                
            except Exception as e:
                if (datetime.now() - start_time).seconds > timeout:
                    raise RuntimeError(f"Memory system initialization timeout after {timeout}s")
                logger.warning(f"Memory system not ready, retrying... Error: {str(e)}")
                await asyncio.sleep(1)
        
        # Verify memory system is ready
        if not hasattr(memory_system, 'episodic') or not hasattr(memory_system.episodic, 'store'):
            raise RuntimeError("Memory system not properly initialized")
        logger.info("Memory system initialized and verified")
        
        # Initialize system threads
        logger.info("Initializing system threads...")
        await initialize_system_threads()
        logger.info("System threads initialized")
        
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
