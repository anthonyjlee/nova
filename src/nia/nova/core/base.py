"""Nova base agent with core functionality."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from nia.core.types import DialogueMessage, DomainContext
from ..core.agent_types import AgentResponse
from ...core.interfaces.prompts import AGENT_PROMPTS
from ...memory.chunking import chunk_content

logger = logging.getLogger(__name__)

class NovaAgent:
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
    
    def _combine_responses(self, responses: List[Dict]) -> AgentResponse:
        """Combine multiple chunk responses into single response.
        
        Args:
            responses: List of chunk responses
            
        Returns:
            Combined response
        """
        if not responses:
            return AgentResponse(
                response="",
                agent_id=self.agent_type,
                status="success",
                message="No responses to combine"
            )
            
        # Combine concepts
        all_concepts = []
        seen_concepts = set()
        for response in responses:
            for concept in response.get("concepts", []):
                concept_key = (concept["name"], concept["type"])
                if concept_key not in seen_concepts:
                    all_concepts.append(concept)
                    seen_concepts.add(concept_key)
                    
        # Combine key points
        all_points = []
        seen_points = set()
        for response in responses:
            for point in response.get("key_points", []):
                if point not in seen_points:
                    all_points.append(point)
                    seen_points.add(point)
                    
        # Combine implications and uncertainties
        all_implications = []
        all_uncertainties = []
        seen_implications = set()
        seen_uncertainties = set()
        
        for response in responses:
            for imp in response.get("implications", []):
                if imp not in seen_implications:
                    all_implications.append(imp)
                    seen_implications.add(imp)
                    
            for unc in response.get("uncertainties", []):
                if unc not in seen_uncertainties:
                    all_uncertainties.append(unc)
                    seen_uncertainties.add(unc)
                    
        # Combine reasoning steps
        all_reasoning = []
        for response in responses:
            reasoning = response.get("reasoning", [])
            if isinstance(reasoning, list):
                all_reasoning.extend(reasoning)
            else:
                all_reasoning.append(str(reasoning))
            
        # Create combined response
        return AgentResponse(
            response="\n\n".join(r.get("response", "") for r in responses),
            concepts=all_concepts,
            key_points=all_points,
            implications=all_implications,
            uncertainties=all_uncertainties,
            reasoning="\n".join(all_reasoning),
            metadata=responses[0].get("metadata", {}) if responses else {},
            agent_id=self.agent_type,
            status="success",
            message="Combined response"
        )
    
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
            # Split content into chunks with validation logging
            logger.debug(f"Chunking content: {content}")
            chunks = chunk_content(content)
            logger.debug(f"Created {len(chunks)} chunks")
            chunk_responses = []
            
            # Process each chunk with validation
            for i, chunk in enumerate(chunks):
                # Format prompt for chunk
                prompt = self._format_prompt(chunk)
                logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
                logger.debug(f"Chunk content: {chunk}")
                logger.debug(f"Formatted prompt: {prompt}")
                
                try:
                    # Get structured completion for chunk
                    chunk_response = await self.llm.get_structured_completion(
                        prompt,
                        agent_type=self.agent_type,
                        metadata=metadata
                    )
                    logger.debug(f"Chunk {i+1} response: {chunk_response}")
                    
                    # Validate response structure
                    if not isinstance(chunk_response, (dict, str)):
                        raise ValueError(f"Invalid response type: {type(chunk_response)}")
                    
                    # Add chunk metadata
                    if isinstance(chunk_response, dict):
                        chunk_response["chunk_metadata"] = {
                            "index": i,
                            "total_chunks": len(chunks),
                            "chunk_size": len(str(chunk))
                        }
                    
                    chunk_responses.append(chunk_response)
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {i+1}: {str(e)}")
                    logger.error(f"Chunk content: {chunk}")
                    logger.error(f"Formatted prompt: {prompt}")
                    raise
            
            # Combine chunk responses with validation
            logger.debug("Combining chunk responses")
            response = self._combine_responses(chunk_responses)
            logger.debug(f"Combined response: {response}")
            
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
            
            # Update response metadata
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
                reasoning="Error handling protocol activated",
                perspective=self.agent_type,
                confidence=0.0,
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
                },
                agent_id=self.agent_type,
                status="error",
                message=str(e)
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
    ) -> Optional[DialogueMessage]:
        """Provide insight into current dialogue.
        
        Args:
            content: Insight content
            references: Optional list of referenced concepts/messages
            
        Returns:
            New dialogue message or None if no dialogue
        """
        if not self.current_dialogue:
            logger.warning("No active dialogue for insight")
            return None
            
        message = DialogueMessage(
            content=content,
            message_type="insight",
            agent_type=self.agent_type,
            references=references or [],
            timestamp=datetime.now(),
            sender=self.agent_type
        )
        
        self.current_dialogue.add_message(message)
        return message
    
    async def send_message(
        self,
        content: str,
        message_type: str,
        references: Optional[List[str]] = None
    ) -> Optional[DialogueMessage]:
        """Send message to current dialogue.
        
        Args:
            content: Message content
            message_type: Type of message
            references: Optional list of referenced concepts/messages
            
        Returns:
            New dialogue message or None if no dialogue
        """
        if not self.current_dialogue:
            logger.warning("No active dialogue for message")
            return None
            
        message = DialogueMessage(
            content=content,
            message_type=message_type,
            agent_type=self.agent_type,
            references=references or [],
            timestamp=datetime.now(),
            sender=self.agent_type
        )
        
        self.current_dialogue.add_message(message)
        return message
