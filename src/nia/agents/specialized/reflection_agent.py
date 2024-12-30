"""Reflection agent for meta-learning and pattern analysis."""

import logging
from typing import Dict, Any
from ..base import BaseAgent
from ..prompts import AGENT_PROMPTS

logger = logging.getLogger(__name__)

class ReflectionAgent(BaseAgent):
    """Agent for analyzing patterns and meta-learning."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize reflection agent."""
        super().__init__(llm, store, vector_store, "reflection")
        
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for reflection analysis."""
        text = content.get('content', '')
        return AGENT_PROMPTS["reflection"].format(content=text)
