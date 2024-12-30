"""Task planner agent implementation."""

import logging
from typing import Dict, Any, Optional
from .base import BaseAgent
from ..prompts import AGENT_PROMPTS

logger = logging.getLogger(__name__)

class TaskPlannerAgent(BaseAgent):
    """Task planner agent for creating and managing task plans."""
    
    def __init__(self, *args, **kwargs):
        """Initialize task planner agent."""
        super().__init__(*args, agent_type="task_planner", **kwargs)
        self.task_graphs = {}  # Store task graphs by ID
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for task planning."""
        # Get content text
        text = content.get('content', '')
        
        # Get dialogue context if available
        dialogue = content.get('dialogue_context')
        dialogue_text = ""
        if dialogue:
            dialogue_text = "\n".join([
                f"{m.agent_type}: {m.content}"
                for m in dialogue.messages[-5:]  # Last 5 messages
            ])
            dialogue_text = f"\nCurrent Dialogue:\n{dialogue_text}\n"
        
        # Get relevant concepts
        concepts = content.get('relevant_concepts', [])
        concept_text = '\n'.join([
            f"Concept {i+1}: {c.get('name')} ({c.get('type')}) - {c.get('description')}"
            for i, c in enumerate(concepts)
        ])
        
        # Format prompt with context
        content_with_context = f"""Task Content:
{text}
{dialogue_text}

Known Concepts:
{concept_text}"""
        
        return AGENT_PROMPTS["task_planner"].format(content=content_with_context)
    
    def get_graph(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Get task graph by ID."""
        return self.task_graphs.get(graph_id)
    
    def update_task_status(
        self,
        graph_id: str,
        task_id: str,
        status: str
    ) -> bool:
        """Update task status in graph."""
        graph = self.task_graphs.get(graph_id)
        if not graph:
            return False
        
        for task in graph.get("tasks", []):
            if task["id"] == task_id:
                task["status"] = status
                return True
        
        return False
