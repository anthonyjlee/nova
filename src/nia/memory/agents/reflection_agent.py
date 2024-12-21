"""Reflection agent for meta-learning and pattern analysis."""

import logging
from typing import Dict, Any
from .base import BaseAgent

logger = logging.getLogger(__name__)

class ReflectionAgent(BaseAgent):
    """Agent for analyzing patterns and meta-learning."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize reflection agent."""
        super().__init__(llm, store, vector_store, "reflection")
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for reflection analysis."""
        return f"""Analyze the patterns and meta-learning aspects in this content:

Content:
{content.get('content', '')}

Provide analysis in this format:
{{
    "response": "Clear analysis of patterns and learning",
    "concepts": [
        {{
            "name": "Pattern/Learning concept",
            "type": "pattern|insight|learning|evolution",
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
        "Key pattern or learning insight"
    ],
    "implications": [
        "Important implication for learning/growth"
    ],
    "uncertainties": [
        "Area of uncertainty"
    ],
    "reasoning": [
        "Step in analysis"
    ]
}}"""
