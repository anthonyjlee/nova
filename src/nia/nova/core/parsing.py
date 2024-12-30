"""Core parsing functionality from ParsingAgent."""

import logging
import orjson
import re
from typing import Dict, List, Any, Optional, Union, TYPE_CHECKING
from jsonschema import validate, ValidationError
from datetime import datetime
from ...types.memory_types import AgentResponse
from ...agents.base import BaseAgent
from ..prompts import AGENT_PROMPTS

if TYPE_CHECKING:
    from ...llm_interface import LLMInterface
    from ...memory.neo4j.neo4j_store import Neo4jMemoryStore
    from ...memory.vector.vector_store import VectorStore

logger = logging.getLogger(__name__)

# JSON Schema for LLM Studio response
LLMSTUDIO_SCHEMA = {
    "type": "object",
    "required": ["id", "object", "created", "model", "choices", "usage"],
    "properties": {
        "id": {"type": "string"},
        "object": {"type": "string"},
        "created": {"type": "integer"},
        "model": {"type": "string"},
        "choices": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["index", "message"],
                "properties": {
                    "index": {"type": "integer"},
                    "message": {
                        "type": "object",
                        "required": ["role", "content"],
                        "properties": {
                            "role": {"type": "string"},
                            "content": {"type": "string"}
                        }
                    }
                }
            }
        },
        "usage": {
            "type": "object",
            "required": ["prompt_tokens", "completion_tokens", "total_tokens"],
            "properties": {
                "prompt_tokens": {"type": "integer"},
                "completion_tokens": {"type": "integer"},
                "total_tokens": {"type": "integer"}
            }
        }
    }
}

# JSON Schema for structured content
STRUCTURED_CONTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "response": {"type": "string"},
        "dialogue": {"type": "string"},
        "concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "type", "description", "related", "validation"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "description": {"type": "string"},
                    "related": {"type": "array", "items": {"type": "string"}},
                    "validation": {
                        "type": "object",
                        "required": ["confidence", "supported_by", "contradicted_by", "needs_verification"],
                        "properties": {
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "supported_by": {"type": "array", "items": {"type": "string"}},
                            "contradicted_by": {"type": "array", "items": {"type": "string"}},
                            "needs_verification": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                }
            }
        },
        "key_points": {"type": "array", "items": {"type": "string"}},
        "implications": {"type": "array", "items": {"type": "string"}},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
        "reasoning": {"type": "array", "items": {"type": "string"}},
        "metadata": {"type": "object"}
    }
}

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
            (r'"\s*"', '""'),  # Fix array string spacing
            (r'([{,]\s*)(\w+):', r'\1"\2":'),  # Fix unquoted keys
            (r'([{,]\s*)([^"\s]+):', r'\1"\2":'),  # Fix any remaining unquoted keys
            (r'None', '"None"'),  # Quote None values
            (r'True', 'true'),  # Fix boolean values
            (r'False', 'false'),
            (r'null', '"null"'),  # Quote null values
            (r',\s*,', ''),  # Remove duplicate commas
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
            return orjson.loads(text)
        except ValueError:
            pass
            
        # Clean up text
        text = _clean_json_text(text)
        
        # Try multiple parsing strategies
        strategies = [
            # Strategy 1: Direct JSON parsing after cleaning
            lambda t: orjson.loads(t),
            
            # Strategy 2: Extract JSON object using regex
            lambda t: orjson.loads(re.search(r'({[^}]+})', t).group(1)) if re.search(r'({[^}]+})', t) else None,
            
            # Strategy 3: Fix and parse JSON with missing quotes
            lambda t: orjson.loads(re.sub(r':\s*([^"{}\[\],\s][^,}]*?)(?=[,}])', r': "\1"', t)),
            
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
                            current_concept['related'] = [r.strip() for r in value.split()]
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

class NovaParser:
    """Core parsing functionality from ParsingAgent."""
    
    def __init__(
        self,
        llm: 'LLMInterface',
        store: 'Neo4jMemoryStore',
        vector_store: 'VectorStore'
    ):
        """Initialize parser."""
        self.llm = llm
        self.store = store
        self.vector_store = vector_store
        
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for parsing."""
        text = content.get('content', '')
        return AGENT_PROMPTS["parsing"].format(content=text)
    
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
            
            # Clean up text
            text = text.strip().strip("'").strip('"').strip()
            
            # Try to extract the message content from LLM Studio response
            try:
                # Parse the outer LLM Studio response
                if '"choices"' in text:
                    try:
                        # Parse and validate LLM Studio response
                        studio_response = orjson.loads(text)
                        validate(instance=studio_response, schema=LLMSTUDIO_SCHEMA)
                        text = studio_response["choices"][0]["message"]["content"]
                    except (orjson.JSONDecodeError, ValidationError) as e:
                        logger.error(f"Error parsing LLM Studio response: {str(e)}")
                        return AgentResponse(
                            response=text,
                            dialogue="Error parsing response",
                            concepts=[{
                                "name": "Parse Error",
                                "type": "error",
                                "description": str(e),
                                "related": [],
                                "validation": {
                                    "confidence": 0.0,
                                    "supported_by": [],
                                    "contradicted_by": [],
                                    "needs_verification": ["Response format"]
                                }
                            }],
                            key_points=["Error occurred"],
                            implications=["Response parsing failed"],
                            uncertainties=["Response format"],
                            reasoning=["JSON parsing error"],
                            perspective="parsing",
                            confidence=0.0,
                            timestamp=datetime.now()
                        )
            except:
                pass  # If extraction fails, use the text as-is
                
            # If it's a simple text response (not JSON), wrap it in a basic structure
            if not (text.strip().startswith('{') and text.strip().endswith('}')):
                # Check if it's a greeting-style response
                if any(greeting in text.lower() for greeting in ["hello", "hi", "hey", "greetings"]):
                    return AgentResponse(
                        response=text,
                        dialogue=text,
                        concepts=[{
                            "name": "Greeting",
                            "type": "interaction",
                            "description": "Initial greeting response",
                            "related": ["Conversation Start"],
                            "validation": {
                                "confidence": 0.8,
                                "supported_by": ["Direct greeting"],
                                "contradicted_by": [],
                                "needs_verification": []
                            }
                        }],
                        key_points=["Conversation initiated"],
                        implications=["Begin dialogue"],
                        uncertainties=[],
                        reasoning=["Greeting detected"],
                        perspective="dialogue",
                        confidence=0.8,
                        timestamp=datetime.now(),
                        metadata={
                            "interaction_type": "greeting",
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                else:
                    return AgentResponse(
                        response=text,
                        dialogue=text,
                        concepts=[{
                            "name": "Direct Response",
                            "type": "interaction",
                            "description": text,
                            "related": ["Conversation"],
                            "validation": {
                                "confidence": 0.7,
                                "supported_by": ["Direct response"],
                                "contradicted_by": [],
                                "needs_verification": []
                            }
                        }],
                        key_points=["User interaction"],
                        implications=["Continue dialogue"],
                        uncertainties=[],
                        reasoning=["Direct response"],
                        perspective="dialogue",
                        confidence=0.7,
                        timestamp=datetime.now(),
                        metadata={
                            "interaction_type": "direct_response",
                            "timestamp": datetime.now().isoformat()
                        }
                    )
            
            # Try JSON parsing for structured responses
            try:
                try:
                    # Parse and validate structured content
                    structured = orjson.loads(text)
                    validate(instance=structured, schema=STRUCTURED_CONTENT_SCHEMA)
                except (orjson.JSONDecodeError, ValidationError) as e:
                    logger.error(f"Error parsing structured content: {str(e)}")
                    # Try cleaning the text first
                    cleaned_text = _clean_json_text(text)
                    try:
                        structured = orjson.loads(cleaned_text)
                        validate(instance=structured, schema=STRUCTURED_CONTENT_SCHEMA)
                    except (orjson.JSONDecodeError, ValidationError) as e2:
                        logger.error(f"Error parsing cleaned content: {str(e2)}")
                        return AgentResponse(
                            response=text,
                            dialogue="Error parsing structured content",
                            concepts=[{
                                "name": "Parse Error",
                                "type": "error",
                                "description": str(e2),
                                "related": [],
                                "validation": {
                                    "confidence": 0.0,
                                    "supported_by": [],
                                    "contradicted_by": [],
                                    "needs_verification": ["Content format"]
                                }
                            }],
                            key_points=["Error occurred"],
                            implications=["Content parsing failed"],
                            uncertainties=["Content format"],
                            reasoning=["JSON parsing error"],
                            perspective="parsing",
                            confidence=0.0,
                            timestamp=datetime.now()
                        )
            except ValueError as e:
                logger.debug(f"Initial JSON parse failed: {e}")
                # Try cleaning the text first
                text = _clean_json_text(text)
                logger.debug(f"Cleaned text: {text}")
                structured = orjson.loads(text)
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
                    
                    # Get dialogue field or use response as fallback
                    dialogue = structured.get("dialogue", response)
                    
                    # Create agent response with dialogue field
                    return AgentResponse(
                        response=response,
                        dialogue=dialogue,
                        concepts=concepts,
                        key_points=key_points or ["No key points extracted"],
                        implications=implications or ["No implications found"],
                        uncertainties=uncertainties or ["No uncertainties identified"],
                        reasoning=reasoning or ["No reasoning steps recorded"],
                        perspective="parsing",
                        confidence=confidence,
                        timestamp=datetime.now(),
                        metadata=structured.get("metadata", {})
                    )
            except (ValueError, TypeError) as e:
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
                        concept_text = re.sub(r'"\s*"', '""', concept_text)
                        # Parse as JSON
                        concept_data = orjson.loads(concept_text)
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
                
                # Create response with dialogue field
                return AgentResponse(
                    response=text,
                    dialogue="I've processed your message but encountered some formatting issues.",
                    concepts=concepts,
                    key_points=key_points or ["No key points extracted"],
                    implications=implications or ["No implications found"],
                    uncertainties=uncertainties or ["No uncertainties identified"],
                    reasoning=reasoning or ["No reasoning steps recorded"],
                    perspective="parsing",
                    confidence=0.1,
                    timestamp=datetime.now(),
                    metadata={
                        "parsing_method": "pattern_matching",
                        "timestamp": datetime.now().isoformat()
                    }
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
            # Create error response with dialogue field
            return AgentResponse(
                response=text if isinstance(text, str) else "",
                dialogue="I apologize, but I encountered an error while processing your message.",
                concepts=[{
                    "name": "Parse Error",
                    "type": "error",
                    "description": str(e),
                    "related": [],
                    "validation": {
                        "confidence": 0.0,
                        "supported_by": [],
                        "contradicted_by": [],
                        "needs_verification": ["Error resolution"]
                    }
                }],
                key_points=["Error occurred during parsing"],
                implications=["Response may be incomplete"],
                uncertainties=["Error cause and resolution"],
                reasoning=["Parse error encountered"],
                perspective="parsing",
                confidence=0.0,
                timestamp=datetime.now(),
                metadata={
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
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
