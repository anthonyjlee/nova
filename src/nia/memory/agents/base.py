"""Base agent implementation with collaborative dialogue support."""

import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import json
from ..interfaces import LLMInterfaceBase
from ..neo4j_store import Neo4jMemoryStore
from ..vector_store import VectorStore
from ..memory_types import (
    AgentResponse,
    DialogueMessage,
    DialogueContext
)

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base agent class with collaborative dialogue support."""
    
    def __init__(
        self,
        llm: LLMInterfaceBase,
        store: Neo4jMemoryStore,
        vector_store: VectorStore,
        agent_type: str = "base"
    ):
        """Initialize agent."""
        self.llm = llm
        self.store = store  # Neo4j for concepts only
        self.vector_store = vector_store  # Qdrant for memories
        self.agent_type = agent_type
        self.current_dialogue: Optional[DialogueContext] = None
    
    async def process(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process content through agent lens."""
        try:
            # Get dialogue context if available
            dialogue = content.get('dialogue_context')
            if dialogue:
                self.current_dialogue = dialogue
            
            # Get similar memories for context
            similar_memories = await self.vector_store.search_vectors(
                content=json.dumps(content),  # Convert to string for vector search
                limit=5
            )
            
            # Enrich content with context
            enriched_content = await self._enrich_content(content, similar_memories)
            
            # Get LLM response
            llm_response = await self.llm.get_structured_completion(
                self._format_prompt(enriched_content)
            )
            
            # Process response through agent lens
            response = await self._process_llm_response(llm_response, enriched_content)
            
            # Add to dialogue if active
            if self.current_dialogue:
                message = DialogueMessage(
                    agent_type=self.agent_type,
                    content=response.response,
                    message_type="response",
                    references=[c["name"] for c in response.concepts],
                    metadata={
                        "confidence": response.confidence,
                        "key_points": response.key_points
                    }
                )
                self.current_dialogue.add_message(message)
                response.dialogue_context = self.current_dialogue
            
            # Store processed memory
            await self.vector_store.store_vector(
                content=json.dumps({
                    'original_content': content,
                    'enriched_content': enriched_content,
                    'agent_response': response.dict(),
                    'agent_type': self.agent_type,
                    'timestamp': datetime.now().isoformat()
                }),
                metadata=metadata,
                layer="semantic"
            )
            
            # Store validated concepts
            await self._store_validated_concepts(response.concepts)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in {self.agent_type} agent: {str(e)}")
            return AgentResponse(
                response=f"Error processing from {self.agent_type} perspective: {str(e)}",
                concepts=[],
                perspective=self.agent_type,
                confidence=0.0
            )
    
    async def send_message(
        self,
        content: str,
        message_type: str = "message",
        references: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> DialogueMessage:
        """Send a message to the current dialogue."""
        if not self.current_dialogue:
            raise ValueError("No active dialogue context")
            
        message = DialogueMessage(
            agent_type=self.agent_type,
            content=content,
            message_type=message_type,
            references=references or [],
            metadata=metadata or {}
        )
        
        self.current_dialogue.add_message(message)
        return message
    
    async def ask_question(
        self,
        question: str,
        references: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> DialogueMessage:
        """Ask a question in the current dialogue."""
        return await self.send_message(
            content=question,
            message_type="question",
            references=references,
            metadata=metadata
        )
    
    async def provide_insight(
        self,
        insight: str,
        references: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> DialogueMessage:
        """Share an insight in the current dialogue."""
        return await self.send_message(
            content=insight,
            message_type="insight",
            references=references,
            metadata=metadata
        )
    
    async def _enrich_content(
        self,
        content: Dict[str, Any],
        similar_memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Enrich content with context using LLM."""
        try:
            # Format prompt for context analysis
            context_prompt = f"""Analyze this content and context:
            
            Content: {json.dumps(content)}
            Similar Memories: {json.dumps(similar_memories)}
            
            Provide analysis in this exact format:
            {{
                "concepts": [
                    {{
                        "name": "Concept name",
                        "type": "concept type",
                        "description": "Clear description",
                        "related": ["Related concept names"]
                    }}
                ],
                "relationships": [
                    {{
                        "from": "Concept name",
                        "to": "Related concept name",
                        "type": "relationship type",
                        "description": "Clear description"
                    }}
                ],
                "context_elements": [
                    {{
                        "type": "element type",
                        "content": "element content",
                        "importance": "high|medium|low"
                    }}
                ],
                "implications": [
                    {{
                        "type": "implication type",
                        "description": "Clear description",
                        "confidence": 0.0 to 1.0
                    }}
                ]
            }}"""
            
            # Get context analysis through parsing agent
            analysis = await self.llm.parser.parse_text(
                await self.llm.get_completion(context_prompt)
            )
            
            # Return enriched content
            return {
                **content,
                "similar_memories": similar_memories,
                "context_analysis": analysis.dict()
            }
                
        except Exception as e:
            logger.error(f"Error enriching content: {str(e)}")
            return {
                **content,
                "similar_memories": similar_memories
            }
    
    async def _process_llm_response(
        self,
        llm_response: Any,
        content: Dict[str, Any]
    ) -> AgentResponse:
        """Process LLM response into agent response."""
        # This can be overridden by specific agents
        return AgentResponse(
            response=llm_response.response,
            concepts=llm_response.concepts,
            key_points=llm_response.key_points,
            implications=llm_response.implications,
            uncertainties=llm_response.uncertainties,
            reasoning=llm_response.reasoning,
            dialogue_context=self.current_dialogue,
            perspective=self.agent_type,
            confidence=0.5,  # Default confidence
            timestamp=datetime.now()
        )
    
    async def _store_validated_concepts(
        self,
        concepts: List[Dict[str, Any]]
    ):
        """Store validated concepts in knowledge graph."""
        try:
            for concept in concepts:
                # Store concept
                await self.store.store_concept(
                    name=concept["name"],
                    type=concept["type"],
                    description=concept["description"]
                )
                
                # Store relationships
                for related in concept.get("related", []):
                    await self.store.store_concept_relationship(
                        concept["name"],
                        related,
                        "RELATED_TO"
                    )
                    
        except Exception as e:
            logger.error(f"Error storing concepts: {str(e)}")
    
    @abstractmethod
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM.
        
        This should be implemented by each agent to provide their unique perspective.
        The prompt should guide the LLM to:
        1. Analyze the content through the agent's specialized lens
        2. Extract relevant concepts in the specified format
        3. Provide structured analysis (key points, implications, etc.)
        4. Consider dialogue context if available
        5. Maintain clean separation between memories and concepts
        """
        pass
