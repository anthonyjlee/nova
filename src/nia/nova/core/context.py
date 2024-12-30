"""Context agent for environmental understanding."""

import logging
from typing import Dict, Any
from .base import BaseAgent
from ..prompts import AGENT_PROMPTS

logger = logging.getLogger(__name__)

class ContextAgent(BaseAgent):
    """Agent for analyzing context and environment."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize context agent."""
        super().__init__(llm, store, vector_store, "context")
        
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for context analysis."""
        text = content.get('content', '')
        return AGENT_PROMPTS["context"].format(content=text)
