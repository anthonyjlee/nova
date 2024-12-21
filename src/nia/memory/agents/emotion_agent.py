"""Emotion agent for affective analysis."""

import logging
from typing import Dict, Any
from .base import BaseAgent

logger = logging.getLogger(__name__)

class EmotionAgent(BaseAgent):
    """Agent for analyzing emotional content."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize emotion agent."""
        super().__init__(llm, store, vector_store, "emotion")
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for emotional analysis."""
        return f"""Analyze the emotional content and affective patterns in this content:

Content:
{content.get('content', '')}

Provide analysis in this format:
{{
    "response": "Clear analysis of emotional content",
    "concepts": [
        {{
            "name": "Emotional/Affective concept",
            "type": "emotion|affect|pattern|response",
            "description": "Clear description",
            "related": ["Related concepts"],
            "validation": {{
                "confidence": 0.8,
                "supported_by": ["Supporting evidence"],
                "contradicted_by": ["Contradicting evidence"],
                "needs_verification": ["Points needing verification"]
            }}
        }}
    ],
    "key_points": [
        "Key emotional insight"
    ],
    "implications": [
        "Important implication for emotion/affect"
    ],
    "uncertainties": [
        "Area of uncertainty"
    ],
    "reasoning": [
        "Step in analysis"
    ]
}}"""
