"""Base agent class with common functionality."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..memory.types.memory_types import AgentResponse, DialogueMessage
from ..config.agent_config import get_agent_prompt, validate_agent_config

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
        self.emotions = {}
        self.desires = {}
        self.occupation = "agent"
        self.domains = ["professional", "personal"]  # Default domain access
        self.capabilities = {
            "memory": True,
            "learning": True,
            "reflection": True,
            "domain_access": self.domains
        }
        
        # Validate configuration
        config = {
            "name": "base",
            "agent_type": agent_type,
            "domain": "professional"
        }
        validate_agent_config(agent_type, config)
        
        # Get prompt template
        self.prompt_template = get_agent_prompt(agent_type)
        
    @property
    def memory_system(self):
        """Access to the memory system components."""
        return {
            'semantic': self.store,
            'episodic': self.vector_store
        }
        
    def get_attributes(self):
        """Get agent attributes."""
        return {
            'type': self.agent_type,
            'emotions': self.emotions,
            'desires': self.desires,
            'occupation': self.occupation,
            'capabilities': self.capabilities
        }
        
    async def learn_concept(self, name: str = None, type: str = None, description: str = None, 
                          related: List[str] = None, concept: Dict[str, Any] = None):
        """Learn a new concept.
        
        Args:
            name: Concept name
            type: Concept type
            description: Concept description
            related: Related concept names
            concept: Full concept dictionary (alternative to individual params)
        """
        if concept:
            name = concept.get("name")
            type = concept.get("type")
            description = concept.get("description")
            related = concept.get("related", [])
            
        await self.store.store_concept(
            name=name,
            type=type,
            description=description,
            related=related or []
        )
        
    async def store_memory(self, content: str, metadata: Optional[Dict] = None,
                         importance: float = None, domain: str = None,
                         context: Optional[Dict] = None):
        """Store a memory.
        
        Args:
            content: Memory content
            metadata: Optional metadata
            importance: Memory importance score
            domain: Memory domain
        """
        if metadata is None:
            metadata = {}
            
        metadata.update({
            'agent_type': self.agent_type,
            'timestamp': datetime.now().isoformat(),
            'importance': importance,
            'domain': domain or 'professional',
            'context': context
        })
        
        # Store in both memory systems
        await self.vector_store.store(content, metadata)
        await self.store.store_memory(content, metadata)
    
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
            if not hasattr(response, 'metadata') or not response.metadata:
                response.metadata = {}
            
            # Add base metadata
            base_metadata = {
                "agent_type": self.agent_type,
                "timestamp": datetime.now().isoformat(),
                "whispers": [],
                "agent_interactions": [],
                "domain": metadata.get("domain", "professional") if metadata else "professional"
            }
            
            # Add provided metadata
            if metadata:
                base_metadata.update(metadata)
            
            # Add agent perspective and metadata
            response.perspective = self.agent_type
            response.metadata = base_metadata
            
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
                        "supported_by": ["Working agent responses"],
                        "contradicted_by": [],
                        "needs_verification": ["Critical uncertainties"]
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
                    "name": f"{self.agent_type.title()} Error",
                    "type": concept_types.get(self.agent_type, "error"),
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
                
                # Check if error is due to LMStudio not running
                if "LMStudio is not running" in str(e):
                    return AgentResponse(
                        response="LMStudio is not running. Please start LMStudio and try again.",
                        dialogue="I need LMStudio to be running to process your message. Please start LMStudio and try again.",
                        concepts=[{
                            "name": "LMStudio Required",
                            "type": "system",
                            "description": "LMStudio must be running for message processing",
                            "related": [],
                            "validation": {
                                "confidence": 1.0,
                                "supported_by": ["System check"],
                                "contradicted_by": [],
                                "needs_verification": ["LMStudio status"]
                            }
                        }],
                        key_points=["LMStudio is required but not running"],
                        implications=["Cannot process messages until LMStudio is started"],
                        uncertainties=[],
                        reasoning=["System dependency check failed"],
                        perspective="system",
                        confidence=1.0,
                        timestamp=datetime.now(),
                        metadata={
                            "error_type": "dependency",
                            "dependency": "LMStudio",
                            "status": "not_running",
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                
                # Create error response for other errors
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
