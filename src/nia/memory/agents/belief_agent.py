"""Belief agent for analyzing knowledge and beliefs."""

import logging
from typing import Dict, Any
from .base import BaseAgent
from ..prompts import AGENT_PROMPTS

logger = logging.getLogger(__name__)

class BeliefAgent(BaseAgent):
    """Agent for analyzing beliefs and knowledge."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize belief agent."""
        super().__init__(llm, store, vector_store, "belief")
        
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for belief analysis."""
        text = content.get('content', '')
        return AGENT_PROMPTS["belief"].format(content=text)
