"""Nova's core integration functionality."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class IntegrationResult:
    """Container for integration results."""
    
    def __init__(
        self,
        is_valid: bool,
        integration: Dict,
        insights: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.integration = integration
        self.insights = insights
        self.confidence = confidence
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class IntegrationAgent:
    """Core integration functionality for Nova's ecosystem."""
    
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
        
    async def integrate_content(
        self,
        content: Dict[str, Any],
        integration_type: str,
        metadata: Optional[Dict] = None
    ) -> IntegrationResult:
        """Integrate content with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar integrations if vector store available
            similar_integrations = []
            if self.vector_store:
                similar_integrations = await self._get_similar_integrations(
                    content,
                    integration_type
                )
            
            # Analyze with LLM if available
            if self.llm:
                integration = await self.llm.analyze(
                    {
                        "content": content,
                        "integration_type": integration_type,
                        "metadata": metadata,
                        "similar_integrations": similar_integrations
                    },
                    template="content_integration",
                    max_tokens=1000
                )
            else:
                integration = self._basic_integration(
                    content,
                    integration_type,
                    similar_integrations
                )
                
            # Extract and validate components
            integration_result = self._extract_integration(integration)
            insights = self._extract_insights(integration)
            issues = self._extract_issues(integration)
            
            # Calculate confidence and validity
            confidence = self._calculate_confidence(integration_result, insights, issues)
            is_valid = self._determine_validity(integration_result, insights, issues, confidence)
            
            return IntegrationResult(
                is_valid=is_valid,
                integration=integration_result,
                insights=insights,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "integration_type": integration_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Integration error: {str(e)}")
            return IntegrationResult(
                is_valid=False,
                integration={},
                insights=[],
                confidence=0.0,
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_similar_integrations(
        self,
        content: Dict[str, Any],
        integration_type: str
    ) -> List[Dict]:
        """Get similar integrations from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "integration",
                        "integration_type": integration_type
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar integrations: {str(e)}")
        return []
            
    def _basic_integration(
        self,
        content: Dict[str, Any],
        integration_type: str,
        similar_integrations: List[Dict]
    ) -> Dict:
        """Basic content integration without LLM."""
        integration = {}
        insights = []
        issues = []
        
        # Basic integration rules
        integration_rules = {
            "synthesis": {
                "has_conclusions": 0.8,
                "has_themes": 0.7,
                "has_context": 0.6
            },
            "analysis": {
                "has_insights": 0.8,
                "has_patterns": 0.7,
                "has_evidence": 0.7
            },
            "research": {
                "has_findings": 0.8,
                "has_sources": 0.7,
                "has_validation": 0.6
            }
        }
        
        # Check integration type rules
        if integration_type in integration_rules:
            type_rules = integration_rules[integration_type]
            
            # Extract basic integration structure
            if isinstance(content, dict):
                integration = {
                    "type": integration_type,
                    "components": {},
                    "connections": {},
                    "metadata": {}
                }
                
                # Add components from content
                for key, value in content.items():
                    if isinstance(value, dict):
                        integration["components"][key] = {
                            "type": value.get("type", "unknown"),
                            "importance": value.get("importance", 0.5),
                            "connections": value.get("connections", [])
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
                
            # Add similar integrations as reference
            if similar_integrations:
                integration["similar_integrations"] = [
                    {
                        "content": s.get("content", {}).get("content", ""),
                        "similarity": s.get("similarity", 0.0),
                        "timestamp": s.get("timestamp", "")
                    }
                    for s in similar_integrations
                ]
                
        return {
            "integration": integration,
            "insights": insights,
            "issues": issues
        }
        
    def _check_rule(self, rule: str, content: Dict[str, Any]) -> bool:
        """Check if content satisfies an integration rule."""
        if rule == "has_conclusions":
            return bool(content.get("conclusions", []))
        elif rule == "has_themes":
            return bool(content.get("themes", []))
        elif rule == "has_context":
            return bool(content.get("context", {}))
        elif rule == "has_insights":
            return bool(content.get("insights", []))
        elif rule == "has_patterns":
            return bool(content.get("patterns", []))
        elif rule == "has_evidence":
            return bool(content.get("evidence", []))
        elif rule == "has_findings":
            return bool(content.get("findings", []))
        elif rule == "has_sources":
            return bool(content.get("sources", []))
        elif rule == "has_validation":
            return bool(content.get("validation", {}))
        return False
        
    def _extract_integration(self, integration: Dict) -> Dict:
        """Extract and validate integration result."""
        result = integration.get("integration", {})
        valid_integration = {}
        
        if isinstance(result, dict):
            # Extract core integration fields
            valid_integration["type"] = str(result.get("type", "unknown"))
            valid_integration["components"] = {}
            
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
                        if "connections" in component:
                            valid_component["connections"] = component["connections"]
                        if "metadata" in component:
                            valid_component["metadata"] = component["metadata"]
                            
                        valid_integration["components"][str(name)] = valid_component
                        
            # Add optional integration sections
            if "connections" in result:
                valid_integration["connections"] = result["connections"]
            if "metadata" in result:
                valid_integration["metadata"] = result["metadata"]
            if "similar_integrations" in result:
                valid_integration["similar_integrations"] = result["similar_integrations"]
                
        return valid_integration
        
    def _extract_insights(self, integration: Dict) -> List[Dict]:
        """Extract and validate integration insights."""
        insights = integration.get("insights", [])
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
                if "connections" in insight:
                    valid_insight["connections"] = [str(c) for c in insight["connections"]]
                    
                valid_insights.append(valid_insight)
                
        return valid_insights
        
    def _extract_issues(self, integration: Dict) -> List[Dict]:
        """Extract and validate integration issues."""
        issues = integration.get("issues", [])
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
                if "related_connections" in issue:
                    valid_issue["related_connections"] = [str(c) for c in issue["related_connections"]]
                    
                valid_issues.append(valid_issue)
                
        return valid_issues
        
    def _calculate_confidence(
        self,
        integration: Dict,
        insights: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall integration confidence."""
        if not integration or not insights:
            return 0.0
            
        # Integration completeness confidence
        integration_conf = 0.0
        if integration.get("components"):
            component_count = len(integration["components"])
            component_conf = min(1.0, component_count * 0.1)  # Cap at 1.0
            integration_conf += component_conf
            
        if integration.get("connections"):
            connection_count = len(integration["connections"])
            connection_conf = min(1.0, connection_count * 0.1)
            integration_conf += connection_conf
            
        integration_conf = integration_conf / 2 if integration_conf > 0 else 0.0
        
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
        base_conf = (integration_conf + insight_conf) / 2
        return max(0.0, base_conf - issue_impact)
        
    def _determine_validity(
        self,
        integration: Dict,
        insights: List[Dict],
        issues: List[Dict],
        confidence: float
    ) -> bool:
        """Determine overall integration validity."""
        if not integration or not insights:
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
        
        # Check integration completeness
        has_components = bool(integration.get("components"))
        has_connections = bool(integration.get("connections"))
        
        # Consider all factors
        return (
            insight_ratio >= 0.7 and
            confidence >= 0.6 and
            has_components and
            has_connections
        )
