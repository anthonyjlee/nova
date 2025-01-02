"""Nova's core alerting functionality."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class AlertingResult:
    """Container for alerting results."""
    
    def __init__(
        self,
        is_valid: bool,
        alerting: Dict,
        alerts: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.alerting = alerting
        self.alerts = alerts
        self.confidence = confidence
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class AlertingAgent:
    """Core alerting functionality for Nova's ecosystem."""
    
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
        
    async def process_alerts(
        self,
        content: Dict[str, Any],
        alerting_type: str,
        metadata: Optional[Dict] = None
    ) -> AlertingResult:
        """Process alerts with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar alerting if vector store available
            similar_alerting = []
            if self.vector_store:
                similar_alerting = await self._get_similar_alerting(
                    content,
                    alerting_type
                )
            
            # Analyze with LLM if available
            if self.llm:
                alerting = await self.llm.analyze(
                    {
                        "content": content,
                        "alerting_type": alerting_type,
                        "metadata": metadata,
                        "similar_alerting": similar_alerting
                    },
                    template="alert_processing",
                    max_tokens=1000
                )
            else:
                alerting = self._basic_alerting(
                    content,
                    alerting_type,
                    similar_alerting
                )
                
            # Extract and validate components
            alerting_result = self._extract_alerting(alerting)
            alerts = self._extract_alerts(alerting)
            issues = self._extract_issues(alerting)
            
            # Calculate confidence and validity
            confidence = self._calculate_confidence(alerting_result, alerts, issues)
            is_valid = self._determine_validity(alerting_result, alerts, issues, confidence)
            
            return AlertingResult(
                is_valid=is_valid,
                alerting=alerting_result,
                alerts=alerts,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "alerting_type": alerting_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Alerting error: {str(e)}")
            return AlertingResult(
                is_valid=False,
                alerting={},
                alerts=[],
                confidence=0.0,
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_similar_alerting(
        self,
        content: Dict[str, Any],
        alerting_type: str
    ) -> List[Dict]:
        """Get similar alerting from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "alerting",
                        "alerting_type": alerting_type
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar alerting: {str(e)}")
        return []
            
    def _basic_alerting(
        self,
        content: Dict[str, Any],
        alerting_type: str,
        similar_alerting: List[Dict]
    ) -> Dict:
        """Basic alert processing without LLM."""
        alerting = {}
        alerts = []
        issues = []
        
        # Basic alerting rules
        alerting_rules = {
            "notification": {
                "has_message": 0.8,
                "has_priority": 0.7,
                "has_channels": 0.6
            },
            "incident": {
                "has_severity": 0.8,
                "has_impact": 0.7,
                "has_response": 0.7
            },
            "threshold": {
                "has_conditions": 0.8,
                "has_triggers": 0.7,
                "has_actions": 0.6
            }
        }
        
        # Check alerting type rules
        if alerting_type in alerting_rules:
            type_rules = alerting_rules[alerting_type]
            
            # Extract basic alerting structure
            if isinstance(content, dict):
                alerting = {
                    "type": alerting_type,
                    "alerts": {},
                    "rules": {},
                    "metadata": {}
                }
                
                # Add alerts from content
                for key, value in content.items():
                    if isinstance(value, dict):
                        alerting["alerts"][key] = {
                            "type": value.get("type", "unknown"),
                            "priority": value.get("priority", 0.5),
                            "rules": value.get("rules", [])
                        }
                        
                # Add basic alerts
                for rule, confidence in type_rules.items():
                    if self._check_rule(rule, content):
                        alerts.append({
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
                
            # Add similar alerting as reference
            if similar_alerting:
                alerting["similar_alerting"] = [
                    {
                        "content": s.get("content", {}).get("content", ""),
                        "similarity": s.get("similarity", 0.0),
                        "timestamp": s.get("timestamp", "")
                    }
                    for s in similar_alerting
                ]
                
        return {
            "alerting": alerting,
            "alerts": alerts,
            "issues": issues
        }
        
    def _check_rule(self, rule: str, content: Dict[str, Any]) -> bool:
        """Check if content satisfies an alerting rule."""
        if rule == "has_message":
            return bool(content.get("message", ""))
        elif rule == "has_priority":
            return bool(content.get("priority", {}))
        elif rule == "has_channels":
            return bool(content.get("channels", []))
        elif rule == "has_severity":
            return bool(content.get("severity", {}))
        elif rule == "has_impact":
            return bool(content.get("impact", {}))
        elif rule == "has_response":
            return bool(content.get("response", {}))
        elif rule == "has_conditions":
            return bool(content.get("conditions", {}))
        elif rule == "has_triggers":
            return bool(content.get("triggers", {}))
        elif rule == "has_actions":
            return bool(content.get("actions", {}))
        return False
        
    def _extract_alerting(self, alerting: Dict) -> Dict:
        """Extract and validate alerting result."""
        result = alerting.get("alerting", {})
        valid_alerting = {}
        
        if isinstance(result, dict):
            # Extract core alerting fields
            valid_alerting["type"] = str(result.get("type", "unknown"))
            valid_alerting["alerts"] = {}
            
            # Extract and validate alerts
            alerts = result.get("alerts", {})
            if isinstance(alerts, dict):
                for name, alert in alerts.items():
                    if isinstance(alert, dict):
                        valid_alert = {
                            "type": str(alert.get("type", "unknown")),
                            "priority": float(alert.get("priority", 0.5))
                        }
                        
                        # Add optional alert attributes
                        if "description" in alert:
                            valid_alert["description"] = str(alert["description"])
                        if "rules" in alert:
                            valid_alert["rules"] = alert["rules"]
                        if "metadata" in alert:
                            valid_alert["metadata"] = alert["metadata"]
                            
                        valid_alerting["alerts"][str(name)] = valid_alert
                        
            # Add optional alerting sections
            if "rules" in result:
                valid_alerting["rules"] = result["rules"]
            if "metadata" in result:
                valid_alerting["metadata"] = result["metadata"]
            if "similar_alerting" in result:
                valid_alerting["similar_alerting"] = result["similar_alerting"]
                
        return valid_alerting
        
    def _extract_alerts(self, alerting: Dict) -> List[Dict]:
        """Extract and validate alerting alerts."""
        alerts = alerting.get("alerts", [])
        valid_alerts = []
        
        for alert in alerts:
            if isinstance(alert, dict) and "type" in alert:
                valid_alert = {
                    "type": str(alert["type"]),
                    "description": str(alert.get("description", "Unknown alert")),
                    "confidence": float(alert.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "details" in alert:
                    valid_alert["details"] = str(alert["details"])
                if "domain_relevance" in alert:
                    valid_alert["domain_relevance"] = float(alert["domain_relevance"])
                if "importance" in alert:
                    valid_alert["importance"] = float(alert["importance"])
                if "rules" in alert:
                    valid_alert["rules"] = [str(r) for r in alert["rules"]]
                    
                valid_alerts.append(valid_alert)
                
        return valid_alerts
        
    def _extract_issues(self, alerting: Dict) -> List[Dict]:
        """Extract and validate alerting issues."""
        issues = alerting.get("issues", [])
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
                if "related_rules" in issue:
                    valid_issue["related_rules"] = [str(r) for r in issue["related_rules"]]
                    
                valid_issues.append(valid_issue)
                
        return valid_issues
        
    def _calculate_confidence(
        self,
        alerting: Dict,
        alerts: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall alerting confidence."""
        if not alerting or not alerts:
            return 0.0
            
        # Alerting completeness confidence
        alerting_conf = 0.0
        if alerting.get("alerts"):
            alert_count = len(alerting["alerts"])
            alert_conf = min(1.0, alert_count * 0.1)  # Cap at 1.0
            alerting_conf += alert_conf
            
        if alerting.get("rules"):
            rule_count = len(alerting["rules"])
            rule_conf = min(1.0, rule_count * 0.1)
            alerting_conf += rule_conf
            
        alerting_conf = alerting_conf / 2 if alerting_conf > 0 else 0.0
        
        # Alert confidence
        alert_conf = sum(a.get("confidence", 0.5) for a in alerts) / len(alerts)
        
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
        base_conf = (alerting_conf + alert_conf) / 2
        return max(0.0, base_conf - issue_impact)
        
    def _determine_validity(
        self,
        alerting: Dict,
        alerts: List[Dict],
        issues: List[Dict],
        confidence: float
    ) -> bool:
        """Determine overall alerting validity."""
        if not alerting or not alerts:
            return False
            
        # Check for critical issues
        has_critical_issues = any(
            i.get("severity") == "high"
            for i in issues
        )
        if has_critical_issues:
            return False
            
        # Check alert confidence
        high_confidence_alerts = sum(
            1 for a in alerts
            if a.get("confidence", 0.0) > 0.7
        )
        alert_ratio = high_confidence_alerts / len(alerts)
        
        # Check alerting completeness
        has_alerts = bool(alerting.get("alerts"))
        has_rules = bool(alerting.get("rules"))
        
        # Consider all factors
        return (
            alert_ratio >= 0.7 and
            confidence >= 0.6 and
            has_alerts and
            has_rules
        )
