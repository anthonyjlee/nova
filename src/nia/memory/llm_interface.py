"""Interface for LLM interactions."""

import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime
from .memory_types import AgentResponse

if TYPE_CHECKING:
    from .agents.parsing_agent import ParsingAgent
    from .neo4j_store import Neo4jMemoryStore
    from .vector_store import VectorStore

logger = logging.getLogger(__name__)

class LLMInterface:
    """Interface for LLM interactions."""
    
    def __init__(self):
        """Initialize LLM interface."""
        self.parser = None  # Will be set after initialization
        
    def initialize_parser(
        self,
        store: 'Neo4jMemoryStore',
        vector_store: 'VectorStore'
    ) -> None:
        """Initialize parsing agent.
        
        This method creates a new ParsingAgent instance and sets it as the parser
        for this LLM interface. The parser is used to extract structured content
        from LLM responses.
        
        Args:
            store: Neo4j store for concept storage
            vector_store: Vector store for embeddings
        """
        from .agents.parsing_agent import ParsingAgent
        self.parser = ParsingAgent(self, store, vector_store)
        
    def set_parser(self, parser: 'ParsingAgent'):
        """Set parsing agent."""
        self.parser = parser
    
    def _get_mock_concept(self, agent_type: str) -> Dict[str, Any]:
        """Get mock concept based on agent type."""
        if agent_type == "belief":
            return {
                "name": "Knowledge Structure",
                "type": "belief",
                "description": "Understanding of knowledge organization",
                "related": ["Learning", "Memory"]
            }
        elif agent_type == "emotion":
            return {
                "name": "Emotional Response",
                "type": "emotion",
                "description": "Pattern of emotional reaction",
                "related": ["Affect", "Behavior"]
            }
        elif agent_type == "desire":
            return {
                "name": "Achievement Drive",
                "type": "goal",
                "description": "Motivation to accomplish objectives",
                "related": ["Motivation", "Success"]
            }
        elif agent_type == "reflection":
            return {
                "name": "Learning Pattern",
                "type": "pattern",
                "description": "Recurring learning behavior",
                "related": ["Growth", "Development"]
            }
        elif agent_type == "research":
            return {
                "name": "Information Source",
                "type": "source",
                "description": "Origin of knowledge",
                "related": ["Data", "Evidence"]
            }
        else:
            return {
                "name": "Generic Concept",
                "type": "pattern",
                "description": "Basic pattern or concept",
                "related": []
            }
    
    async def get_completion(self, prompt: str, agent_type: str = "default") -> str:
        """Get LLM completion.
        
        Args:
            prompt: Prompt for LLM
            agent_type: Type of agent making request
            
        Returns:
            LLM completion text
        """
        try:
            # TODO: Implement actual LLM call
            # For now return mock response
            concept = self._get_mock_concept(agent_type)
            return (
                '{\n'
                '    "response": "Mock LLM response",\n'
                '    "concepts": [\n'
                '        {\n'
                f'            "name": "{concept["name"]}",\n'
                f'            "type": "{concept["type"]}",\n'
                f'            "description": "{concept["description"]}",\n'
                f'            "related": {concept["related"]},\n'
                '            "validation": {\n'
                '                "confidence": 0.8,\n'
                '                "supported_by": [],\n'
                '                "contradicted_by": [],\n'
                '                "needs_verification": []\n'
                '            }\n'
                '        }\n'
                '    ],\n'
                '    "key_points": ["Mock key point"],\n'
                '    "implications": ["Mock implication"],\n'
                '    "uncertainties": ["Mock uncertainty"],\n'
                '    "reasoning": ["Mock reasoning step"]\n'
                '}'
            )
            
        except Exception as e:
            logger.error(f"Error getting LLM completion: {str(e)}")
            return "{}"
    
    async def get_structured_completion(
        self,
        prompt: str,
        agent_type: str = "default",
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Get structured LLM completion.
        
        Args:
            prompt: Prompt for LLM
            agent_type: Type of agent making request
            metadata: Optional metadata
            
        Returns:
            Structured agent response
        """
        try:
            # Get raw completion
            completion = await self.get_completion(prompt, agent_type)
            
            # Parse through parsing agent
            if self.parser:
                response = await self.parser.parse_text(completion)
            else:
                # Fallback if parser not set
                logger.warning("Parser not set, returning minimal response")
                response = AgentResponse(
                    response=completion,
                    concepts=[],
                    key_points=[],
                    implications=[],
                    uncertainties=[],
                    reasoning=[],
                    perspective=agent_type,
                    confidence=0.5,
                    timestamp=datetime.now()
                )
            
            # Add metadata if provided
            if metadata:
                if not response.metadata:
                    response.metadata = {}
                response.metadata.update(metadata)
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting structured completion: {str(e)}")
            return AgentResponse(
                response=f"Error getting structured completion: {str(e)}",
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective=agent_type,
                confidence=0.0,
                timestamp=datetime.now()
            )
