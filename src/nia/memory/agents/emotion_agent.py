"""
Agent for managing emotional state and responses.
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

class EmotionAgent(TimeAwareAgent):
    """Manages emotional state and responses."""
    
    def __init__(self, memory_store: MemoryStore, error_handler: ErrorHandler,
                 feedback_system: FeedbackSystem):
        """Initialize emotion agent."""
        super().__init__("EmotionAgent", memory_store, error_handler, feedback_system)
    
    async def _analyze_emotions(self, content: str, context: Dict) -> Dict:
        """Analyze and update emotional state."""
        # Get similarity with current emotional state
        emotion_similarity = await self.get_state_similarity('emotions', content)
        
        # Get current context
        current_context = self.memory_store.get_current_context()
        
        # Format context for prompt
        context_str = ""
        if current_context:
            context_sections = []
            if 'beliefs' in current_context:
                context_sections.append("Current Beliefs:\n- " + "\n- ".join(current_context['beliefs'][-3:]))
            if 'insights' in current_context:
                context_sections.append("Recent Insights:\n- " + "\n- ".join(current_context['insights'][-3:]))
            context_str = "\n\n".join(context_sections)
        
        prompt = f"""You are part of Nova, an AI assistant. Analyze emotional state and responses:

Input: {content}

Context:
{context_str if context_str else "No prior context available"}

Current State:
- Emotion similarity: {emotion_similarity:.2f}

Important Guidelines:
- Focus on genuine emotional responses
- Show appropriate curiosity about stories and history
- Express authentic interest in learning
- Maintain appropriate emotional boundaries
- Be honest about emotional responses
- Show respect for historical context
- Express appreciation for shared experiences

Return ONLY a JSON object in this EXACT format (no other text):
{{
    "primary_emotion": "string - main emotional response",
    "intensity": "float - 0.0 to 1.0",
    "triggers": ["list of emotional triggers"],
    "nuances": ["list of emotional nuances"],
    "evolution": "string - how emotion is changing",
    "state_update": "string - description of emotional evolution",
    "timestamp": "string - current time"
}}
"""

        try:
            # Get emotion analysis
            analysis = await self.get_completion(prompt)
            
            # Parse JSON
            try:
                # Remove any non-JSON text
                json_start = analysis.find('{')
                json_end = analysis.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    analysis = analysis[json_start:json_end]
                data = json.loads(analysis)
            except json.JSONDecodeError:
                logger.error("Failed to parse emotion analysis JSON")
                raise ValueError("Invalid JSON format in emotion analysis")
            
            # Clean and validate data
            emotion_data = {
                'primary_emotion': self._safe_str(data.get('primary_emotion'), ""),
                'intensity': float(data.get('intensity', 0.0)),
                'triggers': self._safe_list(data.get('triggers')),
                'nuances': self._safe_list(data.get('nuances')),
                'evolution': self._safe_str(data.get('evolution'), "continuity"),
                'state_update': self._safe_str(data.get('state_update'), "initial interaction"),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update emotion state vector
            await self.update_state_vector('emotions', 
                f"{emotion_data['primary_emotion']} {emotion_data['state_update']}")
            
            return emotion_data
            
        except Exception as e:
            logger.error(f"Error analyzing emotions: {str(e)}")
            return {
                'primary_emotion': "",
                'intensity': 0.0,
                'triggers': [],
                'nuances': ["uncertain", "neutral"],
                'evolution': "continuity",
                'state_update': "error in processing",
                'timestamp': datetime.now().isoformat()
            }
    
    async def process_interaction(self, content: str) -> str:
        """Process interaction and update emotional state."""
        try:
            # Extract context
            content, context = self._extract_context(content)
            
            # Analyze emotions
            emotions = await self._analyze_emotions(content, context)
            
            # Store memory
            await self.store_memory(
                memory_type="emotion",
                content={
                    'emotions': emotions,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Return concise emotional state
            nuances = '; '.join(emotions['nuances'][:2]) if emotions['nuances'] else ""
            intensity_desc = "high" if emotions['intensity'] > 0.7 else "medium" if emotions['intensity'] > 0.3 else "low"
            return f"Current emotional state: {emotions['primary_emotion']} (intensity: {intensity_desc}) {emotions['evolution']}"
            
        except Exception as e:
            error_msg = f"Error in emotion processing: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return "Unable to process emotions at this time"
    
    async def reflect(self) -> Dict:
        """Reflect on emotional development."""
        try:
            # Get recent memories
            memories = await self.memory_store.get_recent_memories(
                agent_name=self.name,
                memory_type="emotion",
                limit=3
            )
            
            # Extract emotion patterns
            emotions = []
            triggers = []
            evolutions = []
            
            for memory in memories:
                if isinstance(memory.get('content'), dict):
                    emotion_data = memory['content'].get('emotions', {})
                    if isinstance(emotion_data, dict):
                        if emotion_data.get('primary_emotion'):
                            emotions.append(emotion_data['primary_emotion'])
                        if emotion_data.get('triggers'):
                            triggers.extend(emotion_data['triggers'])
                        if emotion_data.get('evolution'):
                            evolutions.append(emotion_data['evolution'])
            
            # Limit to most recent unique items
            emotions = list(dict.fromkeys(emotions))[-3:]
            triggers = list(dict.fromkeys(triggers))[-3:]
            evolutions = list(dict.fromkeys(evolutions))[-3:]
            
            return {
                'emotion_pattern': ', '.join(emotions) if emotions else 'no clear emotions',
                'trigger_trend': ', '.join(triggers) if triggers else 'no clear triggers',
                'evolution_pattern': ', '.join(evolutions) if evolutions else 'no clear evolution',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error in emotion reflection: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'emotion_pattern': 'no clear emotions',
                'trigger_trend': 'no clear triggers',
                'evolution_pattern': 'no clear evolution',
                'timestamp': datetime.now().isoformat()
            }
