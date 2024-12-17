"""Task planner agent implementation."""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..vector_store import VectorStore
from ..memory_types import AgentResponse, DialogueContext
from .base import BaseAgent

logger = logging.getLogger(__name__)

class TaskPlannerAgent(BaseAgent):
    """Task planner agent for creating and managing task plans."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        vector_store: VectorStore
    ):
        """Initialize task planner agent."""
        super().__init__(llm, store, vector_store, agent_type="task_planner")
        self.task_graphs = {}  # Store task graphs by ID
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for task planning."""
        # Get dialogue context if available
        dialogue = content.get('dialogue_context')
        dialogue_text = ""
        if dialogue and isinstance(dialogue, DialogueContext):
            dialogue_text = "\n".join([
                f"{m.agent_type}: {m.content}"
                for m in dialogue.messages[-5:]  # Last 5 messages
            ])
            dialogue_text = f"\nCurrent Dialogue:\n{dialogue_text}\n"
        
        # Format prompt
        return f"""You are a task planner agent. Create a plan to accomplish the given task.
        
        Task Content:
        {json.dumps(content.get('content', ''))}
        {dialogue_text}
        
        Context:
        {json.dumps(content.get('context_analysis', {}))}
        
        Create a task plan in this exact format:
        {{
            "tasks": [
                {{
                    "id": "unique_id",
                    "name": "Task name",
                    "description": "Clear description",
                    "dependencies": ["other_task_ids"],
                    "estimated_time": "time in minutes",
                    "priority": 1-5 score,
                    "status": "pending"
                }}
            ],
            "metadata": {{
                "total_tasks": number,
                "estimated_total_time": "time in minutes",
                "confidence": 0.0-1.0 score
            }}
        }}
        
        Ensure:
        1. Tasks are properly ordered with dependencies
        2. Each task has a clear objective
        3. Time estimates are realistic
        4. Priority reflects importance
        5. Plan is achievable
        
        Respond with properly formatted JSON only."""
    
    async def calculate_plan_confidence(
        self,
        plan: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> float:
        """Calculate confidence in task plan."""
        try:
            # Format prompt for confidence analysis
            prompt = f"""Analyze this task plan and calculate confidence:
            
            Plan:
            {json.dumps(plan)}
            
            Context:
            {json.dumps(context) if context else "No additional context"}
            
            Consider:
            1. Task clarity and specificity
            2. Dependency relationships
            3. Time estimates
            4. Priority assignments
            5. Overall achievability
            
            Provide confidence score in this format:
            {{
                "confidence": 0.0-1.0 score,
                "reasoning": ["List of reasons"]
            }}
            
            Respond with properly formatted JSON only."""
            
            # Get confidence analysis
            response = await self.llm.get_completion(prompt)
            
            try:
                result = json.loads(response)
                return float(result.get("confidence", 0.5))
            except (json.JSONDecodeError, ValueError):
                logger.error("Failed to parse confidence analysis")
                return 0.5
                
        except Exception as e:
            logger.error(f"Error calculating plan confidence: {str(e)}")
            return 0.5
    
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
