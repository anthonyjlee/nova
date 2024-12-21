"""Belief agent for epistemological analysis."""

import logging
from .base import BaseAgent

logger = logging.getLogger(__name__)

class BeliefAgent(BaseAgent):
    """Agent for analyzing beliefs and knowledge."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize belief agent."""
        super().__init__(llm, store, vector_store, "belief")
