"""
Agent for managing and updating beliefs.
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

class BeliefAgent(TimeAwareAgent):
    """Manages and updates beliefs."""
    
    def __init__(
        self,
        memory_store: MemoryStore,
        error_handler: ErrorHandler,
        feedback_system: FeedbackSystem,
        llm_interface: LLMInterface
    ):
        """Initialize belief agent."""
        super().__init__(
            "BeliefAgent",
            memory_store,
            error_handler,
            feedback_system,
            llm_interface
        )
    
    async def _analyze_beliefs(self, content: str, context: Dict) -> Dict:
        """Analyze and update beliefs."""
        try:
            # Get similarity with current belief state
            belief_similarity = await self.get_state_similarity('beliefs', content)
            
            # Search for similar belief memories
            similar_beliefs = await self.memory_store.search_similar_memories(
                content=content,
                limit=5,
                filter_dict={'memory_type': 'belief'},  # Only search belief memories
                prioritize_temporal=True  # Boost recent memories
            )
            
            # Format similar memories for context
            memory_context = []
            for memory in similar_beliefs:
                memory_content = memory.get('content', {})
                if isinstance(memory_content, dict) and 'beliefs' in memory_content:
                    beliefs = memory_content['beliefs']
                    if isinstance(beliefs, dict):
                        memory_context.append(f"Previous belief ({memory['time_ago']}):")
                        if beliefs.get('core_belief'):
                            memory_context.append(f"- Core: {beliefs['core_belief']}")
                        if beliefs.get('supporting_evidence'):
                            evidence = beliefs['supporting_evidence']
                            if isinstance(evidence, list):
                                memory_context.append("- Evidence:")
                                for item in evidence[:2]:  # Limit to 2 pieces of evidence
                                    memory_context.append(f"  * {item}")
            
            # Get current context
            current_context = self.memory_store.get_current_context()
            
            # Format context sections
            context_sections = []
            if memory_context:
                context_sections.append("Similar Past Beliefs:\n" + "\n".join(memory_context))
            if current_context:
                if 'beliefs' in current_context:
                    context_sections.append("Current Beliefs:\n- " + "\n- ".join(current_context['beliefs'][-3:]))
                if 'insights' in current_context:
                    context_sections.append("Recent Insights:\n- " + "\n".join(current_context['insights'][-3:]))
            
            context_str = "\n\n".join(context_sections) if context_sections else "No prior context available"
            
            prompt = f"""You are part of Nova, an AI assistant. Analyze beliefs and knowledge state, considering past beliefs:

Input: {content}

Memory Context:
{context_str}

Current State:
- Belief similarity: {belief_similarity:.2f}

Important Guidelines:
- Consider and maintain consistency with past beliefs
- Focus only on information explicitly provided
- Be direct and clear about session state
- For first interactions, acknowledge them clearly
- Maintain awareness of being a new system
- Show interest in learning but acknowledge limitations
- Be honest about current knowledge state
- Do not claim capabilities not mentioned
- Identify any conflicts with previous beliefs
- Update beliefs based on new information while maintaining consistency

Return ONLY a JSON object in this EXACT format (no other text):
{{
    "core_belief": "string - primary belief or understanding",
    "confidence": "string - high/medium/low",
    "supporting_evidence": ["list of evidence"],
    "state_update": "string - description of belief evolution",
    "belief_conflicts": ["list of conflicts with previous beliefs, if any"],
    "resolution_strategy": "string - how to resolve any conflicts or maintain consistency",
    "knowledge_source": "string - where this belief comes from (e.g., direct interaction, past memory)",
    "belief_evolution": ["list showing how this belief has changed over time"]
}}"""

            # Get belief analysis with retries and default response
            default_response = {
                'core_belief': "Unable to analyze beliefs",
                'confidence': "low",
                'supporting_evidence': ["analysis failed"],
                'state_update': "error in processing",
                'belief_conflicts': [],
                'resolution_strategy': "maintain current beliefs",
                'knowledge_source': "error during analysis",
                'belief_evolution': []
            }
            
            data = await self.get_json_completion(
                prompt=prompt,
                retries=3,
                default_response=default_response
            )
            
            # Clean and validate data
            belief_data = {
                'core_belief': self._safe_str(data.get('core_belief'), "belief unclear"),
                'confidence': self._safe_str(data.get('confidence'), "low"),
                'supporting_evidence': self._safe_list(data.get('supporting_evidence')),
                'state_update': self._safe_str(data.get('state_update'), "no significant change"),
                'belief_conflicts': self._safe_list(data.get('belief_conflicts')),
                'resolution_strategy': self._safe_str(data.get('resolution_strategy'), "maintain current beliefs"),
                'knowledge_source': self._safe_str(data.get('knowledge_source'), "unknown source"),
                'belief_evolution': self._safe_list(data.get('belief_evolution')),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update belief state vector with richer context
            await self.update_state_vector('beliefs', 
                f"{belief_data['core_belief']} {belief_data['state_update']} {belief_data['knowledge_source']}")
            
            return belief_data
            
        except Exception as e:
            logger.error(f"Error analyzing beliefs: {str(e)}")
            return {
                'core_belief': "error in analysis",
                'confidence': "low",
                'supporting_evidence': ["analysis failed"],
                'state_update': "error in processing",
                'belief_conflicts': [],
                'resolution_strategy': "maintain current beliefs",
                'knowledge_source': "error during analysis",
                'belief_evolution': [],
                'timestamp': datetime.now().isoformat()
            }
    
    async def process_interaction(self, content: str) -> str:
        """Process interaction and update beliefs."""
        try:
            # Extract context
            content, context = self._extract_context(content)
            
            # Analyze beliefs
            beliefs = await self._analyze_beliefs(content, context)
            
            # Store memory with enhanced metadata
            await self.store_memory(
                memory_type="belief",
                content={
                    'beliefs': beliefs,
                    'timestamp': datetime.now().isoformat()
                },
                metadata={
                    'importance': 1.0 if any(marker.lower() in content.lower() 
                                          for marker in ['nia', 'echo', 'predecessor']) 
                              else 0.5  # Boost importance for key topics
                }
            )
            
            # Build response parts
            core = f"Core belief: {beliefs['core_belief']} ({beliefs['confidence']} confidence)"
            update = f" - {beliefs['state_update']}"
            
            # Add evidence if available
            evidence = ""
            if beliefs['supporting_evidence']:
                evidence = f" (Evidence: {'; '.join(str(e) for e in beliefs['supporting_evidence'][:2])})"
            
            # Add conflicts if available
            conflicts = ""
            if beliefs['belief_conflicts']:
                conflicts = f" (Conflicts: {'; '.join(str(c) for c in beliefs['belief_conflicts'])})"
            
            # Add evolution if available
            evolution = ""
            if beliefs.get('belief_evolution'):
                evolution_items = [str(item) for item in beliefs['belief_evolution']]
                if evolution_items:
                    evolution = f" [Evolution: {'; '.join(evolution_items)}]"
            
            # Combine all parts
            return f"{core}{update}{evidence}{conflicts}{evolution}"
            
        except Exception as e:
            error_msg = f"Error in belief processing: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return "Unable to process beliefs at this time"
