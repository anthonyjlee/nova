"""Nova's core context analysis functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ContextResult:
    """Container for context analysis results."""
    
    def __init__(
        self,
        concepts: List[Dict],
        key_points: List[str],
        confidence: float,
        metadata: Optional[Dict] = None,
        environment: Optional[Dict] = None
    ):
        self.concepts = concepts
        self.key_points = key_points
        self.confidence = confidence
        self.metadata = metadata or {}
        self.environment = environment or {}
        self.timestamp = datetime.now().isoformat()

class ContextAgent:
    """Core context analysis functionality for Nova's ecosystem."""
    
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
        
    async def analyze_context(
        self,
        context: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> ContextResult:
        """Analyze context with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "context": context,
                        "metadata": metadata
                    },
                    template="context_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_analysis(context)
                
            # Extract and validate components
            concepts = self._extract_concepts(analysis)
            key_points = self._extract_key_points(analysis)
            environment = self._extract_environment(analysis)
            
            # Calculate confidence
            confidence = self._calculate_confidence(concepts, environment)
            
            return ContextResult(
                concepts=concepts,
                key_points=key_points,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "context_type": context.get("type", "general"),
                    "source": context.get("source", "unknown")
                },
                environment=environment
            )
            
        except Exception as e:
            logger.error(f"Context analysis error: {str(e)}")
            return ContextResult(
                concepts=[],
                key_points=[],
                confidence=0.0,
                metadata={"error": str(e)},
                environment={"error": str(e)}
            )
            
    def _basic_analysis(self, context: Dict[str, Any]) -> Dict:
        """Basic context analysis without LLM."""
        concepts = []
        key_points = []
        environment = {}
        
        # Extract basic concepts from context
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                concepts.append({
                    "name": key,
                    "type": "context_factor",
                    "value": str(value),
                    "confidence": 0.6
                })
                
            elif isinstance(value, dict):
                # Handle nested context
                concepts.append({
                    "name": key,
                    "type": "nested_context",
                    "confidence": 0.5
                })
                key_points.append(f"Contains nested context: {key}")
                
            elif isinstance(value, list):
                # Handle list context
                concepts.append({
                    "name": key,
                    "type": "multi_value",
                    "confidence": 0.5
                })
                key_points.append(f"Contains multiple values: {key}")
                
        # Basic environment extraction
        if "environment" in context:
            environment = context["environment"]
        elif "settings" in context:
            environment = context["settings"]
            
        return {
            "concepts": concepts,
            "key_points": key_points,
            "environment": environment
        }
        
    def _extract_concepts(self, analysis: Dict) -> List[Dict]:
        """Extract and validate context concepts."""
        concepts = analysis.get("concepts", [])
        valid_concepts = []
        
        for concept in concepts:
            if isinstance(concept, dict) and "name" in concept:
                valid_concept = {
                    "name": str(concept["name"]),
                    "type": str(concept.get("type", "context")),
                    "confidence": float(concept.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in concept:
                    valid_concept["description"] = str(concept["description"])
                if "value" in concept:
                    valid_concept["value"] = str(concept["value"])
                if "domain_relevance" in concept:
                    valid_concept["domain_relevance"] = float(concept["domain_relevance"])
                    
                valid_concepts.append(valid_concept)
                
        return valid_concepts
        
    def _extract_key_points(self, analysis: Dict) -> List[str]:
        """Extract and validate context key points."""
        key_points = analysis.get("key_points", [])
        valid_points = []
        
        for point in key_points:
            if point and isinstance(point, str):
                valid_points.append(point.strip())
                
        return valid_points
        
    def _extract_environment(self, analysis: Dict) -> Dict:
        """Extract and validate environmental factors."""
        environment = analysis.get("environment", {})
        valid_env = {}
        
        if isinstance(environment, dict):
            for key, value in environment.items():
                # Validate and clean environment values
                if isinstance(value, (str, int, float, bool)):
                    valid_env[str(key)] = value
                elif isinstance(value, dict):
                    valid_env[str(key)] = self._clean_env_dict(value)
                elif isinstance(value, list):
                    valid_env[str(key)] = [str(v) for v in value if v is not None]
                    
        return valid_env
        
    def _clean_env_dict(self, env_dict: Dict) -> Dict:
        """Clean and validate nested environment dictionary."""
        cleaned = {}
        for key, value in env_dict.items():
            if isinstance(value, (str, int, float, bool)):
                cleaned[str(key)] = value
            elif isinstance(value, list):
                cleaned[str(key)] = [str(v) for v in value if v is not None]
            elif isinstance(value, dict):
                cleaned[str(key)] = self._clean_env_dict(value)
        return cleaned
        
    def _calculate_confidence(
        self,
        concepts: List[Dict],
        environment: Dict
    ) -> float:
        """Calculate overall context analysis confidence."""
        if not concepts and not environment:
            return 0.0
            
        # Concept confidence
        concept_conf = 0.0
        if concepts:
            confidences = [c.get("confidence", 0.5) for c in concepts]
            concept_conf = sum(confidences) / len(confidences)
            
        # Environment confidence
        env_conf = 0.0
        if environment:
            # More complex environment = higher confidence (up to a point)
            env_size = len(str(environment))
            env_conf = min(1.0, env_size / 1000)  # Cap at 1000 chars
            
        # Weighted average (concepts weighted more heavily)
        if concepts and environment:
            return (0.7 * concept_conf) + (0.3 * env_conf)
        elif concepts:
            return concept_conf
        else:
            return env_conf
