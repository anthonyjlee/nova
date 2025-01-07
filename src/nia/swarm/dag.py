"""Swarm DAG implementation for task execution flow."""

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class TaskNode:
    """Represents a task node in the execution graph."""
    
    def __init__(
        self,
        task_id: str,
        task_type: str,
        config: Dict[str, Any],
        dependencies: Optional[List[str]] = None
    ):
        """Initialize task node."""
        self.task_id = task_id
        self.task_type = task_type
        self.config = config
        self.dependencies = dependencies or []
        self.status = "pending"
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "config": self.config,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }

class SwarmDAG:
    """Manages runtime task execution flow."""
    
    def __init__(self):
        """Initialize DAG."""
        self.nodes: Dict[str, TaskNode] = {}
        self.edges: Dict[str, List[str]] = {}  # task_id -> [dependent_task_ids]
        self.reverse_edges: Dict[str, List[str]] = {}  # task_id -> [dependency_task_ids]
    
    async def add_task_node(
        self,
        task_type: str,
        config: Dict[str, Any],
        dependencies: Optional[List[str]] = None
    ) -> str:
        """Add task to execution graph."""
        try:
            # Generate unique task ID
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            
            # Create task node
            node = TaskNode(
                task_id=task_id,
                task_type=task_type,
                config=config,
                dependencies=dependencies
            )
            
            # Add node to graph
            self.nodes[task_id] = node
            self.edges[task_id] = []
            self.reverse_edges[task_id] = []
            
            # Add dependencies if provided
            if dependencies:
                for dep_id in dependencies:
                    if dep_id not in self.nodes:
                        raise ValueError(f"Dependency {dep_id} not found")
                    await self.set_dependency(dep_id, task_id)
            
            return task_id
        except Exception as e:
            logger.error(f"Error adding task node: {str(e)}")
            raise
    
    async def set_dependency(self, dependency_id: str, dependent_id: str) -> None:
        """Set task dependencies."""
        try:
            # Validate task IDs
            if dependency_id not in self.nodes:
                raise ValueError(f"Dependency task {dependency_id} not found")
            if dependent_id not in self.nodes:
                raise ValueError(f"Dependent task {dependent_id} not found")
            
            # Check for cycles
            if await self._would_create_cycle(dependency_id, dependent_id):
                raise ValueError("Adding this dependency would create a cycle")
            
            # Add dependency
            if dependent_id not in self.edges[dependency_id]:
                self.edges[dependency_id].append(dependent_id)
            if dependency_id not in self.reverse_edges[dependent_id]:
                self.reverse_edges[dependent_id].append(dependency_id)
            
            # Update node dependencies
            if dependency_id not in self.nodes[dependent_id].dependencies:
                self.nodes[dependent_id].dependencies.append(dependency_id)
        except Exception as e:
            logger.error(f"Error setting dependency: {str(e)}")
            raise
    
    async def get_execution_order(self) -> List[str]:
        """Get topological sort of tasks."""
        try:
            # Initialize variables
            visited: Set[str] = set()
            temp_visited: Set[str] = set()
            order: List[str] = []
            
            async def visit(task_id: str) -> None:
                """Visit node in topological sort."""
                if task_id in temp_visited:
                    raise ValueError("Graph contains a cycle")
                if task_id not in visited:
                    temp_visited.add(task_id)
                    
                    # Visit dependencies
                    for dep_id in self.reverse_edges[task_id]:
                        await visit(dep_id)
                    
                    temp_visited.remove(task_id)
                    visited.add(task_id)
                    order.append(task_id)
            
            # Visit all nodes
            for task_id in self.nodes:
                if task_id not in visited:
                    await visit(task_id)
            
            return list(reversed(order))
        except Exception as e:
            logger.error(f"Error getting execution order: {str(e)}")
            raise
    
    async def get_ready_tasks(self) -> List[str]:
        """Get tasks ready for execution."""
        try:
            ready_tasks = []
            for task_id, node in self.nodes.items():
                if node.status == "pending":
                    # Check if all dependencies are completed
                    deps_completed = True
                    for dep_id in node.dependencies:
                        if self.nodes[dep_id].status != "completed":
                            deps_completed = False
                            break
                    
                    if deps_completed:
                        ready_tasks.append(task_id)
            return ready_tasks
        except Exception as e:
            logger.error(f"Error getting ready tasks: {str(e)}")
            raise
    
    async def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ) -> None:
        """Update task status and results."""
        try:
            if task_id not in self.nodes:
                raise ValueError(f"Task {task_id} not found")
            
            node = self.nodes[task_id]
            node.status = status
            
            if status == "running":
                node.start_time = datetime.now()
            elif status in ["completed", "failed"]:
                node.end_time = datetime.now()
                node.result = result
                node.error = error
        except Exception as e:
            logger.error(f"Error updating task status: {str(e)}")
            raise
    
    async def get_task_info(self, task_id: str) -> Dict[str, Any]:
        """Get task information."""
        try:
            if task_id not in self.nodes:
                raise ValueError(f"Task {task_id} not found")
            
            node = self.nodes[task_id]
            return {
                **node.to_dict(),
                "dependent_tasks": self.edges[task_id],
                "dependency_tasks": self.reverse_edges[task_id]
            }
        except Exception as e:
            logger.error(f"Error getting task info: {str(e)}")
            raise
    
    async def get_graph_state(self) -> Dict[str, Any]:
        """Get current graph state."""
        try:
            return {
                "nodes": {
                    task_id: node.to_dict()
                    for task_id, node in self.nodes.items()
                },
                "edges": self.edges,
                "reverse_edges": self.reverse_edges
            }
        except Exception as e:
            logger.error(f"Error getting graph state: {str(e)}")
            raise
    
    async def _would_create_cycle(self, dependency_id: str, dependent_id: str) -> bool:
        """Check if adding dependency would create cycle."""
        try:
            visited: Set[str] = set()
            
            async def visit(task_id: str) -> bool:
                """Visit node in cycle check."""
                if task_id == dependency_id:
                    return True
                if task_id in visited:
                    return False
                
                visited.add(task_id)
                for dep_id in self.reverse_edges[task_id]:
                    if await visit(dep_id):
                        return True
                return False
            
            return await visit(dependent_id)
        except Exception as e:
            logger.error(f"Error checking for cycle: {str(e)}")
            raise
