"""Structure agent for handling complex data structures."""

import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime
from ...memory.types.memory_types import AgentResponse
from .base import BaseAgent
from ...memory.prompts import AGENT_PROMPTS

if TYPE_CHECKING:
    from ..llm_interface import LLMInterface
    from ..neo4j_store import Neo4jMemoryStore
    from ..vector_store import VectorStore

logger = logging.getLogger(__name__)

class StructureAgent(BaseAgent):
    """Agent for handling complex data structures."""
    
    def __init__(
        self,
        llm: 'LLMInterface',
        store: 'Neo4jMemoryStore',
        vector_store: 'VectorStore'
    ):
        """Initialize structure agent."""
        super().__init__(llm, store, vector_store, "structure")
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for structure analysis."""
        text = content.get('content', '')
        return AGENT_PROMPTS["structure"].format(content=text)
    
    async def analyze_structure(
        self,
        text: str,
        expected_schema: Optional[Dict] = None
    ) -> AgentResponse:
        """Analyze text structure against optional schema."""
        try:
            # Add schema to content if provided
            content = {
                'content': text,
                'schema': expected_schema
            } if expected_schema else {'content': text}
            
            # Get structure analysis
            response = await self.process(content)
            
            # Add schema validation if provided
            if expected_schema and isinstance(response, AgentResponse):
                validation_prompt = AGENT_PROMPTS["structure_validation"].format(
                    structure=response.response,
                    schema=expected_schema
                )

                # Get validation results
                validation = await self.llm.get_completion(validation_prompt)
                
                # Add validation to metadata
                if not response.metadata:
                    response.metadata = {}
                response.metadata['validation'] = validation
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing structure: {str(e)}")
            return AgentResponse(
                response=f"Error analyzing structure: {str(e)}",
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective="structure",
                confidence=0.0,
                timestamp=datetime.now()
            )
    
    async def validate_schema(
        self,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate schema definition."""
        try:
            validation_prompt = AGENT_PROMPTS["schema_validation"].format(schema=schema)

            # Get validation results
            validation = await self.llm.get_completion(validation_prompt)
            
            return validation if isinstance(validation, dict) else {
                "is_valid": False,
                "errors": [{
                    "field": "schema",
                    "error": "Invalid validation result",
                    "severity": "error"
                }],
                "suggestions": [],
                "missing": []
            }
            
        except Exception as e:
            logger.error(f"Error validating schema: {str(e)}")
            return {
                "is_valid": False,
                "errors": [{
                    "field": "schema",
                    "error": str(e),
                    "severity": "error"
                }],
                "suggestions": [],
                "missing": []
            }
    
    async def extract_schema(
        self,
        text: str
    ) -> Dict[str, Any]:
        """Extract schema from text description."""
        try:
            schema_prompt = AGENT_PROMPTS["schema_extraction"].format(text=text)

            # Get schema definition
            schema = await self.llm.get_completion(schema_prompt)
            
            # Validate extracted schema
            validation = await self.validate_schema(schema)
            
            # Return schema with validation
            return {
                "schema": schema,
                "validation": validation
            }
            
        except Exception as e:
            logger.error(f"Error extracting schema: {str(e)}")
            return {
                "schema": {},
                "validation": {
                    "is_valid": False,
                    "errors": [{
                        "field": "schema",
                        "error": str(e),
                        "severity": "error"
                    }],
                    "suggestions": [],
                    "missing": []
                }
            }
