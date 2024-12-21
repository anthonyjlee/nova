"""Research agent for knowledge integration."""

import logging
from typing import Dict, Any
from .agents.base import BaseAgent

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    """Agent for analyzing and integrating knowledge."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize research agent."""
        super().__init__(llm, store, vector_store, "research")
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for research analysis."""
        return f"""Analyze the knowledge and research aspects in this content:

Content:
{content.get('content', '')}

Provide analysis in this format:
{{
    "response": "Clear analysis of knowledge and research",
    "concepts": [
        {{
            "name": "Research/Knowledge concept",
            "type": "knowledge|source|connection|gap",
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
        "Key research insight"
    ],
    "implications": [
        "Important implication for knowledge"
    ],
    "uncertainties": [
        "Area of uncertainty"
    ],
    "reasoning": [
        "Step in analysis"
    ]
}}"""
