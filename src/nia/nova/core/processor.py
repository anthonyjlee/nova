"""Response processor agent for parsing and structuring LLM outputs."""

import logging
from typing import Dict, Any
from datetime import datetime
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..vector_store import VectorStore
from ..memory_types import AgentResponse
from .base import BaseAgent
from ..prompts import AGENT_PROMPTS

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
        text = content.get('text', '')
        return AGENT_PROMPTS["response_processor"].format(content=text)
    
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
