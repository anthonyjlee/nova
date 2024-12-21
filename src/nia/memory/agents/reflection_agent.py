"""
Enhanced reflection agent implementation using LLMs for all operations.
"""

import logging
from typing import Dict, Any
from .base import BaseAgent

logger = logging.getLogger(__name__)

class ReflectionAgent(BaseAgent):
    """Agent for meta-learning and reflection."""
    
    def __init__(self, *args, **kwargs):
        """Initialize reflection agent."""
        super().__init__(*args, agent_type="reflection", **kwargs)
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        # Get content text
        text = content.get('content', '')
        
        # Get similar memories for historical context
        memories = content.get('similar_memories', [])
        memory_text = '\n'.join([
            f"Memory {i+1}: {m.get('content', {}).get('content', '')}"
            for i, m in enumerate(memories)
        ])
        
        # Get relevant concepts
        concepts = content.get('relevant_concepts', [])
        concept_text = '\n'.join([
            f"Concept {i+1}: {c.get('name')} ({c.get('type')}) - {c.get('description')}"
            for i, c in enumerate(concepts)
        ])
        
        # Format prompt
        prompt = f"""Analyze the following content from a reflective and meta-learning perspective.
        Consider patterns, insights, learning opportunities, and system evolution.
        
        Current Content:
        {text}
        
        Historical Context:
        {memory_text}
        
        Known Concepts:
        {concept_text}
        
        Provide analysis in this exact format:
        {{
            "response": "Detailed analysis from reflection perspective",
            "concepts": [
                {{
                    "name": "Concept name",
                    "type": "pattern|insight|learning|evolution",
                    "description": "Clear description of the reflective concept",
                    "related": ["Related concept names"],
                    "validation": {{
                        "confidence": 0.8,
                        "supported_by": ["evidence"],
                        "contradicted_by": [],
                        "needs_verification": []
                    }}
                }}
            ],
            "key_points": [
                "Key point about patterns and insights"
            ],
            "implications": [
                "Implication for learning and evolution"
            ],
            "uncertainties": [
                "Uncertainty in current understanding"
            ],
            "reasoning": [
                "Step in reflection analysis"
            ]
        }}
        
        Focus on:
        - Recurring patterns across experiences
        - Learning opportunities from past interactions
        - Evolution of understanding over time
        - Meta-level insights about the system
        - Growth indicators and potential
        
        Return ONLY the JSON object, no other text."""
        
        return prompt
