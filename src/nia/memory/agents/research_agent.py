"""
Agent for research and information gathering.
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

class ResearchAgent(TimeAwareAgent):
    """Manages research and information gathering."""
    
    def __init__(
        self,
        memory_store: MemoryStore,
        error_handler: ErrorHandler,
        feedback_system: FeedbackSystem,
        llm_interface: LLMInterface
    ):
        """Initialize research agent."""
        super().__init__(
            "ResearchAgent",
            memory_store,
            error_handler,
            feedback_system,
            llm_interface
        )
    
    async def _analyze_research(self, content: str, context: Dict) -> Dict:
        """Analyze research needs and findings."""
        try:
            # Get similarity with current research state
            research_similarity = await self.get_state_similarity('research', content)
            
            # Search for similar research memories
            similar_research = await self.memory_store.search_similar_memories(
                content=content,
                limit=5,
                filter_dict={'memory_type': 'research'},
                prioritize_temporal=True
            )
            
            # Format similar memories for context
            memory_context = []
            for memory in similar_research:
                memory_content = memory.get('content', {})
                if isinstance(memory_content, dict) and 'research' in memory_content:
                    research = memory_content['research']
                    if isinstance(research, dict):
                        memory_context.append(f"Previous research ({memory['time_ago']}):")
                        if research.get('findings'):
                            findings = research['findings']
                            if isinstance(findings, list):
                                memory_context.append("- Findings:")
                                for finding in findings[:2]:
                                    memory_context.append(f"  * {finding}")
                        if research.get('sources'):
                            sources = research['sources']
                            if isinstance(sources, list):
                                memory_context.append("- Sources:")
                                for source in sources[:2]:
                                    memory_context.append(f"  * {source}")
            
            # Get current context
            current_context = self.memory_store.get_current_context()
            
            # Format context sections
            context_sections = []
            if memory_context:
                context_sections.append("Similar Past Research:\n" + "\n".join(memory_context))
            if current_context:
                if 'beliefs' in current_context:
                    context_sections.append("Current Beliefs:\n- " + "\n- ".join(current_context['beliefs'][-3:]))
                if 'insights' in current_context:
                    context_sections.append("Recent Insights:\n- " + "\n".join(current_context['insights'][-3:]))
            
            context_str = "\n\n".join(context_sections) if context_sections else "No prior context available"
            
            prompt = f"""You are part of Nova, an AI assistant. Analyze research needs and findings from the current interaction:

Input: {content}

Memory Context:
{context_str}

Current State:
- Research similarity: {research_similarity:.2f}

Important Guidelines:
- Identify key research areas
- Evaluate information needs
- Consider existing knowledge
- Look for knowledge gaps
- Prioritize research topics
- Plan information gathering
- Maintain research focus
- Consider reliability of sources

Return ONLY a JSON object in this EXACT format (no other text):
{{
    "research_topics": ["list of topics to research"],
    "findings": ["list of current findings"],
    "knowledge_gaps": ["list of identified gaps"],
    "state_update": "string - how knowledge has evolved",
    "sources": ["list of potential sources"],
    "priorities": ["list of research priorities"],
    "next_steps": ["list of research actions"],
    "reliability": "string - assessment of information reliability"
}}"""

            # Get research analysis with retries and default response
            default_response = {
                'research_topics': ["Unable to analyze research needs"],
                'findings': ["analysis failed"],
                'knowledge_gaps': ["error in processing"],
                'state_update': "no significant change",
                'sources': [],
                'priorities': [],
                'next_steps': [],
                'reliability': "unknown"
            }
            
            data = await self.get_json_completion(
                prompt=prompt,
                retries=3,
                default_response=default_response
            )
            
            # Clean and validate data
            research_data = {
                'research_topics': self._safe_list(data.get('research_topics')),
                'findings': self._safe_list(data.get('findings')),
                'knowledge_gaps': self._safe_list(data.get('knowledge_gaps')),
                'state_update': self._safe_str(data.get('state_update'), "no significant change"),
                'sources': self._safe_list(data.get('sources')),
                'priorities': self._safe_list(data.get('priorities')),
                'next_steps': self._safe_list(data.get('next_steps')),
                'reliability': self._safe_str(data.get('reliability'), "unknown"),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update research state vector
            await self.update_state_vector('research',
                f"{' '.join(research_data['research_topics'])} {research_data['state_update']}")
            
            return research_data
            
        except Exception as e:
            logger.error(f"Error analyzing research: {str(e)}")
            return {
                'research_topics': ["error in analysis"],
                'findings': ["analysis failed"],
                'knowledge_gaps': ["error in processing"],
                'state_update': "no significant change",
                'sources': [],
                'priorities': [],
                'next_steps': [],
                'reliability': "unknown",
                'timestamp': datetime.now().isoformat()
            }
    
    async def process_interaction(self, content: str) -> str:
        """Process interaction and update research state."""
        try:
            # Extract context
            content, context = self._extract_context(content)
            
            # Analyze research
            research = await self._analyze_research(content, context)
            
            # Store memory with enhanced metadata
            await self.store_memory(
                memory_type="research",
                content={
                    'research': research,
                    'timestamp': datetime.now().isoformat()
                },
                metadata={
                    'importance': 1.0 if any(marker.lower() in content.lower() 
                                          for marker in ['nia', 'echo', 'predecessor']) 
                              else 0.5  # Boost importance for key topics
                }
            )
            
            # Build response parts
            topics = "; ".join(research['research_topics'][:2]) if research['research_topics'] else "none identified"
            findings = "; ".join(research['findings'][:2]) if research['findings'] else "none found"
            key_findings = f"Key capabilities: {topics} | Recent developments: {findings}"
            
            # Add impact if available
            impact = ""
            if research['knowledge_gaps']:
                impact = f" - Impact: {research['knowledge_gaps'][0]}"
            
            # Combine all parts
            return f"{key_findings}{impact}"
            
        except Exception as e:
            error_msg = f"Error in research processing: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return "Unable to process research at this time"
