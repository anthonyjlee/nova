"""Parsing agent for extracting structured information from text."""

import logging
import json
import re
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime
from ..memory_types import AgentResponse
from .base import BaseAgent

if TYPE_CHECKING:
    from ..llm_interface import LLMInterface
    from ..neo4j_store import Neo4jMemoryStore
    from ..vector_store import VectorStore

logger = logging.getLogger(__name__)

def ensure_valid_concept(concept: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure concept has all required fields."""
    return {
        "name": concept.get("name", "Unknown"),
        "type": concept.get("type", "pattern"),
        "description": concept.get("description", "No description provided"),
        "related": concept.get("related", []),
        "validation": concept.get("validation", {
            "confidence": 0.5,
            "supported_by": [],
            "contradicted_by": [],
            "needs_verification": []
        })
    }

def extract_structured_content(text: str) -> Dict:
    """Extract structured content from text using multiple strategies."""
    # Initialize default structure
    structured = {
        "response": "",
        "concepts": [],
        "key_points": [],
        "implications": [],
        "uncertainties": [],
        "reasoning": []
    }
    
    # Try direct JSON parsing first
    try:
        # Clean up text to handle potential formatting issues
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.endswith('```'):
            text = text[:-3]
        
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            structured.update({
                k: parsed.get(k, structured[k])
                for k in structured.keys()
            })
            structured["concepts"] = [
                ensure_valid_concept(c)
                for c in parsed.get("concepts", [])
            ]
        elif isinstance(parsed, list):
            structured["concepts"] = [
                ensure_valid_concept(c)
                for c in parsed
                if isinstance(c, dict)
            ]
        return structured
    except json.JSONDecodeError:
        pass
    
    # Try to extract structured content from text
    try:
        # Extract response from text before any headers
        first_header = re.search(r'\*\*(?:Key|Concepts|Implications|Uncertainties|Reasoning)\*\*', text)
        if first_header:
            structured["response"] = text[:first_header.start()].strip()
        else:
            structured["response"] = text.strip()
        
        # Extract concepts
        concepts_match = re.search(r'\*\*(?:Validated )?Concepts\*\*\s*(.*?)(?:\*\*|$)', text, re.DOTALL)
        if concepts_match:
            concept_text = concepts_match.group(1)
            concepts = []
            current_concept = {}
            
            for line in concept_text.split('\n'):
                line = line.strip()
                if not line:
                    if current_concept:
                        concepts.append(ensure_valid_concept(current_concept))
                        current_concept = {}
                    continue
                
                if line.startswith('-') or line.startswith('*'):
                    line = line[1:].strip()
                
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'name':
                        if current_concept:
                            concepts.append(ensure_valid_concept(current_concept))
                        current_concept = {"name": value}
                    elif key in ['type', 'description']:
                        current_concept[key] = value
                    elif key == 'related':
                        current_concept['related'] = [r.strip() for r in value.split(',')]
                else:
                    # If no key, treat as name of new concept
                    if current_concept:
                        concepts.append(ensure_valid_concept(current_concept))
                    current_concept = {
                        "name": line,
                        "type": "pattern",
                        "description": "Extracted from text"
                    }
            
            if current_concept:
                concepts.append(ensure_valid_concept(current_concept))
            structured["concepts"] = concepts
        
        # Extract key points
        points_match = re.search(r'\*\*Key (?:Insights|Points)\*\*\s*(.*?)(?:\*\*|$)', text, re.DOTALL)
        if points_match:
            points = []
            for line in points_match.group(1).split('\n'):
                line = line.strip()
                if line and not line.startswith('*'):
                    # Remove bullet points, numbers, and asterisks
                    point = re.sub(r'^[-•*]\s*', '', line)
                    point = re.sub(r'^\d+\.\s*', '', point)
                    point = re.sub(r'^\*\*|\*\*$', '', point)
                    # Remove "Key insight:" prefix if present
                    point = re.sub(r'^Key (?:insight|point):\s*', '', point, flags=re.IGNORECASE)
                    if point:
                        points.append(point)
            structured["key_points"] = points
        
        # Extract implications
        impl_match = re.search(r'\*\*(?:Implications|Areas Needing (?:More )?Discussion)\*\*\s*(.*?)(?:\*\*|$)', text, re.DOTALL)
        if impl_match:
            implications = []
            for line in impl_match.group(1).split('\n'):
                line = line.strip()
                if line and not line.startswith('*'):
                    # Remove bullet points, numbers, and asterisks
                    impl = re.sub(r'^[-•*]\s*', '', line)
                    impl = re.sub(r'^\d+\.\s*', '', impl)
                    impl = re.sub(r'^\*\*|\*\*$', '', impl)
                    # Remove "Implication:" prefix if present
                    impl = re.sub(r'^Implication:\s*', '', impl, flags=re.IGNORECASE)
                    if impl:
                        implications.append(impl)
            structured["implications"] = implications
        
        # Extract uncertainties
        uncert_match = re.search(r'\*\*(?:Uncertainties|Questions|Areas of Uncertainty)\*\*\s*(.*?)(?:\*\*|$)', text, re.DOTALL)
        if uncert_match:
            uncertainties = []
            for line in uncert_match.group(1).split('\n'):
                line = line.strip()
                if line and not line.startswith('*'):
                    # Remove bullet points, numbers, and asterisks
                    uncert = re.sub(r'^[-•*]\s*', '', line)
                    uncert = re.sub(r'^\d+\.\s*', '', uncert)
                    uncert = re.sub(r'^\*\*|\*\*$', '', uncert)
                    # Remove "Uncertainty:" prefix if present
                    uncert = re.sub(r'^Uncertainty:\s*', '', uncert, flags=re.IGNORECASE)
                    if uncert:
                        uncertainties.append(uncert)
            structured["uncertainties"] = uncertainties
        # Also check for questions in the text
        elif not structured["uncertainties"]:
            uncertainties = []
            for line in text.split('\n'):
                line = line.strip()
                if '?' in line and line:
                    # Clean up the question
                    uncert = re.sub(r'^[-•*]\s*', '', line)
                    uncert = re.sub(r'^\d+\.\s*', '', uncert)
                    uncert = re.sub(r'^\*\*|\*\*$', '', uncert)
                    if uncert:
                        uncertainties.append(uncert)
            structured["uncertainties"] = uncertainties
        
        # Extract reasoning from synthesis/analysis section
        reason_match = re.search(r'\*\*(?:Synthesis|Reasoning|Analysis|Steps|Process)\*\*\s*(.*?)(?:\*\*|$)', text, re.DOTALL)
        if reason_match:
            reasoning = []
            for line in reason_match.group(1).split('\n'):
                line = line.strip()
                if line and not line.startswith('*'):
                    # Remove bullet points, numbers, and asterisks
                    reason = re.sub(r'^[-•*]\s*', '', line)
                    reason = re.sub(r'^\d+\.\s*', '', reason)
                    reason = re.sub(r'^\*\*|\*\*$', '', reason)
                    # Remove "Step:" prefix if present
                    reason = re.sub(r'^Step\s*\d*:\s*', '', reason, flags=re.IGNORECASE)
                    if reason:
                        reasoning.append(reason)
            structured["reasoning"] = reasoning
        
        return structured
    except Exception as e:
        logger.error(f"Error extracting structured content: {str(e)}")
        return structured

class ParsingAgent(BaseAgent):
    """Agent for parsing and structuring text."""
    
    def __init__(
        self,
        llm: 'LLMInterface',
        store: 'Neo4jMemoryStore',
        vector_store: 'VectorStore'
    ):
        """Initialize parsing agent."""
        super().__init__(llm, store, vector_store, "parsing")
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for parsing."""
        return f"""Parse and structure the following content into a valid JSON object.

Content to parse:
{content.get('text', '')}

Required format:
{{
    "response": "Clear analysis or summary",
    "concepts": [
        {{
            "name": "Concept name",
            "type": "pattern|insight|learning|evolution",
            "description": "Clear description",
            "related": ["Related concept names"],
            "validation": {{
                "confidence": 0.8,
                "supported_by": ["evidence"],
                "contradicted_by": [],
                "needs_verification": []
            }}
        }}
    ],
    "key_points": [
        "Key insight or observation"
    ],
    "implications": [
        "Important implication"
    ],
    "uncertainties": [
        "Area of uncertainty"
    ],
    "reasoning": [
        "Step in analysis"
    ]
}}

Guidelines:
1. Ensure all fields are present
2. Use valid concept types
3. Include validation for concepts
4. Structure lists consistently
5. Format as proper JSON

Return ONLY the JSON object, no other text."""
    
    async def parse_text(self, text: str) -> AgentResponse:
        """Parse text into structured format."""
        try:
            # Try to extract structured content
            structured = extract_structured_content(text)
            
            if not structured or not structured.get("response"):
                # If extraction failed, try to get structured content from LLM
                structured_text = await self.llm.get_completion(
                    self._format_prompt({'text': text})
                )
                structured = extract_structured_content(structured_text)
            
            if not structured:
                # If still no structure, create minimal response
                structured = {
                    "response": text,
                    "concepts": [],
                    "key_points": [],
                    "implications": [],
                    "uncertainties": [],
                    "reasoning": []
                }
            
            # Ensure response field is populated
            if not structured.get("response"):
                structured["response"] = text
            
            # Create agent response
            return AgentResponse(
                response=structured.get("response", ""),
                concepts=structured.get("concepts", []),
                key_points=structured.get("key_points", []),
                implications=structured.get("implications", []),
                uncertainties=structured.get("uncertainties", []),
                reasoning=structured.get("reasoning", []),
                perspective="parsing",
                confidence=0.9 if structured.get("concepts") else 0.5,
                timestamp=datetime.now()
            )
                
        except Exception as e:
            logger.error(f"Error parsing text: {str(e)}")
            return AgentResponse(
                response=text,
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective="parsing",
                confidence=0.0,
                timestamp=datetime.now()
            )
