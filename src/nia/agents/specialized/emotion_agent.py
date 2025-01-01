"""Emotion agent for affective analysis."""

import logging
from typing import Dict, Any
from ..base import BaseAgent
from ...memory.prompts import AGENT_PROMPTS

logger = logging.getLogger(__name__)

class EmotionAgent(BaseAgent):
    """Agent for analyzing emotional content."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize emotion agent."""
        super().__init__(llm, store, vector_store, "emotion")
        
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for emotion analysis."""
        text = content.get('content', '')
        return AGENT_PROMPTS["emotion"].format(content=text)
