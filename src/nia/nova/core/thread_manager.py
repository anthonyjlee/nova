"""Thread management module for Nova's chat system."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Literal
from pathlib import Path
import asyncio
import uuid
import json
import logging
import traceback
from logging.handlers import RotatingFileHandler
from pydantic import BaseModel, Field

from nia.core.types.memory_types import Memory, MemoryType, EpisodicMemory
from nia.nova.memory.two_layer import TwoLayerMemorySystem
from .error_handling import ResourceNotFoundError, ServiceError
from qdrant_client.http import models

import os

# Pydantic models for validation
class BaseMessage(BaseModel):
    """Base message model for all WebSocket messages."""
    type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    client_id: str
    channel: Optional[str] = None

class ThreadParticipant(BaseModel):
    """Model for thread participants (agents or users)."""
    id: str
    name: str
    type: str
    workspace: str = "personal"
    domain: str = "general"
    status: str = "active"
    metadata_type: str
    metadata_capabilities: List[str]
    metadata_created_at: datetime

class ThreadMetadata(BaseModel):
    """Model for thread metadata."""
    type: Literal["test", "system", "user", "agent", "chat", "task", "agent-team"]
    system: bool = False
    pinned: bool = False
    description: str = ""

class Thread(BaseModel):
    """Model for thread data."""
    id: str
    name: str
    domain: str = "general"
    messages: List[Dict[str, Any]] = []
    createdAt: datetime
    updatedAt: datetime
    workspace: str = "personal"
    participants: List[ThreadParticipant] = []
    metadata: ThreadMetadata

class ThreadMessage(BaseMessage):
    """Model for thread messages."""
    type: Literal["thread_message"]
    data: Dict[str, Any] = Field(
        ...,
        description="Message content and metadata"
    )
    thread_id: str
    sender_id: str

class ThreadUpdate(BaseMessage):
    """Model for thread update notifications."""
    type: Literal["thread_update"]
    data: Thread
    update_type: Literal["created", "updated", "deleted"]

class AgentStatus(BaseMessage):
    """Model for agent status updates."""
    type: Literal["agent_status"]
    data: Dict[str, Any] = Field(
        ...,
        description="Agent status information"
    )
    agent_id: str
    status: str

class ThreadValidation(BaseModel):
    """Model for thread validation results."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []

# Configure logging with file-only output and rotation
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Reduce logging level
logger.propagate = False  # Prevent console output

# Create logs directory if it doesn't exist
LOGS_DIR = Path("scripts/logs/fastapi")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Create session-specific log file with smaller size and more backups
session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
session_log = LOGS_DIR / f"thread_manager_{session_id}.json"

class JsonFormatter(logging.Formatter):
    """Format log records as JSON with minimal info."""
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        }
        
        # Only add exception info for errors
        if record.exc_info and record.levelno >= logging.ERROR:
            log_entry["error"] = str(record.exc_info[1])
            
        return json.dumps(log_entry)

# Configure logging with smaller file size and more backups
handler = RotatingFileHandler(
    session_log,
    maxBytes=1*1024*1024,  # 1MB per file
    backupCount=10,  # Keep more backup files
    encoding='utf-8'
)
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)

# Add debug flags without Redis dependency
DEBUG_FLAGS = {
    'log_validation': False,
    'log_websocket': False,
    'log_storage': False,
    'strict_mode': False
}

class ThreadManager:
    """Manages thread lifecycle and operations."""
    
    # System thread UUIDs
    NOVA_TEAM_UUID = "00000000-0000-4000-a000-000000000001"
    NOVA_UUID = "00000000-0000-4000-a000-000000000002"
    SYSTEM_LOGS_UUID = "00000000-0000-4000-a000-000000000003"
    AGENT_COMMUNICATION_UUID = "00000000-0000-4000-a000-000000000004"

    def __init__(self, memory_system: TwoLayerMemorySystem):
        if not memory_system:
            raise ValueError("Memory system is required")
        if not memory_system.episodic or not memory_system.semantic:
            raise ValueError("Memory system must have both episodic and semantic layers")
        self.memory_system = memory_system
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the thread manager."""
        logger.info("Initializing thread manager")
        try:
            # Verify memory system is ready
            if not self.memory_system.episodic or not self.memory_system.semantic:
                raise RuntimeError("Memory system layers not properly initialized")
                
            # Create system threads if they don't exist
            await self.get_thread(self.NOVA_TEAM_UUID)
            await self.get_thread(self.NOVA_UUID)
            await self.get_thread(self.SYSTEM_LOGS_UUID)
            await self.get_thread(self.AGENT_COMMUNICATION_UUID)
            
            self._initialized = True
            logger.info("Thread manager initialization complete")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize thread manager: {str(e)}")
            self._initialized = False
            raise
    
    async def get_thread(self, thread_id: str, max_retries: int = 3, retry_delay: float = 0.5, recursion_depth: int = 0) -> Dict[str, Any]:
        """Get a thread by ID, creating system threads if needed."""
        # Prevent deep recursion
        if recursion_depth > 3:
            logger.error(f"Maximum recursion depth reached for thread {thread_id}")
            raise ServiceError(f"Maximum recursion depth reached for thread {thread_id}")
        logger.debug(f"Getting thread {thread_id}")
        
        # Map legacy IDs to UUIDs
        id_mapping = {
            "nova-team": self.NOVA_TEAM_UUID,
            "nova": self.NOVA_UUID,
            "system-logs": self.SYSTEM_LOGS_UUID,
            "agent-communication": self.AGENT_COMMUNICATION_UUID
        }

        if not self.memory_system:
            raise ServiceError("Memory system not initialized")
            
        if not self.memory_system.episodic:
            raise ServiceError("Episodic layer not initialized")
            
        if not self.memory_system.semantic:
            raise ServiceError("Semantic layer not initialized")
        
        # Convert legacy IDs to UUIDs
        if thread_id in id_mapping:
            thread_id = id_mapping[thread_id]
            
        for attempt in range(max_retries):
            try:
                # Check episodic layer first
                logger.debug("Querying episodic layer...")
                # Create serializable filter conditions
                filter_dict = {
                    "must": [
                        {
                            "key": "metadata_thread_id",
                            "match": {"value": thread_id}
                        },
                        {
                            "key": "metadata_type",
                            "match": {"value": MemoryType.EPISODIC.value}
                        },
                        {
                            "key": "metadata_consolidated",
                            "match": {"value": False}
                        }
                    ]
                }
                
                if not self.memory_system.episodic.store:
                    raise ServiceError("Episodic store not initialized")
                    
                result = await self.memory_system.episodic.store.search_vectors({
                    "content": {},
                    "filter": filter_dict,
                    "layer": "episodic",
                    "limit": 1,
                    "score_threshold": 0.1
                })

                if result and len(result) > 0 and "content" in result[0]:
                    logger.debug("Found thread in episodic layer")
                    return result[0]["content"]

                # Check semantic layer before creating system thread
                logger.debug("Checking semantic layer...")
                
                if not self.memory_system.semantic:
                    raise ServiceError("Semantic layer not initialized")
                    
                thread_exists = await self.memory_system.semantic.run_query(
                    """
                    MATCH (t:Thread {id: $id})
                    RETURN t
                    """,
                    {"id": thread_id}
                )

                # Base case: If thread exists in semantic layer, recreate if it's a system thread
                if thread_exists:
                    if thread_id in [self.NOVA_TEAM_UUID, self.NOVA_UUID, self.SYSTEM_LOGS_UUID, self.AGENT_COMMUNICATION_UUID]:
                        logger.debug("System thread found in semantic layer but not episodic, recreating...")
                        return await self._create_system_thread(thread_id)
                    else:
                        logger.error(f"Thread {thread_id} exists in semantic but not episodic layer")
                        raise ResourceNotFoundError(f"Thread {thread_id} exists in semantic but not episodic layer")
                # Only create new system thread if it doesn't exist in either layer
                elif thread_id in [self.NOVA_TEAM_UUID, self.NOVA_UUID, self.SYSTEM_LOGS_UUID, self.AGENT_COMMUNICATION_UUID] and recursion_depth == 0:
                    logger.debug("Creating new system thread...")
                    return await self._create_system_thread(thread_id)


                if attempt < max_retries - 1:
                    logger.debug(f"Thread not found, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                    continue

                # If we've exhausted all retries and still haven't found or created the thread
                logger.error(f"Thread {thread_id} not found after {max_retries} attempts")
                raise ResourceNotFoundError(f"Thread {thread_id} not found after {max_retries} attempts")
            except Exception as e:
                logger.error(f"Error getting thread (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    logger.debug(f"Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    continue
                logger.error("Max retries reached, raising error")
                raise ServiceError(f"Failed to get thread: {str(e)}") from e
        
        # This should never be reached due to the raise statements above,
        # but we need it to satisfy the return type
        raise ServiceError("Failed to get thread: Unexpected code path")

    async def _create_system_thread(self, thread_id: str, skip_store: bool = False) -> Dict[str, Any]:
        """Create a system thread."""
        now = datetime.now(timezone.utc).isoformat()
        
        # Define core agents for nova-team
        core_agents = [
            {
                "id": str(uuid.uuid4()),
                "name": "Nova Orchestrator",
                "type": "orchestrator",
                "workspace": "system",
                "domain": "general",
                "status": "active",
                "metadata_type": "agent",
                "metadata_capabilities": ["orchestration"],
                "metadata_created_at": now
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Belief Agent",
                "type": "belief",
                "workspace": "system",
                "domain": "general",
                "status": "active",
                "metadata_type": "agent",
                "metadata_capabilities": ["belief_management"],
                "metadata_created_at": now
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Desire Agent",
                "type": "desire",
                "workspace": "system",
                "domain": "general",
                "status": "active",
                "metadata_type": "agent",
                "metadata_capabilities": ["desire_management"],
                "metadata_created_at": now
            }
        ]

        # Determine thread configuration based on ID
        thread_config = {
            self.NOVA_TEAM_UUID: {
                "name": "Nova Team",
                "participants": core_agents,
                "type": "agent-team",
                "description": "This is where NOVA and core agents collaborate."
            },
            self.NOVA_UUID: {
                "name": "Nova",
                "participants": [],
                "type": "agent-team",
                "description": "Primary Nova thread"
            },
            self.SYSTEM_LOGS_UUID: {
                "name": "System Logs",
                "participants": [],
                "type": "system",
                "description": "System-wide logging and monitoring thread"
            },
            self.AGENT_COMMUNICATION_UUID: {
                "name": "Agent Communication",
                "participants": [],
                "type": "system",
                "description": "Thread for agent-to-agent communication"
            }
        }

        config = thread_config.get(thread_id, {})
        thread = {
            "id": thread_id,
            "name": config.get("name", "Unknown"),
            "domain": "general",
            "messages": [],
            "createdAt": now,
            "updatedAt": now,
            "workspace": "system",
            "participants": config.get("participants", []),
            "metadata": {
                "type": config.get("type", "system"),
                "system": True,
                "pinned": True,
                "description": config.get("description", "")
            }
        }

        try:
            if not skip_store:
                # Store directly in both layers without verification to prevent recursion
                try:
                    # Store in episodic layer
                    memory_data = {
                        "id": thread_id,
                        "content": thread,
                        "type": MemoryType.EPISODIC.value,
                        "importance": 0.8,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "context": {
                            "domain": thread.get("domain", "general"),
                            "source": "nova",
                            "type": MemoryType.EPISODIC.value,
                            "thread_id": thread_id
                        },
                        "metadata": {
                            "thread_id": thread_id,
                            "type": MemoryType.EPISODIC.value,
                            "consolidated": False,
                            "layer": "episodic",
                            "domain": thread.get("domain", "general"),
                            "source": "nova"
                        }
                    }
                    
                    memory = EpisodicMemory(**memory_data)
                    if self.memory_system.episodic:
                        await self.memory_system.episodic.store_memory(memory)
                        
                    # Store in semantic layer
                    if self.memory_system.semantic:
                        properties = {
                            "name": thread["name"],
                            "domain": thread["domain"],
                            "createdAt": thread["createdAt"],
                            "updatedAt": thread["updatedAt"],
                            "workspace": thread["workspace"],
                            "participants": json.dumps(thread.get("participants", [])),
                            "metadata": json.dumps(thread.get("metadata", {}))
                        }
                        
                        await self.memory_system.semantic.run_query(
                            """
                            MERGE (t:Thread {id: $id})
                            SET t += $properties
                            """,
                            {
                                "id": thread_id,
                                "properties": properties
                            }
                        )
                except Exception as e:
                    logger.error(f"Failed to store system thread {thread_id}: {str(e)}")
                    raise ServiceError(f"Failed to store system thread {thread_id}: {str(e)}") from e
            
            return thread
        except Exception as e:
            # Log error and re-raise
            logger.error(f"Error creating system thread {thread_id}: {str(e)}")
            raise ServiceError(f"Failed to create system thread {thread_id}: {str(e)}") from e

    async def create_thread(self, title: str, domain: str = "general", metadata: Optional[Dict] = None, workspace: str = "personal") -> Dict[str, Any]:
        """Create a new thread with validation."""
        thread_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        # Create thread metadata model with null checks
        metadata_dict = metadata or {}
        thread_metadata = ThreadMetadata(
            type=metadata_dict.get("type", "user"),
            system=metadata_dict.get("system", False),
            pinned=metadata_dict.get("pinned", False),
            description=metadata_dict.get("description", "")
        )
        
        # Create thread model with validation
        try:
            thread_model = Thread(
                id=thread_id,
                name=title,
                domain=domain,
                messages=[],
                createdAt=now,
                updatedAt=now,
                workspace=workspace,
                participants=[ThreadParticipant(**p) for p in metadata_dict.get("participants", [])] if metadata_dict.get("participants") else [],
                metadata=thread_metadata
            )
            
            # Convert to dict for storage
            thread = thread_model.model_dump()
        except Exception as e:
            logger.error(f"Failed to create thread model: {str(e)}")
            raise ServiceError(f"Failed to create thread: {str(e)}") from e

        # Store with verification disabled for initial creation to prevent recursion
        await self._store_thread(thread, verify=False)
        
        # Additional verification with retries
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                stored_thread = await self.get_thread(thread_id, max_retries=1)
                if stored_thread:
                    # Verify all fields match
                    for key in thread:
                        if key == "metadata":
                            # Deep compare metadata
                            for meta_key in thread["metadata"]:
                                if thread["metadata"][meta_key] != stored_thread["metadata"][meta_key]:
                                    raise ServiceError(f"Thread metadata mismatch for key: {meta_key}")
                        elif thread[key] != stored_thread[key]:
                            raise ServiceError(f"Thread field mismatch for key: {key}")
                    return stored_thread
            except ResourceNotFoundError:
                if attempt < max_retries - 1:
                    logger.warning(f"Thread verification attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(retry_delay)
                    continue
                raise ServiceError(f"Failed to verify thread creation after {max_retries} attempts")
            except Exception as e:
                logger.error(f"Error during thread verification: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                raise
        
        raise ServiceError("Thread creation verification failed")

    async def _store_thread(self, thread: Dict[str, Any], verify: bool = True) -> None:
        """Store thread in both episodic and semantic layers with idempotency checks."""
        max_retries = 3
        retry_delay = 0.5
        thread_id = thread["id"]
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Attempting to store thread {thread_id} (attempt {attempt + 1}/{max_retries})")
                
                if not self.memory_system.episodic or not self.memory_system.episodic.store:
                    raise ServiceError("Episodic store not initialized")
                    
                # Check if thread already exists in episodic layer, but skip for system threads
                logger.debug("Checking for existing thread...")
                if thread["id"] not in [self.NOVA_TEAM_UUID, self.NOVA_UUID, self.SYSTEM_LOGS_UUID, self.AGENT_COMMUNICATION_UUID]:
                    existing_thread = await self.memory_system.episodic.store.search_vectors({
                    "content": {},
                    "filter": {
                        "must": [
                            {
                                "key": "metadata_thread_id",
                                "match": {"value": thread_id}
                            },
                            {
                                "key": "metadata_type",
                                "match": {"value": MemoryType.EPISODIC.value}
                            },
                            {
                                "key": "metadata_consolidated",
                                "match": {"value": False}
                            }
                        ]
                    },
                    "limit": 1,
                    "score_threshold": 0.95
                })
                
                if existing_thread:
                    logger.info(f"Thread {thread_id} already exists, updating...")
                    # If thread exists, we'll update it but skip verification
                    await self._update_existing_thread(thread)
                    return
                
                # Validate thread data before storage
                required_fields = ["id", "name", "domain", "messages", "createdAt", "updatedAt", "workspace", "participants", "metadata"]
                for field in required_fields:
                    if field not in thread:
                        raise ValueError(f"Missing required field: {field}")
                
                required_metadata = ["type", "system", "pinned", "description"]
                for field in required_metadata:
                    if field not in thread["metadata"]:
                        raise ValueError(f"Missing required metadata field: {field}")
                
                # Store in episodic layer if thread doesn't exist
                logger.debug(f"Storing new thread {thread['id']} in episodic layer...")
                # Prepare metadata first
                metadata = {
                    "thread_id": thread["id"],  # Set thread_id in metadata
                    "type": MemoryType.EPISODIC.value,
                    "consolidated": False,
                    "layer": "episodic",
                    "domain": thread.get("domain", "general"),
                    "source": "nova"
                }

                # Create memory data with enhanced thread ID handling
                logger.info("Creating memory data for thread storage")
                logger.info(f"Thread ID: {thread['id']}")
                
                # Create memory data with explicit thread ID handling
                thread_id = thread["id"]  # Extract thread ID
                memory_data = {
                    "id": thread_id,  # Set explicit ID
                    "content": thread,  # Store full thread data directly
                    "type": MemoryType.EPISODIC.value,  # Use proper memory type
                    "importance": 0.8,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "context": {
                        "domain": thread.get("domain", "general"),
                        "source": "nova",
                        "type": MemoryType.EPISODIC.value,  # Use proper memory type
                        "thread_id": thread_id
                    },
                    "metadata": {
                        "thread_id": thread_id,
                        "type": MemoryType.EPISODIC.value,  # Use proper memory type
                        "consolidated": False,
                        "layer": "episodic",
                        "domain": thread.get("domain", "general"),
                        "source": "nova"
                    }
                }
                
                # Create EpisodicMemory object
                logger.info("Creating EpisodicMemory object")
                # Create memory with proper type handling
                memory_data["type"] = str(memory_data["type"])  # Convert type to string
                memory = EpisodicMemory(**memory_data)
                logger.info(f"Created memory object with ID: {memory.id}")
                
                # Store memory directly in episodic layer
                logger.info("Storing memory in episodic layer")
                if not self.memory_system.episodic:
                    raise ServiceError("Episodic layer not initialized")
                store_result = await self.memory_system.episodic.store_memory(memory)
                logger.debug("Successfully stored in episodic layer")

                # Store in semantic layer with flattened metadata
                logger.debug("Storing in semantic layer...")
                if not self.memory_system.semantic:
                    raise ServiceError("Semantic layer not initialized")
                    
                properties = {
                    "name": thread["name"],
                    "domain": thread["domain"],
                    "createdAt": thread["createdAt"],
                    "updatedAt": thread["updatedAt"],
                    "workspace": thread["workspace"],
                    "participants": json.dumps(thread.get("participants", [])),
                    "metadata": json.dumps(thread.get("metadata", {}))
                }

                result = await self.memory_system.semantic.run_query(
                    """
                    MERGE (t:Thread {id: $id})
                    SET t += $properties
                    """,
                    {
                        "id": thread["id"],
                        "properties": properties
                    }
                )

                logger.debug("Successfully stored in semantic layer")

                # Log successful storage
                logger.info(f"Successfully stored thread {thread_id} in both layers")

                # Verify storage if requested
                if verify:
                    logger.debug(f"Verifying thread storage for {thread_id}")
                    stored_thread = await self.get_thread(thread_id)
                    if not stored_thread:
                        raise RuntimeError(f"Thread {thread_id} verification failed - not found after storage")
                    logger.info(f"Successfully verified thread {thread_id} storage")
                return

            except Exception as e:
                logger.error(f"Error storing thread (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    logger.error(f"Retrying thread storage...")
                    continue
                logger.error("Max retries reached, raising error")
                raise e

    async def update_thread(self, thread: Dict[str, Any], verify: bool = True) -> None:
        """Update an existing thread with validation."""
        # Validate thread exists
        existing_thread = await self.get_thread(thread["id"])
        if not existing_thread:
            raise ResourceNotFoundError(f"Thread {thread['id']} not found")
            
        # Update timestamp
        thread["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        # Preserve creation time
        thread["createdAt"] = existing_thread["createdAt"]
        
        # Validate metadata hasn't been corrupted
        required_metadata = ["type", "system", "pinned", "description"]
        for field in required_metadata:
            if field not in thread["metadata"]:
                thread["metadata"][field] = existing_thread["metadata"][field]
                
        # Store with verification if requested
        await self._store_thread(thread, verify=verify)

    async def list_threads(self, filter_params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """List all threads with optional filtering."""
        # Base filter conditions
        filter_dict = {
            "must": [
                {
                    "key": "metadata_type",
                    "match": {"value": MemoryType.EPISODIC.value}
                },
                {
                    "key": "metadata_consolidated",
                    "match": {"value": False}
                }
            ]
        }
        
        # Add additional filters if provided
        if filter_params:
            # Map legacy IDs to UUIDs in filter params
            if "thread_id" in filter_params:
                id_mapping = {
                    "nova-team": self.NOVA_TEAM_UUID,
                    "nova": self.NOVA_UUID,
                    "system-logs": self.SYSTEM_LOGS_UUID,
                    "agent-communication": self.AGENT_COMMUNICATION_UUID
                }
                if filter_params["thread_id"] in id_mapping:
                    filter_params["thread_id"] = id_mapping[filter_params["thread_id"]]
                    
            for key, value in filter_params.items():
                filter_dict["must"].append({
                    "key": f"metadata_{key}",
                    "match": {"value": value}
                })
        
        try:
                if not self.memory_system.episodic or not self.memory_system.episodic.store:
                    raise ServiceError("Episodic store not initialized")
                    
                results = await self.memory_system.episodic.store.search_vectors({
                    "content": {},
                    "filter": filter_dict,
                    "layer": "episodic"
                })
        except Exception as e:
            logger.error(f"Error querying threads: {str(e)}")
            raise ServiceError("Failed to list threads") from e
        
        # Parse JSON strings back into dicts
        threads = []
        if results:
            for result in results:
                if "content" in result:
                    threads.append(result["content"])
        return threads

    async def add_message(self, thread_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Add a message to a thread."""
        thread = await self.get_thread(thread_id)
        
        # Validate message with ThreadMessage model
        thread_message = ThreadMessage(
            type="thread_message",
            client_id=message.get("client_id", "system"),
            data=message,
            thread_id=thread_id,
            sender_id=message.get("sender_id", "system")
        )
        
        # Add validated message
        thread["messages"].append(thread_message.model_dump())
        await self.update_thread(thread)
        
        # Broadcast update via WebSocket
        thread_update = ThreadUpdate(
            type="thread_update",
            client_id=message.get("client_id", "system"),
            data=Thread(**thread),
            update_type="updated"
        )
        
        # Return updated thread
        return thread

    async def add_participant(self, thread_id: str, participant: Dict[str, Any]) -> Dict[str, Any]:
        """Add a participant to a thread."""
        thread = await self.get_thread(thread_id)
        
        # Validate participant with ThreadParticipant model
        participant_model = ThreadParticipant(
            id=participant["id"],
            name=participant["name"],
            type=participant["type"],
            workspace=participant.get("workspace", "personal"),
            domain=participant.get("domain", "general"),
            status=participant.get("status", "active"),
            metadata_type=participant["metadata_type"],
            metadata_capabilities=participant["metadata_capabilities"],
            metadata_created_at=datetime.now(timezone.utc)
        )
        
        # Add validated participant
        if not thread.get("participants"):
            thread["participants"] = []
        thread["participants"].append(participant_model.model_dump())
        
        # Update thread
        await self.update_thread(thread)
        
        # Broadcast update via WebSocket
        thread_update = ThreadUpdate(
            type="thread_update",
            client_id=participant.get("client_id", "system"),
            data=Thread(**thread),
            update_type="updated"
        )
        
        return thread

    async def add_agent_team(self, thread_id: str, agent_specs: List[Dict[str, Any]], agent_store: Any) -> List[Dict[str, Any]]:
        """Add a team of agents to a thread."""
        thread = await self.get_thread(thread_id)
        
        # Create each agent
        agents = []
        for agent_spec in agent_specs:
            agent_type = agent_spec.get("type")
            workspace = agent_spec.get("workspace", "personal")
            domain = agent_spec.get("domain")
            
            # Ensure agent_type is not None and is a string
            if not agent_type or not isinstance(agent_type, str):
                raise ValueError("Agent type must be a non-empty string")
                
            # Create agent with safe string operations
            agent_id = f"{agent_type}-{str(uuid.uuid4())[:8]}"
            agent_name = f"{agent_type[0].upper()}{agent_type[1:]}Agent" if agent_type else "UnknownAgent"
            
            agent = {
                "id": agent_id,
                "name": agent_name,
                "type": agent_type,
                "workspace": workspace or "personal",
                "domain": domain or "general",
                "status": "active",
                "metadata_type": "agent",
                "metadata_capabilities": [f"{agent_type}_analysis"],
                "metadata_created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store agent
            await agent_store.store_agent(agent)
            agents.append(agent)
        
        # Add agents to thread participants
        if not thread.get("participants"):
            thread["participants"] = []
        thread["participants"].extend(agents)
        
        # Update thread
        await self.update_thread(thread)
        
        return agents

    async def get_thread_agents(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all agents in a thread."""
        try:
            # Map legacy IDs to UUIDs
            id_mapping = {
                "nova-team": self.NOVA_TEAM_UUID,
                "nova": self.NOVA_UUID,
                "system-logs": self.SYSTEM_LOGS_UUID,
                "agent-communication": self.AGENT_COMMUNICATION_UUID
            }
            
            # Convert legacy IDs to UUIDs
            if thread_id in id_mapping:
                thread_id = id_mapping[thread_id]
                
            thread = await self.get_thread(thread_id)
                
            return [
                p for p in thread.get("participants", [])
                if p.get("type") in ["agent", "orchestrator", "belief", "desire"]
            ]
        except Exception as e:
            logger.error(f"Error getting thread agents: {str(e)}")
            raise

    async def _update_existing_thread(self, thread: Dict[str, Any]) -> None:
        """Update an existing thread without verification."""
        try:
            logger.info(f"Updating existing thread {thread['id']}")
            
            if not self.memory_system:
                raise ServiceError("Memory system not initialized")
                
            if not self.memory_system.semantic:
                raise ServiceError("Semantic layer not initialized")

            # Update semantic layer first since it's idempotent
            logger.debug("Updating semantic layer...")
            properties = {
                "name": thread["name"],
                "domain": thread["domain"],
                "createdAt": thread["createdAt"],
                "updatedAt": thread["updatedAt"],
                "workspace": thread["workspace"],
                "participants": json.dumps(thread.get("participants", [])),
                "metadata": json.dumps(thread.get("metadata", {}))
            }
            
            await self.memory_system.semantic.run_query(
                """
                MERGE (t:Thread {id: $id})
                SET t += $properties
                """,
                {
                    "id": thread["id"],
                    "properties": properties
                }
            )
            
            # Update episodic layer
            logger.debug("Updating episodic layer...")
            if not self.memory_system.episodic:
                raise ServiceError("Episodic layer not initialized")
                
            memory_data = {
                "id": thread["id"],
                "content": thread,
                "type": MemoryType.EPISODIC.value,  # Use proper memory type
                "importance": 0.8,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context": {
                    "domain": thread.get("domain", "general"),
                    "source": "nova",
                    "type": MemoryType.EPISODIC.value,  # Use proper memory type
                    "thread_id": thread["id"]
                },
                "metadata": {
                    "thread_id": thread["id"],
                    "type": MemoryType.EPISODIC.value,  # Use proper memory type
                    "consolidated": False,
                    "layer": "episodic",
                    "domain": thread.get("domain", "general"),
                    "source": "nova"
                }
            }
            
            # Convert type to string for EpisodicMemory
            memory_data["type"] = str(memory_data["type"])
            memory = EpisodicMemory(**memory_data)
            
            await self.memory_system.episodic.store_memory(memory)
            logger.info(f"Successfully updated thread {thread['id']}")
            
        except Exception as e:
            logger.error(f"Failed to update thread {thread['id']}: {str(e)}")
            raise ServiceError(f"Failed to update thread {thread['id']}: {str(e)}")

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread from both episodic and semantic layers."""
        try:
            logger.debug(f"Deleting thread {thread_id}")
            
            if not self.memory_system:
                raise ServiceError("Memory system not initialized")
                
            if not self.memory_system.episodic:
                raise ServiceError("Episodic layer not initialized")
                
            if not self.memory_system.semantic:
                raise ServiceError("Semantic layer not initialized")
            
            # Delete from episodic layer
            await self.memory_system.delete_memory(thread_id)
            
            # Delete from semantic layer
            await self.memory_system.semantic.run_query(
                """
                MATCH (t:Thread {id: $id})
                DETACH DELETE t
                """,
                {"id": thread_id}
            )
            
            logger.info(f"Successfully deleted thread {thread_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting thread {thread_id}: {str(e)}")
            raise ServiceError(f"Failed to delete thread {thread_id}: {str(e)}")

    async def add_single_agent(self, thread_id: str, agent_type: str, workspace: str = "personal", domain: Optional[str] = None, agent_store: Any = None) -> Dict[str, Any]:
        """Add a single agent to a thread."""
        try:
            thread = await self.get_thread(thread_id)
            
            # Validate agent_type
            if not agent_type or not isinstance(agent_type, str):
                raise ValueError("Agent type must be a non-empty string")
                
            # Create agent with safe string operations
            agent_id = f"{agent_type}-{str(uuid.uuid4())[:8]}"
            agent_name = f"{agent_type[0].upper()}{agent_type[1:]}Agent" if agent_type else "UnknownAgent"
            
            agent = {
                "id": agent_id,
                "name": agent_name,
                "type": agent_type,
                "workspace": workspace or "personal",
                "domain": domain or "general",
                "status": "active",
                "metadata_type": "agent",
                "metadata_capabilities": [f"{agent_type}_analysis"],
                "metadata_created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store agent if agent_store provided and is valid
            if agent_store and hasattr(agent_store, 'store_agent'):
                await agent_store.store_agent(agent)
            
            # Add agent to thread participants
            if not thread.get("participants"):
                thread["participants"] = []
            thread["participants"].append(agent)
            
            # Update thread
            await self.update_thread(thread)
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to add agent to thread {thread_id}: {str(e)}")
            raise ServiceError(f"Failed to add agent to thread {thread_id}: {str(e)}")
