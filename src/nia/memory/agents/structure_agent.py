"""Structure agent for handling complex data structures."""

import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime
from ..memory_types import AgentResponse
from .base import BaseAgent

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
        return f"""Analyze and structure the following content into a well-organized format.
        Pay special attention to hierarchical relationships, data types, and validation rules.

Content to analyze:
{content.get('content', '')}

Required format:
{{
    "response": "Structure analysis",
    "concepts": [
        {{
            "name": "Structure name",
            "type": "data_type|relationship|constraint",
            "description": "Clear description of the structure",
            "related": ["Related structures"],
            "validation": {{
                "confidence": 0.8,
                "supported_by": ["evidence"],
                "contradicted_by": [],
                "needs_verification": []
            }},
            "schema": {{
                "type": "data type",
                "required": ["required fields"],
                "optional": ["optional fields"],
                "constraints": ["validation rules"],
                "relationships": [
                    {{
                        "from": "source",
                        "to": "target",
                        "type": "relationship type",
                        "cardinality": "one-to-many"
                    }}
                ]
            }}
        }}
    ],
    "key_points": [
        "Key structural insight"
    ],
    "implications": [
        "Structure implication"
    ],
    "uncertainties": [
        "Structure uncertainty"
    ],
    "reasoning": [
        "Structure analysis step"
    ],
    "validation_rules": [
        {{
            "field": "field name",
            "type": "validation type",
            "rule": "validation rule",
            "severity": "error|warning|info"
        }}
    ]
}}

Guidelines:
1. Identify data types and structures
2. Define validation rules
3. Map relationships
4. Document constraints
5. Note edge cases

Return ONLY the JSON object, no other text."""
    
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
                validation_prompt = f"""Validate this structure against the schema:

Structure:
{response.response}

Schema:
{expected_schema}

Provide validation results in this format:
{{
    "is_valid": true/false,
    "errors": [
        {{
            "field": "field name",
            "error": "error description",
            "severity": "error|warning|info"
        }}
    ],
    "suggestions": [
        "Improvement suggestion"
    ]
}}

Return ONLY the JSON object, no other text."""

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
            validation_prompt = f"""Validate this schema definition:

Schema:
{schema}

Check for:
1. Required fields
2. Data type consistency
3. Relationship validity
4. Constraint completeness
5. Edge cases

Provide validation in this format:
{{
    "is_valid": true/false,
    "errors": [
        {{
            "field": "field path",
            "error": "error description",
            "severity": "error|warning|info"
        }}
    ],
    "suggestions": [
        "Schema improvement suggestion"
    ],
    "missing": [
        "Missing required element"
    ]
}}

Return ONLY the JSON object, no other text."""

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
            schema_prompt = f"""Extract a schema definition from this description:

Description:
{text}

Generate a schema in this format:
{{
    "type": "schema type",
    "fields": [
        {{
            "name": "field name",
            "type": "data type",
            "required": true/false,
            "description": "field description",
            "constraints": [
                {{
                    "type": "constraint type",
                    "rule": "constraint rule"
                }}
            ]
        }}
    ],
    "relationships": [
        {{
            "from": "source field",
            "to": "target field",
            "type": "relationship type",
            "cardinality": "one-to-many"
        }}
    ],
    "validation": [
        {{
            "rule": "validation rule",
            "severity": "error|warning|info"
        }}
    ]
}}

Return ONLY the JSON object, no other text."""

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
