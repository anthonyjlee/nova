"""Nova's core synthesis functionality."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class SynthesisResult:
    """Container for synthesis results."""
    
    def __init__(
        self,
        is_valid: bool,
        synthesis: Dict,
        conclusions: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.synthesis = synthesis
        self.conclusions = conclusions
        self.confidence = confidence
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class SynthesisAgent:
    """Core synthesis functionality for Nova's ecosystem."""
    
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
        
    async def synthesize_content(
        self,
        content: Dict[str, Any],
        synthesis_type: str,
        metadata: Optional[Dict] = None
    ) -> SynthesisResult:
        """Synthesize content with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar syntheses if vector store available
            similar_syntheses = []
            if self.vector_store:
                similar_syntheses = await self._get_similar_syntheses(
                    content,
                    synthesis_type
                )
            
            # Analyze with LLM if available
            if self.llm:
                synthesis = await self.llm.analyze(
                    {
                        "content": content,
                        "synthesis_type": synthesis_type,
                        "metadata": metadata,
                        "similar_syntheses": similar_syntheses
                    },
                    template="content_synthesis",
                    max_tokens=1000
                )
            else:
                synthesis = self._basic_synthesis(
                    content,
                    synthesis_type,
                    similar_syntheses
                )
                
            # Extract and validate components
            synthesis_result = self._extract_synthesis(synthesis)
            conclusions = self._extract_conclusions(synthesis)
            issues = self._extract_issues(synthesis)
            
            # Calculate confidence and validity
            confidence = self._calculate_confidence(synthesis_result, conclusions, issues)
            is_valid = self._determine_validity(synthesis_result, conclusions, issues, confidence)
            
            return SynthesisResult(
                is_valid=is_valid,
                synthesis=synthesis_result,
                conclusions=conclusions,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "synthesis_type": synthesis_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Synthesis error: {str(e)}")
            return SynthesisResult(
                is_valid=False,
                synthesis={},
                conclusions=[],
                confidence=0.0,
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_similar_syntheses(
        self,
        content: Dict[str, Any],
        synthesis_type: str
    ) -> List[Dict]:
        """Get similar syntheses from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "synthesis",
                        "synthesis_type": synthesis_type
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar syntheses: {str(e)}")
        return []
            
    def _basic_synthesis(
        self,
        content: Dict[str, Any],
        synthesis_type: str,
        similar_syntheses: List[Dict]
    ) -> Dict:
        """Basic content synthesis without LLM."""
        synthesis = {}
        conclusions = []
        issues = []
        
        # Basic synthesis rules
        synthesis_rules = {
            "analysis": {
                "has_insights": 0.8,
                "has_patterns": 0.7,
                "has_context": 0.6
            },
            "research": {
                "has_findings": 0.8,
                "has_evidence": 0.7,
                "has_sources": 0.7
            },
            "dialogue": {
                "has_themes": 0.8,
                "has_flow": 0.7,
                "has_context": 0.6
            }
        }
        
        # Check synthesis type rules
        if synthesis_type in synthesis_rules:
            type_rules = synthesis_rules[synthesis_type]
            
            # Extract basic synthesis structure
            if isinstance(content, dict):
                synthesis = {
                    "type": synthesis_type,
                    "components": {},
                    "themes": {},
                    "metadata": {}
                }
                
                # Add components from content
                for key, value in content.items():
                    if isinstance(value, dict):
                        synthesis["components"][key] = {
                            "type": value.get("type", "unknown"),
                            "importance": value.get("importance", 0.5),
                            "themes": value.get("themes", [])
                        }
                        
                # Add basic conclusions
                for rule, confidence in type_rules.items():
                    if self._check_rule(rule, content):
                        conclusions.append({
                            "type": rule,
                            "description": f"Content satisfies {rule}",
                            "confidence": confidence
                        })
                    else:
                        issues.append({
                            "type": f"missing_{rule}",
                            "severity": "medium",
                            "description": f"Content is missing {rule}"
                        })
                        
            else:
                issues.append({
                    "type": "invalid_format",
                    "severity": "high",
                    "description": "Content must be a dictionary"
                })
                
            # Add similar syntheses as reference
            if similar_syntheses:
                synthesis["similar_syntheses"] = [
                    {
                        "content": s.get("content", {}).get("content", ""),
                        "similarity": s.get("similarity", 0.0),
                        "timestamp": s.get("timestamp", "")
                    }
                    for s in similar_syntheses
                ]
                
        return {
            "synthesis": synthesis,
            "conclusions": conclusions,
            "issues": issues
        }
        
    def _check_rule(self, rule: str, content: Dict[str, Any]) -> bool:
        """Check if content satisfies a synthesis rule."""
        if rule == "has_insights":
            return bool(content.get("insights", []))
        elif rule == "has_patterns":
            return bool(content.get("patterns", []))
        elif rule == "has_context":
            return bool(content.get("context", {}))
        elif rule == "has_findings":
            return bool(content.get("findings", []))
        elif rule == "has_evidence":
            return bool(content.get("evidence", []))
        elif rule == "has_sources":
            return bool(content.get("sources", []))
        elif rule == "has_themes":
            return bool(content.get("themes", []))
        elif rule == "has_flow":
            return bool(content.get("flow", {}))
        return False
        
    def _extract_synthesis(self, synthesis: Dict) -> Dict:
        """Extract and validate synthesis result."""
        result = synthesis.get("synthesis", {})
        valid_synthesis = {}
        
        if isinstance(result, dict):
            # Extract core synthesis fields
            valid_synthesis["type"] = str(result.get("type", "unknown"))
            valid_synthesis["components"] = {}
            
            # Extract and validate components
            components = result.get("components", {})
            if isinstance(components, dict):
                for name, component in components.items():
                    if isinstance(component, dict):
                        valid_component = {
                            "type": str(component.get("type", "unknown")),
                            "importance": float(component.get("importance", 0.5))
                        }
                        
                        # Add optional component attributes
                        if "description" in component:
                            valid_component["description"] = str(component["description"])
                        if "themes" in component:
                            valid_component["themes"] = component["themes"]
                        if "metadata" in component:
                            valid_component["metadata"] = component["metadata"]
                            
                        valid_synthesis["components"][str(name)] = valid_component
                        
            # Add optional synthesis sections
            if "themes" in result:
                valid_synthesis["themes"] = result["themes"]
            if "metadata" in result:
                valid_synthesis["metadata"] = result["metadata"]
            if "similar_syntheses" in result:
                valid_synthesis["similar_syntheses"] = result["similar_syntheses"]
                
        return valid_synthesis
        
    def _extract_conclusions(self, synthesis: Dict) -> List[Dict]:
        """Extract and validate synthesis conclusions."""
        conclusions = synthesis.get("conclusions", [])
        valid_conclusions = []
        
        for conclusion in conclusions:
            if isinstance(conclusion, dict) and "type" in conclusion:
                valid_conclusion = {
                    "type": str(conclusion["type"]),
                    "description": str(conclusion.get("description", "Unknown conclusion")),
                    "confidence": float(conclusion.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "details" in conclusion:
                    valid_conclusion["details"] = str(conclusion["details"])
                if "domain_relevance" in conclusion:
                    valid_conclusion["domain_relevance"] = float(conclusion["domain_relevance"])
                if "importance" in conclusion:
                    valid_conclusion["importance"] = float(conclusion["importance"])
                if "themes" in conclusion:
                    valid_conclusion["themes"] = [str(t) for t in conclusion["themes"]]
                    
                valid_conclusions.append(valid_conclusion)
                
        return valid_conclusions
        
    def _extract_issues(self, synthesis: Dict) -> List[Dict]:
        """Extract and validate synthesis issues."""
        issues = synthesis.get("issues", [])
        valid_issues = []
        
        for issue in issues:
            if isinstance(issue, dict) and "type" in issue:
                valid_issue = {
                    "type": str(issue["type"]),
                    "severity": str(issue.get("severity", "medium")),
                    "description": str(issue.get("description", "Unknown issue"))
                }
                
                # Add optional fields
                if "details" in issue:
                    valid_issue["details"] = str(issue["details"])
                if "domain_impact" in issue:
                    valid_issue["domain_impact"] = float(issue["domain_impact"])
                if "suggested_fix" in issue:
                    valid_issue["suggested_fix"] = str(issue["suggested_fix"])
                if "related_themes" in issue:
                    valid_issue["related_themes"] = [str(t) for t in issue["related_themes"]]
                    
                valid_issues.append(valid_issue)
                
        return valid_issues
        
    def _calculate_confidence(
        self,
        synthesis: Dict,
        conclusions: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall synthesis confidence."""
        if not synthesis or not conclusions:
            return 0.0
            
        # Synthesis completeness confidence
        synthesis_conf = 0.0
        if synthesis.get("components"):
            component_count = len(synthesis["components"])
            component_conf = min(1.0, component_count * 0.1)  # Cap at 1.0
            synthesis_conf += component_conf
            
        if synthesis.get("themes"):
            theme_count = len(synthesis["themes"])
            theme_conf = min(1.0, theme_count * 0.1)
            synthesis_conf += theme_conf
            
        synthesis_conf = synthesis_conf / 2 if synthesis_conf > 0 else 0.0
        
        # Conclusion confidence
        conclusion_conf = sum(c.get("confidence", 0.5) for c in conclusions) / len(conclusions)
        
        # Issue impact
        issue_impact = 0.0
        if issues:
            severity_weights = {
                "low": 0.1,
                "medium": 0.3,
                "high": 0.5
            }
            
            total_impact = sum(
                severity_weights.get(i.get("severity", "medium"), 0.3)
                for i in issues
            )
            issue_impact = total_impact / len(issues)
            
        # Final confidence calculation
        base_conf = (synthesis_conf + conclusion_conf) / 2
        return max(0.0, base_conf - issue_impact)
        
    def _determine_validity(
        self,
        synthesis: Dict,
        conclusions: List[Dict],
        issues: List[Dict],
        confidence: float
    ) -> bool:
        """Determine overall synthesis validity."""
        if not synthesis or not conclusions:
            return False
            
        # Check for critical issues
        has_critical_issues = any(
            i.get("severity") == "high"
            for i in issues
        )
        if has_critical_issues:
            return False
            
        # Check conclusion confidence
        high_confidence_conclusions = sum(
            1 for c in conclusions
            if c.get("confidence", 0.0) > 0.7
        )
        conclusion_ratio = high_confidence_conclusions / len(conclusions)
        
        # Check synthesis completeness
        has_components = bool(synthesis.get("components"))
        has_themes = bool(synthesis.get("themes"))
        
        # Consider all factors
        return (
            conclusion_ratio >= 0.7 and
            confidence >= 0.6 and
            has_components and
            has_themes
        )
