"""
Meta agent for synthesizing responses from other agents.
"""

import logging
from typing import Dict, Any
from .base import BaseAgent
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..vector_store import VectorStore
from ..prompts import META_PROMPT

logger = logging.getLogger(__name__)

class MetaAgent(BaseAgent):
    """Agent for synthesizing responses."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        vector_store: VectorStore
    ):
        """Initialize meta agent."""
        super().__init__(llm, store, vector_store, "meta")
    
    async def synthesize_responses(
        self,
        responses: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """Synthesize responses from other agents."""
        try:
            # Format content for synthesis
            content = {
                "agent_responses": responses,
                **context
            }
            
            # Process through meta agent
            return await self.process(content)
            
        except Exception as e:
            logger.error(f"Error synthesizing responses: {str(e)}")
            raise
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for response synthesis."""
        # Format content for prompt
        formatted_content = []
        
        # Add agent responses
        if content.get('agent_responses'):
            formatted_content.append("Agent Responses:")
            for agent_type, response in content['agent_responses'].items():
                formatted_content.append(f"\n{agent_type.upper()} RESPONSE:")
                formatted_content.append(f"Response: {response.response}")
                formatted_content.append("Analysis:")
                for point in response.analysis.key_points:
                    formatted_content.append(f"- {point}")
                formatted_content.append(f"Confidence: {response.analysis.confidence}")
                formatted_content.append(f"State Update: {response.analysis.state_update}")
        
        # Add original content
        if content.get('original_content'):
            if isinstance(content['original_content'], str):
                formatted_content.append(f"\nOriginal Content: {content['original_content']}")
            elif isinstance(content['original_content'], dict):
                formatted_content.append("\nOriginal Content:")
                for key, value in content['original_content'].items():
                    formatted_content.append(f"{key}: {value}")
        
        # Add any system info
        if content.get('systems_info'):
            formatted_content.append("\nSystems Information:")
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
        if content.get('similar_memories'):
            formatted_content.append("\nSimilar Memories:")
            for memory in content['similar_memories']:
                formatted_content.append(f"- {memory['type']} ({memory['created_at']})")
                if isinstance(memory.get('content'), str):
                    formatted_content.append(f"  Content: {memory['content'][:100]}...")
                if memory.get('relationships'):
                    formatted_content.append("  Relationships:")
                    for rel in memory['relationships']:
                        formatted_content.append(f"  - {rel['type']} -> {rel['target_type']}")
        
        # Format final prompt
        return META_PROMPT.format(
            content="\n".join(formatted_content)
        )
