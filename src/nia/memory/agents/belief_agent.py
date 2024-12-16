"""
Agent for managing and updating beliefs.
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

class BeliefAgent(TimeAwareAgent):
    """Manages and updates beliefs."""
    
    def __init__(self, memory_store: MemoryStore, error_handler: ErrorHandler,
                 feedback_system: FeedbackSystem):
        """Initialize belief agent."""
        super().__init__("BeliefAgent", memory_store, error_handler, feedback_system)
    
    async def _analyze_beliefs(self, content: str, context: Dict) -> Dict:
        """Analyze and update beliefs."""
        # Get similarity with current belief state
        belief_similarity = await self.get_state_similarity('beliefs', content)
        
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
        
        prompt = f"""You are part of Nova, an AI assistant. Analyze beliefs and knowledge state:

Input: {content}

Context:
{context_str if context_str else "No prior context available"}

Current State:
- Belief similarity: {belief_similarity:.2f}

Important Guidelines:
- Focus only on information explicitly provided
- Be direct and clear about session state
- For first interactions, acknowledge them clearly
- Maintain awareness of being a new system
- Show interest in learning but acknowledge limitations
- Be honest about current knowledge state
- Do not claim capabilities not mentioned

Return ONLY a JSON object in this EXACT format (no other text):
{{
    "core_belief": "string - primary belief or understanding",
    "confidence": "string - high/medium/low",
    "supporting_evidence": ["list of evidence"],
    "state_update": "string - description of belief evolution"
}}
"""

        try:
            # Get belief analysis
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
                logger.error("Failed to parse belief analysis JSON")
                raise ValueError("Invalid JSON format in belief analysis")
            
            # Clean and validate data
            belief_data = {
                'core_belief': self._safe_str(data.get('core_belief'), "belief unclear"),
                'confidence': self._safe_str(data.get('confidence'), "low"),
                'supporting_evidence': self._safe_list(data.get('supporting_evidence')),
                'state_update': self._safe_str(data.get('state_update'), "no significant change"),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update belief state vector
            await self.update_state_vector('beliefs', 
                f"{belief_data['core_belief']} {belief_data['state_update']}")
            
            return belief_data
            
        except Exception as e:
            logger.error(f"Error analyzing beliefs: {str(e)}")
            return {
                'core_belief': "error in analysis",
                'confidence': "low",
                'supporting_evidence': ["analysis failed"],
                'state_update': "error in processing",
                'timestamp': datetime.now().isoformat()
            }
    
    async def process_interaction(self, content: str) -> str:
        """Process interaction and update beliefs."""
        try:
            # Extract context
            content, context = self._extract_context(content)
            
            # Analyze beliefs
            beliefs = await self._analyze_beliefs(content, context)
            
            # Store memory
            await self.store_memory(
                memory_type="belief",
                content={
                    'beliefs': beliefs,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Return concise belief statement
            evidence = '; '.join(beliefs['supporting_evidence'][:2]) if beliefs['supporting_evidence'] else "no clear evidence"
            return f"Core belief: {beliefs['core_belief']} ({beliefs['confidence']} confidence) - {beliefs['state_update']}"
            
        except Exception as e:
            error_msg = f"Error in belief processing: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return "Unable to process beliefs at this time"
    
    async def reflect(self) -> Dict:
        """Reflect on belief development."""
        try:
            # Get recent memories
            memories = await self.memory_store.get_recent_memories(
                agent_name=self.name,
                memory_type="belief",
                limit=3
            )
            
            # Extract belief patterns
            beliefs = []
            evidence = []
            updates = []
            
            for memory in memories:
                if isinstance(memory.get('content'), dict):
                    belief_data = memory['content'].get('beliefs', {})
                    if isinstance(belief_data, dict):
                        if belief_data.get('core_belief'):
                            beliefs.append(belief_data['core_belief'])
                        if belief_data.get('supporting_evidence'):
                            evidence.extend(belief_data['supporting_evidence'])
                        if belief_data.get('state_update'):
                            updates.append(belief_data['state_update'])
            
            # Limit to most recent unique items
            beliefs = list(dict.fromkeys(beliefs))[-3:]
            evidence = list(dict.fromkeys(evidence))[-3:]
            updates = list(dict.fromkeys(updates))[-3:]
            
            return {
                'belief_pattern': ', '.join(beliefs) if beliefs else 'no clear beliefs',
                'evidence_trend': ', '.join(evidence) if evidence else 'no clear evidence',
                'update_evolution': ', '.join(updates) if updates else 'no clear evolution',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error in belief reflection: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'belief_pattern': 'no clear beliefs',
                'evidence_trend': 'no clear evidence',
                'update_evolution': 'no clear evolution',
                'timestamp': datetime.now().isoformat()
            }
