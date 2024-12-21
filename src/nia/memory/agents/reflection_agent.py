"""Reflection agent for meta-learning and pattern analysis."""

import logging
from .base import BaseAgent

logger = logging.getLogger(__name__)

class ReflectionAgent(BaseAgent):
    """Agent for analyzing patterns and meta-learning."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize reflection agent."""
        super().__init__(llm, store, vector_store, "reflection")
