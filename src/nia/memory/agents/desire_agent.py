"""Desire agent for goal and motivation analysis."""

import logging
from typing import Dict, Any
from .base import BaseAgent

logger = logging.getLogger(__name__)

class DesireAgent(BaseAgent):
    """Agent for analyzing goals and motivations."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize desire agent."""
        super().__init__(llm, store, vector_store, "desire")
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for desire analysis."""
        return f"""Analyze the goals, motivations, and desires in this content:

Content:
{content.get('content', '')}

Provide analysis in this format:
{{
    "response": "Clear analysis of goals and motivations",
    "concepts": [
        {{
            "name": "Goal/Motivation concept",
            "type": "goal|motivation|aspiration|desire",
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
        "Key motivational insight"
    ],
    "implications": [
        "Important implication for goals/desires"
    ],
    "uncertainties": [
        "Area of uncertainty"
    ],
    "reasoning": [
        "Step in analysis"
    ]
}}"""
