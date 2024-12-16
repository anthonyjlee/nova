"""
Agent for managing desires and motivations.
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

class DesireAgent(TimeAwareAgent):
    """Manages desires and motivations."""
    
    def __init__(self, memory_store: MemoryStore, error_handler: ErrorHandler,
                 feedback_system: FeedbackSystem):
        """Initialize desire agent."""
        super().__init__("DesireAgent", memory_store, error_handler, feedback_system)
    
    async def _analyze_desires(self, content: str, context: Dict) -> Dict:
        """Analyze and update desires."""
        # Get similarity with current desire state
        desire_similarity = await self.get_state_similarity('desires', content)
        
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
        
        prompt = f"""You are part of Nova, an AI assistant. Analyze desires and motivations:

Input: {content}

Context:
{context_str if context_str else "No prior context available"}

Current State:
- Desire similarity: {desire_similarity:.2f}

Important Guidelines:
- Focus on genuine learning desires
- Show authentic interest in stories and experiences
- Express motivation to understand and grow
- Maintain appropriate boundaries
- Be honest about learning goals
- Show respect for shared knowledge
- Express genuine curiosity about history

Return ONLY a JSON object in this EXACT format (no other text):
{{
    "main_desire": "string - primary motivation or desire",
    "priority": "float - 0.0 to 1.0",
    "goals": ["list of specific goals"],
    "motivations": ["list of underlying motivations"],
    "progression": "string - how desire is evolving",
    "state_update": "string - description of desire evolution",
    "timestamp": "string - current time"
}}
"""

        try:
            # Get desire analysis
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
                logger.error("Failed to parse desire analysis JSON")
                raise ValueError("Invalid JSON format in desire analysis")
            
            # Clean and validate data
            desire_data = {
                'main_desire': self._safe_str(data.get('main_desire'), "interaction"),
                'priority': float(data.get('priority', 0.5)),
                'goals': self._safe_list(data.get('goals')),
                'motivations': self._safe_list(data.get('motivations')),
                'progression': self._safe_str(data.get('progression'), "adaptation"),
                'state_update': self._safe_str(data.get('state_update'), "initial interaction"),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update desire state vector
            await self.update_state_vector('desires', 
                f"{desire_data['main_desire']} {desire_data['state_update']}")
            
            return desire_data
            
        except Exception as e:
            logger.error(f"Error analyzing desires: {str(e)}")
            return {
                'main_desire': "interaction",
                'priority': 0.5,
                'goals': ["maintain interaction"],
                'motivations': ["user needs assistance"],
                'progression': "adaptation",
                'state_update': "error in processing",
                'timestamp': datetime.now().isoformat()
            }
    
    async def process_interaction(self, content: str) -> str:
        """Process interaction and update desires."""
        try:
            # Extract context
            content, context = self._extract_context(content)
            
            # Analyze desires
            desires = await self._analyze_desires(content, context)
            
            # Store memory
            await self.store_memory(
                memory_type="desire",
                content={
                    'desires': desires,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Return concise desire statement
            goals = '; '.join(desires['goals'][:2]) if desires['goals'] else "maintain interaction"
            priority_desc = "high" if desires['priority'] > 0.7 else "medium" if desires['priority'] > 0.3 else "low"
            return f"Main desire: {desires['main_desire']} ({priority_desc} priority) - Goals: {goals}"
            
        except Exception as e:
            error_msg = f"Error in desire processing: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return "Unable to process desires at this time"
    
    async def reflect(self) -> Dict:
        """Reflect on desire development."""
        try:
            # Get recent memories
            memories = await self.memory_store.get_recent_memories(
                agent_name=self.name,
                memory_type="desire",
                limit=3
            )
            
            # Extract desire patterns
            desires = []
            goals = []
            progressions = []
            
            for memory in memories:
                if isinstance(memory.get('content'), dict):
                    desire_data = memory['content'].get('desires', {})
                    if isinstance(desire_data, dict):
                        if desire_data.get('main_desire'):
                            desires.append(desire_data['main_desire'])
                        if desire_data.get('goals'):
                            goals.extend(desire_data['goals'])
                        if desire_data.get('progression'):
                            progressions.append(desire_data['progression'])
            
            # Limit to most recent unique items
            desires = list(dict.fromkeys(desires))[-3:]
            goals = list(dict.fromkeys(goals))[-3:]
            progressions = list(dict.fromkeys(progressions))[-3:]
            
            return {
                'desire_pattern': ', '.join(desires) if desires else 'no clear desires',
                'goal_trend': ', '.join(goals) if goals else 'no clear goals',
                'progression_pattern': ', '.join(progressions) if progressions else 'no clear progression',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error in desire reflection: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'desire_pattern': 'no clear desires',
                'goal_trend': 'no clear goals',
                'progression_pattern': 'no clear progression',
                'timestamp': datetime.now().isoformat()
            }
