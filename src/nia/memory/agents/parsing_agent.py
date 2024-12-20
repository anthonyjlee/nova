"""Parsing agent for extracting structured information from text."""

import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..vector_store import VectorStore
from ..memory_types import AgentResponse
from .base import BaseAgent

logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> Optional[Dict]:
    """Extract JSON from text, handling various formats."""
    # Try direct JSON parsing first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to extract just the array portion if present
    array_match = re.search(r'\[\s*{.*}\s*\]', text, re.DOTALL)
    if array_match:
        try:
            return {"concepts": json.loads(array_match.group(0))}
        except json.JSONDecodeError:
            pass
    
    # Try to extract structured content from text
    try:
        # Look for sections
        sections = {
            "response": "",
            "concepts": [],
            "key_points": [],
            "implications": [],
            "uncertainties": [],
            "reasoning": []
        }
        
        # Extract response from text before any headers
        first_header = re.search(r'\*\*(.*?)\*\*', text)
        if first_header:
            sections["response"] = text[:first_header.start()].strip()
        else:
            sections["response"] = text.strip()
        
        # Extract concepts
        concepts_match = re.search(r'\*\*Validated Concepts\*\*\s*(.*?)(?:\*\*|$)', text, re.DOTALL)
        if concepts_match:
            concept_text = concepts_match.group(1)
            concepts = []
            for line in concept_text.split('\n'):
                if line.strip() and not line.startswith('*'):
                    name = re.sub(r'^\d+\.\s*', '', line.strip())
                    name = re.sub(r'^\*\*|\*\*$', '', name)
                    if name:
                        concepts.append({
                            "name": name,
                            "type": "pattern",
                            "description": "Extracted from text",
                            "related": []
                        })
            sections["concepts"] = concepts
        
        # Extract key points
        points_match = re.search(r'\*\*Key (?:Insights|Points)\*\*\s*(.*?)(?:\*\*|$)', text, re.DOTALL)
        if points_match:
            points = []
            for line in points_match.group(1).split('\n'):
                if line.strip() and not line.startswith('*'):
                    point = re.sub(r'^\d+\.\s*', '', line.strip())
                    point = re.sub(r'^\*\*|\*\*$', '', point)
                    if point:
                        points.append(point)
            sections["key_points"] = points
        
        # Extract implications
        impl_match = re.search(r'\*\*(?:Implications|Areas Needing (?:More )?Discussion)\*\*\s*(.*?)(?:\*\*|$)', text, re.DOTALL)
        if impl_match:
            implications = []
            for line in impl_match.group(1).split('\n'):
                if line.strip() and not line.startswith('*'):
                    impl = re.sub(r'^\d+\.\s*', '', line.strip())
                    impl = re.sub(r'^\*\*|\*\*$', '', impl)
                    if impl:
                        implications.append(impl)
            sections["implications"] = implications
        
        # Extract uncertainties from questions
        uncertainties = []
        for line in text.split('\n'):
            if '?' in line:
                uncertainty = line.strip()
                if uncertainty:
                    uncertainties.append(uncertainty)
        sections["uncertainties"] = uncertainties
        
        # Extract reasoning from synthesis section
        reason_match = re.search(r'\*\*Synthesis\*\*\s*(.*?)(?:\*\*|$)', text, re.DOTALL)
        if reason_match:
            reasoning = []
            for line in reason_match.group(1).split('\n'):
                if line.strip() and not line.startswith('*'):
                    reason = re.sub(r'^\d+\.\s*', '', line.strip())
                    reason = re.sub(r'^\*\*|\*\*$', '', reason)
                    if reason:
                        reasoning.append(reason)
            sections["reasoning"] = reasoning
        
        return sections
    except Exception as e:
        logger.error(f"Error extracting structured content: {str(e)}")
        return None

class ParsingAgent(BaseAgent):
    """Agent for parsing and structuring text."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        vector_store: VectorStore
    ):
        """Initialize parsing agent."""
        super().__init__(llm, store, vector_store, agent_type="parsing")
    
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
            structured = extract_json_from_text(text)
            
            if not structured:
                # If extraction failed, try to get structured content from LLM
                structured_text = await self.llm.get_completion(
                    self._format_prompt({'text': text})
                )
                structured = extract_json_from_text(structured_text)
            
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
