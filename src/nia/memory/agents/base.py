"""Base agent class with common functionality."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..memory_types import AgentResponse, DialogueMessage

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base agent with common functionality."""
    
    def __init__(self, llm, store, vector_store, agent_type: str):
        """Initialize base agent.
        
        Args:
            llm: LLM interface
            store: Neo4j store
            vector_store: Vector store
            agent_type: Type of agent
        """
        self.llm = llm
        self.store = store
        self.vector_store = vector_store
        self.agent_type = agent_type
        self.current_dialogue = None
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for agent.
        
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
            Agent response
        """
        try:
            # Get structured completion
            response = await self.llm.get_structured_completion(
                self._format_prompt(content),
                agent_type=self.agent_type,
                metadata=metadata
            )
            
            # Add agent perspective
            response.perspective = self.agent_type
            
            return response
            
        except Exception as e:
            logger.error(f"Error in {self.agent_type} agent: {str(e)}")
            return AgentResponse(
                response=str(e),
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective=self.agent_type,
                confidence=0.0,
                timestamp=datetime.now()
            )
    
    async def provide_insight(
        self,
        content: str,
        references: Optional[List[str]] = None
    ) -> DialogueMessage:
        """Provide insight into current dialogue.
        
        Args:
            content: Insight content
            references: Optional list of referenced concepts/messages
            
        Returns:
            New dialogue message
        """
        if not self.current_dialogue:
            logger.warning("No active dialogue for insight")
            return None
            
        message = DialogueMessage(
            content=content,
            message_type="insight",
            agent_type=self.agent_type,
            references=references or [],
            timestamp=datetime.now()
        )
        
        self.current_dialogue.add_message(message)
        return message
    
    async def send_message(
        self,
        content: str,
        message_type: str,
        references: Optional[List[str]] = None
    ) -> DialogueMessage:
        """Send message to current dialogue.
        
        Args:
            content: Message content
            message_type: Type of message
            references: Optional list of referenced concepts/messages
            
        Returns:
            New dialogue message
        """
        if not self.current_dialogue:
            logger.warning("No active dialogue for message")
            return None
            
        message = DialogueMessage(
            content=content,
            message_type=message_type,
            agent_type=self.agent_type,
            references=references or [],
            timestamp=datetime.now()
        )
        
        self.current_dialogue.add_message(message)
        return message
