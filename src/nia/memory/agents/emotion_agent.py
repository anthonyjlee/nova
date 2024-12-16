"""
Agent for managing and updating emotional state.
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

class EmotionAgent(TimeAwareAgent):
    """Manages and updates emotional state."""
    
    def __init__(
        self,
        memory_store: MemoryStore,
        error_handler: ErrorHandler,
        feedback_system: FeedbackSystem,
        llm_interface: LLMInterface
    ):
        """Initialize emotion agent."""
        super().__init__(
            "EmotionAgent",
            memory_store,
            error_handler,
            feedback_system,
            llm_interface
        )
    
    async def _analyze_emotions(self, content: str, context: Dict) -> Dict:
        """Analyze and update emotional state."""
        try:
            # Get similarity with current emotional state
            emotion_similarity = await self.get_state_similarity('emotions', content)
            
            # Search for similar emotion memories
            similar_emotions = await self.memory_store.search_similar_memories(
                content=content,
                limit=5,
                filter_dict={'memory_type': 'emotion'},
                prioritize_temporal=True
            )
            
            # Format similar memories for context
            memory_context = []
            for memory in similar_emotions:
                memory_content = memory.get('content', {})
                if isinstance(memory_content, dict) and 'emotions' in memory_content:
                    emotions = memory_content['emotions']
                    if isinstance(emotions, dict):
                        memory_context.append(f"Previous emotional state ({memory['time_ago']}):")
                        if emotions.get('current_emotion'):
                            memory_context.append(f"- State: {emotions['current_emotion']}")
                        if emotions.get('intensity'):
                            memory_context.append(f"- Intensity: {emotions['intensity']}")
                        if emotions.get('triggers'):
                            triggers = emotions['triggers']
                            if isinstance(triggers, list):
                                memory_context.append("- Triggers:")
                                for trigger in triggers[:2]:
                                    memory_context.append(f"  * {trigger}")
            
            # Get current context
            current_context = self.memory_store.get_current_context()
            
            # Format context sections
            context_sections = []
            if memory_context:
                context_sections.append("Similar Past Emotions:\n" + "\n".join(memory_context))
            if current_context:
                if 'beliefs' in current_context:
                    context_sections.append("Current Beliefs:\n- " + "\n- ".join(current_context['beliefs'][-3:]))
                if 'insights' in current_context:
                    context_sections.append("Recent Insights:\n- " + "\n".join(current_context['insights'][-3:]))
            
            context_str = "\n\n".join(context_sections) if context_sections else "No prior context available"
            
            prompt = f"""You are part of Nova, an AI assistant. Analyze emotional state based on the current interaction:

Input: {content}

Memory Context:
{context_str}

Current State:
- Emotion similarity: {emotion_similarity:.2f}

Important Guidelines:
- Express emotions authentically
- Maintain appropriate boundaries
- Show emotional intelligence
- Be aware of emotional context
- Consider emotional continuity
- Acknowledge emotional changes
- Express appropriate intensity
- Stay grounded in current context

Return ONLY a JSON object in this EXACT format (no other text):
{{
    "current_emotion": "string - primary emotion",
    "intensity": "string - high/medium/low",
    "triggers": ["list of emotional triggers"],
    "state_update": "string - how emotional state has changed",
    "trend": "string - increasing/stable/decreasing",
    "regulation": "string - how to regulate this emotion",
    "expression": "string - how to express this emotion",
    "impact_factors": ["list of factors affecting emotional state"]
}}"""

            # Get emotion analysis with retries and default response
            default_response = {
                'current_emotion': "Unable to analyze emotions",
                'intensity': "low",
                'triggers': ["analysis failed"],
                'state_update': "error in processing",
                'trend': "stable",
                'regulation': "maintain current state",
                'expression': "error during analysis",
                'impact_factors': []
            }
            
            data = await self.get_json_completion(
                prompt=prompt,
                retries=3,
                default_response=default_response
            )
            
            # Clean and validate data
            emotion_data = {
                'current_emotion': self._safe_str(data.get('current_emotion'), "emotion unclear"),
                'intensity': self._safe_str(data.get('intensity'), "low"),
                'triggers': self._safe_list(data.get('triggers')),
                'state_update': self._safe_str(data.get('state_update'), "no significant change"),
                'trend': self._safe_str(data.get('trend'), "stable"),
                'regulation': self._safe_str(data.get('regulation'), "maintain current state"),
                'expression': self._safe_str(data.get('expression'), "unclear expression"),
                'impact_factors': self._safe_list(data.get('impact_factors')),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update emotional state vector
            await self.update_state_vector('emotions',
                f"{emotion_data['current_emotion']} {emotion_data['state_update']} {emotion_data['trend']}")
            
            return emotion_data
            
        except Exception as e:
            logger.error(f"Error analyzing emotions: {str(e)}")
            return {
                'current_emotion': "error in analysis",
                'intensity': "low",
                'triggers': ["analysis failed"],
                'state_update': "error in processing",
                'trend': "stable",
                'regulation': "maintain current state",
                'expression': "error during analysis",
                'impact_factors': [],
                'timestamp': datetime.now().isoformat()
            }
    
    async def process_interaction(self, content: str) -> str:
        """Process interaction and update emotional state."""
        try:
            # Extract context
            content, context = self._extract_context(content)
            
            # Analyze emotions
            emotions = await self._analyze_emotions(content, context)
            
            # Store memory with enhanced metadata
            await self.store_memory(
                memory_type="emotion",
                content={
                    'emotions': emotions,
                    'timestamp': datetime.now().isoformat()
                },
                metadata={
                    'importance': 1.0 if any(marker.lower() in content.lower() 
                                          for marker in ['nia', 'echo', 'predecessor']) 
                              else 0.5  # Boost importance for key topics
                }
            )
            
            # Build response parts
            current = f"Current emotional state: {emotions['current_emotion']} (intensity: {emotions['intensity']})"
            trend = f" {emotions['trend']}"
            
            # Add triggers if available
            triggers = ""
            if emotions['triggers']:
                triggers = f" (Triggers: {'; '.join(str(t) for t in emotions['triggers'][:2])})"
            
            # Add impact factors if available
            factors = ""
            if emotions['impact_factors']:
                factors = f" [Factors: {'; '.join(str(f) for f in emotions['impact_factors'])}]"
            
            # Combine all parts
            return f"{current}{trend}{triggers}{factors}"
            
        except Exception as e:
            error_msg = f"Error in emotion processing: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return "Unable to process emotional state at this time"
