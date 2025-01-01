"""Nova's core structure analysis functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class StructureResult:
    """Container for structure analysis results."""
    
    def __init__(
        self,
        response: str,
        concepts: List[Dict],
        key_points: List[str],
        confidence: float,
        validation: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ):
        self.response = response
        self.concepts = concepts
        self.key_points = key_points
        self.confidence = confidence
        self.validation = validation or {}
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()

class StructureAgent:
    """Core structure analysis functionality for Nova's ecosystem."""
    
    def __init__(
        self,
        llm=None,
        store=None,
        vector_store=None,
        domain: Optional[str] = None
    ):
        self.llm = llm
        self.store = store
        self.vector_store = vector_store
        self.domain = domain or "professional"  # Default to professional domain
        
    async def analyze_structure(
        self,
        text: str,
        expected_schema: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> StructureResult:
        """Analyze text structure with optional schema validation."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "text": text,
                        "expected_schema": expected_schema,
                        "metadata": metadata
                    },
                    template="structure_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_analysis(text, expected_schema)
                
            # Extract and validate components
            concepts = self._extract_concepts(analysis)
            key_points = self._extract_key_points(analysis)
            validation = self._validate_against_schema(text, expected_schema) if expected_schema else {}
            
            # Calculate confidence
            confidence = self._calculate_confidence(concepts, validation)
            
            return StructureResult(
                response=analysis.get("response", ""),
                concepts=concepts,
                key_points=key_points,
                confidence=confidence,
                validation=validation,
                metadata={
                    "domain": self.domain,
                    "has_schema": bool(expected_schema),
                    "source_length": len(text)
                }
            )
            
        except Exception as e:
            logger.error(f"Structure analysis error: {str(e)}")
            return StructureResult(
                response="Error during structure analysis",
                concepts=[],
                key_points=[],
                confidence=0.0,
                validation={"error": str(e)},
                metadata={"error": str(e)}
            )
            
    async def validate_schema(
        self,
        schema: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Validate schema structure and constraints."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            validation_result = {
                "is_valid": True,
                "issues": [],
                "domain": self.domain,
                "timestamp": datetime.now().isoformat()
            }
            
            # Basic schema validation
            if not isinstance(schema, dict):
                validation_result["is_valid"] = False
                validation_result["issues"].append("Schema must be a dictionary")
                return validation_result
                
            # Validate schema structure
            issues = []
            self._validate_schema_structure(schema, "", issues)
            
            if issues:
                validation_result["is_valid"] = False
                validation_result["issues"].extend(issues)
                
            return validation_result
            
        except Exception as e:
            logger.error(f"Schema validation error: {str(e)}")
            return {
                "is_valid": False,
                "issues": [str(e)],
                "domain": self.domain,
                "timestamp": datetime.now().isoformat()
            }
            
    def _basic_analysis(
        self,
        text: str,
        expected_schema: Optional[Dict] = None
    ) -> Dict:
        """Basic structure analysis without LLM."""
        concepts = []
        key_points = []
        
        # Basic structure detection
        lines = text.split("\n")
        indentation_levels = set()
        
        for line in lines:
            # Analyze indentation
            indent = len(line) - len(line.lstrip())
            indentation_levels.add(indent)
            
            # Look for potential structural elements
            stripped = line.strip()
            if stripped.endswith(":"):
                concepts.append({
                    "name": stripped[:-1],
                    "type": "section",
                    "confidence": 0.7
                })
            elif "=" in stripped:
                concepts.append({
                    "name": stripped.split("=")[0].strip(),
                    "type": "assignment",
                    "confidence": 0.6
                })
                
        # Generate key points about structure
        if len(indentation_levels) > 1:
            key_points.append("Multiple indentation levels detected")
        if expected_schema:
            key_points.append("Schema validation requested")
            
        return {
            "response": "Basic structure analysis completed",
            "concepts": concepts,
            "key_points": key_points
        }
        
    def _extract_concepts(self, analysis: Dict) -> List[Dict]:
        """Extract and validate structural concepts."""
        concepts = analysis.get("concepts", [])
        valid_concepts = []
        
        for concept in concepts:
            if isinstance(concept, dict) and "name" in concept:
                valid_concept = {
                    "name": str(concept["name"]),
                    "type": str(concept.get("type", "structure")),
                    "confidence": float(concept.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in concept:
                    valid_concept["description"] = str(concept["description"])
                if "level" in concept:
                    valid_concept["level"] = int(concept["level"])
                    
                valid_concepts.append(valid_concept)
                
        return valid_concepts
        
    def _extract_key_points(self, analysis: Dict) -> List[str]:
        """Extract and validate structural key points."""
        key_points = analysis.get("key_points", [])
        valid_points = []
        
        for point in key_points:
            if point and isinstance(point, str):
                valid_points.append(point.strip())
                
        return valid_points
        
    def _validate_against_schema(
        self,
        text: str,
        schema: Dict[str, Any]
    ) -> Dict:
        """Validate text structure against expected schema."""
        validation = {
            "matches_schema": True,
            "issues": []
        }
        
        try:
            # Basic structure validation
            if not text or not schema:
                validation["matches_schema"] = False
                validation["issues"].append("Missing text or schema")
                return validation
                
            # TODO: Implement more sophisticated schema validation
            # This is a placeholder for basic validation
            
            return validation
            
        except Exception as e:
            validation["matches_schema"] = False
            validation["issues"].append(f"Validation error: {str(e)}")
            return validation
            
    def _validate_schema_structure(
        self,
        schema: Dict,
        path: str,
        issues: List[str]
    ):
        """Recursively validate schema structure."""
        for key, value in schema.items():
            current_path = f"{path}.{key}" if path else key
            
            # Validate key naming
            if not isinstance(key, str):
                issues.append(f"Invalid key type at {current_path}")
                
            # Validate nested structures
            if isinstance(value, dict):
                self._validate_schema_structure(value, current_path, issues)
            elif isinstance(value, list):
                if not value:
                    issues.append(f"Empty array at {current_path}")
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._validate_schema_structure(
                            item,
                            f"{current_path}[{i}]",
                            issues
                        )
                        
    def _calculate_confidence(
        self,
        concepts: List[Dict],
        validation: Dict
    ) -> float:
        """Calculate overall structure analysis confidence."""
        if not concepts:
            return 0.0
            
        # Concept confidence
        concept_conf = sum(c.get("confidence", 0.5) for c in concepts) / len(concepts)
        
        # Validation confidence
        validation_conf = 1.0
        if validation.get("issues"):
            validation_conf = max(0.0, 1.0 - (len(validation["issues"]) * 0.1))
            
        # Weighted average (concepts weighted more heavily)
        return (0.7 * concept_conf) + (0.3 * validation_conf)
