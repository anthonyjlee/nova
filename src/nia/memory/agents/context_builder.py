"""
Context builder for gathering and formatting memory context.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

from ..persistence import MemoryStore

logger = logging.getLogger(__name__)

class ContextBuilder:
    """Handles building context from memories for agent interactions."""
    
    def __init__(self, memory_store: MemoryStore):
        """Initialize context builder."""
        self.memory_store = memory_store
    
    def format_interaction(self, memory: Dict) -> List[str]:
        """Format an interaction memory into readable lines."""
        lines = []
        memory_content = memory.get('content', {})
        
        if isinstance(memory_content, dict):
            if 'input' in memory_content:
                lines.append(f"Previous interaction ({memory['time_ago']}):")
                lines.append(f"- Input: {memory_content['input']}")
                if 'synthesis' in memory_content:
                    synthesis = memory_content['synthesis']
                    if isinstance(synthesis, dict):
                        if synthesis.get('response'):
                            lines.append(f"- Response: {synthesis['response']}")
                        if synthesis.get('key_points'):
                            lines.append("- Key points:")
                            for point in synthesis['key_points']:
                                lines.append(f"  * {point}")
        
        return lines
    
    def format_belief(self, memory: Dict) -> List[str]:
        """Format a belief memory into readable lines."""
        lines = []
        memory_content = memory.get('content', {})
        
        if isinstance(memory_content, dict) and 'beliefs' in memory_content:
            beliefs = memory_content['beliefs']
            if isinstance(beliefs, dict):
                lines.append(f"Previous belief ({memory['time_ago']}):")
                if beliefs.get('core_belief'):
                    lines.append(f"- Core: {beliefs['core_belief']}")
                if beliefs.get('supporting_evidence'):
                    evidence = beliefs['supporting_evidence']
                    if isinstance(evidence, list):
                        lines.append("- Evidence:")
                        for item in evidence[:2]:  # Limit to 2 pieces of evidence
                            lines.append(f"  * {item}")
        
        return lines
    
    def format_current_context(self, context: Dict[str, Any]) -> List[str]:
        """Format current context into readable lines."""
        context_lines = []
        
        if 'beliefs' in context:
            context_lines.append("Current Beliefs:")
            for belief in context['beliefs'][-3:]:  # Last 3 beliefs
                context_lines.append(f"- {belief}")
        
        if 'insights' in context:
            context_lines.append("Recent Insights:")
            for insight in context['insights'][-2:]:  # Last 2 insights
                context_lines.append(f"- {insight}")
        
        if 'findings' in context:
            context_lines.append("Recent Findings:")
            for finding in context['findings'][-2:]:  # Last 2 findings
                context_lines.append(f"- {finding}")
        
        return context_lines
    
    async def build_full_context(self, content: str) -> str:
        """Build complete context including interactions, beliefs, and current state."""
        try:
            # Get interaction memories
            similar_interactions = await self.memory_store.search_similar_memories(
                content=content,
                limit=10,
                filter_dict={'memory_type': 'interaction'},
                prioritize_temporal=True
            )
            
            # Deduplicate interactions by input content
            seen_inputs = set()
            unique_interactions = []
            for memory in similar_interactions:
                memory_content = memory.get('content', {})
                if isinstance(memory_content, dict):
                    input_content = memory_content.get('input', '')
                    if input_content and input_content not in seen_inputs:
                        seen_inputs.add(input_content)
                        unique_interactions.append(memory)
            
            # Get belief memories
            similar_beliefs = await self.memory_store.search_similar_memories(
                content=content,
                limit=5,
                filter_dict={'memory_type': 'belief'},
                prioritize_temporal=True
            )
            
            # Deduplicate beliefs by core belief
            seen_beliefs = set()
            unique_beliefs = []
            for memory in similar_beliefs:
                memory_content = memory.get('content', {})
                if isinstance(memory_content, dict) and 'beliefs' in memory_content:
                    beliefs = memory_content['beliefs']
                    if isinstance(beliefs, dict):
                        core_belief = beliefs.get('core_belief', '')
                        if core_belief and core_belief not in seen_beliefs:
                            seen_beliefs.add(core_belief)
                            unique_beliefs.append(memory)
            
            # Format context sections
            context_sections = []
            
            # Add interaction context (limit to 5 most recent)
            if unique_interactions:
                interaction_lines = []
                interaction_lines.append("Previous Interactions:")
                for memory in unique_interactions[:5]:  # Limit to 5 interactions
                    interaction_lines.extend(self.format_interaction(memory))
                context_sections.append("\n".join(interaction_lines))
            
            # Add belief context (limit to 3 most recent)
            if unique_beliefs:
                belief_lines = []
                belief_lines.append("Related Beliefs:")
                for memory in unique_beliefs[:3]:  # Limit to 3 beliefs
                    belief_lines.extend(self.format_belief(memory))
                context_sections.append("\n".join(belief_lines))
            
            # Add current context
            current_context = self.memory_store.get_current_context()
            current_lines = self.format_current_context(current_context)
            if current_lines:
                context_sections.append("Current Context:\n" + "\n".join(current_lines))
            
            return "\n\n".join(context_sections) if context_sections else "No prior context available"
            
        except Exception as e:
            logger.error(f"Error building context: {str(e)}")
            return "Error retrieving context"
