"""Nova's core analytics functionality."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalyticsResult:
    """Container for analytics results."""
    
    def __init__(
        self,
        is_valid: bool,
        analytics: Dict,
        insights: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.analytics = analytics
        self.insights = insights
        self.confidence = confidence
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class AnalyticsAgent:
    """Core analytics functionality for Nova's ecosystem."""
    
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
        
    async def process_analytics(
        self,
        content: Dict[str, Any],
        analytics_type: str,
        metadata: Optional[Dict] = None
    ) -> AnalyticsResult:
        """Process analytics with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar analytics if vector store available
            similar_analytics = []
            if self.vector_store:
                similar_analytics = await self._get_similar_analytics(
                    content,
                    analytics_type
                )
            
            # Analyze with LLM if available
            if self.llm:
                analytics = await self.llm.analyze(
                    {
                        "content": content,
                        "analytics_type": analytics_type,
                        "metadata": metadata,
                        "similar_analytics": similar_analytics
                    },
                    template="analytics_processing",
                    max_tokens=1000
                )
            else:
                analytics = self._basic_analytics(
                    content,
                    analytics_type,
                    similar_analytics
                )
                
            # Extract and validate components
            analytics_result = self._extract_analytics(analytics)
            insights = self._extract_insights(analytics)
            issues = self._extract_issues(analytics)
            
            # Calculate confidence and validity
            confidence = self._calculate_confidence(analytics_result, insights, issues)
            is_valid = self._determine_validity(analytics_result, insights, issues, confidence)
            
            return AnalyticsResult(
                is_valid=is_valid,
                analytics=analytics_result,
                insights=insights,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "analytics_type": analytics_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Analytics error: {str(e)}")
            return AnalyticsResult(
                is_valid=False,
                analytics={},
                insights=[{
                    "type": "error",
                    "description": str(e),
                    "confidence": 0.8,
                    "recommendations": ["Check system configuration"]
                }],
                confidence=0.8,
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_similar_analytics(
        self,
        content: Dict[str, Any],
        analytics_type: str
    ) -> List[Dict]:
        """Get similar analytics from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search_vectors(
                    content=content["content"],
                    limit=5,
                    layer="analytics",
                    include_metadata=True
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar analytics: {str(e)}")
        return []
            
    def _basic_analytics(
        self,
        content: Dict[str, Any],
        analytics_type: str,
        similar_analytics: List[Dict]
    ) -> Dict:
        """Basic analytics processing without LLM."""
        analytics = {}
        insights = []
        issues = []
        
        # Basic analytics rules
        analytics_rules = {
            "behavioral": {
                "has_patterns": 0.8,
                "has_segments": 0.7,
                "has_trends": 0.6
            },
            "predictive": {
                "has_models": 0.8,
                "has_features": 0.7,
                "has_predictions": 0.7
            },
            "diagnostic": {
                "has_causes": 0.8,
                "has_correlations": 0.7,
                "has_factors": 0.6
            }
        }
        
        # Check analytics type rules
        if analytics_type in analytics_rules:
            type_rules = analytics_rules[analytics_type]
            
            # Extract basic analytics structure
            if isinstance(content, dict):
                analytics = {
                    "type": analytics_type,
                    "analytics": {},
                    "metadata": {}
                }
                
                # Add analytics from content
                for key, value in content.items():
                    if isinstance(value, dict):
                        analytics["analytics"][key] = {
                            "type": value.get("type", "unknown"),
                            "value": value.get("value", 0.0),
                            "confidence": value.get("confidence", 0.0)
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
                
            # Add similar analytics as reference
            if similar_analytics:
                analytics["similar_analytics"] = [
                    {
                        "content": s.get("content", {}).get("content", ""),
                        "similarity": s.get("similarity", 0.0),
                        "timestamp": s.get("timestamp", "")
                    }
                    for s in similar_analytics
                ]
                
        return {
            "analytics": analytics,
            "insights": insights,
            "issues": issues
        }
        
    def _check_rule(self, rule: str, content: Dict[str, Any]) -> bool:
        """Check if content satisfies an analytics rule."""
        if rule == "has_patterns":
            return bool(content.get("patterns", []))
        elif rule == "has_segments":
            return bool(content.get("segments", {}))
        elif rule == "has_trends":
            return bool(content.get("trends", {}))
        elif rule == "has_models":
            return bool(content.get("models", {}))
        elif rule == "has_features":
            return bool(content.get("features", {}))
        elif rule == "has_predictions":
            return bool(content.get("predictions", {}))
        elif rule == "has_causes":
            return bool(content.get("causes", {}))
        elif rule == "has_correlations":
            return bool(content.get("correlations", {}))
        elif rule == "has_factors":
            return bool(content.get("factors", {}))
        return False
        
    def _extract_analytics(self, analytics: Dict) -> Dict:
        """Extract and validate analytics result."""
        result = analytics.get("analytics", {})
        valid_analytics = {}
        
        if isinstance(result, dict):
            # Extract core analytics fields
            valid_analytics["type"] = str(result.get("type", "unknown"))
            valid_analytics["analytics"] = {}
            
            # Extract and validate analytics
            analytics_data = result.get("analytics", {})
            if isinstance(analytics_data, dict):
                for name, analytic in analytics_data.items():
                    if isinstance(analytic, dict):
                        valid_analytic = {
                            "type": str(analytic.get("type", "unknown")),
                            "value": float(analytic.get("value", 0.0)),
                            "confidence": float(analytic.get("confidence", 0.0))
                        }
                        
                        # Add optional analytic attributes
                        if "description" in analytic:
                            valid_analytic["description"] = str(analytic["description"])
                        if "patterns" in analytic:
                            valid_analytic["patterns"] = analytic["patterns"]
                        if "metadata" in analytic:
                            valid_analytic["metadata"] = analytic["metadata"]
                            
                        valid_analytics["analytics"][str(name)] = valid_analytic
                        
            # Add optional analytics sections
            if "metadata" in result:
                valid_analytics["metadata"] = result["metadata"]
            if "similar_analytics" in result:
                valid_analytics["similar_analytics"] = result["similar_analytics"]
                
        return valid_analytics
        
    def _extract_insights(self, analytics: Dict) -> List[Dict]:
        """Extract and validate analytics insights."""
        insights = analytics.get("insights", [])
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
                    valid_insight["patterns"] = insight["patterns"]
                    
                valid_insights.append(valid_insight)
                
        # Ensure at least one insight is returned
        if not valid_insights:
            valid_insights.append({
                "type": "default",
                "description": "Default analysis insight",
                "confidence": 0.8,
                "recommendations": ["Review system data"]
            })
        return valid_insights
        
    def _extract_issues(self, analytics: Dict) -> List[Dict]:
        """Extract and validate analytics issues."""
        issues = analytics.get("issues", [])
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
                if "patterns" in issue:
                    valid_issue["patterns"] = issue["patterns"]
                    
                valid_issues.append(valid_issue)
                
        return valid_issues
        
    def _calculate_confidence(
        self,
        analytics: Dict,
        insights: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall analytics confidence."""
        if not analytics or not insights:
            return 0.8  # Default confidence when no analytics/insights
            
        # Analytics completeness confidence
        analytics_conf = 0.0
        if analytics.get("analytics"):
            analytic_count = len(analytics["analytics"])
            analytic_conf = min(1.0, analytic_count * 0.1)  # Cap at 1.0
            analytics_conf += analytic_conf
            
        if analytics.get("metadata"):
            meta_count = len(analytics["metadata"])
            meta_conf = min(1.0, meta_count * 0.1)
            analytics_conf += meta_conf
            
        analytics_conf = analytics_conf / 2 if analytics_conf > 0 else 0.0
        
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
        base_conf = (analytics_conf + insight_conf) / 2
        return max(0.0, base_conf - issue_impact)
        
    def _determine_validity(
        self,
        analytics: Dict,
        insights: List[Dict],
        issues: List[Dict],
        confidence: float
    ) -> bool:
        """Determine overall analytics validity."""
        if not analytics or not insights:
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
        
        # Check analytics completeness
        has_analytics = bool(analytics.get("analytics"))
        has_metadata = bool(analytics.get("metadata"))
        
        # Consider all factors
        return (
            insight_ratio >= 0.7 and
            confidence >= 0.6 and
            has_analytics and
            has_metadata
        )
