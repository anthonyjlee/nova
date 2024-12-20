"""Meta agent for synthesizing responses from other agents."""

import logging
import json
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime
from ..memory_types import AgentResponse, DialogueContext
from .base import BaseAgent

if TYPE_CHECKING:
    from ..llm_interface import LLMInterface
    from ..neo4j_store import Neo4jMemoryStore
    from ..vector_store import VectorStore

logger = logging.getLogger(__name__)

class MetaAgent(BaseAgent):
    """Agent for synthesizing responses and managing dialogue."""
    
    def __init__(
        self,
        llm: 'LLMInterface',
        store: 'Neo4jMemoryStore',
        vector_store: 'VectorStore'
    ):
        """Initialize meta agent."""
        super().__init__(llm, store, vector_store, agent_type="meta")
        self.current_dialogue = None
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        # Get content and responses
        text = content.get('content', {}).get('content', '')
        responses = content.get('agent_responses', {})
        dialogue = content.get('dialogue_context')
        
        # Format agent responses
        response_text = '\n\n'.join([
            f"{agent_type.capitalize()} Agent Response:\n{response.response}\n"
            f"Concepts: {json.dumps(response.concepts)}\n"
            f"Key Points: {json.dumps(response.key_points)}\n"
            f"Implications: {json.dumps(response.implications)}"
            for agent_type, response in responses.items()
        ])
        
        # Format dialogue context if available
        dialogue_text = ""
        if dialogue:
            dialogue_text = "\nDialogue Context:\n" + "\n".join([
                f"{m.agent_type}: {m.content}"
                for m in dialogue.messages
            ])
        
        # Format prompt
        prompt = f"""Synthesize the following agent responses into a coherent dialogue.

Content:
{text}

Agent Responses:
{response_text}

{dialogue_text}

Provide synthesis in this exact format:
{{
    "response": "Detailed dialogue synthesis",
    "concepts": [
        {{
            "name": "Concept name",
            "type": "pattern|insight|learning|evolution",
            "description": "Clear description",
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
        "Key insight or observation"
    ],
    "implications": [
        "Important implication"
    ],
    "uncertainties": [
        "Area of uncertainty"
    ],
    "reasoning": [
        "Step in synthesis"
    ]
}}

Guidelines:
1. Synthesize responses into a coherent narrative
2. Extract common themes and concepts
3. Identify key insights and implications
4. Note areas of uncertainty or disagreement
5. Format as proper JSON

Return ONLY the JSON object, no other text."""
        
        return prompt
    
    async def synthesize_dialogue(
        self,
        content: Dict[str, Any]
    ) -> AgentResponse:
        """Synthesize dialogue from agent responses."""
        try:
            # Get structured completion
            response = await self.llm.get_structured_completion(
                self._format_prompt(content)
            )
            
            # Add dialogue context if available
            if content.get('dialogue_context'):
                response.dialogue_context = content['dialogue_context']
            
            # Add metadata
            response.metadata = {
                'dialogue_turns': len(content.get('dialogue_context', {}).messages) if content.get('dialogue_context') else 0,
                'participating_agents': list(content.get('agent_responses', {}).keys()),
                'synthesis_timestamp': datetime.now().isoformat()
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error synthesizing dialogue: {str(e)}")
            return AgentResponse(
                response="Error synthesizing dialogue",
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective="meta",
                confidence=0.0,
                timestamp=datetime.now()
            )
    
    async def process_interaction(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process interaction through meta agent."""
        try:
            # Create content dict
            content_dict = {
                'content': {'content': content},
                'dialogue_context': self.current_dialogue,
                'agent_responses': {}
            }
            
            # Get agent responses
            for agent_type in ['belief', 'desire', 'emotion', 'reflection', 'research']:
                agent = getattr(self, f"{agent_type}_agent", None)
                if agent:
                    content_dict['agent_responses'][agent_type] = await agent.process(
                        content_dict['content'],
                        metadata
                    )
            
            # Synthesize responses
            return await self.synthesize_dialogue(content_dict)
            
        except Exception as e:
            logger.error(f"Error processing interaction: {str(e)}")
            return AgentResponse(
                response="Error processing interaction",
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective="meta",
                confidence=0.0,
                timestamp=datetime.now()
            )
