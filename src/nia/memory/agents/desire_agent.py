"""
Enhanced desire agent implementation using LLMs for all operations.
"""

import logging
from typing import Dict, Any
from .base import BaseAgent

logger = logging.getLogger(__name__)

class DesireAgent(BaseAgent):
    """Agent for analyzing goals, motivations, and aspirations."""
    
    def __init__(self, *args, **kwargs):
        """Initialize desire agent."""
        super().__init__(*args, agent_type="desire", **kwargs)
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        # Get content text
        text = content.get('content', '')
        
        # Get similar memories for goal context
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
        prompt = f"""Analyze the following content from a motivational and goal-oriented perspective.
        Consider desires, aspirations, objectives, and underlying motivations.
        
        Content:
        {text}
        
        Goal Context:
        {memory_text}
        
        Known Concepts:
        {concept_text}
        
        Provide analysis in this exact format:
        {{
            "response": "Detailed analysis from desire perspective",
            "concepts": [
                {{
                    "name": "Concept name",
                    "type": "goal|motivation|aspiration|desire",
                    "description": "Clear description of the motivational concept",
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
                "Key point about goals and motivations"
            ],
            "implications": [
                "Implication for goal pursuit"
            ],
            "uncertainties": [
                "Uncertainty in motivation analysis"
            ],
            "reasoning": [
                "Step in desire analysis"
            ]
        }}
        
        Focus on:
        - Short and long-term goals
        - Underlying motivations
        - Goal relationships and dependencies
        - Progress indicators
        - Potential obstacles
        - Growth aspirations
        
        Return ONLY the JSON object, no other text."""
        
        return prompt
