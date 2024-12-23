"""Parsing agent for extracting structured information from text."""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Union, TYPE_CHECKING
from datetime import datetime
from ..memory_types import AgentResponse
from .base import BaseAgent

if TYPE_CHECKING:
    from ..llm_interface import LLMInterface
    from ..neo4j_store import Neo4jMemoryStore
    from ..vector_store import VectorStore
    from .structure_agent import StructureAgent

logger = logging.getLogger(__name__)

def _clean_json_text(text: str) -> str:
    """Clean JSON text to handle common formatting issues."""
    try:
        if not text or not isinstance(text, str):
            logger.warning("Invalid text input for cleaning")
            return "{}"
            
        # Remove code block markers
        text = re.sub(r'```(?:json)?\s*', '', text)
        text = text.strip()
        
        # Handle empty or invalid text
        if not text or text == "null":
            logger.warning("Empty text after cleaning")
            return "{}"
        
        # Fix common syntax errors
        replacements = [
            (r'!', ':'),  # Fix exclamation marks used as colons
            (r'(\w+):', r'"\1":'),  # Add quotes around property names
            (r':\s*"([^"]*)"', r': "\1"'),  # Fix quote spacing
            (r',\s*([}\]])', r'\1'),  # Remove trailing commas
            (r'"\s*"', '", "'),  # Fix missing commas between strings
            (r'([{,]\s*)(\w+):', r'\1"\2":'),  # Fix unquoted keys
            (r'([{,]\s*)([^"\s]+):', r'\1"\2":'),  # Fix any remaining unquoted keys
            (r'None', '"None"'),  # Quote None values
            (r'True', 'true'),  # Fix boolean values
            (r'False', 'false'),
            (r'null', '"null"'),  # Quote null values
            (r',\s*,', ','),  # Remove duplicate commas
            (r'\[\s*,', '['),  # Fix leading commas in arrays
            (r',\s*\]', ']'),  # Fix trailing commas in arrays
        ]
        
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
        
        # Ensure proper JSON structure
        if not text.startswith('{'):
            text = '{' + text
        if not text.endswith('}'):
            text = text + '}'
            
        return text
        
    except Exception as e:
        logger.error(f"Error cleaning JSON text: {str(e)}")
        return "{}"

def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON object from text."""
    try:
        if not text or not isinstance(text, str):
            logger.warning("Invalid text input for JSON extraction")
            return None
            
        # Try direct JSON parsing first
        try:
            # Remove any leading/trailing quotes and escape characters
            text = text.strip().strip("'").strip('"')
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
        # Clean up text
        text = _clean_json_text(text)
        
        # Try multiple parsing strategies
        strategies = [
            # Strategy 1: Direct JSON parsing after cleaning
            lambda t: json.loads(t),
            
            # Strategy 2: Extract JSON object using regex
            lambda t: json.loads(re.search(r'({[^}]+})', t).group(1)) if re.search(r'({[^}]+})', t) else None,
            
            # Strategy 3: Fix and parse JSON with missing quotes
            lambda t: json.loads(re.sub(r':\s*([^"{}\[\],\s][^,}]*?)(?=[,}])', r': "\1"', t)),
            
            # Strategy 4: Extract and parse individual fields
            lambda t: {
                "response": re.search(r'"response":\s*"([^"]+)"', t).group(1) if re.search(r'"response":\s*"([^"]+)"', t) else "",
                "concepts": [],
                "key_points": [],
                "implications": [],
                "uncertainties": [],
                "reasoning": []
            }
        ]
        
        # Try each strategy
        for strategy in strategies:
            try:
                result = strategy(text)
                if result:
                    return result
            except Exception:
                continue
        
        logger.warning("All JSON extraction strategies failed")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting JSON: {str(e)}")
        return None

def _ensure_valid_concept(concept: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure concept has all required fields with valid values."""
    try:
        if not isinstance(concept, dict):
            logger.warning("Invalid concept format")
            return {
                "name": "Unknown",
                "type": "pattern",
                "description": "Invalid concept format",
                "related": [],
                "validation": {
                    "confidence": 0.5,
                    "supported_by": [],
                    "contradicted_by": [],
                    "needs_verification": []
                }
            }
        
        # Ensure required fields with valid values
        validated = {
            "name": str(concept.get("name", "Unknown")),
            "type": str(concept.get("type", "pattern")),
            "description": str(concept.get("description", "No description provided")),
            "related": list(concept.get("related", [])),
            "validation": {
                "confidence": float(concept.get("validation", {}).get("confidence", 0.5)),
                "supported_by": list(concept.get("validation", {}).get("supported_by", [])),
                "contradicted_by": list(concept.get("validation", {}).get("contradicted_by", [])),
                "needs_verification": list(concept.get("validation", {}).get("needs_verification", []))
            }
        }
        
        # Validate confidence range
        validated["validation"]["confidence"] = max(0.0, min(1.0, validated["validation"]["confidence"]))
        
        return validated
        
    except Exception as e:
        logger.error(f"Error validating concept: {str(e)}")
        return {
            "name": "Error",
            "type": "error",
            "description": f"Error validating concept: {str(e)}",
            "related": [],
            "validation": {
                "confidence": 0.0,
                "supported_by": [],
                "contradicted_by": [],
                "needs_verification": []
            }
        }

def _extract_structured_content(text: str) -> Dict[str, Any]:
    """Extract structured content from text using multiple strategies."""
    try:
        if not text or not isinstance(text, str):
            logger.warning("Invalid text input for content extraction")
            return {
                "response": "",
                "concepts": [],
                "key_points": [],
                "implications": [],
                "uncertainties": [],
                "reasoning": []
            }
        
        # Initialize default structure
        structured = {
            "response": "",
            "concepts": [],
            "key_points": [],
            "implications": [],
            "uncertainties": [],
            "reasoning": []
        }
        
        # Try JSON extraction first
        json_content = _extract_json_from_text(text)
        if json_content:
            # Update with extracted content
            for key in structured.keys():
                if key in json_content:
                    structured[key] = json_content[key]
            
            # Validate concepts
            structured["concepts"] = [
                _ensure_valid_concept(c)
                for c in json_content.get("concepts", [])
                if isinstance(c, dict)
            ]
            
            return structured
        
        # Extract content using patterns
        try:
            # Extract response (everything before first section)
            first_section = re.search(r'\n(?:Key points|Concepts|Implications|Uncertainties|Reasoning):', text)
            if first_section:
                structured["response"] = text[:first_section.start()].strip()
            else:
                structured["response"] = text.strip()
            
            # Extract sections
            sections = {
                "key_points": r'Key points?:?\s*(.*?)(?:\n\s*(?:[A-Z][\w\s]*:|$)|$)',
                "implications": r'Implications:?\s*(.*?)(?:\n\s*(?:[A-Z][\w\s]*:|$)|$)',
                "uncertainties": r'Uncertainties:?\s*(.*?)(?:\n\s*(?:[A-Z][\w\s]*:|$)|$)',
                "reasoning": r'Reasoning:?\s*(.*?)(?:\n\s*(?:[A-Z][\w\s]*:|$)|$)'
            }
            
            for section, pattern in sections.items():
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    items = []
                    for line in match.group(1).split('\n'):
                        line = line.strip()
                        if line:
                            # Clean up line
                            item = re.sub(r'^[-•*]\s*', '', line)  # Remove bullets
                            item = re.sub(r'^\d+\.\s*', '', item)  # Remove numbers
                            item = re.sub(r'^["\']|["\']$', '', item)  # Remove quotes
                            if item:
                                items.append(item)
                    structured[section] = items
            
            # Extract concepts
            concepts_match = re.search(r'(?:Concepts?|Extracted Concepts?):?\s*(.*?)(?:\n\s*(?:[A-Z][\w\s]*:|$)|$)', text, re.DOTALL | re.IGNORECASE)
            if concepts_match:
                concepts = []
                current_concept = {}
                
                for line in concepts_match.group(1).split('\n'):
                    line = line.strip()
                    if not line:
                        if current_concept:
                            concepts.append(_ensure_valid_concept(current_concept))
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
                                concepts.append(_ensure_valid_concept(current_concept))
                            current_concept = {"name": value}
                        elif key in ['type', 'description']:
                            current_concept[key] = value
                        elif key == 'related':
                            current_concept['related'] = [r.strip() for r in value.split(',')]
                    else:
                        # If no key, treat as name of new concept
                        if current_concept:
                            concepts.append(_ensure_valid_concept(current_concept))
                        current_concept = {
                            "name": line,
                            "type": "pattern",
                            "description": "Extracted from text"
                        }
                
                if current_concept:
                    concepts.append(_ensure_valid_concept(current_concept))
                structured["concepts"] = concepts
            
            return structured
            
        except Exception as e:
            logger.error(f"Error extracting content using patterns: {str(e)}")
            return structured
            
    except Exception as e:
        logger.error(f"Error extracting structured content: {str(e)}")
        return {
            "response": text if isinstance(text, str) else "",
            "concepts": [],
            "key_points": [],
            "implications": [],
            "uncertainties": [],
            "reasoning": []
        }

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
        self.structure_agent = None  # Will be set after initialization
    
    def set_structure_agent(self, agent: 'StructureAgent'):
        """Set structure agent for complex parsing."""
        self.structure_agent = agent
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for parsing."""
        return f"""Parse and structure the following content into a valid JSON object.

Content to parse:
{content.get('content', '')}

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
        """Parse text into structured format.
        
        This is the main public method for parsing text. It uses multiple strategies
        including direct parsing, pattern matching, and LLM-based parsing to extract
        structured content from text.
        
        Args:
            text: Text to parse
            
        Returns:
            AgentResponse containing structured content
        """
        try:
            if not text or not isinstance(text, str):
                logger.warning("Invalid text input for parsing")
                return AgentResponse(
                    response="",
                    concepts=[],
                    key_points=[],
                    implications=[],
                    uncertainties=[],
                    reasoning=[],
                    perspective="parsing",
                    confidence=0.0,
                    timestamp=datetime.now()
                )
            
            # Try to parse as JSON first
            try:
                # Remove any leading/trailing quotes and escape characters
                text = text.strip().strip("'").strip('"').strip()
                
                # Try direct JSON parsing
                try:
                    logger.debug(f"Attempting to parse text: {text}")
                    if "LMStudio is not running" in text or "Error in belief agent" in text:
                        return AgentResponse(
                            response="LMStudio is not running or not accessible",
                            concepts=[{
                                "name": "LMStudio Error",
                                "type": "error",
                                "description": "Could not connect to LMStudio API",
                                "related": [],
                                "validation": {
                                    "confidence": 0.0,
                                    "supported_by": [],
                                    "contradicted_by": [],
                                    "needs_verification": []
                                }
                            }],
                            key_points=["LMStudio connection failed"],
                            implications=["System cannot process requests"],
                            uncertainties=["LMStudio availability"],
                            reasoning=["Connection attempt failed"],
                            perspective="parsing",
                            confidence=0.0,
                            timestamp=datetime.now()
                        )
                    structured = json.loads(text)
                except json.JSONDecodeError as e:
                    logger.debug(f"Initial JSON parse failed: {e}")
                    # Try cleaning the text first
                    text = _clean_json_text(text)
                    logger.debug(f"Cleaned text: {text}")
                    structured = json.loads(text)
                if isinstance(structured, dict):
                    # Validate all fields
                    response = structured.get("response", "")
                    concepts = [
                        _ensure_valid_concept(c)
                        for c in structured.get("concepts", [])
                        if isinstance(c, dict)
                    ]
                    key_points = [
                        str(p) for p in structured.get("key_points", [])
                        if p and isinstance(p, (str, int, float))
                    ]
                    implications = [
                        str(i) for i in structured.get("implications", [])
                        if i and isinstance(i, (str, int, float))
                    ]
                    uncertainties = [
                        str(u) for u in structured.get("uncertainties", [])
                        if u and isinstance(u, (str, int, float))
                    ]
                    reasoning = [
                        str(r) for r in structured.get("reasoning", [])
                        if r and isinstance(r, (str, int, float))
                    ]
                    
                    # Calculate confidence based on content quality
                    confidence = min(1.0, max(0.1, (
                        (0.3 if concepts else 0.0) +
                        (0.2 if key_points else 0.0) +
                        (0.2 if implications else 0.0) +
                        (0.15 if uncertainties else 0.0) +
                        (0.15 if reasoning else 0.0)
                    )))
                    
                    return AgentResponse(
                        response=response,
                        concepts=concepts,
                        key_points=key_points or ["No key points extracted"],
                        implications=implications or ["No implications found"],
                        uncertainties=uncertainties or ["No uncertainties identified"],
                        reasoning=reasoning or ["No reasoning steps recorded"],
                        perspective="parsing",
                        confidence=confidence,
                        timestamp=datetime.now()
                    )
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON: {str(e)}")
                
                # Try to extract concepts from the text
                concepts = []
                if "[" in text and "]" in text:
                    try:
                        # Extract text between first [ and last ]
                        concept_text = text[text.find("["):text.rfind("]")+1]
                        # Fix JSON formatting issues
                        concept_text = concept_text.replace("'", '"')
                        concept_text = re.sub(r'(\w+):', r'"\1":', concept_text)
                        concept_text = re.sub(r',\s*([}\]])', r'\1', concept_text)
                        concept_text = re.sub(r'"\s*"', '", "', concept_text)
                        # Parse as JSON
                        concept_data = json.loads(concept_text)
                        if isinstance(concept_data, list):
                            concepts = [
                                _ensure_valid_concept(c)
                                for c in concept_data
                                if isinstance(c, dict)
                            ]
                    except Exception as e:
                        logger.warning(f"Failed to extract concepts: {str(e)}")
                        
                # Try to extract sections using patterns
                key_points = []
                implications = []
                uncertainties = []
                reasoning = []
                
                # Extract key points
                if "Key points:" in text:
                    points_text = text[text.find("Key points:"):].split("\n")
                    for line in points_text[1:]:
                        if line.strip().startswith("-"):
                            key_points.append(line.strip("- ").strip())
                        elif line.strip() and not any(s in line for s in ["Implications:", "Uncertainties:", "Reasoning:"]):
                            key_points.append(line.strip())
                        elif any(s in line for s in ["Implications:", "Uncertainties:", "Reasoning:"]):
                            break
                
                # Extract implications
                if "Implications:" in text:
                    impl_text = text[text.find("Implications:"):].split("\n")
                    for line in impl_text[1:]:
                        if line.strip().startswith("-"):
                            implications.append(line.strip("- ").strip())
                        elif line.strip() and not any(s in line for s in ["Uncertainties:", "Reasoning:"]):
                            implications.append(line.strip())
                        elif any(s in line for s in ["Uncertainties:", "Reasoning:"]):
                            break
                
                # Extract uncertainties
                if "Uncertainties:" in text:
                    uncert_text = text[text.find("Uncertainties:"):].split("\n")
                    for line in uncert_text[1:]:
                        if line.strip().startswith("-"):
                            uncertainties.append(line.strip("- ").strip())
                        elif line.strip() and not any(s in line for s in ["Reasoning:"]):
                            uncertainties.append(line.strip())
                        elif "Reasoning:" in line:
                            break
                
                # Extract reasoning
                if "Reasoning:" in text:
                    reason_text = text[text.find("Reasoning:"):].split("\n")
                    for line in reason_text[1:]:
                        if line.strip().startswith("1.") or line.strip().startswith("2."):
                            reasoning.append(line.strip("12. ").strip())
                        elif line.strip():
                            reasoning.append(line.strip())
                
                return AgentResponse(
                    response=text,
                    concepts=concepts,
                    key_points=key_points or ["No key points extracted"],
                    implications=implications or ["No implications found"],
                    uncertainties=uncertainties or ["No uncertainties identified"],
                    reasoning=reasoning or ["No reasoning steps recorded"],
                    perspective="parsing",
                    confidence=0.1,
                    timestamp=datetime.now()
                )
            
            # If JSON parsing failed, try pattern matching
            structured = _extract_structured_content(text)
            
            # If still no structure, create minimal response
            if not structured:
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
            
            # Validate all fields
            response = structured.get("response", "")
            concepts = [
                _ensure_valid_concept(c)
                for c in structured.get("concepts", [])
                if isinstance(c, dict)
            ]
            key_points = [
                str(p) for p in structured.get("key_points", [])
                if p and isinstance(p, (str, int, float))
            ]
            implications = [
                str(i) for i in structured.get("implications", [])
                if i and isinstance(i, (str, int, float))
            ]
            uncertainties = [
                str(u) for u in structured.get("uncertainties", [])
                if u and isinstance(u, (str, int, float))
            ]
            reasoning = [
                str(r) for r in structured.get("reasoning", [])
                if r and isinstance(r, (str, int, float))
            ]
            
            # Calculate confidence based on content quality
            confidence = min(1.0, max(0.1, (
                (0.3 if concepts else 0.0) +
                (0.2 if key_points else 0.0) +
                (0.2 if implications else 0.0) +
                (0.15 if uncertainties else 0.0) +
                (0.15 if reasoning else 0.0)
            )))
            
            # Create agent response
            return AgentResponse(
                response=response,
                concepts=concepts,
                key_points=key_points,
                implications=implications,
                uncertainties=uncertainties,
                reasoning=reasoning,
                perspective="parsing",
                confidence=confidence,
                timestamp=datetime.now()
            )
                
        except Exception as e:
            logger.error(f"Error parsing text: {str(e)}")
            return AgentResponse(
                response=text if isinstance(text, str) else "",
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective="parsing",
                confidence=0.0,
                timestamp=datetime.now()
            )
    
    async def parse_sentiment(self, text: str) -> Dict[str, float]:
        """Parse sentiment from text."""
        try:
            if not text or not isinstance(text, str):
                logger.warning("Invalid text input for sentiment parsing")
                return {
                    "positive": 0.0,
                    "negative": 0.0,
                    "neutral": 1.0
                }
            
            structured = _extract_structured_content(text)
            if isinstance(structured, dict) and "sentiment" in structured:
                sentiment = structured["sentiment"]
                if isinstance(sentiment, dict):
                    return {
                        "positive": float(sentiment.get("positive", 0.0)),
                        "negative": float(sentiment.get("negative", 0.0)),
                        "neutral": float(sentiment.get("neutral", 1.0))
                    }
            
            return {
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0
            }
            
        except Exception as e:
            logger.error(f"Error parsing sentiment: {str(e)}")
            return {
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0
            }
