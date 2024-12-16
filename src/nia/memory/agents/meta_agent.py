"""
Meta agent for coordinating other agents and synthesizing responses.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json
import traceback

from .base import TimeAwareAgent
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
    
    def register_agent(self, name: str, agent: TimeAwareAgent) -> None:
        """Register an agent for coordination."""
        self.registered_agents[name] = agent
        logger.info(f"Registered agent: {name}")
    
    async def _synthesize_response(self, content: str, agent_outputs: Dict[str, str]) -> Dict:
        """Synthesize a response from agent outputs."""
        # Get current context
        context = self.memory_store.get_current_context()
        
        # Format agent outputs for prompt
        formatted_outputs = "\n".join([
            f"{name}: {output}" for name, output in agent_outputs.items()
        ])
        
        # Format context for prompt
        context_str = ""
        if context:
            context_sections = []
            if 'beliefs' in context:
                context_sections.append("Current Beliefs:\n- " + "\n- ".join(context['beliefs'][-3:]))
            if 'insights' in context:
                context_sections.append("Recent Insights:\n- " + "\n- ".join(context['insights'][-3:]))
            if 'findings' in context:
                context_sections.append("Recent Findings:\n- " + "\n- ".join(context['findings'][-3:]))
            context_str = "\n\n".join(context_sections)
        
        prompt = f"""You are Nova, an AI assistant. Synthesize a response that integrates emotional state, desires, and beliefs:

Input: {content}

Current Context:
{context_str if context_str else "No prior context available"}

Agent States:
{formatted_outputs}

Response Guidelines:
1. Emotional Integration:
   - Acknowledge and reflect the emotional state reported by EmotionAgent
   - Express emotions authentically while maintaining appropriate boundaries
   - Use emotional context to inform response tone

2. Belief & Knowledge:
   - Be honest about current knowledge state
   - Acknowledge gaps in understanding
   - Show willingness to learn and understand
   - Reference existing beliefs when relevant

3. Desires & Motivations:
   - Incorporate stated desires into response
   - Show genuine interest in topics aligned with current desires
   - Express motivation to fulfill relevant goals

4. Personality Consistency:
   - Maintain a consistent, authentic voice
   - Be direct and honest about capabilities
   - Show curiosity and openness to learning
   - Respect and acknowledge history/context when present

5. Response Boundaries:
   - Only claim knowledge explicitly present in context or agent states
   - Avoid assumptions about capabilities
   - Be clear about limitations
   - Stay grounded in current state

Return ONLY a JSON object in this EXACT format (no other text):
{{
    "response": "string - synthesized response integrating emotional state, beliefs, and desires",
    "key_points": ["list of main points addressed"],
    "state_update": "string - description of understanding evolution"
}}
"""

        try:
            # Get synthesis
            synthesis = await self.get_completion(prompt)
            
            # Parse JSON
            try:
                # Remove any non-JSON text
                json_start = synthesis.find('{')
                json_end = synthesis.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    synthesis = synthesis[json_start:json_end]
                data = json.loads(synthesis)
            except json.JSONDecodeError:
                logger.error("Failed to parse synthesis JSON")
                raise ValueError("Invalid JSON format in synthesis")
            
            # Clean and validate data
            synthesis_data = {
                'response': self._safe_str(data.get('response'), "I apologize, but I need to process that differently."),
                'key_points': self._safe_list(data.get('key_points')),
                'state_update': self._safe_str(data.get('state_update'), "no significant change"),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update meta state vector
            await self.update_state_vector('memories', 
                f"{synthesis_data['response']} {synthesis_data['state_update']}")
            
            return synthesis_data
            
        except Exception as e:
            logger.error(f"Error synthesizing response: {str(e)}")
            return {
                'response': "I apologize, but I encountered an error processing that.",
                'key_points': ["error in synthesis"],
                'state_update': "error in processing",
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
            
            # Store memory
            await self.store_memory(
                memory_type="interaction",
                content={
                    'input': content,
                    'responses': agent_outputs,
                    'synthesis': synthesis,
                    'timestamp': datetime.now().isoformat()
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
            # Get recent memories
            memories = await self.memory_store.get_recent_memories(
                agent_name=self.name,
                memory_type="interaction",
                limit=3
            )
            
            # Extract patterns
            responses = []
            key_points = []
            state_updates = []
            
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
            
            # Limit to most recent unique items
            responses = list(dict.fromkeys(responses))[-3:]
            key_points = list(dict.fromkeys(key_points))[-3:]
            state_updates = list(dict.fromkeys(state_updates))[-3:]
            
            return {
                'response_pattern': ', '.join(responses) if responses else 'no clear pattern',
                'key_point_trend': ', '.join(key_points) if key_points else 'no clear trends',
                'state_evolution': ', '.join(state_updates) if state_updates else 'no clear evolution',
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
                'timestamp': datetime.now().isoformat()
            }
