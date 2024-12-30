"""Dialogue agent for conversation flow analysis."""

import logging
from typing import Dict, Any
from ..base import BaseAgent
from ..prompts import AGENT_PROMPTS

logger = logging.getLogger(__name__)

class DialogueAgent(BaseAgent):
    """Agent for analyzing dialogue and conversation flow."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize dialogue agent."""
        super().__init__(llm, store, vector_store, "dialogue")
        
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for dialogue analysis."""
        text = content.get('content', '')
        return AGENT_PROMPTS["dialogue"].format(content=text)
