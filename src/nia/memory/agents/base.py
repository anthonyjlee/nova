"""Base agent class with common functionality."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..memory_types import AgentResponse, DialogueMessage
from ..prompts import AGENT_PROMPTS

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
        
        # Get prompt template for this agent type
        if agent_type not in AGENT_PROMPTS:
            raise ValueError(f"No prompt template found for agent type: {agent_type}")
        self.prompt_template = AGENT_PROMPTS[agent_type]
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for agent using template.
        
        Args:
            content: Content to format prompt for
            
        Returns:
            Formatted prompt string
        """
        # Extract content from dictionary
        if not content:
            content_str = ""
        elif isinstance(content, str):
            content_str = content
        elif isinstance(content, dict):
            # Handle nested content
            if 'content' in content:
                content_str = content['content']
                if isinstance(content_str, dict) and 'content' in content_str:
                    content_str = content_str['content']
                elif isinstance(content_str, str):
                    content_str = content_str.strip()
                else:
                    content_str = str(content_str)
            else:
                content_str = str(content)
        else:
            content_str = str(content)
            
        # Format prompt template
        return self.prompt_template.format(content=content_str.strip())
    
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
            # Format prompt and get structured completion
            prompt = self._format_prompt(content)
            logger.debug(f"Formatted prompt: {prompt}")
            
            response = await self.llm.get_structured_completion(
                prompt,
                agent_type=self.agent_type,
                metadata=metadata
            )
            logger.debug(f"LLM response: {response}")
            
            # Add agent perspective and dialogue context
            response.perspective = self.agent_type
            if self.current_dialogue:
                response.dialogue_context = self.current_dialogue
                
                # Add message to dialogue
                await self.provide_insight(
                    content=response.response,
                    references=[c["name"] for c in response.concepts]
                )
            
            # Add metadata if provided
            if metadata:
                if not response.metadata:
                    response.metadata = {}
                response.metadata.update(metadata)
            
            return response
            
        except Exception as e:
            error_msg = f"Error in {self.agent_type} agent: {str(e)}"
            logger.error(error_msg)
            
            # If using mock mode, return mock response
            if hasattr(self.llm, 'use_mock') and self.llm.use_mock:
                concept = self.llm._get_mock_concept(self.agent_type)
                mock_concept = {
                    "name": concept["name"],
                    "type": concept["type"],
                    "description": concept["description"],
                    "related": concept["related"],
                    "validation": {
                        "confidence": 0.8,
                        "supported_by": ["Evidence 1"],
                        "contradicted_by": [],
                        "needs_verification": []
                    }
                }
                
                return AgentResponse(
                    response=f"Mock {self.agent_type} response",
                    concepts=[mock_concept],
                    key_points=["Mock key point"],
                    implications=["Mock implication"],
                    uncertainties=["Mock uncertainty"],
                    reasoning=["Mock reasoning step"],
                    perspective=self.agent_type,
                    confidence=0.8,
                    timestamp=datetime.now()
                )
            else:
                # Create error response with appropriate concept type
                concept_types = {
                    "belief": "belief",
                    "emotion": "emotion",
                    "desire": "goal",
                    "reflection": "pattern",
                    "research": "knowledge",
                    "task": "task",
                    "dialogue": "interaction",
                    "context": "context",
                    "parsing": "pattern",
                    "meta": "synthesis"
                }
                
                error_concept = {
                    "name": "Error",
                    "type": concept_types.get(self.agent_type, "error"),
                    "description": error_msg,
                    "related": [],
                    "validation": {
                        "confidence": 0.0,
                        "supported_by": [],
                        "contradicted_by": [],
                        "needs_verification": []
                    }
                }
                
                return AgentResponse(
                    response=error_msg,
                    concepts=[error_concept],
                    key_points=["Error occurred during processing"],
                    implications=["System may need attention"],
                    uncertainties=["Root cause needs investigation"],
                    reasoning=["Error handling activated"],
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
