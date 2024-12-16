"""
Task planner for creating and managing task graphs.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .types import TaskType, AgentType, TaskContext
from .task_node import TaskNode
from .task_graph import TaskGraph

logger = logging.getLogger(__name__)

class TaskPlanner:
    """Plans and creates task graphs for complex operations."""
    
    def __init__(self):
        """Initialize task planner."""
        self.active_graphs: Dict[str, TaskGraph] = {}
        self.completed_graphs: Dict[str, TaskGraph] = {}
        self.failed_graphs: Dict[str, TaskGraph] = {}
    
    def create_interaction_graph(
        self,
        content: str,
        graph_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> TaskGraph:
        """Create a task graph for processing an interaction."""
        # Create graph
        graph = TaskGraph(
            name=f"Interaction_{datetime.now().isoformat()}",
            description=f"Process interaction: {content[:100]}..."
        )
        
        # Create analysis task
        analysis = TaskNode(
            task_id="analyze_input",
            task_type=TaskType.ANALYSIS,
            agent_type=AgentType.META,
            description="Analyze user input and determine required actions",
            inputs={
                "content": content,
                "context": context or {}
            }
        )
        
        # Create memory check task
        memory = TaskNode(
            task_id="check_memory",
            task_type=TaskType.MEMORY,
            agent_type=AgentType.MEMORY,
            description="Check memory for relevant context",
            inputs={
                "content": content,
                "context": context or {}
            }
        )
        
        # Create belief update task
        beliefs = TaskNode(
            task_id="update_beliefs",
            task_type=TaskType.ANALYSIS,
            agent_type=AgentType.BELIEF,
            description="Update belief state based on input",
            inputs={
                "content": content,
                "context": context or {}
            }
        )
        
        # Create desire update task
        desires = TaskNode(
            task_id="update_desires",
            task_type=TaskType.ANALYSIS,
            agent_type=AgentType.DESIRE,
            description="Update desire state based on input",
            inputs={
                "content": content,
                "context": context or {}
            }
        )
        
        # Create emotion update task
        emotions = TaskNode(
            task_id="update_emotions",
            task_type=TaskType.ANALYSIS,
            agent_type=AgentType.EMOTION,
            description="Update emotional state based on input",
            inputs={
                "content": content,
                "context": context or {}
            }
        )
        
        # Create planning task
        planning = TaskNode(
            task_id="plan_response",
            task_type=TaskType.PLANNING,
            agent_type=AgentType.META,
            description="Plan response based on analysis and state updates"
        )
        
        # Create execution task
        execution = TaskNode(
            task_id="execute_response",
            task_type=TaskType.EXECUTION,
            agent_type=AgentType.META,
            description="Execute planned response"
        )
        
        # Create reflection task
        reflection = TaskNode(
            task_id="reflect",
            task_type=TaskType.REFLECTION,
            agent_type=AgentType.REFLECTION,
            description="Reflect on interaction and update memory"
        )
        
        # Add all tasks to graph
        graph.add_task(analysis)
        graph.add_task(memory)
        graph.add_task(beliefs)
        graph.add_task(desires)
        graph.add_task(emotions)
        graph.add_task(planning)
        graph.add_task(execution)
        graph.add_task(reflection)
        
        # Add dependencies
        
        # Planning depends on all analysis and state updates
        graph.add_dependency("plan_response", "analyze_input")
        graph.add_dependency("plan_response", "check_memory")
        graph.add_dependency("plan_response", "update_beliefs")
        graph.add_dependency("plan_response", "update_desires")
        graph.add_dependency("plan_response", "update_emotions")
        
        # Execution depends on planning
        graph.add_dependency("execute_response", "plan_response")
        
        # Reflection depends on execution
        graph.add_dependency("reflect", "execute_response")
        
        # Store and return graph
        self.active_graphs[graph_id or graph.name] = graph
        return graph
    
    def create_research_graph(
        self,
        query: str,
        graph_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> TaskGraph:
        """Create a task graph for research tasks."""
        # Create graph
        graph = TaskGraph(
            name=f"Research_{datetime.now().isoformat()}",
            description=f"Research query: {query[:100]}..."
        )
        
        # Create analysis task
        analysis = TaskNode(
            task_id="analyze_query",
            task_type=TaskType.ANALYSIS,
            agent_type=AgentType.META,
            description="Analyze research query",
            inputs={
                "query": query,
                "context": context or {}
            }
        )
        
        # Create memory check task
        memory = TaskNode(
            task_id="check_memory",
            task_type=TaskType.MEMORY,
            agent_type=AgentType.MEMORY,
            description="Check memory for relevant research",
            inputs={
                "query": query,
                "context": context or {}
            }
        )
        
        # Create research task
        research = TaskNode(
            task_id="conduct_research",
            task_type=TaskType.RESEARCH,
            agent_type=AgentType.RESEARCH,
            description="Conduct research based on query",
            inputs={
                "query": query,
                "context": context or {}
            }
        )
        
        # Create synthesis task
        synthesis = TaskNode(
            task_id="synthesize_results",
            task_type=TaskType.SYNTHESIS,
            agent_type=AgentType.META,
            description="Synthesize research results"
        )
        
        # Create memory update task
        memory_update = TaskNode(
            task_id="update_memory",
            task_type=TaskType.MEMORY,
            agent_type=AgentType.MEMORY,
            description="Update memory with research findings"
        )
        
        # Add all tasks to graph
        graph.add_task(analysis)
        graph.add_task(memory)
        graph.add_task(research)
        graph.add_task(synthesis)
        graph.add_task(memory_update)
        
        # Add dependencies
        
        # Research depends on analysis and memory check
        graph.add_dependency("conduct_research", "analyze_query")
        graph.add_dependency("conduct_research", "check_memory")
        
        # Synthesis depends on research
        graph.add_dependency("synthesize_results", "conduct_research")
        
        # Memory update depends on synthesis
        graph.add_dependency("update_memory", "synthesize_results")
        
        # Store and return graph
        self.active_graphs[graph_id or graph.name] = graph
        return graph
    
    def get_graph(self, graph_id: str) -> Optional[TaskGraph]:
        """Get a graph by ID."""
        return (
            self.active_graphs.get(graph_id) or
            self.completed_graphs.get(graph_id) or
            self.failed_graphs.get(graph_id)
        )
    
    def complete_graph(self, graph_id: str) -> None:
        """Mark a graph as completed."""
        if graph_id in self.active_graphs:
            graph = self.active_graphs.pop(graph_id)
            self.completed_graphs[graph_id] = graph
    
    def fail_graph(self, graph_id: str) -> None:
        """Mark a graph as failed."""
        if graph_id in self.active_graphs:
            graph = self.active_graphs.pop(graph_id)
            self.failed_graphs[graph_id] = graph
    
    def cleanup(self) -> None:
        """Clean up completed and failed graphs."""
        self.completed_graphs.clear()
        self.failed_graphs.clear()
