"""
Meta agent for synthesizing responses.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base import BaseAgent, serialize_datetime
from ..memory_types import AgentResponse

logger = logging.getLogger(__name__)

class MetaAgent(BaseAgent):
    """Meta agent for synthesizing responses."""
    
    def __init__(self, *args, **kwargs):
        """Initialize meta agent."""
        super().__init__(*args, agent_type="meta", **kwargs)
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        return f"""Analyze the following content and extract key concepts:
        {content}"""
    
    async def synthesize_responses(
        self,
        responses: Dict[str, AgentResponse],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """Synthesize responses from multiple agents."""
        try:
            # Combine all concepts from agent responses
            all_concepts = []
            for agent_type, response in responses.items():
                all_concepts.extend(response.concepts)
            
            # Create synthesized response text
            response_text = "Based on my analysis:\n\n"
            
            # Add belief perspective
            if responses.get('belief'):
                response_text += f"From a belief perspective: {responses['belief'].response}\n\n"
            
            # Add desire perspective
            if responses.get('desire'):
                response_text += f"Regarding desires and goals: {responses['desire'].response}\n\n"
            
            # Add emotional perspective
            if responses.get('emotion'):
                response_text += f"Emotionally: {responses['emotion'].response}\n\n"
            
            # Add reflection
            if responses.get('reflection'):
                response_text += f"Upon reflection: {responses['reflection'].response}\n\n"
            
            # Add research insights
            if responses.get('research'):
                response_text += f"Research suggests: {responses['research'].response}\n"
            
            # Create synthesized response
            response = AgentResponse(
                response=response_text.strip(),
                concepts=all_concepts
            )
            
            # Store synthesized response in vector store
            await self.vector_store.store_vector(
                content=serialize_datetime({
                    'original_content': context.get('original_content'),
                    'metadata': context.get('metadata'),
                    'episodic_id': context.get('episodic_id'),
                    'similar_memories': context.get('similar_memories'),
                    'final_response': serialize_datetime(response.dict()),
                    'agent_responses': {
                        agent_type: serialize_datetime(agent_response.dict())
                        for agent_type, agent_response in responses.items()
                    }
                }),
                metadata={'type': 'synthesized_response'},
                layer="semantic"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error synthesizing responses: {str(e)}")
            # Return basic response on error
            return AgentResponse(
                response="I'm processing multiple perspectives on this.",
                concepts=[]
            )
