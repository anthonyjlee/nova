"""Desire agent for goal and motivation analysis."""

import logging
from typing import Dict, Any
from ..base import BaseAgent
from ..prompts import AGENT_PROMPTS

logger = logging.getLogger(__name__)

class DesireAgent(BaseAgent):
    """Agent for analyzing goals and motivations."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize desire agent."""
        super().__init__(llm, store, vector_store, "desire")
        
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for desire analysis."""
        text = content.get('content', '')
        return AGENT_PROMPTS["desire"].format(content=text)
