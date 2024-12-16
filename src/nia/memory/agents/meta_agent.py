"""
Meta-cognitive agent for synthesizing responses and self-reflection.
"""

import logging
from typing import Dict, Any, Optional, List
from .base import BaseAgent
from ..llm_interface import LLMInterface, LLMResponse
from ..neo4j_store import Neo4jMemoryStore
from ..prompts import META_PROMPT
from ..memory_types import AgentResponse, Analysis

logger = logging.getLogger(__name__)

class MetaAgent(BaseAgent):
    """Agent for metacognition and response synthesis."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore
    ):
        """Initialize meta agent."""
        super().__init__(llm, store, "meta")
    
    def _format_prompt(
        self,
        responses: Dict[str, AgentResponse],
        context: Dict[str, Any]
    ) -> str:
        """Format prompt for meta-cognitive analysis."""
        try:
            # Format agent responses
            formatted_responses = []
            for agent_type, response in responses.items():
                if not isinstance(response, AgentResponse):
                    logger.warning(f"Invalid response type from {agent_type}: {type(response)}")
                    continue
                    
                formatted_responses.append(f"\n{agent_type.upper()} RESPONSE:")
                formatted_responses.append(f"Response: {response.response}")
                formatted_responses.append("Analysis:")
                
                if not isinstance(response.analysis, Analysis):
                    logger.warning(f"Invalid analysis type from {agent_type}: {type(response.analysis)}")
                    continue
                    
                for point in response.analysis.key_points:
                    formatted_responses.append(f"- {point}")
                formatted_responses.append(f"Confidence: {response.analysis.confidence}")
                formatted_responses.append(f"State Update: {response.analysis.state_update}")
            
            # Format context
            context_sections = []
            
            # Add original content
            if context.get('original_content'):
                context_sections.append("Original Content:")
                context_sections.append(str(context['original_content']))
            
            # Add similar memories
            if context.get('similar_memories'):
                context_sections.append("\nSimilar Past Memories:")
                for memory in context['similar_memories']:
                    context_sections.append(f"- {memory.get('content', '')}")
                    if memory.get('concepts'):
                        concepts = [f"{c['name']} ({c['type']})" for c in memory['concepts']]
                        context_sections.append(f"  Concepts: {', '.join(concepts)}")
            
            # Add system capabilities
            if context.get('capabilities_info'):
                context_sections.append("\nSystem Capabilities:")
                for cap in context['capabilities_info']:
                    context_sections.append(f"- {cap['description']} ({cap['type']})")
                    if cap.get('systems'):
                        context_sections.append(f"  Used by: {', '.join(s['name'] for s in cap['systems'])}")
            
            # Format final prompt
            prompt = META_PROMPT.format(
                responses="\n".join(formatted_responses),
                context="\n".join(context_sections)
            )
            
            # Add metacognition guidance
            prompt += """

Focus on:
1. Identifying patterns and relationships between different agent responses
2. Evaluating the quality and coherence of the overall system response
3. Reflecting on how this interaction contributes to system growth
4. Analyzing gaps in knowledge or capabilities
5. Suggesting improvements to the reasoning process
6. Understanding the relationship between past experiences and current responses
7. Evaluating emotional and cognitive development
8. Identifying emergent behaviors and insights
"""
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error formatting prompt: {str(e)}")
            return META_PROMPT.format(
                responses="Error formatting responses",
                context="Error formatting context"
            )
    
    async def synthesize_responses(
        self,
        responses: Dict[str, AgentResponse],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """Synthesize responses from different agents."""
        try:
            # Get system capabilities
            capabilities = await self.get_capabilities()
            if capabilities:
                context['capabilities_info'] = capabilities
            
            # Get similar memories
            memories = await self.search_memories(
                content_pattern=str(context.get('original_content')),
                limit=5
            )
            if memories:
                context['similar_memories'] = memories
            
            # Get LLM response
            llm_response = await self.llm.get_structured_completion(
                self._format_prompt(responses, context)
            )
            
            if not isinstance(llm_response, LLMResponse):
                raise ValueError(f"Invalid LLM response type: {type(llm_response)}")
            
            # Convert LLM response to AgentResponse
            response = AgentResponse(
                response=llm_response.response,
                analysis=Analysis(
                    key_points=llm_response.analysis["key_points"],
                    confidence=llm_response.analysis["confidence"],
                    state_update=llm_response.analysis["state_update"]
                )
            )
            
            # Store synthesis
            try:
                await self.store.store_memory(
                    memory_type="synthesis",
                    content={
                        'original_content': context.get('original_content'),
                        'agent_responses': {k: v.dict() for k, v in responses.items()},
                        'synthesis': response.dict(),
                        'similar_memories': [m['id'] for m in memories] if memories else [],
                        'capabilities': [c['id'] for c in capabilities] if capabilities else []
                    },
                    metadata={
                        'confidence': response.analysis.confidence,
                        'state_update': response.analysis.state_update
                    }
                )
            except Exception as e:
                logger.error(f"Failed to store synthesis memory: {str(e)}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in meta agent: {str(e)}")
            # Return fallback response
            return AgentResponse(
                response="Error synthesizing responses",
                analysis=Analysis(
                    key_points=["Error occurred during synthesis"],
                    confidence=0.0,
                    state_update="Error state"
                )
            )
