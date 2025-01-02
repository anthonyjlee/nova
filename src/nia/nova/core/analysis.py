"""Nova's core analysis functionality."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalysisResult:
    """Container for analysis results."""
    
    def __init__(
        self,
        is_valid: bool,
        analysis: Dict,
        insights: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.analysis = analysis
        self.insights = insights
        self.confidence = confidence
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class AnalysisAgent:
    """Core analysis functionality for Nova's ecosystem."""
    
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
        
    async def analyze_content(
        self,
        content: Dict[str, Any],
        analysis_type: str,
        metadata: Optional[Dict] = None
    ) -> AnalysisResult:
        """Analyze content with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar analyses if vector store available
            similar_analyses = []
            if self.vector_store:
                similar_analyses = await self._get_similar_analyses(
                    content,
                    analysis_type
                )
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "content": content,
                        "analysis_type": analysis_type,
                        "metadata": metadata,
                        "similar_analyses": similar_analyses
                    },
                    template="content_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_analysis(
                    content,
                    analysis_type,
                    similar_analyses
                )
                
            # Extract and validate components
            analysis_result = self._extract_analysis(analysis)
            insights = self._extract_insights(analysis)
            issues = self._extract_issues(analysis)
            
            # Calculate confidence and validity
            confidence = self._calculate_confidence(analysis_result, insights, issues)
            is_valid = self._determine_validity(analysis_result, insights, issues, confidence)
            
            return AnalysisResult(
                is_valid=is_valid,
                analysis=analysis_result,
                insights=insights,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "analysis_type": analysis_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return AnalysisResult(
                is_valid=False,
                analysis={},
                insights=[],
                confidence=0.0,
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_similar_analyses(
        self,
        content: Dict[str, Any],
        analysis_type: str
    ) -> List[Dict]:
        """Get similar analyses from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "analysis",
                        "analysis_type": analysis_type
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar analyses: {str(e)}")
        return []
            
    def _basic_analysis(
        self,
        content: Dict[str, Any],
        analysis_type: str,
        similar_analyses: List[Dict]
    ) -> Dict:
        """Basic content analysis without LLM."""
        analysis = {}
        insights = []
        issues = []
        
        # Basic analysis rules
        analysis_rules = {
            "text": {
                "has_content": 0.8,
                "has_structure": 0.7,
                "has_metadata": 0.6
            },
            "data": {
                "has_fields": 0.8,
                "has_values": 0.7,
                "has_types": 0.7
            },
            "code": {
                "has_syntax": 0.8,
                "has_structure": 0.7,
                "has_patterns": 0.6
            }
        }
        
        # Check analysis type rules
        if analysis_type in analysis_rules:
            type_rules = analysis_rules[analysis_type]
            
            # Extract basic analysis structure
            if isinstance(content, dict):
                analysis = {
                    "type": analysis_type,
                    "components": {},
                    "patterns": {},
                    "metadata": {}
                }
                
                # Add components from content
                for key, value in content.items():
                    if isinstance(value, dict):
                        analysis["components"][key] = {
                            "type": value.get("type", "unknown"),
                            "importance": value.get("importance", 0.5),
                            "patterns": value.get("patterns", [])
                        }
                        
                # Add basic insights
                for rule, confidence in type_rules.items():
                    if self._check_rule(rule, content):
                        insights.append({
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
                
            # Add similar analyses as reference
            if similar_analyses:
                analysis["similar_analyses"] = [
                    {
                        "content": s.get("content", {}).get("content", ""),
                        "similarity": s.get("similarity", 0.0),
                        "timestamp": s.get("timestamp", "")
                    }
                    for s in similar_analyses
                ]
                
        return {
            "analysis": analysis,
            "insights": insights,
            "issues": issues
        }
        
    def _check_rule(self, rule: str, content: Dict[str, Any]) -> bool:
        """Check if content satisfies an analysis rule."""
        if rule == "has_content":
            return bool(content.get("content", ""))
        elif rule == "has_structure":
            return bool(content.get("structure", {}))
        elif rule == "has_metadata":
            return bool(content.get("metadata", {}))
        elif rule == "has_fields":
            return bool(content.get("fields", {}))
        elif rule == "has_values":
            return any(
                "value" in f for f in content.get("fields", {}).values()
            )
        elif rule == "has_types":
            return any(
                "type" in f for f in content.get("fields", {}).values()
            )
        elif rule == "has_syntax":
            return bool(content.get("syntax", {}))
        elif rule == "has_patterns":
            return bool(content.get("patterns", []))
        return False
        
    def _extract_analysis(self, analysis: Dict) -> Dict:
        """Extract and validate analysis result."""
        result = analysis.get("analysis", {})
        valid_analysis = {}
        
        if isinstance(result, dict):
            # Extract core analysis fields
            valid_analysis["type"] = str(result.get("type", "unknown"))
            valid_analysis["components"] = {}
            
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
                        if "patterns" in component:
                            valid_component["patterns"] = component["patterns"]
                        if "metadata" in component:
                            valid_component["metadata"] = component["metadata"]
                            
                        valid_analysis["components"][str(name)] = valid_component
                        
            # Add optional analysis sections
            if "patterns" in result:
                valid_analysis["patterns"] = result["patterns"]
            if "metadata" in result:
                valid_analysis["metadata"] = result["metadata"]
            if "similar_analyses" in result:
                valid_analysis["similar_analyses"] = result["similar_analyses"]
                
        return valid_analysis
        
    def _extract_insights(self, analysis: Dict) -> List[Dict]:
        """Extract and validate analysis insights."""
        insights = analysis.get("insights", [])
        valid_insights = []
        
        for insight in insights:
            if isinstance(insight, dict) and "type" in insight:
                valid_insight = {
                    "type": str(insight["type"]),
                    "description": str(insight.get("description", "Unknown insight")),
                    "confidence": float(insight.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "details" in insight:
                    valid_insight["details"] = str(insight["details"])
                if "domain_relevance" in insight:
                    valid_insight["domain_relevance"] = float(insight["domain_relevance"])
                if "importance" in insight:
                    valid_insight["importance"] = float(insight["importance"])
                if "patterns" in insight:
                    valid_insight["patterns"] = [str(p) for p in insight["patterns"]]
                    
                valid_insights.append(valid_insight)
                
        return valid_insights
        
    def _extract_issues(self, analysis: Dict) -> List[Dict]:
        """Extract and validate analysis issues."""
        issues = analysis.get("issues", [])
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
                if "related_patterns" in issue:
                    valid_issue["related_patterns"] = [str(p) for p in issue["related_patterns"]]
                    
                valid_issues.append(valid_issue)
                
        return valid_issues
        
    def _calculate_confidence(
        self,
        analysis: Dict,
        insights: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall analysis confidence."""
        if not analysis or not insights:
            return 0.0
            
        # Analysis completeness confidence
        analysis_conf = 0.0
        if analysis.get("components"):
            component_count = len(analysis["components"])
            component_conf = min(1.0, component_count * 0.1)  # Cap at 1.0
            analysis_conf += component_conf
            
        if analysis.get("patterns"):
            pattern_count = len(analysis["patterns"])
            pattern_conf = min(1.0, pattern_count * 0.1)
            analysis_conf += pattern_conf
            
        analysis_conf = analysis_conf / 2 if analysis_conf > 0 else 0.0
        
        # Insight confidence
        insight_conf = sum(i.get("confidence", 0.5) for i in insights) / len(insights)
        
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
        base_conf = (analysis_conf + insight_conf) / 2
        return max(0.0, base_conf - issue_impact)
        
    def _determine_validity(
        self,
        analysis: Dict,
        insights: List[Dict],
        issues: List[Dict],
        confidence: float
    ) -> bool:
        """Determine overall analysis validity."""
        if not analysis or not insights:
            return False
            
        # Check for critical issues
        has_critical_issues = any(
            i.get("severity") == "high"
            for i in issues
        )
        if has_critical_issues:
            return False
            
        # Check insight confidence
        high_confidence_insights = sum(
            1 for i in insights
            if i.get("confidence", 0.0) > 0.7
        )
        insight_ratio = high_confidence_insights / len(insights)
        
        # Check analysis completeness
        has_components = bool(analysis.get("components"))
        has_patterns = bool(analysis.get("patterns"))
        
        # Consider all factors
        return (
            insight_ratio >= 0.7 and
            confidence >= 0.6 and
            has_components and
            has_patterns
        )
