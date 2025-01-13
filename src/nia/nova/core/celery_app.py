"""Celery configuration and tasks for Nova."""

from celery import Celery
from typing import Dict, Any, Optional, List
import json
import uuid
import asyncio
import logging
import traceback
from datetime import datetime
from fastapi import HTTPException as ServiceError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize Celery app
celery_app = Celery(
    'nova',
    broker='redis://redis:6379/0',  # Use Docker service name
    backend='redis://redis:6379/1'  # Use Docker service name
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
        from .thread_manager import ThreadManager
        
        logger.debug(f"Creating thread: {title} (domain: {domain})")
        memory_system = get_sync_memory_system()
        thread_manager = ThreadManager(memory_system)
        
        thread_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        thread = {
            "id": thread_id,
            "title": title,
            "domain": domain,
            "messages": [],
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {}
        }
        
        # Store thread
        thread_manager._store_thread(thread)
        
        # Update task state
        self.update_state(state='STORED', meta={'thread_id': thread_id})
        
        # Verify storage
        stored_thread = thread_manager.get_thread(thread_id)
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
        from .thread_manager import ThreadManager
        
        logger.debug(f"Adding agent to thread {thread_id}: {agent_type}")
        memory_system = get_sync_memory_system()
        agent_store = get_sync_agent_store()
        thread_manager = ThreadManager(memory_system)
        
        # Get thread first to ensure it exists
        thread = thread_manager.get_thread(thread_id)
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
        agent_store.store_agent(agent)
        self.update_state(state='AGENT_STORED', meta={'agent_id': agent['id']})
        
        # Add agent to thread participants
        if "participants" not in thread["metadata"]:
            thread["metadata"]["participants"] = []
        thread["metadata"]["participants"].append(agent)
        
        # Update thread
        thread_manager.update_thread(thread)
        self.update_state(state='THREAD_UPDATED')
        
        logger.debug(f"Successfully added agent {agent['id']} to thread {thread_id}")
        return agent
    except Exception as e:
        logger.error(f"Error adding agent to thread: {str(e)}")
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
        from .thread_manager import ThreadManager
        
        logger.debug(f"Adding agent team to thread {thread_id}")
        memory_system = get_sync_memory_system()
        agent_store = get_sync_agent_store()
        thread_manager = ThreadManager(memory_system)
        
        # Get thread first to ensure it exists
        thread = thread_manager.get_thread(thread_id)
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
            agent_store.store_agent(agent)
            agents.append(agent)
            self.update_state(state='AGENT_STORED', meta={'agent_id': agent['id']})
        
        # Add agents to thread participants
        if "participants" not in thread["metadata"]:
            thread["metadata"]["participants"] = []
        thread["metadata"]["participants"].extend(agents)
        
        # Update thread
        thread_manager.update_thread(thread)
        self.update_state(state='THREAD_UPDATED')
        
        logger.debug(f"Successfully added {len(agents)} agents to thread {thread_id}")
        return agents
    except Exception as e:
        logger.error(f"Error adding agent team to thread: {str(e)}")
        logger.error(traceback.format_exc())
        raise
