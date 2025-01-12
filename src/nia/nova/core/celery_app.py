"""Celery configuration and tasks for Nova."""

from celery import Celery
from typing import Dict, Any, Optional
import json
from datetime import datetime

# Initialize Celery app
celery_app = Celery(
    'nova',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
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

@celery_app.task(bind=True, name='nova.create_thread')
def create_thread(self, title: str, domain: str = "general", metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a new thread."""
    from .thread_manager import ThreadManager
    from .dependencies import get_memory_system
    
    memory_system = get_memory_system()
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
    
    return stored_thread

@celery_app.task(bind=True, name='nova.add_agent_to_thread')
def add_agent_to_thread(
    self,
    thread_id: str,
    agent_type: str,
    workspace: str = "personal",
    domain: Optional[str] = None
) -> Dict[str, Any]:
    """Add an agent to a thread."""
    from .thread_manager import ThreadManager
    from .dependencies import get_memory_system, get_agent_store
    
    memory_system = get_memory_system()
    agent_store = get_agent_store()
    thread_manager = ThreadManager(memory_system)
    
    # Get thread first to ensure it exists
    thread = thread_manager.get_thread(thread_id)
    
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
    
    return agent

@celery_app.task(bind=True, name='nova.add_agent_team_to_thread')
def add_agent_team_to_thread(
    self,
    thread_id: str,
    agent_specs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Add a team of agents to a thread."""
    from .thread_manager import ThreadManager
    from .dependencies import get_memory_system, get_agent_store
    
    memory_system = get_memory_system()
    agent_store = get_agent_store()
    thread_manager = ThreadManager(memory_system)
    
    # Get thread first to ensure it exists
    thread = thread_manager.get_thread(thread_id)
    
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
    
    return agents
