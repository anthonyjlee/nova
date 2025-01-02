"""Nova's core desire analysis functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DesireResult:
    """Container for desire analysis results."""
    
    def __init__(
        self,
        desires: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        motivations: Optional[Dict] = None
    ):
        self.desires = desires
        self.confidence = confidence
        self.metadata = metadata or {}
        self.motivations = motivations or {}
        self.timestamp = datetime.now().isoformat()

class DesireAgent:
    """Core desire analysis functionality for Nova's ecosystem."""
    
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
        
    async def analyze_desires(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> DesireResult:
        """Analyze desires with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "content": content,
                        "metadata": metadata
                    },
                    template="desire_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_analysis(content)
                
            # Extract and validate components
            desires = self._extract_desires(analysis)
            motivations = self._extract_motivations(analysis)
            
            # Calculate confidence
            confidence = self._calculate_confidence(desires, motivations)
            
            return DesireResult(
                desires=desires,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "content_type": content.get("type", "text"),
                    "source": content.get("source", "unknown")
                },
                motivations=motivations
            )
            
        except Exception as e:
            logger.error(f"Desire analysis error: {str(e)}")
            return DesireResult(
                desires=[],
                confidence=0.0,
                metadata={"error": str(e)},
                motivations={"error": str(e)}
            )
            
    def _basic_analysis(self, content: Dict[str, Any]) -> Dict:
        """Basic desire analysis without LLM."""
        desires = []
        motivations = {}
        
        # Basic desire extraction from text
        text = str(content.get("content", "")).lower()
        
        # Basic desire indicators and their confidences
        desire_indicators = {
            "want to": 0.7,
            "need to": 0.8,
            "would like to": 0.6,
            "wish to": 0.6,
            "hope to": 0.5,
            "aim to": 0.7,
            "plan to": 0.8,
            "intend to": 0.8
        }
        
        # Check for desire indicators
        for indicator, base_confidence in desire_indicators.items():
            if indicator in text:
                # Extract the desire statement
                start_idx = text.find(indicator) + len(indicator)
                end_idx = text.find(".", start_idx)
                if end_idx == -1:
                    end_idx = len(text)
                    
                desire_statement = text[start_idx:end_idx].strip()
                if desire_statement:
                    desires.append({
                        "statement": desire_statement,
                        "type": "inferred_desire",
                        "confidence": base_confidence,
                        "source": "text_analysis"
                    })
                    
        # Basic motivation extraction
        if "because" in text:
            start_idx = text.find("because") + len("because")
            end_idx = text.find(".", start_idx)
            if end_idx == -1:
                end_idx = len(text)
                
            motivation = text[start_idx:end_idx].strip()
            if motivation:
                motivations["explicit_reason"] = motivation
                
        return {
            "desires": desires,
            "motivations": motivations
        }
        
    def _extract_desires(self, analysis: Dict) -> List[Dict]:
        """Extract and validate desires."""
        desires = analysis.get("desires", [])
        valid_desires = []
        
        for desire in desires:
            if isinstance(desire, dict) and "statement" in desire:
                valid_desire = {
                    "statement": str(desire["statement"]),
                    "type": str(desire.get("type", "desire")),
                    "confidence": float(desire.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in desire:
                    valid_desire["description"] = str(desire["description"])
                if "source" in desire:
                    valid_desire["source"] = str(desire["source"])
                if "domain_relevance" in desire:
                    valid_desire["domain_relevance"] = float(desire["domain_relevance"])
                if "priority" in desire:
                    valid_desire["priority"] = float(desire["priority"])
                if "achievability" in desire:
                    valid_desire["achievability"] = float(desire["achievability"])
                    
                valid_desires.append(valid_desire)
                
        return valid_desires
        
    def _extract_motivations(self, analysis: Dict) -> Dict:
        """Extract and validate motivations."""
        motivations = analysis.get("motivations", {})
        valid_motivations = {}
        
        if isinstance(motivations, dict):
            # Extract relevant motivation fields
            if "reasons" in motivations:
                valid_motivations["reasons"] = [
                    str(r) for r in motivations["reasons"]
                    if isinstance(r, str)
                ]
                
            if "drivers" in motivations:
                valid_motivations["drivers"] = [
                    str(d) for d in motivations["drivers"]
                    if isinstance(d, str)
                ]
                
            if "constraints" in motivations:
                valid_motivations["constraints"] = [
                    str(c) for c in motivations["constraints"]
                    if isinstance(c, str)
                ]
                
            if "domain_factors" in motivations:
                valid_motivations["domain_factors"] = {
                    str(k): str(v)
                    for k, v in motivations["domain_factors"].items()
                    if isinstance(k, str) and isinstance(v, (str, int, float, bool))
                }
                
            if "priority_factors" in motivations:
                valid_motivations["priority_factors"] = [
                    {
                        "factor": str(f.get("factor", "")),
                        "weight": float(f.get("weight", 0.5))
                    }
                    for f in motivations.get("priority_factors", [])
                    if isinstance(f, dict)
                ]
                
        return valid_motivations
        
    def _calculate_confidence(
        self,
        desires: List[Dict],
        motivations: Dict
    ) -> float:
        """Calculate overall desire analysis confidence."""
        if not desires:
            return 0.0
            
        # Base confidence from desire confidences
        desire_conf = sum(d.get("confidence", 0.5) for d in desires) / len(desires)
        
        # Motivation confidence factors
        motivation_conf = 0.0
        motivation_weight = 0.0
        
        # Explicit reasons boost confidence
        if "reasons" in motivations:
            reason_count = len(motivations["reasons"])
            reason_conf = min(1.0, reason_count * 0.2)  # Cap at 1.0
            motivation_conf += reason_conf
            motivation_weight += 1
            
        # Drivers boost confidence
        if "drivers" in motivations:
            driver_count = len(motivations["drivers"])
            driver_conf = min(1.0, driver_count * 0.15)  # Cap at 1.0
            motivation_conf += driver_conf
            motivation_weight += 1
            
        # Constraints provide context
        if "constraints" in motivations:
            constraint_count = len(motivations["constraints"])
            constraint_conf = min(1.0, constraint_count * 0.1)  # Cap at 1.0
            motivation_conf += constraint_conf
            motivation_weight += 1
            
        # Domain factors influence confidence
        if "domain_factors" in motivations:
            domain_conf = min(1.0, len(motivations["domain_factors"]) * 0.1)
            motivation_conf += domain_conf
            motivation_weight += 1
            
        # Priority factors boost confidence
        if "priority_factors" in motivations:
            priority_conf = min(1.0, len(motivations["priority_factors"]) * 0.15)
            motivation_conf += priority_conf
            motivation_weight += 1
            
        # Calculate final motivation confidence
        if motivation_weight > 0:
            motivation_conf = motivation_conf / motivation_weight
            
            # Weighted combination of desire and motivation confidence
            return (0.6 * desire_conf) + (0.4 * motivation_conf)
        else:
            return desire_conf
