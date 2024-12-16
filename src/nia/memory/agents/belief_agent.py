"""
Belief system agent implementation.
"""

import logging
from typing import Dict, Any
from .base import BaseAgent

logger = logging.getLogger(__name__)

class BeliefAgent(BaseAgent):
    """Agent for managing belief system."""
    
    def __init__(self, *args, **kwargs):
        """Initialize belief agent."""
        super().__init__(*args, agent_type="belief", **kwargs)
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        # Get content text
        text = content.get('content', '')
        
        # Get similar memories
        memories = content.get('similar_memories', [])
        memory_text = '\n'.join([
            f"Memory {i+1}: {m.get('content', {}).get('content', '')}"
            for i, m in enumerate(memories)
        ])
        
        # Format prompt
        prompt = f"""Analyze the following content from a belief system perspective.
        Extract key concepts and their relationships.
        
        Content: {text}
        
        Similar Memories:
        {memory_text}
        
        Respond with a list of concepts in this exact format:
        [
          {{
            "CONCEPT": "Concept name",
            "TYPE": "Concept type",
            "DESC": "Clear description",
            "RELATED": "Space separated list of related concepts"
          }}
        ]
        
        Focus on beliefs, worldview, and philosophical concepts.
        IMPORTANT: Ensure the response starts with the JSON array and contains proper JSON formatting with commas between objects."""
        
        return prompt
