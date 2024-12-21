"""Context agent for environmental understanding."""

import logging
from .base import BaseAgent

logger = logging.getLogger(__name__)

class ContextAgent(BaseAgent):
    """Agent for analyzing context and environment."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize context agent."""
        super().__init__(llm, store, vector_store, "context")
