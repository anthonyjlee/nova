"""
Agent for gathering and analyzing external information.
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

class ResearchAgent(TimeAwareAgent):
    """Gathers and analyzes external information."""
    
    def __init__(self, memory_store: MemoryStore, error_handler: ErrorHandler,
                 feedback_system: FeedbackSystem):
        """Initialize research agent."""
        super().__init__("ResearchAgent", memory_store, error_handler, feedback_system)
    
    async def _analyze_research(self, content: str, context: Dict) -> Dict:
        """Analyze research needs and findings."""
        # Get similarity with current research interests
        research_similarity = await self.get_state_similarity('memories', content)
        
        prompt = f"""You are part of Nova, an AI assistant. Analyze research needs and findings:

Input: {content}

Context:
{json.dumps(context, indent=2)}

Current State:
- Research similarity: {research_similarity:.2f}

Important Guidelines:
- Focus only on information explicitly provided
- Do not make assumptions about capabilities
- Maintain awareness of being a new system
- Show interest in learning but acknowledge limitations
- Be direct and honest about current state
- Do not claim knowledge or research areas not mentioned

Return ONLY a JSON object in this EXACT format (no other text):
{{
    "key_capabilities": ["list of relevant capabilities"],
    "recent_developments": ["list of recent findings or developments"],
    "impact_areas": ["list of areas impacted by findings"],
    "synthesis": "string - overall synthesis of research state",
    "state_update": "string - description of knowledge evolution"
}}
"""

        try:
            # Get research analysis
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
                logger.error("Failed to parse research analysis JSON")
                raise ValueError("Invalid JSON format in research analysis")
            
            # Clean and validate data
            research_data = {
                'key_capabilities': self._safe_list(data.get('key_capabilities')),
                'recent_developments': self._safe_list(data.get('recent_developments')),
                'impact_areas': self._safe_list(data.get('impact_areas')),
                'synthesis': self._safe_str(data.get('synthesis'), "analysis incomplete"),
                'state_update': self._safe_str(data.get('state_update'), "no significant change"),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update research state vector
            await self.update_state_vector('memories', 
                f"{research_data['synthesis']} {research_data['state_update']}")
            
            return research_data
            
        except Exception as e:
            logger.error(f"Error analyzing research: {str(e)}")
            return {
                'key_capabilities': ["analysis error"],
                'recent_developments': ["processing failed"],
                'impact_areas': ["unknown"],
                'synthesis': "analysis incomplete",
                'state_update': "error in processing",
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_research_history(self, limit: int = 3) -> List[Dict]:
        """Get recent research memories."""
        try:
            memories = await self.memory_store.get_recent_memories(
                agent_name=self.name,
                memory_type="research",
                limit=limit
            )
            return memories if isinstance(memories, list) else []
        except Exception as e:
            logger.error(f"Error getting research history: {str(e)}")
            return []
    
    async def process_interaction(self, content: str) -> str:
        """Process interaction and update research state."""
        try:
            # Extract context
            content, context = self._extract_context(content)
            
            # Analyze research
            research = await self._analyze_research(content, context)
            
            # Store memory
            await self.store_memory(
                memory_type="research",
                content={
                    'research': research,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Return concise research insight
            capabilities = '; '.join(research['key_capabilities'][:2]) if research['key_capabilities'] else "none identified"
            developments = '; '.join(research['recent_developments'][:1]) if research['recent_developments'] else "none found"
            return f"Key capabilities: {capabilities} | Recent developments: {developments} - Impact: {research['synthesis']}"
            
        except Exception as e:
            error_msg = f"Error in research processing: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return "Unable to process research at this time"
    
    async def reflect(self) -> Dict:
        """Reflect on research development."""
        try:
            history = await self._get_research_history()
            
            # Extract research patterns
            capabilities = []
            developments = []
            syntheses = []
            
            for memory in history:
                if isinstance(memory.get('content'), dict):
                    research_data = memory['content'].get('research', {})
                    if isinstance(research_data, dict):
                        if research_data.get('key_capabilities'):
                            capabilities.extend(research_data['key_capabilities'])
                        if research_data.get('recent_developments'):
                            developments.extend(research_data['recent_developments'])
                        synthesis = self._safe_str(research_data.get('synthesis'))
                        if synthesis:
                            syntheses.append(synthesis)
            
            # Limit to most recent unique items
            capabilities = list(dict.fromkeys(capabilities))[-3:]
            developments = list(dict.fromkeys(developments))[-3:]
            syntheses = list(dict.fromkeys(syntheses))[-3:]
            
            return {
                'capability_pattern': ', '.join(capabilities) if capabilities else 'no clear capabilities',
                'development_trend': ', '.join(developments) if developments else 'no clear developments',
                'synthesis_evolution': ', '.join(syntheses) if syntheses else 'analysis incomplete',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error in research reflection: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'capability_pattern': 'no clear capabilities',
                'development_trend': 'no clear developments',
                'synthesis_evolution': 'analysis incomplete',
                'timestamp': datetime.now().isoformat()
            }
