"""Desire agent for goal and motivation analysis."""

import logging
from .base import BaseAgent

logger = logging.getLogger(__name__)

class DesireAgent(BaseAgent):
    """Agent for analyzing goals and motivations."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize desire agent."""
        super().__init__(llm, store, vector_store, "desire")
