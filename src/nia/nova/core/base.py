"""Nova base agent with core functionality."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...memory.types.memory_types import AgentResponse, DialogueMessage
from ...memory.prompts import AGENT_PROMPTS

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base agent with core Nova functionality."""
    
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
            
            raw_response = await self.llm.get_structured_completion(
                prompt,
                agent_type=self.agent_type,
                metadata=metadata
            )
            logger.debug(f"Raw LLM response: {raw_response}")
            
            # Handle raw string response
            if isinstance(raw_response, str):
                # Convert to structured response
                structured_response = {
                    "response": raw_response,
                    "dialogue": raw_response,
                    "concepts": [{
                        "name": f"{self.agent_type.title()} Analysis",
                        "type": self.agent_type,
                        "description": raw_response,
                        "related": [],
                        "validation": {
                            "confidence": 0.8,
                            "supported_by": ["Direct analysis"],
                            "contradicted_by": [],
                            "needs_verification": []
                        }
                    }],
                    "key_points": [f"{self.agent_type} perspective: {raw_response}"],
                    "implications": ["Analysis in progress"],
                    "uncertainties": [],
                    "reasoning": [f"{self.agent_type} analysis initiated"],
                    "metadata": {
                        "response_type": "direct_analysis",
                        "agent_type": self.agent_type,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                raw_response = AgentResponse(**structured_response)
            
            response = raw_response
            
            # Initialize response metadata
            if not response.metadata:
                response.metadata = {}
            
            # Add base metadata
            base_metadata = {
                "agent_type": self.agent_type,
                "timestamp": datetime.now().isoformat(),
                "whispers": [],
                "agent_interactions": []
            }
            
            # Add provided metadata
            if metadata:
                base_metadata.update(metadata)
            
            # Add agent perspective and metadata
            response.perspective = self.agent_type
            response.metadata.update(base_metadata)
            
            # Add dialogue context and message
            if self.current_dialogue:
                response.dialogue_context = self.current_dialogue
                
                # Add message to dialogue
                message = await self.provide_insight(
                    content=response.response,
                    references=[c["name"] for c in response.concepts]
                )
                
                # Record interaction
                if message:
                    response.metadata["agent_interactions"].append({
                        "role": "assistant",
                        "content": f"[{self.agent_type.capitalize()}] {message.content}",
                        "timestamp": message.timestamp.isoformat()
                    })
                    
                    # Add whisper
                    response.metadata["whispers"].append(
                        f"*{self.agent_type.capitalize()} agent processing: {message.content}*"
                    )
            
            # Store concepts in Neo4j
            for concept in response.concepts:
                await self.store.store_concept(
                    name=concept["name"],
                    type=concept["type"],
                    description=concept["description"],
                    related=concept.get("related", [])
                )
            
            return response
            
        except Exception as e:
            error_msg = f"Error in {self.agent_type} agent: {str(e)}"
            logger.error(error_msg)
            
            # Create error response
            error_concept = {
                "name": f"{self.agent_type.title()} Error",
                "type": "error",
                "description": str(e),
                "related": [],
                "validation": {
                    "confidence": 0.0,
                    "supported_by": ["Error handling"],
                    "contradicted_by": [],
                    "needs_verification": ["System recovery"]
                }
            }
            
            # Store error concept
            try:
                await self.store.store_concept(
                    name=error_concept["name"],
                    type=error_concept["type"],
                    description=error_concept["description"],
                    related=error_concept["related"]
                )
            except Exception as store_error:
                logger.error(f"Error storing error concept: {str(store_error)}")
            
            # Create error response
            error_response = AgentResponse(
                response=f"Error in {self.agent_type} processing: {str(e)}",
                dialogue=f"I apologize, but I encountered an error while processing your message.",
                concepts=[error_concept],
                key_points=[f"Error in {self.agent_type} agent"],
                implications=["System needs attention"],
                uncertainties=["Error cause needs investigation"],
                reasoning=["Error handling protocol activated"],
                perspective=self.agent_type,
                confidence=0.0,
                timestamp=datetime.now(),
                metadata={
                    "error": str(e),
                    "agent_type": self.agent_type,
                    "error_time": datetime.now().isoformat(),
                    "whispers": [f"*{self.agent_type.capitalize()} agent error: {str(e)}*"],
                    "agent_interactions": [{
                        "role": "assistant",
                        "content": f"[{self.agent_type.capitalize()}] Error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }]
                }
            )

            # Add error message to dialogue if available
            if self.current_dialogue:
                message = await self.send_message(
                    content=f"Error: {str(e)}",
                    message_type="error",
                    references=[error_concept["name"]]
                )
                if message:
                    error_response.dialogue_context = self.current_dialogue

            return error_response
    
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
