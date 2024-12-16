"""
Meta agent for coordinating other agents and synthesizing responses.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import traceback

from .base import TimeAwareAgent
from .response_processor import ResponseProcessor
from .context_builder import ContextBuilder
from ..error_handling import ErrorHandler
from ..feedback import FeedbackSystem
from ..persistence import MemoryStore

logger = logging.getLogger(__name__)

class MetaAgent(TimeAwareAgent):
    """Coordinates other agents and synthesizes responses."""
    
    def __init__(self, memory_store: MemoryStore, error_handler: ErrorHandler,
                 feedback_system: FeedbackSystem):
        """Initialize meta agent."""
        super().__init__("MetaAgent", memory_store, error_handler, feedback_system)
        self.registered_agents = {}
        self.response_processor = ResponseProcessor()
        self.context_builder = ContextBuilder(memory_store)
    
    def register_agent(self, name: str, agent: TimeAwareAgent) -> None:
        """Register an agent for coordination."""
        self.registered_agents[name] = agent
        logger.info(f"Registered agent: {name}")
    
    async def _synthesize_response(self, content: str, agent_outputs: Dict[str, str]) -> Dict:
        """Synthesize a response from agent outputs."""
        try:
            # Build context from memories
            context_str = await self.context_builder.build_full_context(content)
            
            # Format agent outputs
            formatted_outputs = "\n".join([
                f"{name}: {output}" for name, output in agent_outputs.items()
            ])
            
            prompt = f"""You are Nova, an AI assistant. Your task is to synthesize a response considering the following information and guidelines.

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
   - Include timestamps or context references

Remember: Return ONLY the JSON object, no other text."""

            # Get synthesis from LLM
            synthesis = await self.get_completion(prompt)
            
            # Process response
            synthesis_data = self.response_processor.process_llm_response(synthesis)
            
            # Update meta state vector
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
    
    async def process_interaction(self, content: str, agent_outputs: Optional[Dict[str, str]] = None) -> str:
        """Process interaction and synthesize response."""
        try:
            # Extract context
            content, context = self._extract_context(content)
            
            # Use provided agent outputs or empty dict
            agent_outputs = agent_outputs or {}
            
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
    
    async def reflect(self) -> Dict:
        """Reflect on meta agent state."""
        try:
            # Get recent memories with increased limit
            memories = await self.memory_store.get_recent_memories(
                agent_name=self.name,
                memory_type="interaction",
                limit=5  # Increased limit for better reflection
            )
            
            # Extract patterns
            responses = []
            key_points = []
            state_updates = []
            memory_influences = []
            continuity_markers = []
            
            for memory in memories:
                if isinstance(memory.get('content'), dict):
                    synthesis = memory['content'].get('synthesis', {})
                    if isinstance(synthesis, dict):
                        if synthesis.get('response'):
                            responses.append(synthesis['response'])
                        if synthesis.get('key_points'):
                            key_points.extend(synthesis['key_points'])
                        if synthesis.get('state_update'):
                            state_updates.append(synthesis['state_update'])
                        if synthesis.get('memory_influence'):
                            memory_influences.append(synthesis['memory_influence'])
                        if synthesis.get('continuity_markers'):
                            continuity_markers.extend(synthesis['continuity_markers'])
            
            # Limit to most recent unique items
            responses = list(dict.fromkeys(responses))[-3:]
            key_points = list(dict.fromkeys(key_points))[-5:]
            state_updates = list(dict.fromkeys(state_updates))[-3:]
            memory_influences = list(dict.fromkeys(memory_influences))[-3:]
            continuity_markers = list(dict.fromkeys(continuity_markers))[-5:]
            
            return {
                'response_pattern': ', '.join(responses) if responses else 'no clear pattern',
                'key_point_trend': ', '.join(key_points) if key_points else 'no clear trends',
                'state_evolution': ', '.join(state_updates) if state_updates else 'no clear evolution',
                'memory_influence_pattern': ', '.join(memory_influences) if memory_influences else 'no clear memory patterns',
                'continuity_trend': ', '.join(continuity_markers) if continuity_markers else 'no clear continuity',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error in meta reflection: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'response_pattern': 'no clear pattern',
                'key_point_trend': 'no clear trends',
                'state_evolution': 'no clear evolution',
                'memory_influence_pattern': 'no clear memory patterns',
                'continuity_trend': 'no clear continuity',
                'timestamp': datetime.now().isoformat()
            }
