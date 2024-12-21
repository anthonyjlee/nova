"""Dialogue agent for conversation flow analysis."""

import logging
from .base import BaseAgent

logger = logging.getLogger(__name__)

class DialogueAgent(BaseAgent):
    """Agent for analyzing dialogue and conversation flow."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize dialogue agent."""
        super().__init__(llm, store, vector_store, "dialogue")
