"""Base agent implementation."""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
from ..memory_types import AgentResponse

if TYPE_CHECKING:
    from ..llm_interface import LLMInterface
    from ..neo4j_store import Neo4jMemoryStore
    from ..vector_store import VectorStore

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all agents."""
    
    def __init__(
        self,
        llm: 'LLMInterface',
        store: 'Neo4jMemoryStore',
        vector_store: 'VectorStore',
        agent_type: str
    ):
        """Initialize base agent."""
        self.llm = llm
        self.store = store
        self.vector_store = vector_store
        self.agent_type = agent_type
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM.
        
        Args:
            content: Content to format prompt for
            
        Returns:
            Formatted prompt string
        """
        raise NotImplementedError("Subclasses must implement _format_prompt")
    
    async def process(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process content through agent.
        
        Args:
            content: Content to process
            metadata: Optional metadata
            
        Returns:
            Processed agent response
        """
        try:
            # Get structured completion
            response = await self.llm.get_structured_completion(
                self._format_prompt(content)
            )
            
            # Add metadata if provided
            if metadata:
                if not response.metadata:
                    response.metadata = {}
                response.metadata.update(metadata)
            
            # Add agent type
            response.perspective = self.agent_type
            
            return response
            
        except Exception as e:
            logger.error(f"Error in {self.agent_type} agent: {str(e)}")
            return AgentResponse(
                response=f"Error in {self.agent_type} agent: {str(e)}",
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective=self.agent_type,
                confidence=0.0,
                timestamp=datetime.now()
            )
