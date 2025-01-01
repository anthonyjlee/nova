"""Nova's core parsing functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ParseResult:
    """Container for parsing results."""
    
    def __init__(
        self,
        concepts: List[Dict],
        key_points: List[str],
        confidence: float,
        metadata: Optional[Dict] = None
    ):
        self.concepts = concepts
        self.key_points = key_points
        self.confidence = confidence
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()

class NovaParser:
    """Core parsing functionality for Nova's ecosystem."""
    
    def __init__(
        self,
        llm=None,
        store=None,
        vector_store=None,
        schema_validator=None
    ):
        self.llm = llm
        self.store = store
        self.vector_store = vector_store
        self.schema_validator = schema_validator or self.load_default_schema_validator()
        
    def load_default_schema_validator(self):
        """Load default schema validation rules."""
        return {
            "concepts": {
                "required": ["name", "type"],
                "optional": ["description", "attributes", "confidence"]
            },
            "key_points": {
                "min_length": 1,
                "max_length": 500
            },
            "confidence": {
                "min": 0.0,
                "max": 1.0
            }
        }
        
    async def parse_text(self, text: str) -> ParseResult:
        """Parse text into structured information."""
        try:
            # Use LLM to extract concepts and key points
            if self.llm:
                analysis = await self.llm.analyze(
                    text,
                    template="parsing",
                    max_tokens=1000
                )
            else:
                # Fallback to basic parsing if no LLM
                analysis = self._basic_parse(text)
                
            # Validate and structure the results
            concepts = self._validate_concepts(analysis.get("concepts", []))
            key_points = self._validate_key_points(analysis.get("key_points", []))
            confidence = self._calculate_confidence(concepts, key_points)
            
            return ParseResult(
                concepts=concepts,
                key_points=key_points,
                confidence=confidence,
                metadata={"source_length": len(text)}
            )
            
        except Exception as e:
            logger.error(f"Parsing error: {str(e)}")
            # Return minimal valid result
            return ParseResult(
                concepts=[],
                key_points=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )
            
    def _basic_parse(self, text: str) -> Dict:
        """Basic parsing without LLM."""
        # Split into sentences and extract basic concepts
        sentences = text.split(". ")
        concepts = []
        key_points = []
        
        for sentence in sentences:
            # Extract potential concepts (capitalized terms)
            words = sentence.split()
            for word in words:
                if word[0].isupper() and len(word) > 2:
                    concepts.append({
                        "name": word,
                        "type": "extracted_term",
                        "confidence": 0.5
                    })
                    
            # Use sentences as key points if they seem significant
            if len(sentence.split()) > 5:  # Arbitrary threshold
                key_points.append(sentence)
                
        return {
            "concepts": concepts[:10],  # Limit to top 10
            "key_points": key_points[:5]  # Limit to top 5
        }
        
    def _validate_concepts(self, concepts: List[Dict]) -> List[Dict]:
        """Validate and clean concept data."""
        valid_concepts = []
        schema = self.schema_validator["concepts"]
        
        for concept in concepts:
            # Check required fields
            if all(field in concept for field in schema["required"]):
                # Clean and validate
                valid_concept = {
                    "name": str(concept["name"]),
                    "type": str(concept["type"])
                }
                
                # Add optional fields if present and valid
                for field in schema["optional"]:
                    if field in concept:
                        if field == "confidence":
                            # Ensure confidence is float between 0 and 1
                            try:
                                conf = float(concept[field])
                                valid_concept[field] = max(0.0, min(1.0, conf))
                            except (ValueError, TypeError):
                                valid_concept[field] = 0.5
                        else:
                            valid_concept[field] = concept[field]
                            
                valid_concepts.append(valid_concept)
                
        return valid_concepts
        
    def _validate_key_points(self, key_points: List[str]) -> List[str]:
        """Validate and clean key points."""
        schema = self.schema_validator["key_points"]
        valid_points = []
        
        for point in key_points:
            # Convert to string and clean
            point_str = str(point).strip()
            
            # Check length constraints
            if schema["min_length"] <= len(point_str) <= schema["max_length"]:
                valid_points.append(point_str)
                
        return valid_points
        
    def _calculate_confidence(self, concepts: List[Dict], key_points: List[str]) -> float:
        """Calculate overall parsing confidence."""
        if not concepts and not key_points:
            return 0.0
            
        # Average concept confidences
        concept_conf = 0.0
        if concepts:
            confidences = [c.get("confidence", 0.5) for c in concepts]
            concept_conf = sum(confidences) / len(confidences)
            
        # Key points confidence based on quantity and quality
        kp_conf = 0.0
        if key_points:
            # Simple metric: ratio of key points to max expected
            max_expected = 10  # Arbitrary threshold
            kp_conf = min(1.0, len(key_points) / max_expected)
            
        # Weighted average (concepts weighted more heavily)
        if concepts and key_points:
            return (0.7 * concept_conf) + (0.3 * kp_conf)
        elif concepts:
            return concept_conf
        else:
            return kp_conf
