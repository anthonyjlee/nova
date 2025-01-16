"""Nova's core belief analysis functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class BeliefResult:
    """Container for belief analysis results."""
    
    def __init__(
        self,
        beliefs: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        evidence: Optional[Dict] = None
    ):
        self.beliefs = beliefs
        self.confidence = confidence
        self.metadata = metadata or {}
        self.evidence = evidence or {}
        self.timestamp = datetime.now().isoformat()

class BeliefAgent:
    """Core belief analysis functionality for Nova's ecosystem."""
    
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
        self._initialized = False
        
    async def initialize(self):
        """Initialize connections."""
        if not self._initialized:
            try:
                # Initialize vector store if available
                if self.vector_store and hasattr(self.vector_store, 'connect'):
                    await self.vector_store.connect()
                    logger.debug("Vector store initialized")
                    
                # Initialize store if available
                if self.store and hasattr(self.store, 'connect'):
                    await self.store.connect()
                    logger.debug("Store initialized")
                    
                self._initialized = True
                logger.debug("BeliefAgent initialization complete")
            except Exception as e:
                logger.error(f"Failed to initialize BeliefAgent: {str(e)}")
                raise
        
    async def analyze_beliefs(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> BeliefResult:
        """Analyze beliefs with domain awareness."""
        try:
            # Ensure initialized
            if not self._initialized:
                await self.initialize()
                
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
                    template="belief_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_analysis(content)
                
            # Extract and validate components
            beliefs = self._extract_beliefs(analysis)
            evidence = self._extract_evidence(analysis)
            
            # Calculate confidence
            confidence = self._calculate_confidence(beliefs, evidence)
            
            return BeliefResult(
                beliefs=beliefs,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "content_type": content.get("type", "text"),
                    "source": content.get("source", "unknown")
                },
                evidence=evidence
            )
            
        except Exception as e:
            logger.error(f"Belief analysis error: {str(e)}")
            return BeliefResult(
                beliefs=[],
                confidence=0.0,
                metadata={"error": str(e)},
                evidence={"error": str(e)}
            )
            
    def _basic_analysis(self, content: Dict[str, Any]) -> Dict:
        """Basic belief analysis without LLM."""
        beliefs = []
        evidence = {}
        
        # Basic belief extraction from text
        text = str(content.get("content", "")).lower()
        
        # Basic belief indicators and their confidences
        belief_indicators = {
            "i think": 0.6,
            "i believe": 0.7,
            "i know": 0.8,
            "i understand": 0.7,
            "i feel": 0.5,
            "must be": 0.6,
            "should be": 0.5,
            "could be": 0.4
        }
        
        # Check for belief indicators
        for indicator, base_confidence in belief_indicators.items():
            if indicator in text:
                # Extract the belief statement
                start_idx = text.find(indicator) + len(indicator)
                end_idx = text.find(".", start_idx)
                if end_idx == -1:
                    end_idx = len(text)
                    
                belief_statement = text[start_idx:end_idx].strip()
                if belief_statement:
                    beliefs.append({
                        "statement": belief_statement,
                        "type": "inferred_belief",
                        "confidence": base_confidence,
                        "source": "text_analysis"
                    })
                    
        # Basic evidence collection
        if "context" in content:
            evidence["context"] = content["context"]
        if "source" in content:
            evidence["source"] = content["source"]
            
        return {
            "beliefs": beliefs,
            "evidence": evidence
        }
        
    def _extract_beliefs(self, analysis: Dict) -> List[Dict]:
        """Extract and validate beliefs."""
        beliefs = analysis.get("beliefs", [])
        valid_beliefs = []
        
        for belief in beliefs:
            if isinstance(belief, dict) and "statement" in belief:
                valid_belief = {
                    "statement": str(belief["statement"]),
                    "type": str(belief.get("type", "belief")),
                    "confidence": float(belief.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in belief:
                    valid_belief["description"] = str(belief["description"])
                if "source" in belief:
                    valid_belief["source"] = str(belief["source"])
                if "domain_relevance" in belief:
                    valid_belief["domain_relevance"] = float(belief["domain_relevance"])
                if "certainty" in belief:
                    valid_belief["certainty"] = float(belief["certainty"])
                if "impact" in belief:
                    valid_belief["impact"] = float(belief["impact"])
                    
                valid_beliefs.append(valid_belief)
                
        return valid_beliefs
        
    def _extract_evidence(self, analysis: Dict) -> Dict:
        """Extract and validate evidence."""
        evidence = analysis.get("evidence", {})
        valid_evidence = {}
        
        if isinstance(evidence, dict):
            # Extract relevant evidence fields
            if "sources" in evidence:
                valid_evidence["sources"] = [
                    str(s) for s in evidence["sources"]
                    if isinstance(s, (str, int, float, bool))
                ]
                
            if "context" in evidence:
                valid_evidence["context"] = str(evidence["context"])
                
            if "supporting_facts" in evidence:
                valid_evidence["supporting_facts"] = [
                    str(f) for f in evidence["supporting_facts"]
                    if isinstance(f, str)
                ]
                
            if "contradictions" in evidence:
                valid_evidence["contradictions"] = [
                    str(c) for c in evidence["contradictions"]
                    if isinstance(c, str)
                ]
                
            if "domain_factors" in evidence:
                valid_evidence["domain_factors"] = {
                    str(k): str(v)
                    for k, v in evidence["domain_factors"].items()
                    if isinstance(k, str) and isinstance(v, (str, int, float, bool))
                }
                
        return valid_evidence
        
    def _calculate_confidence(
        self,
        beliefs: List[Dict],
        evidence: Dict
    ) -> float:
        """Calculate overall belief analysis confidence."""
        if not beliefs:
            return 0.0
            
        # Base confidence from belief confidences
        belief_conf = sum(b.get("confidence", 0.5) for b in beliefs) / len(beliefs)
        
        # Evidence confidence factors
        evidence_conf = 0.0
        evidence_weight = 0.0
        
        # Supporting facts boost confidence
        if "supporting_facts" in evidence:
            fact_count = len(evidence["supporting_facts"])
            fact_conf = min(1.0, fact_count * 0.1)  # Cap at 1.0
            evidence_conf += fact_conf
            evidence_weight += 1
            
        # Contradictions reduce confidence
        if "contradictions" in evidence:
            contra_count = len(evidence["contradictions"])
            contra_penalty = max(0.0, 1.0 - (contra_count * 0.2))  # Floor at 0.0
            evidence_conf += contra_penalty
            evidence_weight += 1
            
        # Sources boost confidence
        if "sources" in evidence:
            source_count = len(evidence["sources"])
            source_conf = min(1.0, source_count * 0.15)  # Cap at 1.0
            evidence_conf += source_conf
            evidence_weight += 1
            
        # Domain factors influence confidence
        if "domain_factors" in evidence:
            domain_conf = min(1.0, len(evidence["domain_factors"]) * 0.1)
            evidence_conf += domain_conf
            evidence_weight += 1
            
        # Calculate final evidence confidence
        if evidence_weight > 0:
            evidence_conf = evidence_conf / evidence_weight
            
            # Weighted combination of belief and evidence confidence
            return (0.6 * belief_conf) + (0.4 * evidence_conf)
        else:
            return belief_conf
