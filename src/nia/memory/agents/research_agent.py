"""Research system agent implementation."""

import logging
from typing import Dict, Any
from .base import BaseAgent
from ..prompts import AGENT_PROMPTS

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    """Agent for managing research system."""
    
    def __init__(self, *args, **kwargs):
        """Initialize research agent."""
        super().__init__(*args, agent_type="research", **kwargs)
    
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
        
        # Format prompt with memories
        content_with_memories = f"""Content:
{text}

Similar Memories:
{memory_text}"""
        
        return AGENT_PROMPTS["research"].format(content=content_with_memories)
