"""Nova's core response processing functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ResponseResult:
    """Container for response processing results."""
    
    def __init__(
        self,
        components: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        structure: Optional[Dict] = None
    ):
        self.components = components
        self.confidence = confidence
        self.metadata = metadata or {}
        self.structure = structure or {}
        self.timestamp = datetime.now().isoformat()

class ResponseAgent:
    """Core response processing functionality for Nova's ecosystem."""
    
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
        
    async def analyze_response(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> ResponseResult:
        """Analyze response with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar responses if vector store available
            similar_responses = []
            if self.vector_store:
                similar_responses = await self._get_similar_responses(content)
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "content": content,
                        "metadata": metadata,
                        "similar_responses": similar_responses
                    },
                    template="response_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_analysis(content, similar_responses)
                
            # Extract and validate components
            components = self._extract_components(analysis)
            structure = self._extract_structure(analysis)
            
            # Calculate confidence
            confidence = self._calculate_confidence(components, structure)
            
            return ResponseResult(
                components=components,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "content_type": content.get("type", "text"),
                    "source": content.get("source", "unknown")
                },
                structure=structure
            )
            
        except Exception as e:
            logger.error(f"Response analysis error: {str(e)}")
            return ResponseResult(
                components=[],
                confidence=0.0,
                metadata={"error": str(e)},
                structure={"error": str(e)}
            )
            
    async def _get_similar_responses(self, content: Dict[str, Any]) -> List[Dict]:
        """Get similar responses from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "response"
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar responses: {str(e)}")
        return []
            
    def _basic_analysis(
        self,
        content: Dict[str, Any],
        similar_responses: List[Dict]
    ) -> Dict:
        """Basic response analysis without LLM."""
        components = []
        structure = {}
        
        # Basic component extraction from text
        text = str(content.get("content", "")).lower()
        
        # Basic component indicators and their confidences
        component_indicators = {
            "statement": 0.8,
            "question": 0.8,
            "instruction": 0.7,
            "explanation": 0.7,
            "suggestion": 0.7,
            "clarification": 0.7,
            "reference": 0.6,
            "example": 0.6
        }
        
        # Check for component indicators
        for indicator, base_confidence in component_indicators.items():
            if indicator in text:
                # Extract the component statement
                start_idx = text.find(indicator) + len(indicator)
                end_idx = text.find(".", start_idx)
                if end_idx == -1:
                    end_idx = len(text)
                    
                component_statement = text[start_idx:end_idx].strip()
                if component_statement:
                    components.append({
                        "statement": component_statement,
                        "type": f"inferred_{indicator}",
                        "confidence": base_confidence,
                        "source": "text_analysis"
                    })
                    
        # Add similar responses as structure
        if similar_responses:
            structure["similar_responses"] = [
                {
                    "content": m.get("content", {}).get("content", ""),
                    "similarity": m.get("similarity", 0.0),
                    "timestamp": m.get("timestamp", "")
                }
                for m in similar_responses
            ]
                
        return {
            "components": components,
            "structure": structure
        }
        
    def _extract_components(self, analysis: Dict) -> List[Dict]:
        """Extract and validate components."""
        components = analysis.get("components", [])
        valid_components = []
        
        for component in components:
            if isinstance(component, dict) and "statement" in component:
                valid_component = {
                    "statement": str(component["statement"]),
                    "type": str(component.get("type", "component")),
                    "confidence": float(component.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in component:
                    valid_component["description"] = str(component["description"])
                if "source" in component:
                    valid_component["source"] = str(component["source"])
                if "domain_relevance" in component:
                    valid_component["domain_relevance"] = float(component["domain_relevance"])
                if "intent" in component:
                    valid_component["intent"] = str(component["intent"])
                if "context" in component:
                    valid_component["context"] = str(component["context"])
                if "role" in component:
                    valid_component["role"] = str(component["role"])
                    
                valid_components.append(valid_component)
                
        return valid_components
        
    def _extract_structure(self, analysis: Dict) -> Dict:
        """Extract and validate structure."""
        structure = analysis.get("structure", {})
        valid_structure = {}
        
        if isinstance(structure, dict):
            # Extract relevant structure fields
            if "similar_responses" in structure:
                valid_structure["similar_responses"] = [
                    {
                        "content": str(r.get("content", "")),
                        "similarity": float(r.get("similarity", 0.0)),
                        "timestamp": str(r.get("timestamp", ""))
                    }
                    for r in structure["similar_responses"]
                    if isinstance(r, dict)
                ]
                
            if "sequence" in structure:
                valid_structure["sequence"] = [
                    str(s) for s in structure["sequence"]
                    if isinstance(s, str)
                ]
                
            if "dependencies" in structure:
                valid_structure["dependencies"] = [
                    str(d) for d in structure["dependencies"]
                    if isinstance(d, str)
                ]
                
            if "domain_factors" in structure:
                valid_structure["domain_factors"] = {
                    str(k): str(v)
                    for k, v in structure["domain_factors"].items()
                    if isinstance(k, str) and isinstance(v, (str, int, float, bool))
                }
                
            if "quality_factors" in structure:
                valid_structure["quality_factors"] = [
                    {
                        "factor": str(f.get("factor", "")),
                        "weight": float(f.get("weight", 0.5))
                    }
                    for f in structure.get("quality_factors", [])
                    if isinstance(f, dict)
                ]
                
        return valid_structure
        
    def _calculate_confidence(
        self,
        components: List[Dict],
        structure: Dict
    ) -> float:
        """Calculate overall response analysis confidence."""
        if not components:
            return 0.0
            
        # Base confidence from component confidences
        component_conf = sum(c.get("confidence", 0.5) for c in components) / len(components)
        
        # Structure confidence factors
        structure_conf = 0.0
        structure_weight = 0.0
        
        # Similar responses boost confidence
        if "similar_responses" in structure:
            resp_count = len(structure["similar_responses"])
            resp_conf = min(1.0, resp_count * 0.2)  # Cap at 1.0
            structure_conf += resp_conf
            structure_weight += 1
            
        # Sequence boosts confidence
        if "sequence" in structure:
            seq_count = len(structure["sequence"])
            seq_conf = min(1.0, seq_count * 0.15)  # Cap at 1.0
            structure_conf += seq_conf
            structure_weight += 1
            
        # Dependencies boost confidence
        if "dependencies" in structure:
            dep_count = len(structure["dependencies"])
            dep_conf = min(1.0, dep_count * 0.1)  # Cap at 1.0
            structure_conf += dep_conf
            structure_weight += 1
            
        # Domain factors influence confidence
        if "domain_factors" in structure:
            domain_conf = min(1.0, len(structure["domain_factors"]) * 0.1)
            structure_conf += domain_conf
            structure_weight += 1
            
        # Quality factors boost confidence
        if "quality_factors" in structure:
            quality_conf = min(1.0, len(structure["quality_factors"]) * 0.15)
            structure_conf += quality_conf
            structure_weight += 1
            
        # Calculate final structure confidence
        if structure_weight > 0:
            structure_conf = structure_conf / structure_weight
            
            # Weighted combination of component and structure confidence
            return (0.6 * component_conf) + (0.4 * structure_conf)
        else:
            return component_conf
