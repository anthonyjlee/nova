"""Response processor agent for parsing and structuring LLM outputs."""

import logging
from typing import Dict, Any
from datetime import datetime
from nia.core.interfaces.llm_interface import LLMInterface
from nia.core.neo4j.neo4j_store import Neo4jMemoryStore
from nia.memory.vector_store import VectorStore
from nia.core.types.memory_types import AgentResponse
from nia.agents.base import BaseAgent
from nia.core.prompts import AGENT_PROMPTS

logger = logging.getLogger(__name__)

class ResponseProcessor(BaseAgent):
    """Agent for processing and structuring LLM responses."""
    
    def __init__(
        self,
        name: str = "ResponseProcessor",
        memory_system = None,
        world = None,
        attributes: Dict[str, Any] = {}
    ):
        """Initialize response processor."""
        super().__init__(
            name=name,
            agent_type="response_processor",
            memory_system=memory_system,
            world=world,
            attributes=attributes
        )
        
    async def parse(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Parse input content."""
        text = content.get('text', '')
        # Basic parsing implementation - could be enhanced
        return {
            'text': text,
            'confidence': 1.0,
            'parsed_at': datetime.now().isoformat()
        }
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for response processing."""
        text = content.get('text', '')
        return AGENT_PROMPTS["response_processor"].format(content=text)
    
    async def process_response(self, text: str) -> AgentResponse:
        """Process and structure an LLM response using parsing agent."""
        try:
            # Parse the text and return structured response
            parsed = await self.parse({'text': text})
            return AgentResponse(
                content=text,
                confidence=parsed.get('confidence', 1.0),
                metadata=parsed
            )
                
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return AgentResponse(
                content=text,
                confidence=0.0,
                metadata={"error": str(e)}
            )
