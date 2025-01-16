"""FastAPI application configuration."""

from neo4j import GraphDatabase
from fastapi import FastAPI, APIRouter, Request, HTTPException
from .auth import validate_api_key, get_api_key
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from pathlib import Path
import sys
import traceback
import asyncio

from .api_docs import API_DESCRIPTION

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
    analytics_router,
    orchestration_router,
    chat_router
)
from .debug_websocket import debug_websocket_endpoint
from .agent_endpoints import agent_router
from .graph_endpoints import graph_router
from .knowledge_endpoints import kg_router
from .nova_endpoints import nova_router
from .tasks_endpoints import tasks_router
from .websocket_endpoints import ws_router
from .user_endpoints import user_router
from .channel_endpoints import channel_router
from .debug_endpoints import router as debug_router
from .dependencies import get_memory_system, get_thread_manager
from nia.core.feature_flags import FeatureFlags

# Create FastAPI app
app = FastAPI(
    title="Nova API",
    description=API_DESCRIPTION,
    version="0.1.0"
)

# Configure CORS - must be first middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*", "X-API-Key", "Content-Type", "Authorization"],
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
app.include_router(channel_router)        # Channel management
app.include_router(debug_router)          # Debug endpoints

# Add WebSocket endpoints
app.add_api_websocket_route("/ws/debug", debug_websocket_endpoint)

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
    api_key = get_api_key(request)  # Use helper from auth.py
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
            # Check if threads exist in Neo4j first
            try:
                # Check nova team thread
                nova_team_exists = await thread_manager.memory_system.semantic.run_query(
                    """
                    MATCH (t:Thread {id: $id}) RETURN COUNT(t) > 0 as exists
                    """,
                    {"id": thread_manager.NOVA_TEAM_UUID}
                )
                
                if not nova_team_exists or not nova_team_exists[0]["exists"]:
                    # Create nova team thread directly in Neo4j
                    await thread_manager.memory_system.semantic.run_query(
                        """
                        CREATE (t:Thread {
                            id: $id,
                            title: $title,
                            domain: $domain,
                            type: $type,
                            system: true,
                            pinned: true,
                            description: $description,
                            workspace: $workspace,
                            created_at: datetime()
                        })
                        """,
                        {
                            "id": thread_manager.NOVA_TEAM_UUID,
                            "title": "Nova Team",
                            "domain": "system",
                            "type": "agent-team",
                            "description": "Nova AI Team",
                            "workspace": "system"
                        }
                    )
                    logger.info("Created nova team thread")
                else:
                    logger.info("Nova team thread exists")
                    
                # Check nova thread
                nova_exists = await thread_manager.memory_system.semantic.run_query(
                    """
                    MATCH (t:Thread {id: $id}) RETURN COUNT(t) > 0 as exists
                    """,
                    {"id": thread_manager.NOVA_UUID}
                )
                
                if not nova_exists or not nova_exists[0]["exists"]:
                    # Create nova thread directly in Neo4j
                    await thread_manager.memory_system.semantic.run_query(
                        """
                        CREATE (t:Thread {
                            id: $id,
                            title: $title,
                            domain: $domain,
                            type: $type,
                            system: true,
                            pinned: true,
                            description: $description,
                            workspace: $workspace,
                            created_at: datetime()
                        })
                        """,
                        {
                            "id": thread_manager.NOVA_UUID,
                            "title": "Nova",
                            "domain": "system",
                            "type": "agent",
                            "description": "Nova AI Assistant",
                            "workspace": "system"
                        }
                    )
                    logger.info("Created nova thread")
                else:
                    logger.info("Nova thread exists")
                    
            except Exception as e:
                logger.warning(f"Error managing system threads: {str(e)}")
                
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
        
        # Initialize Redis for feature flags
        feature_flags = FeatureFlags()
        app.state.feature_flags = feature_flags
        
        # Enable debug flags for development
        await feature_flags.enable_debug('log_validation')
        await feature_flags.enable_debug('log_websocket')
        await feature_flags.enable_debug('log_storage')
        logger.info("Feature flags initialized")
        
        # Initialize services with non-blocking retries
        logger.warning("Initializing services...")
        
        # Initialize services with proper task handling
        init_task = asyncio.create_task(get_memory_system())
        try:
            memory_system = await init_task
            logger.info("Memory system initialized with Neo4j connection")
            
            # Initialize system threads with timeout
            thread_task = asyncio.create_task(initialize_system_threads())
            try:
                await asyncio.wait_for(thread_task, timeout=10.0)
                logger.info("System threads initialized")
            except asyncio.TimeoutError:
                logger.error("System threads initialization timed out")
            except Exception as e:
                logger.error(f"System threads initialization failed: {str(e)}")
        except Exception as e:
            logger.error(f"Service initialization error: {str(e)}")
        
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
