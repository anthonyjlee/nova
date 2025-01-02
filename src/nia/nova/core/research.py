"""Nova's core research analysis functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ResearchResult:
    """Container for research analysis results."""
    
    def __init__(
        self,
        findings: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        sources: Optional[Dict] = None
    ):
        self.findings = findings
        self.confidence = confidence
        self.metadata = metadata or {}
        self.sources = sources or {}
        self.timestamp = datetime.now().isoformat()

class ResearchAgent:
    """Core research analysis functionality for Nova's ecosystem."""
    
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
        
    async def analyze_research(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> ResearchResult:
        """Analyze research with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar memories if vector store available
            similar_memories = []
            if self.vector_store:
                similar_memories = await self._get_similar_memories(content)
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "content": content,
                        "metadata": metadata,
                        "similar_memories": similar_memories
                    },
                    template="research_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_analysis(content, similar_memories)
                
            # Extract and validate components
            findings = self._extract_findings(analysis)
            sources = self._extract_sources(analysis)
            
            # Calculate confidence
            confidence = self._calculate_confidence(findings, sources)
            
            return ResearchResult(
                findings=findings,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "content_type": content.get("type", "text"),
                    "source": content.get("source", "unknown")
                },
                sources=sources
            )
            
        except Exception as e:
            logger.error(f"Research analysis error: {str(e)}")
            return ResearchResult(
                findings=[],
                confidence=0.0,
                metadata={"error": str(e)},
                sources={"error": str(e)}
            )
            
    async def _get_similar_memories(self, content: Dict[str, Any]) -> List[Dict]:
        """Get similar memories from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={"domain": self.domain}
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar memories: {str(e)}")
        return []
            
    def _basic_analysis(
        self,
        content: Dict[str, Any],
        similar_memories: List[Dict]
    ) -> Dict:
        """Basic research analysis without LLM."""
        findings = []
        sources = {}
        
        # Basic finding extraction from text
        text = str(content.get("content", "")).lower()
        
        # Basic finding indicators and their confidences
        finding_indicators = {
            "found that": 0.8,
            "discovered": 0.8,
            "indicates": 0.7,
            "suggests": 0.6,
            "shows": 0.7,
            "reveals": 0.7,
            "demonstrates": 0.8,
            "concludes": 0.8
        }
        
        # Check for finding indicators
        for indicator, base_confidence in finding_indicators.items():
            if indicator in text:
                # Extract the finding statement
                start_idx = text.find(indicator) + len(indicator)
                end_idx = text.find(".", start_idx)
                if end_idx == -1:
                    end_idx = len(text)
                    
                finding_statement = text[start_idx:end_idx].strip()
                if finding_statement:
                    findings.append({
                        "statement": finding_statement,
                        "type": "inferred_finding",
                        "confidence": base_confidence,
                        "source": "text_analysis"
                    })
                    
        # Add similar memories as sources
        if similar_memories:
            sources["similar_memories"] = [
                {
                    "content": m.get("content", {}).get("content", ""),
                    "similarity": m.get("similarity", 0.0),
                    "timestamp": m.get("timestamp", "")
                }
                for m in similar_memories
            ]
                
        return {
            "findings": findings,
            "sources": sources
        }
        
    def _extract_findings(self, analysis: Dict) -> List[Dict]:
        """Extract and validate findings."""
        findings = analysis.get("findings", [])
        valid_findings = []
        
        for finding in findings:
            if isinstance(finding, dict) and "statement" in finding:
                valid_finding = {
                    "statement": str(finding["statement"]),
                    "type": str(finding.get("type", "finding")),
                    "confidence": float(finding.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in finding:
                    valid_finding["description"] = str(finding["description"])
                if "source" in finding:
                    valid_finding["source"] = str(finding["source"])
                if "domain_relevance" in finding:
                    valid_finding["domain_relevance"] = float(finding["domain_relevance"])
                if "impact" in finding:
                    valid_finding["impact"] = float(finding["impact"])
                if "novelty" in finding:
                    valid_finding["novelty"] = float(finding["novelty"])
                if "status" in finding:
                    valid_finding["status"] = str(finding["status"])
                    
                valid_findings.append(valid_finding)
                
        return valid_findings
        
    def _extract_sources(self, analysis: Dict) -> Dict:
        """Extract and validate sources."""
        sources = analysis.get("sources", {})
        valid_sources = {}
        
        if isinstance(sources, dict):
            # Extract relevant source fields
            if "similar_memories" in sources:
                valid_sources["similar_memories"] = [
                    {
                        "content": str(m.get("content", "")),
                        "similarity": float(m.get("similarity", 0.0)),
                        "timestamp": str(m.get("timestamp", ""))
                    }
                    for m in sources["similar_memories"]
                    if isinstance(m, dict)
                ]
                
            if "references" in sources:
                valid_sources["references"] = [
                    str(r) for r in sources["references"]
                    if isinstance(r, str)
                ]
                
            if "citations" in sources:
                valid_sources["citations"] = [
                    str(c) for c in sources["citations"]
                    if isinstance(c, str)
                ]
                
            if "domain_factors" in sources:
                valid_sources["domain_factors"] = {
                    str(k): str(v)
                    for k, v in sources["domain_factors"].items()
                    if isinstance(k, str) and isinstance(v, (str, int, float, bool))
                }
                
            if "quality_factors" in sources:
                valid_sources["quality_factors"] = [
                    {
                        "factor": str(f.get("factor", "")),
                        "weight": float(f.get("weight", 0.5))
                    }
                    for f in sources.get("quality_factors", [])
                    if isinstance(f, dict)
                ]
                
        return valid_sources
        
    def _calculate_confidence(
        self,
        findings: List[Dict],
        sources: Dict
    ) -> float:
        """Calculate overall research analysis confidence."""
        if not findings:
            return 0.0
            
        # Base confidence from finding confidences
        finding_conf = sum(f.get("confidence", 0.5) for f in findings) / len(findings)
        
        # Source confidence factors
        source_conf = 0.0
        source_weight = 0.0
        
        # Similar memories boost confidence
        if "similar_memories" in sources:
            mem_count = len(sources["similar_memories"])
            mem_conf = min(1.0, mem_count * 0.2)  # Cap at 1.0
            source_conf += mem_conf
            source_weight += 1
            
        # References boost confidence
        if "references" in sources:
            ref_count = len(sources["references"])
            ref_conf = min(1.0, ref_count * 0.15)  # Cap at 1.0
            source_conf += ref_conf
            source_weight += 1
            
        # Citations boost confidence
        if "citations" in sources:
            cite_count = len(sources["citations"])
            cite_conf = min(1.0, cite_count * 0.1)  # Cap at 1.0
            source_conf += cite_conf
            source_weight += 1
            
        # Domain factors influence confidence
        if "domain_factors" in sources:
            domain_conf = min(1.0, len(sources["domain_factors"]) * 0.1)
            source_conf += domain_conf
            source_weight += 1
            
        # Quality factors boost confidence
        if "quality_factors" in sources:
            quality_conf = min(1.0, len(sources["quality_factors"]) * 0.15)
            source_conf += quality_conf
            source_weight += 1
            
        # Calculate final source confidence
        if source_weight > 0:
            source_conf = source_conf / source_weight
            
            # Weighted combination of finding and source confidence
            return (0.6 * finding_conf) + (0.4 * source_conf)
        else:
            return finding_conf
