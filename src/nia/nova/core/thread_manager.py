"""Thread management module for Nova's chat system."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import asyncio
import uuid
import json
import logging
import traceback

from nia.core.types.memory_types import Memory, MemoryType, EpisodicMemory
from nia.memory.two_layer import TwoLayerMemorySystem
from .error_handling import ResourceNotFoundError, ServiceError
from qdrant_client.http import models

import os

# Configure logging with consistent format
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs/thread_manager")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Create session-specific log file
session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
session_log = LOGS_DIR / f"session_{session_id}.json"

class JsonLogHandler:
    def __init__(self, log_file):
        self.log_file = log_file
        self.logs = []
        
    def emit(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        self.logs.append(log_entry)
        self._save_logs()
        
    def _save_logs(self):
        with open(self.log_file, 'w') as f:
            json.dump({
                "session_id": session_id,
                "logs": self.logs
            }, f, indent=2)

# Add JSON handler
json_handler = JsonLogHandler(session_log)
logger.addHandler(json_handler)

class ThreadManager:
    """Manages thread lifecycle and operations."""
    
    def __init__(self, memory_system: TwoLayerMemorySystem):
        self.memory_system = memory_system

    async def get_thread(self, thread_id: str, max_retries: int = 3, retry_delay: float = 0.5) -> Dict[str, Any]:
        """Get a thread by ID, creating system threads if needed."""
        logger.debug(f"Getting thread {thread_id}")
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
                            "match": {"value": "episodic"}
                        },
                        {
                            "key": "metadata_consolidated",
                            "match": {"value": False}
                        }
                    ]
                }
                
                result = await self.memory_system.query_episodic({
                    "content": {},
                    "filter": filter_dict,
                    "layer": "episodic",
                    "limit": 1,
                    "score_threshold": 0.1
                })

                if result:
                    logger.debug("Found thread in episodic layer")
                    # Get content directly without parsing
                    return result[0]["content"]

                # Handle system threads
                if thread_id in ["nova-team", "nova"]:
                    logger.debug(f"Creating system thread {thread_id}")
                    return await self._create_system_thread(thread_id)

                # Check semantic layer as fallback
                logger.debug("Checking semantic layer...")
                thread_exists = await self.memory_system.semantic.run_query(
                    """
                    MATCH (t:Thread {id: $id})
                    RETURN t
                    """,
                    {"id": thread_id}
                )

                if thread_exists:
                    # Thread exists in semantic but not episodic - recreate it
                    logger.debug("Thread found in semantic layer but not episodic, recreating...")
                    return await self._create_system_thread(thread_id)

                if attempt < max_retries - 1:
                    logger.debug(f"Thread not found, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                    continue

                logger.error(f"Thread {thread_id} not found after {max_retries} attempts")
                raise ResourceNotFoundError(f"Thread {thread_id} not found after {max_retries} attempts")
            except Exception as e:
                logger.error(f"Error getting thread (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    logger.debug(f"Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    continue
                logger.error("Max retries reached, raising error")
                raise e

    async def _create_system_thread(self, thread_id: str) -> Dict[str, Any]:
        """Create a system thread."""
        now = datetime.now().isoformat()
        
        # Define core agents for nova-team
        core_agents = [
            {
                "id": "nova-orchestrator",
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
                "id": "belief-agent",
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
                "id": "desire-agent",
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

        thread = {
            "id": thread_id,
            "name": "Nova Team" if thread_id == "nova-team" else "Nova",
            "domain": "general",
            "messages": [],
            "createdAt": now,
            "updatedAt": now,
            "workspace": "system",  # Changed to system workspace
            "participants": core_agents if thread_id == "nova-team" else [],
            "metadata": {
                "type": "agent-team",
                "system": True,
                "pinned": True,
                "description": "This is where NOVA and core agents collaborate." if thread_id == "nova-team" else "Primary Nova thread"
            }
        }

        try:
            # Store in both layers
            await self._store_thread(thread)
            
            # Return thread after successful storage
            return thread
        except Exception as e:
            # Log error and re-raise
            logger.error(f"Error creating system thread {thread_id}: {str(e)}")
            raise ServiceError(f"Failed to create system thread {thread_id}: {str(e)}") from e

    async def create_thread(self, title: str, domain: str = "general", metadata: Optional[Dict] = None, workspace: str = "personal") -> Dict[str, Any]:
        """Create a new thread with validation."""
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
        
        # Validate thread type
        valid_types = ["test", "system", "user", "agent", "chat", "task", "agent-team"]
        if metadata["type"] not in valid_types:
            raise ValueError(f"Invalid thread type. Must be one of: {valid_types}")
            
        # Validate domain
        if not domain:
            raise ValueError("Domain cannot be empty")
            
        # Create thread with validated data
        thread = {
            "id": thread_id,
            "name": title,
            "domain": domain,
            "messages": [],
            "createdAt": now,
            "updatedAt": now,
            "workspace": workspace,
            "participants": metadata.get("participants", []),
            "metadata": metadata
        }

        # Store with verification enabled
        await self._store_thread(thread, verify=True)
        
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
                
                # Check if thread already exists in episodic layer
                logger.debug("Checking for existing thread...")
                existing_thread = await self.memory_system.query_episodic({
                    "content": {},
                    "filter": {
                        "must": [
                            {
                                "key": "metadata_thread_id",
                                "match": {"value": thread_id}
                            },
                            {
                                "key": "metadata_type",
                                "match": {"value": "episodic"}
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
                    "type": "episodic",
                    "consolidated": False,
                    "layer": "episodic",
                    "domain": thread.get("domain", "general"),
                    "source": "nova"
                }

                # Create memory data with enhanced thread ID handling
                logger.info("Creating memory data for thread storage")
                logger.info(f"Thread ID: {thread['id']}")
                logger.info(f"Thread content: {json.dumps(thread, indent=2)}")
                
                # Create memory data with explicit thread ID handling
                thread_id = thread["id"]  # Extract thread ID
                memory_data = {
                    "id": thread_id,  # Set explicit ID
                    "content": thread,  # Store full thread data directly
                    "type": MemoryType.EPISODIC,
                    "importance": 0.8,
                    "timestamp": datetime.now().isoformat(),
                    "context": {
                        "domain": thread.get("domain", "general"),
                        "source": "nova",
                        "type": "thread",
                        "thread_id": thread_id
                    },
                    "metadata": {
                        "thread_id": thread_id,
                        "type": "episodic",
                        "consolidated": False,
                        "layer": "episodic",
                        "domain": thread.get("domain", "general"),
                        "source": "nova"
                    }
                }
                logger.info(f"Prepared memory data: {json.dumps(memory_data, indent=2)}")
                
                # Create EpisodicMemory object
                logger.info("Creating EpisodicMemory object")
                memory = EpisodicMemory(**memory_data)
                logger.info(f"Created memory object with ID: {memory.id}")
                
                # Store memory
                logger.info("Storing memory in episodic layer")
                store_result = await self.memory_system.store_experience(memory)
                logger.info(f"Store result: {json.dumps(store_result, indent=2) if store_result else None}")
                logger.debug("Successfully stored in episodic layer")

                # Store in semantic layer with flattened metadata
                logger.debug("Storing in semantic layer...")
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
                logger.debug(f"Episodic store result: {store_result}")
                logger.debug(f"Semantic store result: {result}")

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
        thread["updatedAt"] = datetime.now().isoformat()
        
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
                    "match": {"value": "episodic"}
                },
                {
                    "key": "metadata_consolidated",
                    "match": {"value": False}
                }
            ]
        }
        
        # Add additional filters if provided
        if filter_params:
            for key, value in filter_params.items():
                filter_dict["must"].append({
                    "key": f"metadata_{key}",
                    "match": {"value": value}
                })
        
        try:
            results = await self.memory_system.query_episodic({
                "content": {},
                "filter": filter_dict,
                "layer": "episodic"
            })
        except Exception as e:
            logger.error(f"Error querying threads: {str(e)}")
            raise ServiceError("Failed to list threads") from e
        
        # Parse JSON strings back into dicts
        threads = []
        for result in results:
            threads.append(result["content"])
        return threads

    async def add_message(self, thread_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Add a message to a thread."""
        thread = await self.get_thread(thread_id)
        thread["messages"].append(message)
        await self.update_thread(thread)
        return thread

    async def add_participant(self, thread_id: str, participant: Dict[str, Any]) -> Dict[str, Any]:
        """Add a participant to a thread."""
        thread = await self.get_thread(thread_id)
        if not thread.get("participants"):
            thread["participants"] = []
        thread["participants"].append(participant)
        await self.update_thread(thread)
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
            
            agent = {
                "id": f"{agent_type}-{str(uuid.uuid4())[:8]}",
                "name": f"{agent_type.capitalize()}Agent",
                "type": agent_type,
                "workspace": workspace,
                "domain": domain,
                "status": "active",
                "metadata_type": "agent",
                "metadata_capabilities": [f"{agent_type}_analysis"],
                "metadata_created_at": datetime.now().isoformat()
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
            # Create system threads if they don't exist
            if thread_id in ["nova-team", "nova"]:
                thread = await self._create_system_thread(thread_id)
            else:
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
            memory_data = {
                "id": thread["id"],
                "content": thread,
                "type": MemoryType.EPISODIC,
                "importance": 0.8,
                "timestamp": datetime.now().isoformat(),
                "context": {
                    "domain": thread.get("domain", "general"),
                    "source": "nova",
                    "type": "thread",
                    "thread_id": thread["id"]
                },
                "metadata": {
                    "thread_id": thread["id"],
                    "type": "episodic",
                    "consolidated": False,
                    "layer": "episodic",
                    "domain": thread.get("domain", "general"),
                    "source": "nova"
                }
            }
            
            memory = EpisodicMemory(**memory_data)
            await self.memory_system.store_experience(memory)
            logger.info(f"Successfully updated thread {thread['id']}")
            
        except Exception as e:
            logger.error(f"Failed to update thread {thread['id']}: {str(e)}")
            raise ServiceError(f"Failed to update thread {thread['id']}: {str(e)}")

    async def add_single_agent(self, thread_id: str, agent_type: str, workspace: str = "personal", domain: Optional[str] = None, agent_store: Any = None) -> Dict[str, Any]:
        """Add a single agent to a thread."""
        thread = await self.get_thread(thread_id)
        
        # Create agent
        agent = {
            "id": f"{agent_type}-{str(uuid.uuid4())[:8]}",
            "name": f"{agent_type.capitalize()}Agent",
            "type": agent_type,
            "workspace": workspace,
            "domain": domain,
            "status": "active",
            "metadata_type": "agent",
            "metadata_capabilities": [f"{agent_type}_analysis"],
            "metadata_created_at": datetime.now().isoformat()
        }
        
        # Store agent if agent_store provided
        if agent_store:
            await agent_store.store_agent(agent)
        
        # Add agent to thread participants
        if not thread.get("participants"):
            thread["participants"] = []
        thread["participants"].append(agent)
        
        # Update thread
        await self.update_thread(thread)
        
        return agent
