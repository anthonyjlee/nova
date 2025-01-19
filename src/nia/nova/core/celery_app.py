"""Celery configuration and tasks for Nova."""

from celery import Celery
from typing import Dict, Any, Optional, cast
from nia.memory.two_layer import TwoLayerMemorySystem
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from logging.handlers import RotatingFileHandler
from nia.core.types.memory_types import EpisodicMemory

from nia.nova.core.websocket import websocket_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'nova',
    broker='redis://localhost:6379/0',  # Use db 0 for message broker
    backend='redis://localhost:6379/1'   # Use db 1 for results backend
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
    task_max_retries=3  # Maximum of 3 retries
)

def run_async(coro):
    """Run an async function synchronously."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@celery_app.task(name='nova.check_status')
def check_status() -> Dict[str, Any]:
    """Check connection status for all services."""
    return {
        'celery': {
            'active': True,
            'workers': [{
                'name': 'worker1',
                'status': 'active'
            }],
            'timestamp': datetime.now().isoformat()
        }
    }

@celery_app.task(bind=True, name='nova.store_chat_message')
def store_chat_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store and broadcast a chat message."""
    try:
        # Get memory system
        from .dependencies import get_memory_system
        memory_system = cast(Optional[TwoLayerMemorySystem], run_async(get_memory_system()))
        
        # Check memory system
        if not memory_system:
            logger.error("Memory system not initialized")
            return {"error": "Memory system not initialized"}
            
        # Create message
        message = {
            "type": "chat_message",
            "content": data.get("content", ""),  # Default to empty string
            "sender_id": data.get("sender_id"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in memory if system is initialized
        if not memory_system.episodic or not memory_system.episodic.store:
            logger.error("Memory system episodic layer not initialized")
            return {"error": "Memory system episodic layer not initialized"}
            
        now = datetime.now(timezone.utc)
        run_async(memory_system.episodic.store_memory(EpisodicMemory(
            type="chat_message",
            content=str(message["content"]),  # Ensure string content
            timestamp=now,
            metadata={
                "sender_id": message["sender_id"],
                "timestamp": now.isoformat()
            }
        )))
        
        # Broadcast update
        client_id = data.get("client_id")
        channel = data.get("channel")
        if client_id:
            run_async(websocket_manager.broadcast_chat_message(
                message,
                channel=channel
            ))
        return message
    except Exception as e:
        logger.error(f"Store message error: {e}")
        return {"error": str(e)}

@celery_app.task(bind=True, name='nova.store_task_update')
def store_task_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store and broadcast a task update."""
    try:
        # Get memory system
        from .dependencies import get_memory_system
        memory_system = cast(Optional[TwoLayerMemorySystem], run_async(get_memory_system()))
        
        # Check memory system
        if not memory_system:
            logger.error("Memory system not initialized")
            return {"error": "Memory system not initialized"}
            
        # Create update
        update = {
            "type": "task_update",
            "task_id": data.get("task_id"),
            "status": data.get("status", "unknown"),  # Default status
            "timestamp": datetime.now().isoformat(),
            "metadata": data.get("metadata", {})
        }
        
        # Store in memory if system is initialized
        if not memory_system.episodic or not memory_system.episodic.store:
            logger.error("Memory system episodic layer not initialized")
            return {"error": "Memory system episodic layer not initialized"}
            
        now = datetime.now(timezone.utc)
        run_async(memory_system.episodic.store_memory(EpisodicMemory(
            type="task_update",
            content=str(update["status"]),  # Use status as content
            timestamp=now,
            metadata={
                "task_id": update["task_id"],
                "timestamp": now.isoformat()
            }
        )))
        
        # Broadcast update
        client_id = data.get("client_id")
        channel = data.get("channel")
        if client_id:
            run_async(websocket_manager.broadcast_task_update(
                update,
                channel=channel
            ))
        return update
    except Exception as e:
        logger.error(f"Task update error: {e}")
        return {"error": str(e)}

@celery_app.task(bind=True, name='nova.store_agent_status')
def store_agent_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store and broadcast an agent status update."""
    try:
        # Get memory system
        from .dependencies import get_memory_system
        memory_system = cast(Optional[TwoLayerMemorySystem], run_async(get_memory_system()))
        
        # Check memory system
        if not memory_system:
            logger.error("Memory system not initialized")
            return {"error": "Memory system not initialized"}
            
        # Create status
        status = {
            "type": "agent_status",
            "agent_id": data.get("agent_id"),
            "status": data.get("status", "unknown"),  # Default status
            "timestamp": datetime.now().isoformat(),
            "metadata": data.get("metadata", {})
        }
        
        # Store in memory if system is initialized
        if not memory_system.episodic or not memory_system.episodic.store:
            logger.error("Memory system episodic layer not initialized")
            return {"error": "Memory system episodic layer not initialized"}
            
        now = datetime.now(timezone.utc)
        run_async(memory_system.episodic.store_memory(EpisodicMemory(
            type="agent_status",
            content=str(status["status"]),  # Use status as content
            timestamp=now,
            metadata={
                "agent_id": status["agent_id"],
                "timestamp": now.isoformat()
            }
        )))
        
        # Broadcast update
        client_id = data.get("client_id")
        channel = data.get("channel")
        if client_id:
            run_async(websocket_manager.broadcast_agent_status(
                status,
                channel=channel
            ))
        return status
    except Exception as e:
        logger.error(f"Agent status error: {e}")
        return {"error": str(e)}

@celery_app.task(bind=True, name='nova.store_graph_update')
def store_graph_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store and broadcast a graph update."""
    try:
        # Get memory system
        from .dependencies import get_memory_system
        memory_system = cast(Optional[TwoLayerMemorySystem], run_async(get_memory_system()))
        
        # Check memory system
        if not memory_system:
            logger.error("Memory system not initialized")
            return {"error": "Memory system not initialized"}
            
        # Create update
        update = {
            "type": "graph_update",
            "nodes": data.get("nodes", []),
            "edges": data.get("edges", []),
            "timestamp": datetime.now().isoformat(),
            "metadata": data.get("metadata", {})
        }
        
        # Store in memory if system is initialized
        if not memory_system.episodic or not memory_system.episodic.store:
            logger.error("Memory system episodic layer not initialized")
            return {"error": "Memory system episodic layer not initialized"}
            
        now = datetime.now(timezone.utc)
        run_async(memory_system.episodic.store_memory(EpisodicMemory(
            type="graph_update",
            content=str(len(update["nodes"])) + " nodes, " + str(len(update["edges"])) + " edges",
            timestamp=now,
            metadata={
                "graph_id": data.get("graph_id"),
                "timestamp": now.isoformat()
            }
        )))
        
        # Broadcast update
        client_id = data.get("client_id")
        channel = data.get("channel")
        if client_id:
            run_async(websocket_manager.broadcast_graph_update(
                update,
                channel=channel
            ))
        return update
    except Exception as e:
        logger.error(f"Graph update error: {e}")
        return {"error": str(e)}

# Register startup handler
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Check service status every 30 seconds
    sender.add_periodic_task(30.0, check_status.s(), name='check_service_status')
