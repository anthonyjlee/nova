"""Base agent class with common functionality."""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from ..memory_types import AgentResponse, DialogueContext, DialogueMessage
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..vector_store import VectorStore

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all agents."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        vector_store: VectorStore,
        agent_type: str
    ):
        """Initialize base agent."""
        self.llm = llm
        self.store = store
        self.vector_store = vector_store
        self.agent_type = agent_type
        self.current_dialogue = None
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM. Override in subclasses."""
        raise NotImplementedError
    
    async def _enrich_content(
        self,
        content: Union[str, Dict[str, Any]],
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Enrich content with additional context."""
        try:
            # Convert string content to dict if needed
            if isinstance(content, str):
                content = {'content': content}
            elif not isinstance(content, dict):
                content = {'content': str(content)}
            
            # Ensure content field exists
            if 'content' not in content:
                content['content'] = ''
            
            # Get similar memories if content exists
            if content['content']:
                similar = await self.vector_store.search_vectors(
                    content=content['content'],
                    limit=5
                )
                content['similar_memories'] = similar
            
            # Get relevant concepts
            concepts = await self.store.get_concepts_by_type(self.agent_type)
            content['relevant_concepts'] = concepts
            
            # Add metadata
            if metadata:
                content['metadata'] = metadata
            
            return content
            
        except Exception as e:
            logger.error(f"Error enriching content: {str(e)}")
            return {'content': str(content)}
    
    async def _process_llm_response(
        self,
        llm_response: Any,
        content: Dict[str, Any]
    ) -> AgentResponse:
        """Process LLM response."""
        try:
            # Parse response using parser if available
            if self.llm.parser:
                parsed = await self.llm.parser.parse_text(str(llm_response))
                
                # Add agent-specific metadata
                parsed.perspective = self.agent_type
                if content.get('metadata'):
                    parsed.metadata.update(content['metadata'])
                
                # Add relevant concepts from memory
                if content.get('relevant_concepts'):
                    for concept in content['relevant_concepts']:
                        if concept not in parsed.concepts:
                            parsed.concepts.append(concept)
                
                return parsed
            
            # Fallback if parser not initialized
            return AgentResponse(
                response=str(llm_response),
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective=self.agent_type,
                confidence=0.5,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in {self.agent_type} agent: {str(e)}")
            return AgentResponse(
                response=f"Error in {self.agent_type} agent",
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective=self.agent_type,
                confidence=0.0,
                timestamp=datetime.now()
            )
    
    async def process(
        self,
        content: Union[str, Dict[str, Any]],
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process content through agent."""
        try:
            # Enrich content
            enriched = await self._enrich_content(content, metadata)
            
            # Get LLM completion
            prompt = self._format_prompt(enriched)
            response = await self.llm.get_completion(prompt)
            
            # Process response
            return await self._process_llm_response(response, enriched)
            
        except Exception as e:
            logger.error(f"Error in {self.agent_type} agent: {str(e)}")
            return AgentResponse(
                response=f"Error in {self.agent_type} agent",
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective=self.agent_type,
                confidence=0.0,
                timestamp=datetime.now()
            )
    
    async def process_interaction(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process raw interaction text."""
        return await self.process(
            {'content': content},
            metadata
        )
    
    async def send_message(
        self,
        content: str,
        message_type: str = "message",
        references: Optional[List[str]] = None
    ) -> DialogueMessage:
        """Send message to current dialogue."""
        if not self.current_dialogue:
            raise ValueError("No active dialogue")
            
        message = DialogueMessage(
            content=content,
            agent_type=self.agent_type,
            message_type=message_type,
            references=references or [],
            timestamp=datetime.now()
        )
        
        self.current_dialogue.add_message(message)
        return message
    
    async def provide_insight(
        self,
        content: str,
        references: Optional[List[str]] = None
    ) -> DialogueMessage:
        """Provide insight to current dialogue."""
        return await self.send_message(
            content=content,
            message_type="insight",
            references=references
        )
    
    async def ask_question(
        self,
        content: str,
        references: Optional[List[str]] = None
    ) -> DialogueMessage:
        """Ask question in current dialogue."""
        return await self.send_message(
            content=content,
            message_type="question",
            references=references
        )
    
    async def provide_answer(
        self,
        content: str,
        references: Optional[List[str]] = None
    ) -> DialogueMessage:
        """Provide answer in current dialogue."""
        return await self.send_message(
            content=content,
            message_type="answer",
            references=references
        )
