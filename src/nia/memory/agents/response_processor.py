"""Response processor agent for parsing and structuring LLM outputs."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import re
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..vector_store import VectorStore
from ..memory_types import AgentResponse
from .base import BaseAgent

logger = logging.getLogger(__name__)

VALIDATION_SCHEMA = {
    "supported_by": [],
    "contradicted_by": [],
    "needs_verification": []
}

class ResponseProcessor(BaseAgent):
    """Agent for processing and structuring LLM responses."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        vector_store: VectorStore
    ):
        """Initialize response processor."""
        super().__init__(llm, store, vector_store, agent_type="response_processor")
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for response processing."""
        return f"""You are a response processing agent. Extract and structure information from the given text.

Text to process:
{content.get('text', '')}

Extract and return in this exact format:
{{
    "concepts": [
        {{
            "name": "concept name",
            "type": "concept type",
            "description": "clear description",
            "related": ["related concepts"],
            "source_perspectives": ["source1", "source2"],
            "confidence": 0.0-1.0,
            "validation": {{
                "supported_by": ["support1", "support2"],
                "contradicted_by": ["contradiction1", "contradiction2"],
                "needs_verification": ["verification1", "verification2"]
            }}
        }}
    ],
    "key_points": [
        "key point 1",
        "key point 2"
    ],
    "implications": [
        "implication 1",
        "implication 2"
    ],
    "uncertainties": [
        "uncertainty 1",
        "uncertainty 2"
    ],
    "reasoning": [
        "reasoning point 1",
        "reasoning point 2"
    ]
}}

IMPORTANT: Every concept MUST have all validation fields (supported_by, contradicted_by, needs_verification).
Ensure all sections are properly formatted as JSON. Extract information exactly as presented in the text."""
    
    def _clean_json_text(self, text: str) -> str:
        """Clean JSON text to handle common formatting issues."""
        # Remove code block markers
        text = re.sub(r'```(?:json)?\s*', '', text)
        text = text.strip()
        
        # Fix common syntax errors
        text = text.replace('!', ':')  # Fix exclamation marks used as colons
        text = re.sub(r'(\w+):', r'"\1":', text)  # Add quotes around property names
        text = re.sub(r':\s*"([^"]*)"', r': "\1"', text)  # Fix quote spacing
        text = re.sub(r',\s*([}\]])', r'\1', text)  # Remove trailing commas
        text = re.sub(r'"\s*"', '", "', text)  # Fix missing commas between strings
        
        return text
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a section from the response text."""
        pattern = f'\\*\\*{section_name}\\*\\*\\s*\n+```(?:json)?([\\s\\S]*?)```'
        match = re.search(pattern, text)
        if match:
            return self._clean_json_text(match.group(1))
        return ""
    
    def _ensure_validation_schema(self, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure all concepts have the required validation fields."""
        for concept in concepts:
            if 'validation' not in concept:
                concept['validation'] = VALIDATION_SCHEMA.copy()
            else:
                # Ensure all required fields exist
                for field, default in VALIDATION_SCHEMA.items():
                    if field not in concept['validation']:
                        concept['validation'][field] = default.copy()
        return concepts
    
    async def process_response(self, text: str) -> AgentResponse:
        """Process and structure an LLM response."""
        try:
            # Extract sections
            concepts_text = self._extract_section(text, "Validated Concepts")
            if concepts_text:
                try:
                    concepts = json.loads(concepts_text)
                    if not isinstance(concepts, list):
                        concepts = [concepts]
                    concepts = self._ensure_validation_schema(concepts)
                except json.JSONDecodeError:
                    logger.error("Failed to parse concepts JSON")
                    concepts = []
            else:
                concepts = []
            
            # Extract list sections
            key_points = []
            implications = []
            uncertainties = []
            reasoning = []
            
            # Extract key points
            points_match = re.search(r'\*\*Key Insights.*?\*\*\s*\n((?:\d+\.\s*[^\n]+\n*)+)', text)
            if points_match:
                key_points = [p.strip() for p in re.findall(r'\d+\.\s*([^\n]+)', points_match.group(1))]
            
            # Extract implications
            impl_match = re.search(r'\*\*Areas Needing.*?\*\*\s*\n((?:\d+\.\s*[^\n]+\n*)+)', text)
            if impl_match:
                implications = [i.strip() for i in re.findall(r'\d+\.\s*([^\n]+)', impl_match.group(1))]
            
            # Extract reasoning
            reason_match = re.search(r'\*\*Synthesis.*?\*\*\s*\n((?:[^\n]+\n*)+)', text)
            if reason_match:
                reasoning = [r.strip() for r in reason_match.group(1).split('\n') if r.strip()]
            
            # Create response
            return AgentResponse(
                response=text,
                concepts=concepts,
                key_points=key_points,
                implications=implications,
                uncertainties=uncertainties,
                reasoning=reasoning,
                perspective="response_processor",
                confidence=0.9,
                timestamp=datetime.now()
            )
                
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return AgentResponse(
                response=text,
                concepts=[],
                perspective="response_processor",
                confidence=0.0,
                timestamp=datetime.now()
            )
