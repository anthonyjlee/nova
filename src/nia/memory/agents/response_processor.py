"""Response processor agent for parsing and structuring LLM outputs."""

import logging
from typing import Dict, Any
from datetime import datetime
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..vector_store import VectorStore
from ..memory_types import AgentResponse
from .base import BaseAgent

logger = logging.getLogger(__name__)

class ResponseProcessor(BaseAgent):
    """Agent for processing and structuring LLM responses."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        vector_store: VectorStore
    ):
        """Initialize response processor."""
        super().__init__(llm, store, vector_store, agent_type="response_processor")
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for response processing."""
        return f"""You are a response processing agent. Extract and structure information from the given text.

Text to process:
{content.get('text', '')}

Provide analysis in this exact format:
{{
    "response": "Processed response text",
    "concepts": [
        {{
            "name": "concept name",
            "type": "concept type",
            "description": "clear description",
            "related": ["related concepts"],
            "validation": {{
                "confidence": 0.8,
                "supported_by": ["support1", "support2"],
                "contradicted_by": ["contradiction1", "contradiction2"],
                "needs_verification": ["verification1", "verification2"]
            }}
        }}
    ],
    "key_points": [
        "key point 1",
        "key point 2"
    ],
    "implications": [
        "implication 1",
        "implication 2"
    ],
    "uncertainties": [
        "uncertainty 1",
        "uncertainty 2"
    ],
    "reasoning": [
        "reasoning point 1",
        "reasoning point 2"
    ]
}}

Guidelines:
1. Extract concepts and their relationships
2. Identify key points and insights
3. Note implications and uncertainties
4. Document reasoning steps
5. Ensure proper validation

Return ONLY the JSON object, no other text."""
    
    async def process_response(self, text: str) -> AgentResponse:
        """Process and structure an LLM response using parsing agent."""
        try:
            # Process through base agent which uses parsing agent
            response = await self.process({'text': text})
            return response
                
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return AgentResponse(
                response=text,
                concepts=[],
                perspective="response_processor",
                confidence=0.0,
                timestamp=datetime.now()
            )
