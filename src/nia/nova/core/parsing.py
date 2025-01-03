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
        key_points: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        structure: Optional[Dict] = None
    ):
        self.concepts = concepts
        self.key_points = key_points
        self.confidence = confidence
        self.metadata = metadata or {}
        self.structure = structure or {}
        self.timestamp = datetime.now().isoformat()

class NovaParser:
    """Core parsing functionality for Nova's ecosystem."""

    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> ParseResult:
        """Process content through parsing."""
        text = content.get("text", "")
        return await self.parse_text(text, metadata)
    
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
        
    async def parse_text(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> ParseResult:
        """Parse text with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar parses if vector store available
            similar_parses = []
            if self.vector_store:
                similar_parses = await self._get_similar_parses(text)
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "text": text,
                        "metadata": metadata,
                        "similar_parses": similar_parses
                    },
                    template="parsing_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_analysis(text, similar_parses)
                
            # Extract and validate components
            concepts = self._extract_concepts(analysis)
            key_points = self._extract_key_points(analysis)
            structure = self._extract_structure(analysis)
            
            # Use confidence from analysis if available, otherwise calculate
            confidence = analysis.get("confidence", self._calculate_confidence(concepts, key_points, structure))
            
            return ParseResult(
                concepts=concepts,
                key_points=key_points,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "content_type": "text",
                    "source": metadata.get("source", "unknown")
                },
                structure=structure
            )
            
        except Exception as e:
            logger.error(f"Parsing error: {str(e)}")
            return ParseResult(
                concepts=[{
                    "statement": "Error occurred during parsing",
                    "type": "error",
                    "confidence": 0.0
                }],
                key_points=[{
                    "statement": str(e),
                    "type": "error",
                    "confidence": 0.0
                }],
                confidence=0.0,
                metadata={"error": str(e)},
                structure={"error": str(e)}
            )
            
    async def _get_similar_parses(self, text: str) -> List[Dict]:
        """Get similar parses from vector store."""
        try:
            if hasattr(self.vector_store, 'search_vectors'):
                results = await self.vector_store.search_vectors(
                    content=text,
                    limit=5,
                    layer="parse",
                    include_metadata=True
                )
            elif hasattr(self.vector_store, 'search'):
                results = await self.vector_store.search(
                    content=text,
                    limit=5
                )
            else:
                results = []
            return results
        except Exception as e:
            logger.error(f"Error getting similar parses: {str(e)}")
        return []
            
    def _basic_analysis(
        self,
        text: str,
        similar_parses: List[Dict]
    ) -> Dict:
        """Basic text parsing without LLM."""
        concepts = []
        key_points = []
        structure = {}
        
        # Basic concept extraction
        concept_indicators = {
            "definition": 0.8,
            "example": 0.7,
            "comparison": 0.7,
            "process": 0.8,
            "principle": 0.8,
            "theory": 0.7,
            "method": 0.7,
            "result": 0.6
        }
        
        # Check for concept indicators
        for indicator, base_confidence in concept_indicators.items():
            if indicator in text.lower():
                # Extract the concept statement
                start_idx = text.lower().find(indicator)
                end_idx = text.find(".", start_idx)
                if end_idx == -1:
                    end_idx = len(text)
                    
                concept_statement = text[start_idx:end_idx].strip()
                if concept_statement:
                    concepts.append({
                        "statement": concept_statement,
                        "type": f"inferred_{indicator}",
                        "confidence": base_confidence,
                        "source": "text_analysis"
                    })
                    
        # Basic key point extraction
        key_point_indicators = {
            "important": 0.8,
            "key": 0.8,
            "main": 0.7,
            "critical": 0.8,
            "essential": 0.7,
            "significant": 0.7,
            "fundamental": 0.7,
            "crucial": 0.8
        }
        
        # Check for key point indicators
        for indicator, base_confidence in key_point_indicators.items():
            if indicator in text.lower():
                # Extract the key point statement
                start_idx = text.lower().find(indicator)
                end_idx = text.find(".", start_idx)
                if end_idx == -1:
                    end_idx = len(text)
                    
                key_point_statement = text[start_idx:end_idx].strip()
                if key_point_statement:
                    key_points.append({
                        "statement": key_point_statement,
                        "type": f"inferred_key_point",
                        "confidence": base_confidence,
                        "source": "text_analysis"
                    })
                    
        # Add similar parses as structure
        if similar_parses:
            structure["similar_parses"] = [
                {
                    "content": p.get("content", {}).get("content", ""),
                    "similarity": p.get("similarity", 0.0),
                    "timestamp": p.get("timestamp", "")
                }
                for p in similar_parses
            ]
                
        return {
            "concepts": concepts,
            "key_points": key_points,
            "structure": structure
        }
        
    def _extract_concepts(self, analysis: Dict) -> List[Dict]:
        """Extract and validate concepts."""
        concepts = analysis.get("concepts", [])
        valid_concepts = []
        
        for concept in concepts:
            if isinstance(concept, dict) and "statement" in concept:
                valid_concept = {
                    "statement": str(concept["statement"]),
                    "type": str(concept.get("type", "concept")),
                    "confidence": float(concept.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in concept:
                    valid_concept["description"] = str(concept["description"])
                if "source" in concept:
                    valid_concept["source"] = str(concept["source"])
                if "domain_relevance" in concept:
                    valid_concept["domain_relevance"] = float(concept["domain_relevance"])
                if "complexity" in concept:
                    valid_concept["complexity"] = float(concept["complexity"])
                if "category" in concept:
                    valid_concept["category"] = str(concept["category"])
                if "relations" in concept:
                    valid_concept["relations"] = [str(r) for r in concept["relations"]]
                    
                valid_concepts.append(valid_concept)
                
        return valid_concepts
        
    def _extract_key_points(self, analysis: Dict) -> List[Dict]:
        """Extract and validate key points."""
        key_points = analysis.get("key_points", [])
        valid_key_points = []
        
        for point in key_points:
            if isinstance(point, dict) and "statement" in point:
                valid_point = {
                    "statement": str(point["statement"]),
                    "type": str(point.get("type", "key_point")),
                    "confidence": float(point.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in point:
                    valid_point["description"] = str(point["description"])
                if "source" in point:
                    valid_point["source"] = str(point["source"])
                if "domain_relevance" in point:
                    valid_point["domain_relevance"] = float(point["domain_relevance"])
                if "importance" in point:
                    valid_point["importance"] = float(point["importance"])
                if "category" in point:
                    valid_point["category"] = str(point["category"])
                if "dependencies" in point:
                    valid_point["dependencies"] = [str(d) for d in point["dependencies"]]
                    
                valid_key_points.append(valid_point)
                
        return valid_key_points
        
    def _extract_structure(self, analysis: Dict) -> Dict:
        """Extract and validate structure."""
        structure = analysis.get("structure", {})
        valid_structure = {}
        
        if isinstance(structure, dict):
            # Extract relevant structure fields
            if "similar_parses" in structure:
                valid_structure["similar_parses"] = [
                    {
                        "content": str(p.get("content", "")),
                        "similarity": float(p.get("similarity", 0.0)),
                        "timestamp": str(p.get("timestamp", ""))
                    }
                    for p in structure["similar_parses"]
                    if isinstance(p, dict)
                ]
                
            if "sections" in structure:
                valid_structure["sections"] = [
                    str(s) for s in structure["sections"]
                    if isinstance(s, str)
                ]
                
            if "relationships" in structure:
                valid_structure["relationships"] = [
                    str(r) for r in structure["relationships"]
                    if isinstance(r, str)
                ]
                
            if "domain_factors" in structure:
                valid_structure["domain_factors"] = {
                    str(k): str(v)
                    for k, v in structure["domain_factors"].items()
                    if isinstance(k, str) and isinstance(v, (str, int, float, bool))
                }
                
            if "complexity_factors" in structure:
                valid_structure["complexity_factors"] = [
                    {
                        "factor": str(f.get("factor", "")),
                        "weight": float(f.get("weight", 0.5))
                    }
                    for f in structure.get("complexity_factors", [])
                    if isinstance(f, dict)
                ]
                
        return valid_structure
        
    def _calculate_confidence(
        self,
        concepts: List[Dict],
        key_points: List[Dict],
        structure: Dict
    ) -> float:
        """Calculate overall parsing confidence."""
        if not concepts and not key_points:
            return 0.8  # Default confidence when no concepts/key points
            
        # Base confidence from concept and key point confidences
        concept_conf = (
            sum(c.get("confidence", 0.5) for c in concepts) / len(concepts)
            if concepts else 0.0
        )
        key_point_conf = (
            sum(p.get("confidence", 0.5) for p in key_points) / len(key_points)
            if key_points else 0.0
        )
        
        # Combined base confidence
        base_conf = (
            (concept_conf + key_point_conf) / 2
            if concept_conf > 0 and key_point_conf > 0
            else max(concept_conf, key_point_conf)
        )
        
        # Structure confidence factors
        structure_conf = 0.0
        structure_weight = 0.0
        
        # Similar parses boost confidence
        if "similar_parses" in structure:
            parse_count = len(structure["similar_parses"])
            parse_conf = min(1.0, parse_count * 0.2)  # Cap at 1.0
            structure_conf += parse_conf
            structure_weight += 1
            
        # Sections boost confidence
        if "sections" in structure:
            sect_count = len(structure["sections"])
            sect_conf = min(1.0, sect_count * 0.15)  # Cap at 1.0
            structure_conf += sect_conf
            structure_weight += 1
            
        # Relationships boost confidence
        if "relationships" in structure:
            rel_count = len(structure["relationships"])
            rel_conf = min(1.0, rel_count * 0.1)  # Cap at 1.0
            structure_conf += rel_conf
            structure_weight += 1
            
        # Domain factors influence confidence
        if "domain_factors" in structure:
            domain_conf = min(1.0, len(structure["domain_factors"]) * 0.1)
            structure_conf += domain_conf
            structure_weight += 1
            
        # Complexity factors boost confidence
        if "complexity_factors" in structure:
            complex_conf = min(1.0, len(structure["complexity_factors"]) * 0.15)
            structure_conf += complex_conf
            structure_weight += 1
            
        # Calculate final structure confidence
        if structure_weight > 0:
            structure_conf = structure_conf / structure_weight
            
            # Weighted combination of base and structure confidence
            return (0.6 * base_conf) + (0.4 * structure_conf)
        else:
            return base_conf
