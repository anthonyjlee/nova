"""Belief agent for epistemological analysis."""

import logging
from typing import Dict, Any
from .base import BaseAgent

logger = logging.getLogger(__name__)

class BeliefAgent(BaseAgent):
    """Agent for analyzing beliefs and knowledge."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize belief agent."""
        super().__init__(llm, store, vector_store, "belief")
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for belief analysis."""
        return f"""Analyze the beliefs and knowledge claims in this content:

Content:
{content.get('content', '')}

Provide analysis in this format:
{{
    "response": "Clear analysis of beliefs and knowledge",
    "concepts": [
        {{
            "name": "Belief/Knowledge concept",
            "type": "belief|knowledge|assumption|evidence",
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
        "Key epistemological insight"
    ],
    "implications": [
        "Important implication for knowledge/belief"
    ],
    "uncertainties": [
        "Area of uncertainty"
    ],
    "reasoning": [
        "Step in analysis"
    ]
}}"""
