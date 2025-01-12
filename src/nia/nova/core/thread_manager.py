"""Thread management module for Nova's chat system."""

from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio

from nia.core.types.memory_types import Memory, MemoryType
from nia.memory.two_layer import TwoLayerMemorySystem
from .error_handling import ResourceNotFoundError, ServiceError

class ThreadManager:
    """Manages thread lifecycle and operations."""
    
    def __init__(self, memory_system: TwoLayerMemorySystem):
        self.memory_system = memory_system

    async def get_thread(self, thread_id: str, max_retries: int = 3, retry_delay: float = 0.5) -> Dict[str, Any]:
        """Get a thread by ID, creating system threads if needed."""
        for attempt in range(max_retries):
            try:
                # Check episodic layer first
                result = await self.memory_system.query_episodic({
                    "content": {},
                    "filter": {
                        "metadata.thread_id": thread_id,
                        "metadata.type": "thread"
                    },
                    "layer": "episodic"
                })

                if result:
                    return result[0]["content"]["data"]

                # Handle system threads
                if thread_id in ["nova-team", "nova"]:
                    return await self._create_system_thread(thread_id)

                # Check semantic layer as fallback
                thread_exists = await self.memory_system.semantic.run_query(
                    """
                    MATCH (t:Thread {id: $id})
                    RETURN t
                    """,
                    {"id": thread_id}
                )

                if thread_exists:
                    # Thread exists in semantic but not episodic - recreate it
                    return await self._create_system_thread(thread_id)

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue

                raise ResourceNotFoundError(f"Thread {thread_id} not found after {max_retries} attempts")
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                raise e

    async def _create_system_thread(self, thread_id: str) -> Dict[str, Any]:
        """Create a system thread."""
        now = datetime.now().isoformat()
        thread = {
            "id": thread_id,
            "title": "Nova Team" if thread_id == "nova-team" else "Nova",
            "domain": "general",
            "messages": [],
            "created_at": now,
            "updated_at": now,
            "workspace": "personal",
            "metadata": {
                "type": "agent-team",
                "system": True,
                "pinned": True,
                "description": "This is where NOVA and core agents collaborate." if thread_id == "nova-team" else "Primary Nova thread",
                "participants": []
            }
        }

        # Store in both layers
        await self._store_thread(thread)
        return thread

    async def create_thread(self, title: str, domain: str = "general", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new thread."""
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

        await self._store_thread(thread)
        
        # Verify thread was stored before returning
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                stored_thread = await self.get_thread(thread_id, max_retries=1)
                if stored_thread:
                    return stored_thread
            except ResourceNotFoundError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                raise ServiceError(f"Failed to verify thread creation after {max_retries} attempts")
        
        return thread

    async def _store_thread(self, thread: Dict[str, Any]) -> None:
        """Store thread in both episodic and semantic layers."""
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                # Store in episodic layer
                memory = Memory(
                    content={
                        "data": thread,
                        "metadata": {
                            "type": "thread",
                            "domain": thread.get("domain", "general"),
                            "thread_id": thread["id"],
                            "timestamp": thread["updated_at"],
                            "id": thread["id"]
                        }
                    },
                    type=MemoryType.EPISODIC,
                    importance=0.8,
                    context={
                        "domain": thread.get("domain", "general"),
                        "thread_id": thread["id"],
                        "source": "nova"
                    }
                )
                await self.memory_system.store_experience(memory)

                # Store in semantic layer
                await self.memory_system.semantic.run_query(
                    """
                    MERGE (t:Thread {id: $id})
                    SET t += $properties
                    """,
                    {
                        "id": thread["id"],
                        "properties": {
                            "title": thread["title"],
                            "domain": thread["domain"],
                            "created_at": thread["created_at"],
                            "updated_at": thread["updated_at"]
                        }
                    }
                )

                # Verify storage
                verify_result = await self.memory_system.query_episodic({
                    "content": {},
                    "filter": {
                        "metadata.thread_id": thread["id"],
                        "metadata.type": "thread"
                    },
                    "layer": "episodic"
                })

                if verify_result:
                    return

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue

                raise ServiceError(f"Failed to store thread {thread['id']} after {max_retries} attempts")
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                raise e

    async def update_thread(self, thread: Dict[str, Any]) -> None:
        """Update an existing thread."""
        thread["updated_at"] = datetime.now().isoformat()
        await self._store_thread(thread)

    async def list_threads(self) -> List[Dict[str, Any]]:
        """List all threads."""
        results = await self.memory_system.query_episodic({
            "content": {},
            "filter": {"metadata.type": "thread"},
            "layer": "episodic"
        })
        
        return [result["content"]["data"] for result in results]

    async def add_message(self, thread_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Add a message to a thread."""
        thread = await self.get_thread(thread_id)
        thread["messages"].append(message)
        await self.update_thread(thread)
        return thread

    async def add_participant(self, thread_id: str, participant: Dict[str, Any]) -> Dict[str, Any]:
        """Add a participant to a thread."""
        thread = await self.get_thread(thread_id)
        if "participants" not in thread["metadata"]:
            thread["metadata"]["participants"] = []
        thread["metadata"]["participants"].append(participant)
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
                "metadata": {
                    "capabilities": [f"{agent_type}_analysis"],
                    "created_at": datetime.now().isoformat()
                }
            }
            
            # Store agent
            await agent_store.store_agent(agent)
            agents.append(agent)
        
        # Add agents to thread participants
        if "participants" not in thread["metadata"]:
            thread["metadata"]["participants"] = []
        thread["metadata"]["participants"].extend(agents)
        
        # Update thread
        await self.update_thread(thread)
        
        return agents

    async def get_thread_agents(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all agents in a thread."""
        thread = await self.get_thread(thread_id)
        return [
            p for p in thread.get("metadata", {}).get("participants", [])
            if p.get("type") == "agent"
        ]

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
            "metadata": {
                "capabilities": [f"{agent_type}_analysis"],
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Store agent if agent_store provided
        if agent_store:
            await agent_store.store_agent(agent)
        
        # Add agent to thread participants
        if "participants" not in thread["metadata"]:
            thread["metadata"]["participants"] = []
        thread["metadata"]["participants"].append(agent)
        
        # Update thread
        await self.update_thread(thread)
        
        return agent
