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

# Configure logging with consistent format
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Prevent propagation to root logger
logger.propagate = False

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs/celery")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Create session-specific log file
session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
session_log = LOGS_DIR / f"celery_{session_id}.json"

class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno,
            "thread_id": record.thread,
            "process_id": record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_entry)

# Configure logging with RotatingFileHandler
handler = RotatingFileHandler(
    session_log,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)

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
)

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
            logger.error("Failed to get memory system")
            raise RuntimeError("Memory system not available")
        return memory_system
    except Exception as e:
        logger.error(f"Error getting memory system: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def get_sync_agent_store():
    """Get agent store instance synchronously."""
    from .dependencies import get_agent_store
    try:
        agent_store = run_async(get_agent_store())
        if not agent_store:
            logger.error("Failed to get agent store")
            raise RuntimeError("Agent store not available")
        return agent_store
    except Exception as e:
        logger.error(f"Error getting agent store: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@celery_app.task(bind=True, name='nova.create_thread')
def create_thread(self, title: str, domain: str = "general", metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a new thread."""
    try:
        logger.debug(f"Creating thread: {title} (domain: {domain})")
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

        # Store thread directly
        run_async(thread_manager._store_thread(thread_content))
        
        # Update task state
        self.update_state(state='STORED', meta={'thread_id': thread_id})
        
        # Verify storage
        stored_thread = run_async(thread_manager.get_thread(thread_id))
        if not stored_thread:
            raise ServiceError(f"Failed to verify thread creation for {thread_id}")
        
        logger.debug(f"Successfully created thread {thread_id}")
        return stored_thread
    except Exception as e:
        logger.error(f"Error creating thread: {str(e)}")
        logger.error(traceback.format_exc())
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
        logger.debug(f"Adding agent to thread {thread_id}: {agent_type}")
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
        self.update_state(state='AGENT_STORED', meta={'agent_id': agent['id']})
        
        # Add agent to thread participants
        if "participants" not in thread["metadata"]:
            thread["metadata"]["participants"] = []
        thread["metadata"]["participants"].append(agent)
        
        # Update thread
        run_async(thread_manager.update_thread(thread))
        self.update_state(state='THREAD_UPDATED')
        
        logger.debug(f"Successfully added agent {agent['id']} to thread {thread_id}")
        return agent
    except Exception as e:
        logger.error(f"Error adding agent to thread: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@celery_app.task(bind=True, name='nova.store_chat_message')
def store_chat_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store a chat message."""
    try:
        logger.debug(f"Storing chat message: {data}")
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
        
        # Update thread
        run_async(thread_manager.update_thread(thread))
        self.update_state(state='MESSAGE_STORED')
        
        logger.debug(f"Successfully stored message in thread {thread_id}")
        return thread
    except Exception as e:
        logger.error(f"Error storing chat message: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@celery_app.task(bind=True, name='nova.store_task_update')
def store_task_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store a task update."""
    try:
        logger.debug(f"Storing task update: {data}")
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
        
        # Update thread
        run_async(thread_manager.update_thread(thread))
        self.update_state(state='TASK_UPDATED')
        
        logger.debug(f"Successfully updated task in thread {thread_id}")
        return thread
    except Exception as e:
        logger.error(f"Error storing task update: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@celery_app.task(bind=True, name='nova.store_agent_status')
def store_agent_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store an agent status update."""
    try:
        logger.debug(f"Storing agent status: {data}")
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
        self.update_state(state='STATUS_UPDATED')
        
        logger.debug(f"Successfully updated agent {agent_id} status")
        return agent
    except Exception as e:
        logger.error(f"Error storing agent status: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@celery_app.task(bind=True, name='nova.store_graph_update')
def store_graph_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store a knowledge graph update."""
    try:
        logger.debug(f"Storing graph update: {data}")
        memory_system = get_sync_memory_system()
        
        # Extract graph data
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        
        # Store nodes and edges
        for node in nodes:
            run_async(memory_system.store_node(node))
            self.update_state(state='NODE_STORED', meta={'node_id': node.get('id')})
            
        for edge in edges:
            run_async(memory_system.store_edge(edge))
            self.update_state(state='EDGE_STORED', meta={'edge_id': edge.get('id')})
            
        logger.debug(f"Successfully stored graph update with {len(nodes)} nodes and {len(edges)} edges")
        return data
    except Exception as e:
        logger.error(f"Error storing graph update: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@celery_app.task(bind=True, name='nova.add_agent_team_to_thread')
def add_agent_team_to_thread(
    self,
    thread_id: str,
    agent_specs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Add a team of agents to a thread."""
    try:
        logger.debug(f"Adding agent team to thread {thread_id}")
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
            self.update_state(state='AGENT_STORED', meta={'agent_id': agent['id']})
        
        # Add agents to thread participants
        if "participants" not in thread["metadata"]:
            thread["metadata"]["participants"] = []
        thread["metadata"]["participants"].extend(agents)
        
        # Update thread
        run_async(thread_manager.update_thread(thread))
        self.update_state(state='THREAD_UPDATED')
        
        logger.debug(f"Successfully added {len(agents)} agents to thread {thread_id}")
        return agents
    except Exception as e:
        logger.error(f"Error adding agent team to thread: {str(e)}")
        logger.error(traceback.format_exc())
        raise
