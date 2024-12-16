"""
Agent for analyzing patterns and synthesizing insights across agent states.
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime
import logging
import json
import traceback

from .base import TimeAwareAgent
from ..error_handling import ErrorHandler
from ..feedback import FeedbackSystem
from ..persistence import MemoryStore

logger = logging.getLogger(__name__)

class ReflectionAgent(TimeAwareAgent):
    """Analyzes patterns and synthesizes insights across agent states."""
    
    def __init__(self, memory_store: MemoryStore, error_handler: ErrorHandler,
                 feedback_system: FeedbackSystem):
        """Initialize reflection agent."""
        super().__init__("ReflectionAgent", memory_store, error_handler, feedback_system)
    
    def _format_memory_summary(self, memories: List[Dict]) -> str:
        """Format memories into a concise summary."""
        summary = []
        for memory in memories:
            if isinstance(memory.get('content'), dict):
                content = memory['content']
                if 'beliefs' in content:
                    summary.append(f"Belief: {content['beliefs'].get('core_belief', '')}")
                elif 'emotions' in content:
                    summary.append(f"Emotion: {content['emotions'].get('primary_emotion', '')}")
                elif 'desires' in content:
                    summary.append(f"Desire: {content['desires'].get('main_desire', '')}")
        return "; ".join(summary[-2:])  # Only return last 2 memories
    
    async def _analyze_patterns(self, content: str, context: Dict) -> Dict:
        """Analyze patterns across agent states."""
        # Get similarity with current reflection state
        reflection_similarity = await self.get_state_similarity('memories', content)
        
        # Get recent memories from other agents
        belief_memories = await self.memory_store.get_recent_memories(
            agent_name="BeliefAgent",
            limit=2
        )
        emotion_memories = await self.memory_store.get_recent_memories(
            agent_name="EmotionAgent",
            limit=2
        )
        desire_memories = await self.memory_store.get_recent_memories(
            agent_name="DesireAgent",
            limit=2
        )
        
        # Create concise summaries
        belief_summary = self._format_memory_summary(belief_memories)
        emotion_summary = self._format_memory_summary(emotion_memories)
        desire_summary = self._format_memory_summary(desire_memories)
        
        prompt = f"""You are part of Nova, an AI assistant. Analyze patterns and synthesize insights across agent states:

Input: {content}

State Summary:
- Reflection similarity: {reflection_similarity:.2f}
- Beliefs: {belief_summary}
- Emotions: {emotion_summary}
- Desires: {desire_summary}

Important Guidelines:
- Focus only on information explicitly provided
- Do not make assumptions about capabilities
- Maintain awareness of being a new system
- Show interest in learning but acknowledge limitations
- Be direct and honest about current state
- Do not claim capabilities or knowledge not mentioned

Return ONLY a JSON object in this EXACT format (no other text):
{{
    "key_insights": ["list of main insights"],
    "patterns": ["list of observed patterns"],
    "implications": ["list of potential implications"],
    "synthesis": "string - overall synthesis of observations",
    "state_update": "string - description of understanding evolution"
}}
"""

        try:
            # Get pattern analysis
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
                logger.error("Failed to parse reflection analysis JSON")
                raise ValueError("Invalid JSON format in reflection analysis")
            
            # Clean and validate data
            reflection_data = {
                'key_insights': self._safe_list(data.get('key_insights')),
                'patterns': self._safe_list(data.get('patterns')),
                'implications': self._safe_list(data.get('implications')),
                'synthesis': self._safe_str(data.get('synthesis'), "analysis incomplete"),
                'state_update': self._safe_str(data.get('state_update'), "no significant change"),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update reflection state vector
            await self.update_state_vector('memories', 
                f"{reflection_data['synthesis']} {reflection_data['state_update']}")
            
            return reflection_data
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {str(e)}")
            return {
                'key_insights': ["analysis error"],
                'patterns': ["processing failed"],
                'implications': ["unknown"],
                'synthesis': "analysis incomplete",
                'state_update': "error in processing",
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_reflection_history(self, limit: int = 3) -> List[Dict]:
        """Get recent reflection memories."""
        try:
            memories = await self.memory_store.get_recent_memories(
                agent_name=self.name,
                memory_type="reflection",
                limit=limit
            )
            return memories if isinstance(memories, list) else []
        except Exception as e:
            logger.error(f"Error getting reflection history: {str(e)}")
            return []
    
    async def process_interaction(self, content: str) -> str:
        """Process interaction and update reflections."""
        try:
            # Extract context
            content, context = self._extract_context(content)
            
            # Analyze patterns
            reflections = await self._analyze_patterns(content, context)
            
            # Store memory
            await self.store_memory(
                memory_type="reflection",
                content={
                    'reflections': reflections,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Return concise reflection insight
            insights = '; '.join(reflections['key_insights'][:2]) if reflections['key_insights'] else "no clear insights"
            return f"Key insights: {insights}. {reflections['synthesis']}"
            
        except Exception as e:
            error_msg = f"Error in reflection processing: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return "Unable to process reflections at this time"
    
    async def reflect(self) -> Dict:
        """Reflect on pattern development."""
        try:
            history = await self._get_reflection_history()
            
            # Extract reflection patterns
            insights = []
            patterns = []
            syntheses = []
            
            for memory in history:
                if isinstance(memory.get('content'), dict):
                    reflection_data = memory['content'].get('reflections', {})
                    if isinstance(reflection_data, dict):
                        if reflection_data.get('key_insights'):
                            insights.extend(reflection_data['key_insights'])
                        if reflection_data.get('patterns'):
                            patterns.extend(reflection_data['patterns'])
                        synthesis = self._safe_str(reflection_data.get('synthesis'))
                        if synthesis:
                            syntheses.append(synthesis)
            
            # Limit to most recent unique items
            insights = list(dict.fromkeys(insights))[-3:]
            patterns = list(dict.fromkeys(patterns))[-3:]
            syntheses = list(dict.fromkeys(syntheses))[-3:]
            
            return {
                'insight_pattern': ', '.join(insights) if insights else 'no clear insights',
                'pattern_trend': ', '.join(patterns) if patterns else 'no clear patterns',
                'synthesis_evolution': ', '.join(syntheses) if syntheses else 'analysis incomplete',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error in reflection analysis: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'insight_pattern': 'no clear insights',
                'pattern_trend': 'no clear patterns',
                'synthesis_evolution': 'analysis incomplete',
                'timestamp': datetime.now().isoformat()
            }
