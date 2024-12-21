"""Emotion agent for affective analysis."""

import logging
from .base import BaseAgent

logger = logging.getLogger(__name__)

class EmotionAgent(BaseAgent):
    """Agent for analyzing emotional content."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize emotion agent."""
        super().__init__(llm, store, vector_store, "emotion")
