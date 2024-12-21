"""Task agent for planning and execution analysis."""

import logging
from .base import BaseAgent

logger = logging.getLogger(__name__)

class TaskAgent(BaseAgent):
    """Agent for analyzing and planning tasks."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize task agent."""
        super().__init__(llm, store, vector_store, "task")
