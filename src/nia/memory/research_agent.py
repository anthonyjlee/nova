"""Research agent for knowledge integration."""

import logging
from .agents.base import BaseAgent

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    """Agent for analyzing and integrating knowledge."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize research agent."""
        super().__init__(llm, store, vector_store, "research")
