"""
Reflection agent for analyzing patterns and growth.
"""

import logging
from typing import Dict, Any
from .base import BaseAgent
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..prompts import REFLECTION_PROMPT

logger = logging.getLogger(__name__)

class ReflectionAgent(BaseAgent):
    """Agent for analyzing patterns and tracking growth."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore
    ):
        """Initialize reflection agent."""
        super().__init__(llm, store, "reflection")
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for reflection analysis."""
        # Format content for prompt
        formatted_content = []
        
        # Add original content
        if isinstance(content.get('content'), str):
            formatted_content.append(f"Content: {content['content']}")
        
        # Add any command results
        if content.get('command_result'):
            result = content['command_result']
            formatted_content.append("Command Result:")
            formatted_content.append(f"Success: {result.get('success', False)}")
            if result.get('output'):
                formatted_content.append(f"Output: {result['output']}")
            if result.get('error'):
                formatted_content.append(f"Error: {result['error']}")
        
        # Add any system info
        if content.get('systems_info'):
            formatted_content.append("Systems Information:")
            for info in content['systems_info']:
                system = info['system']
                formatted_content.append(f"- {system['name']} ({system['type']})")
                formatted_content.append(f"  Created: {system['created_at']}")
                if system.get('capabilities'):
                    formatted_content.append("  Capabilities:")
                    for cap in system['capabilities']:
                        formatted_content.append(f"  - {cap['description']} ({cap['type']})")
                if info.get('relationships'):
                    formatted_content.append("  Relationships:")
                    for rel in info['relationships']:
                        formatted_content.append(f"  - {rel['relationship_type']} -> {rel['target_name']}")
        
        # Add any related memories
        if content.get('related_memories'):
            formatted_content.append("Related Memories:")
            for memory in content['related_memories']:
                formatted_content.append(f"- {memory['type']} ({memory['created_at']})")
                if isinstance(memory.get('content'), str):
                    formatted_content.append(f"  Content: {memory['content'][:100]}...")
                if memory.get('relationships'):
                    formatted_content.append("  Relationships:")
                    for rel in memory['relationships']:
                        formatted_content.append(f"  - {rel['type']} -> {rel['target_type']}")
        
        # Format final prompt
        return REFLECTION_PROMPT.format(
            content="\n".join(formatted_content)
        )
