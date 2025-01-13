"""Task management functionality for OrchestrationAgent."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import Memory

class TaskManagement:
    """Mixin class for task management capabilities."""
    
    async def create_task(
        self,
        task_id: str,
        task_data: Dict[str, Any],
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Create a new task."""
        # Prepare task data
        task = {
            "task_id": task_id,
            "status": task_data.get("status", "pending"),
            "type": task_data.get("type", "unknown"),
            "content": task_data.get("content", {}),
            "created_at": datetime.now().isoformat(),
            "domain": domain or self.domain,
            "metadata": metadata or {},
            "assigned_agents": task_data.get("assigned_agents", []),
            "dependencies": task_data.get("dependencies", []),
            "resources": task_data.get("resources", {}),
            "swarm_pattern": task_data.get("swarm_pattern"),
            "swarm_type": task_data.get("swarm_type")
        }
        
        # Store task in memory system
        await self.memory_system.episodic.store_memory(
            Memory(
                content=task,
                type="task",
                importance=0.8,
                context={
                    "domain": domain or self.domain,
                    "task_id": task_id,
                    "task_type": task["type"]
                }
            )
        )
        
        # Record task creation reflection
        await self.record_reflection(
            f"Created task {task_id} of type {task['type']} in {task['domain']} domain",
            domain=domain
        )
        
        return task
        
    async def get_task(
        self,
        task_id: str,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Get task details."""
        # Search for task in memory system
        results = await self.memory_system.query_episodic({
            "content": {
                "task_id": task_id,
                "type": "task"
            },
            "filter": {
                "domain": domain or self.domain
            }
        })
        
        if not results:
            raise ValueError(f"Task {task_id} not found")
            
        return results[0].dict()
        
    async def update_task(
        self,
        task_id: str,
        task_data: Dict[str, Any],
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Update task details."""
        # Get existing task
        task = await self.get_task(task_id, domain)
        
        # Update task data
        task.update({
            "status": task_data.get("status", task["status"]),
            "content": task_data.get("content", task["content"]),
            "assigned_agents": task_data.get("assigned_agents", task["assigned_agents"]),
            "dependencies": task_data.get("dependencies", task["dependencies"]),
            "resources": task_data.get("resources", task["resources"]),
            "swarm_pattern": task_data.get("swarm_pattern", task.get("swarm_pattern")),
            "swarm_type": task_data.get("swarm_type", task.get("swarm_type")),
            "updated_at": datetime.now().isoformat(),
            "metadata": {**(task.get("metadata", {})), **(metadata or {})}
        })
        
        # Store updated task
        await self.memory_system.episodic.store_memory(
            Memory(
                content=task,
                type="task",
                importance=0.8,
                context={
                    "domain": domain or self.domain,
                    "task_id": task_id,
                    "task_type": task["type"]
                }
            )
        )
        
        # Record task update reflection
        await self.record_reflection(
            f"Updated task {task_id} status to {task['status']} in {task['domain']} domain",
            domain=domain
        )
        
        return task
        
    async def get_task_dependencies(
        self,
        task_id: str,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """Get task dependencies."""
        # Get task details
        task = await self.get_task(task_id, domain)
        
        # Get dependent tasks
        dependent_tasks = []
        for dep_id in task.get("dependencies", []):
            try:
                dep_task = await self.get_task(dep_id, domain)
                dependent_tasks.append(dep_task)
            except ValueError:
                # Skip missing dependencies
                continue
                
        return dependent_tasks
        
    async def get_task_resources(
        self,
        task_id: str,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Get task resource allocations."""
        # Get task details
        task = await self.get_task(task_id, domain)
        
        # Return resource allocations
        return task.get("resources", {})
        
    async def get_task_agents(
        self,
        task_id: str,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> List[str]:
        """Get agents assigned to task."""
        # Get task details
        task = await self.get_task(task_id, domain)
        
        # Return assigned agents
        return task.get("assigned_agents", [])
