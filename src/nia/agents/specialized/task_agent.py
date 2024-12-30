"""Task agent for planning and execution analysis."""

import logging
from typing import Dict, Any
from ..base import BaseAgent
from ..prompts import AGENT_PROMPTS

logger = logging.getLogger(__name__)

class TaskAgent(BaseAgent):
    """Agent for analyzing and planning tasks."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize task agent."""
        super().__init__(llm, store, vector_store, "task")
        
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for task analysis."""
        text = content.get('content', '')
        return AGENT_PROMPTS["task"].format(content=text)
