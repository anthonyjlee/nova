"""Nova's core reflection analysis functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ReflectionResult:
    """Container for reflection analysis results."""
    
    def __init__(
        self,
        insights: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        patterns: Optional[Dict] = None
    ):
        self.insights = insights
        self.confidence = confidence
        self.metadata = metadata or {}
        self.patterns = patterns or {}
        self.timestamp = datetime.now().isoformat()

class ReflectionAgent:
    """Core reflection analysis functionality for Nova's ecosystem."""
    
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
        
    async def analyze_reflection(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> ReflectionResult:
        """Analyze reflection with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar reflections if vector store available
            similar_reflections = []
            if self.vector_store:
                similar_reflections = await self._get_similar_reflections(content)
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "content": content,
                        "metadata": metadata,
                        "similar_reflections": similar_reflections
                    },
                    template="reflection_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_analysis(content, similar_reflections)
                
            # Extract and validate components
            insights = self._extract_insights(analysis)
            patterns = self._extract_patterns(analysis)
            
            # Calculate confidence
            confidence = self._calculate_confidence(insights, patterns)
            
            return ReflectionResult(
                insights=insights,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "content_type": content.get("type", "text"),
                    "source": content.get("source", "unknown")
                },
                patterns=patterns
            )
            
        except Exception as e:
            logger.error(f"Reflection analysis error: {str(e)}")
            return ReflectionResult(
                insights=[],
                confidence=0.0,
                metadata={"error": str(e)},
                patterns={"error": str(e)}
            )
            
    async def _get_similar_reflections(self, content: Dict[str, Any]) -> List[Dict]:
        """Get similar reflections from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "reflection"
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar reflections: {str(e)}")
        return []
            
    def _basic_analysis(
        self,
        content: Dict[str, Any],
        similar_reflections: List[Dict]
    ) -> Dict:
        """Basic reflection analysis without LLM."""
        insights = []
        patterns = {}
        
        # Basic insight extraction from text
        text = str(content.get("content", "")).lower()
        
        # Basic insight indicators and their confidences
        insight_indicators = {
            "realized": 0.8,
            "noticed": 0.7,
            "observed": 0.7,
            "learned": 0.8,
            "understood": 0.8,
            "recognized": 0.7,
            "discovered": 0.8,
            "concluded": 0.7
        }
        
        # Check for insight indicators
        for indicator, base_confidence in insight_indicators.items():
            if indicator in text:
                # Extract the insight statement
                start_idx = text.find(indicator) + len(indicator)
                end_idx = text.find(".", start_idx)
                if end_idx == -1:
                    end_idx = len(text)
                    
                insight_statement = text[start_idx:end_idx].strip()
                if insight_statement:
                    insights.append({
                        "statement": insight_statement,
                        "type": "inferred_insight",
                        "confidence": base_confidence,
                        "source": "text_analysis"
                    })
                    
        # Add similar reflections as patterns
        if similar_reflections:
            patterns["similar_reflections"] = [
                {
                    "content": m.get("content", {}).get("content", ""),
                    "similarity": m.get("similarity", 0.0),
                    "timestamp": m.get("timestamp", "")
                }
                for m in similar_reflections
            ]
                
        return {
            "insights": insights,
            "patterns": patterns
        }
        
    def _extract_insights(self, analysis: Dict) -> List[Dict]:
        """Extract and validate insights."""
        insights = analysis.get("insights", [])
        valid_insights = []
        
        for insight in insights:
            if isinstance(insight, dict) and "statement" in insight:
                valid_insight = {
                    "statement": str(insight["statement"]),
                    "type": str(insight.get("type", "insight")),
                    "confidence": float(insight.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in insight:
                    valid_insight["description"] = str(insight["description"])
                if "source" in insight:
                    valid_insight["source"] = str(insight["source"])
                if "domain_relevance" in insight:
                    valid_insight["domain_relevance"] = float(insight["domain_relevance"])
                if "impact" in insight:
                    valid_insight["impact"] = float(insight["impact"])
                if "novelty" in insight:
                    valid_insight["novelty"] = float(insight["novelty"])
                if "status" in insight:
                    valid_insight["status"] = str(insight["status"])
                    
                valid_insights.append(valid_insight)
                
        return valid_insights
        
    def _extract_patterns(self, analysis: Dict) -> Dict:
        """Extract and validate patterns."""
        patterns = analysis.get("patterns", {})
        valid_patterns = {}
        
        if isinstance(patterns, dict):
            # Extract relevant pattern fields
            if "similar_reflections" in patterns:
                valid_patterns["similar_reflections"] = [
                    {
                        "content": str(r.get("content", "")),
                        "similarity": float(r.get("similarity", 0.0)),
                        "timestamp": str(r.get("timestamp", ""))
                    }
                    for r in patterns["similar_reflections"]
                    if isinstance(r, dict)
                ]
                
            if "recurring_themes" in patterns:
                valid_patterns["recurring_themes"] = [
                    str(t) for t in patterns["recurring_themes"]
                    if isinstance(t, str)
                ]
                
            if "connections" in patterns:
                valid_patterns["connections"] = [
                    str(c) for c in patterns["connections"]
                    if isinstance(c, str)
                ]
                
            if "domain_factors" in patterns:
                valid_patterns["domain_factors"] = {
                    str(k): str(v)
                    for k, v in patterns["domain_factors"].items()
                    if isinstance(k, str) and isinstance(v, (str, int, float, bool))
                }
                
            if "learning_factors" in patterns:
                valid_patterns["learning_factors"] = [
                    {
                        "factor": str(f.get("factor", "")),
                        "weight": float(f.get("weight", 0.5))
                    }
                    for f in patterns.get("learning_factors", [])
                    if isinstance(f, dict)
                ]
                
        return valid_patterns
        
    def _calculate_confidence(
        self,
        insights: List[Dict],
        patterns: Dict
    ) -> float:
        """Calculate overall reflection analysis confidence."""
        if not insights:
            return 0.0
            
        # Base confidence from insight confidences
        insight_conf = sum(i.get("confidence", 0.5) for i in insights) / len(insights)
        
        # Pattern confidence factors
        pattern_conf = 0.0
        pattern_weight = 0.0
        
        # Similar reflections boost confidence
        if "similar_reflections" in patterns:
            ref_count = len(patterns["similar_reflections"])
            ref_conf = min(1.0, ref_count * 0.2)  # Cap at 1.0
            pattern_conf += ref_conf
            pattern_weight += 1
            
        # Recurring themes boost confidence
        if "recurring_themes" in patterns:
            theme_count = len(patterns["recurring_themes"])
            theme_conf = min(1.0, theme_count * 0.15)  # Cap at 1.0
            pattern_conf += theme_conf
            pattern_weight += 1
            
        # Connections boost confidence
        if "connections" in patterns:
            conn_count = len(patterns["connections"])
            conn_conf = min(1.0, conn_count * 0.1)  # Cap at 1.0
            pattern_conf += conn_conf
            pattern_weight += 1
            
        # Domain factors influence confidence
        if "domain_factors" in patterns:
            domain_conf = min(1.0, len(patterns["domain_factors"]) * 0.1)
            pattern_conf += domain_conf
            pattern_weight += 1
            
        # Learning factors boost confidence
        if "learning_factors" in patterns:
            learn_conf = min(1.0, len(patterns["learning_factors"]) * 0.15)
            pattern_conf += learn_conf
            pattern_weight += 1
            
        # Calculate final pattern confidence
        if pattern_weight > 0:
            pattern_conf = pattern_conf / pattern_weight
            
            # Weighted combination of insight and pattern confidence
            return (0.6 * insight_conf) + (0.4 * pattern_conf)
        else:
            return insight_conf
