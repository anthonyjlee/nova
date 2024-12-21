"""
Enhanced research agent implementation using LLMs for all operations.
"""

import logging
from typing import Dict, Any
from .agents.base import BaseAgent
from .memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    """Agent for research and knowledge integration."""
    
    def __init__(self, *args, **kwargs):
        """Initialize research agent."""
        super().__init__(*args, agent_type="research", **kwargs)
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        # Get content text
        text = content.get('content', '')
        
        # Get similar memories for knowledge context
        memories = content.get('similar_memories', [])
        memory_text = '\n'.join([
            f"Memory {i+1}: {m.get('content', {}).get('content', '')}"
            for i, m in enumerate(memories)
        ])
        
        # Get relevant concepts
        concepts = content.get('relevant_concepts', [])
        concept_text = '\n'.join([
            f"Concept {i+1}: {c.get('name')} ({c.get('type')}) - {c.get('description')}"
            for i, c in enumerate(concepts)
        ])
        
        # Format prompt
        prompt = f"""Analyze the following content from a research and knowledge integration perspective.
        Consider information sources, knowledge gaps, and integration opportunities.
        
        Content to Research:
        {text}
        
        Existing Knowledge:
        {memory_text}
        
        Known Concepts:
        {concept_text}
        
        Provide analysis in this exact format:
        {{
            "response": "Detailed analysis from research perspective",
            "concepts": [
                {{
                    "name": "Concept name",
                    "type": "knowledge|source|connection|gap",
                    "description": "Clear description of the research concept",
                    "related": ["Related concept names"],
                    "validation": {{
                        "confidence": 0.8,
                        "supported_by": ["evidence"],
                        "contradicted_by": [],
                        "needs_verification": []
                    }}
                }}
            ],
            "key_points": [
                "Key point about information gathered"
            ],
            "implications": [
                "Implication for knowledge integration"
            ],
            "uncertainties": [
                "Uncertainty requiring further research"
            ],
            "reasoning": [
                "Step in research process"
            ]
        }}
        
        Focus on:
        - Knowledge gaps and research needs
        - Information sources and reliability
        - Integration opportunities with existing knowledge
        - Verification requirements
        - Research priorities
        
        Return ONLY the JSON object, no other text."""
        
        return prompt
    
    async def research_topic(
        self,
        topic: str,
        context: Dict[str, Any] = None
    ) -> AgentResponse:
        """Conduct research on a specific topic."""
        try:
            # Format research content
            content = {
                'content': topic,
                'context': context or {}
            }
            
            # Process through research lens
            return await self.process(content)
            
        except Exception as e:
            logger.error(f"Error researching topic: {str(e)}")
            return AgentResponse(
                response=f"Error researching topic: {str(e)}",
                concepts=[],
                perspective="research",
                confidence=0.0
            )
