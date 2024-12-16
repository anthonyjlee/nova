"""
Meta agent for coordinating other agents and synthesizing responses.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import traceback

from .base import TimeAwareAgent
from ..error_handling import ErrorHandler
from ..feedback import FeedbackSystem
from ..persistence import MemoryStore
from ..llm_interface import LLMInterface

logger = logging.getLogger(__name__)

class MetaAgent(TimeAwareAgent):
    """Coordinates other agents and synthesizes responses."""
    
    def __init__(
        self,
        memory_store: MemoryStore,
        error_handler: ErrorHandler,
        feedback_system: FeedbackSystem,
        llm_interface: LLMInterface
    ):
        """Initialize meta agent."""
        super().__init__(
            "MetaAgent",
            memory_store,
            error_handler,
            feedback_system,
            llm_interface
        )
        self.registered_agents = {}
    
    def register_agent(self, name: str, agent: TimeAwareAgent) -> None:
        """Register an agent for coordination."""
        self.registered_agents[name] = agent
        logger.info(f"Registered agent: {name}")
    
    async def _synthesize_response(self, content: str, agent_outputs: Dict[str, str]) -> Dict:
        """Synthesize a response from agent outputs."""
        try:
            # Search for similar interactions
            similar_interactions = await self.memory_store.search_similar_memories(
                content=content,
                limit=5,
                filter_dict={'memory_type': 'interaction'},
                prioritize_temporal=True
            )
            
            # Format similar interactions for context
            interaction_context = []
            for memory in similar_interactions:
                memory_content = memory.get('content', {})
                if isinstance(memory_content, dict):
                    if 'input' in memory_content:
                        interaction_context.append(f"Previous interaction ({memory['time_ago']}):")
                        interaction_context.append(f"- Input: {memory_content['input']}")
                        if 'synthesis' in memory_content:
                            synthesis = memory_content['synthesis']
                            if isinstance(synthesis, dict):
                                if synthesis.get('response'):
                                    interaction_context.append(f"- Response: {synthesis['response']}")
                                if synthesis.get('key_points'):
                                    interaction_context.append("- Key points:")
                                    for point in synthesis['key_points']:
                                        interaction_context.append(f"  * {point}")
            
            # Get current context
            current_context = self.memory_store.get_current_context()
            
            # Format agent outputs for prompt
            formatted_outputs = "\n".join([
                f"{name}: {output}" for name, output in agent_outputs.items()
            ])
            
            # Format context sections
            context_sections = []
            if interaction_context:
                context_sections.append("Previous Interactions:\n" + "\n".join(interaction_context))
            if current_context:
                if 'beliefs' in current_context:
                    context_sections.append("Current Beliefs:\n- " + "\n- ".join(current_context['beliefs'][-3:]))
                if 'insights' in current_context:
                    context_sections.append("Recent Insights:\n- " + "\n".join(current_context['insights'][-3:]))
            
            context_str = "\n\n".join(context_sections) if context_sections else "No prior context available"
            
            prompt = f"""You are Nova, an AI assistant. Synthesize a response that integrates emotional state, desires, and beliefs, while considering similar past interactions.

Input: {content}

Memory Context:
{context_str}

Agent States:
{formatted_outputs}

IMPORTANT: You must respond with ONLY a JSON object. No other text, no explanations, no markdown.
The JSON object must follow this EXACT format:
{{
    "response": "your main response that integrates emotional state, beliefs, and past context",
    "key_points": [
        "key point 1 about the response",
        "key point 2 about the response",
        "etc"
    ],
    "state_update": "how your understanding has evolved",
    "memory_influence": "how past memories influenced this response",
    "continuity_markers": [
        "connection to previous interaction 1",
        "connection to previous interaction 2",
        "etc"
    ]
}}

Guidelines for JSON fields:
1. response: 
   - Reference and learn from similar past interactions
   - Show continuity with previous conversations
   - Acknowledge emotional state from EmotionAgent
   - Be honest about current knowledge
   - Express genuine interest in topics
   - Maintain consistent voice

2. key_points:
   - List 2-3 main points from your response
   - Focus on important insights or decisions
   - Include relevant past context

3. state_update:
   - Describe how your understanding has changed
   - Reference specific new insights

4. memory_influence:
   - Explain how past interactions shaped response
   - Reference specific past conversations

5. continuity_markers:
   - List specific connections to past interactions
   - Include timestamps or context references"""

            # Get synthesis with retries and default response
            default_response = {
                'response': "I apologize, but I need to process that differently.",
                'key_points': ["error in synthesis"],
                'state_update': "no significant change",
                'memory_influence': "no clear memory influence",
                'continuity_markers': [],
                'timestamp': datetime.now().isoformat()
            }
            
            data = await self.get_json_completion(
                prompt=prompt,
                retries=3,
                default_response=default_response
            )
            
            # Clean and validate data
            synthesis_data = {
                'response': self._safe_str(data.get('response'), "I apologize, but I need to process that differently."),
                'key_points': self._safe_list(data.get('key_points')),
                'state_update': self._safe_str(data.get('state_update'), "no significant change"),
                'memory_influence': self._safe_str(data.get('memory_influence'), "no clear memory influence"),
                'continuity_markers': self._safe_list(data.get('continuity_markers')),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update meta state vector with richer context
            await self.update_state_vector('memories', 
                f"{synthesis_data['response']} {synthesis_data['state_update']} {synthesis_data['memory_influence']}")
            
            return synthesis_data
            
        except Exception as e:
            logger.error(f"Error synthesizing response: {str(e)}")
            return {
                'response': "I apologize, but I encountered an error processing that.",
                'key_points': ["error in synthesis"],
                'state_update': "error in processing",
                'memory_influence': "error retrieving memories",
                'continuity_markers': [],
                'timestamp': datetime.now().isoformat()
            }
    
    async def process_interaction(self, content: str) -> str:
        """Process interaction and synthesize response."""
        try:
            # Extract context
            content, context = self._extract_context(content)
            
            # Get responses from other agents
            agent_outputs = {}
            for name, agent in self.registered_agents.items():
                try:
                    response = await agent.process_interaction(content)
                    agent_outputs[name] = response
                except Exception as e:
                    logger.error(f"Error getting response from {name}: {str(e)}")
                    agent_outputs[name] = f"Error: {str(e)}"
            
            # Synthesize response
            synthesis = await self._synthesize_response(content, agent_outputs)
            
            # Store memory with enhanced metadata
            await self.store_memory(
                memory_type="interaction",
                content={
                    'input': content,
                    'responses': agent_outputs,
                    'synthesis': synthesis,
                    'timestamp': datetime.now().isoformat()
                },
                metadata={
                    'importance': 1.0 if any(marker.lower() in content.lower() 
                                          for marker in ['nia', 'echo', 'predecessor']) 
                              else 0.5  # Boost importance for key topics
                }
            )
            
            # Return synthesized response
            return synthesis['response']
            
        except Exception as e:
            error_msg = f"Error in meta processing: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return "I apologize, but I encountered an error processing that interaction."
