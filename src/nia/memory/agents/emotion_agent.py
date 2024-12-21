"""
Enhanced emotion agent implementation using LLMs for all operations.
"""

import logging
from typing import Dict, Any
from .base import BaseAgent

logger = logging.getLogger(__name__)

class EmotionAgent(BaseAgent):
    """Agent for emotional processing and analysis."""
    
    def __init__(self, *args, **kwargs):
        """Initialize emotion agent."""
        super().__init__(*args, agent_type="emotion", **kwargs)
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        # Get content text
        text = content.get('content', '')
        
        # Get similar memories for emotional context
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
        prompt = f"""Analyze the following content from an emotional intelligence perspective.
        Consider emotional states, affective patterns, and emotional implications.
        
        Content:
        {text}
        
        Emotional Context:
        {memory_text}
        
        Known Concepts:
        {concept_text}
        
        Provide analysis in this exact format:
        {{
            "response": "Detailed analysis from emotional perspective",
            "concepts": [
                {{
                    "name": "Concept name",
                    "type": "emotion|affect|pattern|response",
                    "description": "Clear description of the emotional concept",
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
                "Key point about emotional content"
            ],
            "implications": [
                "Implication for emotional understanding"
            ],
            "uncertainties": [
                "Uncertainty in emotional interpretation"
            ],
            "reasoning": [
                "Step in emotional analysis"
            ]
        }}
        
        Focus on:
        - Emotional states and patterns
        - Affective responses and triggers
        - Emotional context and history
        - Relationship dynamics
        - Emotional intelligence insights
        
        Return ONLY the JSON object, no other text."""
        
        return prompt
