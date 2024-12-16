"""
Task graph management for DAG system.
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
import json
from collections import deque

from .types import TaskStatus, TaskType, AgentType, TaskResult, TaskContext
from .task_node import TaskNode

logger = logging.getLogger(__name__)

class CyclicDependencyError(Exception):
    """Raised when a cyclic dependency is detected."""
    pass

class TaskNotFoundError(Exception):
    """Raised when a task is not found in the graph."""
    pass

class TaskGraph:
    """Manages a directed acyclic graph of tasks."""
    
    def __init__(self, name: str = "", description: str = ""):
        """Initialize task graph."""
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        
        # Task management
        self.tasks: Dict[str, TaskNode] = {}
        self.root_tasks: Set[str] = set()  # Tasks with no dependencies
        self.leaf_tasks: Set[str] = set()  # Tasks with no dependents
        
        # State tracking
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        self.cancelled_tasks: Set[str] = set()
        self.running_tasks: Set[str] = set()
        
        # Execution tracking
        self.execution_order: List[str] = []
        self.last_executed: Optional[str] = None
        self.error_history: List[Tuple[str, str]] = []  # (task_id, error)
    
    def add_task(self, task: TaskNode) -> None:
        """Add a task to the graph."""
        if task.task_id in self.tasks:
            logger.warning(f"Task {task.task_id} already exists, updating")
        
        self.tasks[task.task_id] = task
        
        # Update root and leaf sets
        if not task.dependencies:
            self.root_tasks.add(task.task_id)
        if not task.dependents:
            self.leaf_tasks.add(task.task_id)
    
    def remove_task(self, task_id: str) -> None:
        """Remove a task from the graph."""
        if task_id not in self.tasks:
            raise TaskNotFoundError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        
        # Remove dependencies
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                self.tasks[dep_id].dependents.discard(task_id)
                if not self.tasks[dep_id].dependents:
                    self.leaf_tasks.add(dep_id)
        
        # Remove dependents
        for dep_id in task.dependents:
            if dep_id in self.tasks:
                self.tasks[dep_id].dependencies.discard(task_id)
                if not self.tasks[dep_id].dependencies:
                    self.root_tasks.add(dep_id)
        
        # Remove from tracking sets
        self.root_tasks.discard(task_id)
        self.leaf_tasks.discard(task_id)
        self.completed_tasks.discard(task_id)
        self.failed_tasks.discard(task_id)
        self.cancelled_tasks.discard(task_id)
        self.running_tasks.discard(task_id)
        
        # Remove from tasks dict
        del self.tasks[task_id]
    
    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """Add a dependency between tasks."""
        if task_id not in self.tasks:
            raise TaskNotFoundError(f"Task {task_id} not found")
        if depends_on not in self.tasks:
            raise TaskNotFoundError(f"Dependency task {depends_on} not found")
        if task_id == depends_on:
            raise ValueError("Task cannot depend on itself")
        
        # Add dependency
        self.tasks[task_id].add_dependency(depends_on)
        self.tasks[depends_on].add_dependent(task_id)
        
        # Update root and leaf sets
        self.root_tasks.discard(task_id)
        self.leaf_tasks.discard(depends_on)
        
        # Check for cycles
        if self._has_cycle():
            # Rollback changes
            self.tasks[task_id].remove_dependency(depends_on)
            self.tasks[depends_on].remove_dependent(task_id)
            if not self.tasks[task_id].dependencies:
                self.root_tasks.add(task_id)
            if not self.tasks[depends_on].dependents:
                self.leaf_tasks.add(depends_on)
            raise CyclicDependencyError(f"Adding dependency from {task_id} to {depends_on} would create a cycle")
    
    def remove_dependency(self, task_id: str, depends_on: str) -> None:
        """Remove a dependency between tasks."""
        if task_id not in self.tasks:
            raise TaskNotFoundError(f"Task {task_id} not found")
        if depends_on not in self.tasks:
            raise TaskNotFoundError(f"Dependency task {depends_on} not found")
        
        # Remove dependency
        self.tasks[task_id].remove_dependency(depends_on)
        self.tasks[depends_on].remove_dependent(task_id)
        
        # Update root and leaf sets
        if not self.tasks[task_id].dependencies:
            self.root_tasks.add(task_id)
        if not self.tasks[depends_on].dependents:
            self.leaf_tasks.add(depends_on)
    
    def get_ready_tasks(self) -> List[str]:
        """Get list of tasks ready to execute."""
        ready_tasks = []
        for task_id, task in self.tasks.items():
            if (task.status == TaskStatus.PENDING and 
                not task.dependencies and 
                task_id not in self.running_tasks):
                ready_tasks.append(task_id)
        return ready_tasks
    
    def get_blocked_tasks(self) -> List[str]:
        """Get list of tasks blocked by dependencies."""
        return [
            task_id for task_id, task in self.tasks.items()
            if task.status == TaskStatus.PENDING and task.dependencies
        ]
    
    def get_task_order(self) -> List[str]:
        """Get topologically sorted list of tasks."""
        if not self.tasks:
            return []
        
        # Initialize
        result = []
        visited = set()
        temp_visited = set()
        
        def visit(task_id: str) -> None:
            """Visit a task in topological sort."""
            if task_id in temp_visited:
                raise CyclicDependencyError("Cycle detected during topological sort")
            if task_id in visited:
                return
            
            temp_visited.add(task_id)
            task = self.tasks[task_id]
            for dep_id in sorted(task.dependencies):  # Sort for deterministic order
                visit(dep_id)
            temp_visited.remove(task_id)
            visited.add(task_id)
            result.append(task_id)
        
        # Visit all tasks
        for task_id in sorted(self.tasks.keys()):  # Sort for deterministic order
            if task_id not in visited:
                visit(task_id)
        
        return result
    
    def _has_cycle(self) -> bool:
        """Check if graph has a cycle."""
        visited = set()
        temp_visited = set()
        
        def visit(task_id: str) -> bool:
            """Visit a task in cycle detection."""
            if task_id in temp_visited:
                return True
            if task_id in visited:
                return False
            
            temp_visited.add(task_id)
            task = self.tasks[task_id]
            for dep_id in task.dependencies:
                if visit(dep_id):
                    return True
            temp_visited.remove(task_id)
            visited.add(task_id)
            return False
        
        # Check all tasks
        for task_id in self.tasks:
            if task_id not in visited:
                if visit(task_id):
                    return True
        return False
    
    def validate(self) -> List[str]:
        """Validate graph structure and return list of errors."""
        errors = []
        
        # Check for cycles
        try:
            self.get_task_order()
        except CyclicDependencyError:
            errors.append("Graph contains cyclic dependencies")
        
        # Check for missing dependencies
        for task_id, task in self.tasks.items():
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    errors.append(f"Task {task_id} depends on missing task {dep_id}")
        
        # Check for orphaned tasks
        for task_id, task in self.tasks.items():
            if not task.dependencies and task_id not in self.root_tasks:
                errors.append(f"Task {task_id} should be in root_tasks")
            if not task.dependents and task_id not in self.leaf_tasks:
                errors.append(f"Task {task_id} should be in leaf_tasks")
        
        return errors
    
    def reset(self) -> None:
        """Reset all tasks to initial state."""
        for task in self.tasks.values():
            task.reset()
        
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        self.cancelled_tasks.clear()
        self.running_tasks.clear()
        self.execution_order.clear()
        self.last_executed = None
        self.error_history.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'tasks': {
                task_id: task.to_dict()
                for task_id, task in self.tasks.items()
            },
            'root_tasks': list(self.root_tasks),
            'leaf_tasks': list(self.leaf_tasks),
            'completed_tasks': list(self.completed_tasks),
            'failed_tasks': list(self.failed_tasks),
            'cancelled_tasks': list(self.cancelled_tasks),
            'running_tasks': list(self.running_tasks),
            'execution_order': self.execution_order,
            'last_executed': self.last_executed,
            'error_history': [
                {'task_id': task_id, 'error': error}
                for task_id, error in self.error_history
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskGraph':
        """Create graph from dictionary."""
        graph = cls(
            name=data['name'],
            description=data['description']
        )
        
        graph.created_at = datetime.fromisoformat(data['created_at'])
        
        # Restore tasks
        for task_id, task_data in data['tasks'].items():
            task = TaskNode.from_dict(task_data)
            graph.add_task(task)
        
        # Restore sets
        graph.root_tasks = set(data['root_tasks'])
        graph.leaf_tasks = set(data['leaf_tasks'])
        graph.completed_tasks = set(data['completed_tasks'])
        graph.failed_tasks = set(data['failed_tasks'])
        graph.cancelled_tasks = set(data['cancelled_tasks'])
        graph.running_tasks = set(data['running_tasks'])
        
        # Restore lists
        graph.execution_order = data['execution_order']
        graph.last_executed = data['last_executed']
        graph.error_history = [
            (error['task_id'], error['error'])
            for error in data['error_history']
        ]
        
        return graph
    
    def to_json(self, indent: int = 2) -> str:
        """Convert graph to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TaskGraph':
        """Create graph from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
