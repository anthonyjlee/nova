"""Belief agent for analyzing knowledge and beliefs."""

import logging
from .base import BaseAgent

logger = logging.getLogger(__name__)

class BeliefAgent(BaseAgent):
    """Agent for analyzing beliefs and knowledge."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize belief agent."""
        super().__init__(llm, store, vector_store, "belief")
        
    def _format_prompt(self, content):
        """Format prompt with additional logging."""
        prompt = super()._format_prompt(content)
        logger.debug(f"Belief agent formatted prompt: {prompt}")
        return prompt
