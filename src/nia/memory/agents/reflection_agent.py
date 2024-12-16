"""
Agent for reflection and learning from interactions.
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

class ReflectionAgent(TimeAwareAgent):
    """Manages reflection and learning from interactions."""
    
    def __init__(
        self,
        memory_store: MemoryStore,
        error_handler: ErrorHandler,
        feedback_system: FeedbackSystem,
        llm_interface: LLMInterface
    ):
        """Initialize reflection agent."""
        super().__init__(
            "ReflectionAgent",
            memory_store,
            error_handler,
            feedback_system,
            llm_interface
        )
    
    async def _analyze_patterns(self, content: str, context: Dict) -> Dict:
        """Analyze patterns and insights from interactions."""
        try:
            # Get similarity with current reflection state
            reflection_similarity = await self.get_state_similarity('reflections', content)
            
            # Search for similar reflection memories
            similar_reflections = await self.memory_store.search_similar_memories(
                content=content,
                limit=5,
                filter_dict={'memory_type': 'reflection'},
                prioritize_temporal=True
            )
            
            # Format similar memories for context
            memory_context = []
            for memory in similar_reflections:
                memory_content = memory.get('content', {})
                if isinstance(memory_content, dict) and 'reflections' in memory_content:
                    reflections = memory_content['reflections']
                    if isinstance(reflections, dict):
                        memory_context.append(f"Previous reflection ({memory['time_ago']}):")
                        if reflections.get('key_insights'):
                            insights = reflections['key_insights']
                            if isinstance(insights, list):
                                memory_context.append("- Insights:")
                                for insight in insights[:2]:
                                    memory_context.append(f"  * {insight}")
                        if reflections.get('patterns'):
                            patterns = reflections['patterns']
                            if isinstance(patterns, list):
                                memory_context.append("- Patterns:")
                                for pattern in patterns[:2]:
                                    memory_context.append(f"  * {pattern}")
            
            # Get current context
            current_context = self.memory_store.get_current_context()
            
            # Format context sections
            context_sections = []
            if memory_context:
                context_sections.append("Similar Past Reflections:\n" + "\n".join(memory_context))
            if current_context:
                if 'beliefs' in current_context:
                    context_sections.append("Current Beliefs:\n- " + "\n- ".join(current_context['beliefs'][-3:]))
                if 'insights' in current_context:
                    context_sections.append("Recent Insights:\n- " + "\n".join(current_context['insights'][-3:]))
            
            context_str = "\n\n".join(context_sections) if context_sections else "No prior context available"
            
            prompt = f"""You are part of Nova, an AI assistant. Analyze patterns and insights from the current interaction:

Input: {content}

Memory Context:
{context_str}

Current State:
- Reflection similarity: {reflection_similarity:.2f}

Important Guidelines:
- Identify meaningful patterns
- Extract key insights
- Consider long-term implications
- Look for recurring themes
- Connect related concepts
- Build on past insights
- Maintain learning continuity
- Focus on growth opportunities

Return ONLY a JSON object in this EXACT format (no other text):
{{
    "key_insights": ["list of main insights gained"],
    "patterns": ["list of identified patterns"],
    "learning_points": ["list of things learned"],
    "state_update": "string - how understanding has evolved",
    "connections": ["list of connections to past experiences"],
    "implications": ["list of future implications"],
    "growth_areas": ["list of areas for improvement"],
    "action_items": ["list of suggested actions"]
}}"""

            # Get reflection analysis with retries and default response
            default_response = {
                'key_insights': ["Unable to analyze patterns"],
                'patterns': ["analysis failed"],
                'learning_points': ["error in processing"],
                'state_update': "no significant change",
                'connections': [],
                'implications': [],
                'growth_areas': [],
                'action_items': []
            }
            
            data = await self.get_json_completion(
                prompt=prompt,
                retries=3,
                default_response=default_response
            )
            
            # Clean and validate data
            reflection_data = {
                'key_insights': self._safe_list(data.get('key_insights')),
                'patterns': self._safe_list(data.get('patterns')),
                'learning_points': self._safe_list(data.get('learning_points')),
                'state_update': self._safe_str(data.get('state_update'), "no significant change"),
                'connections': self._safe_list(data.get('connections')),
                'implications': self._safe_list(data.get('implications')),
                'growth_areas': self._safe_list(data.get('growth_areas')),
                'action_items': self._safe_list(data.get('action_items')),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update reflection state vector
            await self.update_state_vector('reflections',
                f"{' '.join(reflection_data['key_insights'])} {reflection_data['state_update']}")
            
            return reflection_data
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {str(e)}")
            return {
                'key_insights': ["error in analysis"],
                'patterns': ["analysis failed"],
                'learning_points': ["error in processing"],
                'state_update': "no significant change",
                'connections': [],
                'implications': [],
                'growth_areas': [],
                'action_items': [],
                'timestamp': datetime.now().isoformat()
            }
    
    async def process_interaction(self, content: str) -> str:
        """Process interaction and update reflections."""
        try:
            # Extract context
            content, context = self._extract_context(content)
            
            # Analyze patterns
            reflections = await self._analyze_patterns(content, context)
            
            # Store memory with enhanced metadata
            await self.store_memory(
                memory_type="reflection",
                content={
                    'reflections': reflections,
                    'timestamp': datetime.now().isoformat()
                },
                metadata={
                    'importance': 1.0 if any(marker.lower() in content.lower() 
                                          for marker in ['nia', 'echo', 'predecessor']) 
                              else 0.5  # Boost importance for key topics
                }
            )
            
            # Build response parts
            insights = "; ".join(reflections['key_insights'][:2]) if reflections['key_insights'] else "No clear insights"
            key_insights = f"Key insights: {insights}"
            
            # Add patterns if available
            patterns = ""
            if reflections['patterns']:
                patterns = f" (Patterns: {'; '.join(reflections['patterns'][:2])})"
            
            # Add learning points if available
            learning = ""
            if reflections['learning_points']:
                learning = f" [Learned: {'; '.join(reflections['learning_points'][:2])}]"
            
            # Combine all parts
            return f"{key_insights}{patterns}{learning}"
            
        except Exception as e:
            error_msg = f"Error in reflection processing: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return "Unable to process reflections at this time"
