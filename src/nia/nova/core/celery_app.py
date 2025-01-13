"""Celery configuration and tasks for Nova."""

from celery import Celery
from typing import Dict, Any, Optional, List
import json
import uuid
import asyncio
import logging
import traceback
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from fastapi import HTTPException as ServiceError
from .thread_manager import ThreadManager

# Configure minimal logging with rate limiting
class RateLimitedLogger:
    def __init__(self, name: str, rate_limit: float = 1.0):  # Increased rate limit to 1 second
        self.logger = logging.getLogger(name)
        self.rate_limit = rate_limit
        self.last_log = {}
        
        # Configure basic logging
        LOGS_DIR = Path("logs/celery")
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / f"celery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # File handler with rotation for all logs
        handler = RotatingFileHandler(
            log_file,
            maxBytes=1024*1024,  # 1MB
            backupCount=3,
            encoding='utf-8'
        )
        handler.setLevel(logging.INFO)  # Changed to INFO for more detailed file logging
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Configure logger - Set base level to INFO for file logging
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        self.logger.propagate = False  # Prevent duplicate logging
    
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

logger = RateLimitedLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'nova',
    broker='redis://localhost:6379/0',  # Use localhost since we're running outside Docker
    backend='redis://localhost:6379/1'  # Use localhost since we're running outside Docker
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_always_eager=False,
    task_eager_propagates=True,
    task_default_retry_delay=5,  # 5 seconds between retries
    task_max_retries=3,  # Maximum of 3 retries
)

# Flag to prevent recursive store_experience calls
_storing_experience = False

def run_async(coro):
    """Run an async function synchronously."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def get_sync_memory_system():
    """Get memory system instance synchronously."""
    from .dependencies import get_memory_system
    try:
        memory_system = run_async(get_memory_system())
        if not memory_system:
            raise RuntimeError("Memory system not available")
        return memory_system
    except Exception as e:
        logger.error("Memory system error")  # Simplified error message
        raise

def get_sync_agent_store():
    """Get agent store instance synchronously."""
    from .dependencies import get_agent_store
    try:
        agent_store = run_async(get_agent_store())
        if not agent_store:
            raise RuntimeError("Agent store not available")
        return agent_store
    except Exception as e:
        logger.error("Agent store error")  # Simplified error message
        raise

@celery_app.task(bind=True, name='nova.create_thread')
def create_thread(self, title: str, domain: str = "general", metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a new thread."""
    try:
        thread_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Validate metadata
        if metadata is None:
            metadata = {}
        
        # Ensure required metadata fields with defaults
        required_metadata = {
            "type": "user",  # Default type
            "system": False,
            "pinned": False,
            "description": ""
        }
        
        # Update with provided metadata
        for key, default in required_metadata.items():
            if key not in metadata:
                metadata[key] = default
        
        # Initialize memory system and thread manager
        memory_system = get_sync_memory_system()
        thread_manager = ThreadManager(memory_system)

        # Create thread content first
        thread_content = {
            "id": thread_id,
            "name": title,  # Ensure name is included
            "domain": domain,
            "messages": [],
            "createdAt": now,
            "updatedAt": now,
            "workspace": "personal",
            "participants": [],
            "metadata": metadata
        }

        # Store thread with recursion prevention
        global _storing_experience
        if not _storing_experience:
            try:
                _storing_experience = True
                run_async(thread_manager._store_thread(thread_content))
            finally:
                _storing_experience = False
        
        # Verify storage
        stored_thread = run_async(thread_manager.get_thread(thread_id))
        if not stored_thread:
            raise ServiceError(f"Failed to verify thread creation for {thread_id}")
        
        return stored_thread
    except Exception as e:
        logger.error("Thread creation error")  # Simplified error message
        raise

@celery_app.task(bind=True, name='nova.add_agent_to_thread')
def add_agent_to_thread(
    self,
    thread_id: str,
    agent_type: str,
    workspace: str = "personal",
    domain: Optional[str] = None
) -> Dict[str, Any]:
    """Add an agent to a thread."""
    try:
        memory_system = get_sync_memory_system()
        agent_store = get_sync_agent_store()
        thread_manager = ThreadManager(memory_system)
        
        # Get thread first to ensure it exists
        thread = run_async(thread_manager.get_thread(thread_id))
        if not thread:
            raise ServiceError(f"Thread {thread_id} not found")
        
        # Create agent
        agent = {
            "id": f"{agent_type}-{str(uuid.uuid4())[:8]}",
            "name": f"{agent_type.capitalize()}Agent",
            "type": agent_type,
            "workspace": workspace,
            "domain": domain,
            "status": "active",
            "metadata": {
                "capabilities": [f"{agent_type}_analysis"],
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Store agent
        run_async(agent_store.store_agent(agent))
        
        # Add agent to thread participants
        if "participants" not in thread["metadata"]:
            thread["metadata"]["participants"] = []
        thread["metadata"]["participants"].append(agent)
        
        # Update thread with recursion prevention
        global _storing_experience
        if not _storing_experience:
            try:
                _storing_experience = True
                run_async(thread_manager.update_thread(thread))
            finally:
                _storing_experience = False
        
        return agent
    except Exception as e:
        logger.error("Add agent error")  # Simplified error message
        raise

@celery_app.task(bind=True, name='nova.store_chat_message')
def store_chat_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store a chat message."""
    try:
        memory_system = get_sync_memory_system()
        thread_manager = ThreadManager(memory_system)
        
        thread_id = data.get("thread_id")
        if not thread_id:
            raise ServiceError("Missing thread_id in chat message")
            
        # Get thread first to ensure it exists
        thread = run_async(thread_manager.get_thread(thread_id))
        if not thread:
            raise ServiceError(f"Thread {thread_id} not found")
            
        # Add message to thread
        if "messages" not in thread:
            thread["messages"] = []
        thread["messages"].append({
            "id": str(uuid.uuid4()),
            "content": data.get("content"),
            "sender": data.get("sender"),
            "timestamp": datetime.now().isoformat(),
            "metadata": data.get("metadata", {})
        })
        
        # Update thread with recursion prevention
        global _storing_experience
        if not _storing_experience:
            try:
                _storing_experience = True
                run_async(thread_manager.update_thread(thread))
            finally:
                _storing_experience = False
        return thread
    except Exception as e:
        logger.error("Store message error")  # Simplified error message
        raise

@celery_app.task(bind=True, name='nova.store_task_update')
def store_task_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store a task update."""
    try:
        memory_system = get_sync_memory_system()
        thread_manager = ThreadManager(memory_system)
        
        thread_id = data.get("thread_id")
        if not thread_id:
            raise ServiceError("Missing thread_id in task update")
            
        # Get thread first to ensure it exists
        thread = run_async(thread_manager.get_thread(thread_id))
        if not thread:
            raise ServiceError(f"Thread {thread_id} not found")
            
        # Update task metadata
        if "metadata" not in thread:
            thread["metadata"] = {}
        if "tasks" not in thread["metadata"]:
            thread["metadata"]["tasks"] = []
            
        task_id = data.get("task_id")
        if task_id:
            # Update existing task
            for task in thread["metadata"]["tasks"]:
                if task["id"] == task_id:
                    task.update(data)
                    break
            else:
                # Task not found, create new
                thread["metadata"]["tasks"].append({
                    "id": task_id,
                    "status": data.get("status", "pending"),
                    "title": data.get("title"),
                    "description": data.get("description"),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })
        
        # Update thread with recursion prevention
        global _storing_experience
        if not _storing_experience:
            try:
                _storing_experience = True
                run_async(thread_manager.update_thread(thread))
            finally:
                _storing_experience = False
        return thread
    except Exception as e:
        logger.error("Task update error")  # Simplified error message
        raise

@celery_app.task(bind=True, name='nova.store_agent_status')
def store_agent_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store an agent status update."""
    try:
        agent_store = get_sync_agent_store()
        
        agent_id = data.get("agent_id")
        if not agent_id:
            raise ServiceError("Missing agent_id in status update")
            
        # Get agent first to ensure it exists
        agent = run_async(agent_store.get_agent(agent_id))
        if not agent:
            raise ServiceError(f"Agent {agent_id} not found")
            
        # Update agent status
        agent["status"] = data.get("status", agent["status"])
        agent["updated_at"] = datetime.now().isoformat()
        if "metadata" not in agent:
            agent["metadata"] = {}
        agent["metadata"].update(data.get("metadata", {}))
        
        # Store updated agent
        run_async(agent_store.update_agent(agent))
        return agent
    except Exception as e:
        logger.error("Status update error")  # Simplified error message
        raise

@celery_app.task(bind=True, name='nova.store_graph_update')
def store_graph_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store a knowledge graph update."""
    try:
        memory_system = get_sync_memory_system()
        
        # Extract graph data
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        
        # Store nodes and edges
        for node in nodes:
            run_async(memory_system.store_node(node))
        for edge in edges:
            run_async(memory_system.store_edge(edge))
            
        return data
    except Exception as e:
        logger.error("Graph update error")  # Simplified error message
        raise

@celery_app.task(bind=True, name='nova.add_agent_team_to_thread')
def add_agent_team_to_thread(
    self,
    thread_id: str,
    agent_specs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Add a team of agents to a thread."""
    try:
        memory_system = get_sync_memory_system()
        agent_store = get_sync_agent_store()
        thread_manager = ThreadManager(memory_system)
        
        # Get thread first to ensure it exists
        thread = run_async(thread_manager.get_thread(thread_id))
        if not thread:
            raise ServiceError(f"Thread {thread_id} not found")
        
        # Create each agent
        agents = []
        for agent_spec in agent_specs:
            agent_type = agent_spec.get("type")
            workspace = agent_spec.get("workspace", "personal")
            domain = agent_spec.get("domain")
            
            agent = {
                "id": f"{agent_type}-{str(uuid.uuid4())[:8]}",
                "name": f"{agent_type.capitalize()}Agent",
                "type": agent_type,
                "workspace": workspace,
                "domain": domain,
                "status": "active",
                "metadata": {
                    "capabilities": [f"{agent_type}_analysis"],
                    "created_at": datetime.now().isoformat()
                }
            }
            
            # Store agent
            run_async(agent_store.store_agent(agent))
            agents.append(agent)
        
        # Add agents to thread participants
        if "participants" not in thread["metadata"]:
            thread["metadata"]["participants"] = []
        thread["metadata"]["participants"].extend(agents)
        
        # Update thread
        run_async(thread_manager.update_thread(thread))
        return agents
    except Exception as e:
        logger.error("Add team error")  # Simplified error message
        raise
