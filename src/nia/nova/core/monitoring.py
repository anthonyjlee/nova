"""Nova's core monitoring functionality."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class MonitoringResult:
    """Container for monitoring results."""
    
    def __init__(
        self,
        is_valid: bool,
        monitoring: Dict,
        metrics: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.monitoring = monitoring
        self.metrics = metrics
        self.confidence = confidence
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class MonitoringAgent:
    """Core monitoring functionality for Nova's ecosystem."""
    
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
        
    async def monitor_agents(
        self,
        content: Dict[str, Any],
        monitoring_type: str,
        metadata: Optional[Dict] = None
    ) -> MonitoringResult:
        """Monitor agents with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar monitoring if vector store available
            similar_monitoring = []
            if self.vector_store:
                similar_monitoring = await self._get_similar_monitoring(
                    content,
                    monitoring_type
                )
            
            # Analyze with LLM if available
            if self.llm:
                monitoring = await self.llm.analyze(
                    {
                        "content": content,
                        "monitoring_type": monitoring_type,
                        "metadata": metadata,
                        "similar_monitoring": similar_monitoring
                    },
                    template="agent_monitoring",
                    max_tokens=1000
                )
            else:
                monitoring = self._basic_monitoring(
                    content,
                    monitoring_type,
                    similar_monitoring
                )
                
            # Extract and validate components
            monitoring_result = self._extract_monitoring(monitoring)
            metrics = self._extract_metrics(monitoring)
            issues = self._extract_issues(monitoring)
            
            # Calculate confidence and validity
            confidence = self._calculate_confidence(monitoring_result, metrics, issues)
            is_valid = self._determine_validity(monitoring_result, metrics, issues, confidence)
            
            return MonitoringResult(
                is_valid=is_valid,
                monitoring=monitoring_result,
                metrics=metrics,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "monitoring_type": monitoring_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Monitoring error: {str(e)}")
            return MonitoringResult(
                is_valid=False,
                monitoring={},
                metrics=[],
                confidence=0.0,
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_similar_monitoring(
        self,
        content: Dict[str, Any],
        monitoring_type: str
    ) -> List[Dict]:
        """Get similar monitoring from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "monitoring",
                        "monitoring_type": monitoring_type
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar monitoring: {str(e)}")
        return []
            
    def _basic_monitoring(
        self,
        content: Dict[str, Any],
        monitoring_type: str,
        similar_monitoring: List[Dict]
    ) -> Dict:
        """Basic agent monitoring without LLM."""
        monitoring = {}
        metrics = []
        issues = []
        
        # Basic monitoring rules
        monitoring_rules = {
            "performance": {
                "has_metrics": 0.8,
                "has_thresholds": 0.7,
                "has_trends": 0.6
            },
            "health": {
                "has_status": 0.8,
                "has_diagnostics": 0.7,
                "has_recovery": 0.7
            },
            "resource": {
                "has_usage": 0.8,
                "has_limits": 0.7,
                "has_allocation": 0.6
            }
        }
        
        # Check monitoring type rules
        if monitoring_type in monitoring_rules:
            type_rules = monitoring_rules[monitoring_type]
            
            # Extract basic monitoring structure
            if isinstance(content, dict):
                monitoring = {
                    "type": monitoring_type,
                    "agents": {},
                    "metrics": {},
                    "metadata": {}
                }
                
                # Add agents from content
                for key, value in content.items():
                    if isinstance(value, dict):
                        monitoring["agents"][key] = {
                            "type": value.get("type", "unknown"),
                            "priority": value.get("priority", 0.5),
                            "metrics": value.get("metrics", [])
                        }
                        
                # Add basic metrics
                for rule, confidence in type_rules.items():
                    if self._check_rule(rule, content):
                        metrics.append({
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
                
            # Add similar monitoring as reference
            if similar_monitoring:
                monitoring["similar_monitoring"] = [
                    {
                        "content": s.get("content", {}).get("content", ""),
                        "similarity": s.get("similarity", 0.0),
                        "timestamp": s.get("timestamp", "")
                    }
                    for s in similar_monitoring
                ]
                
        return {
            "monitoring": monitoring,
            "metrics": metrics,
            "issues": issues
        }
        
    def _check_rule(self, rule: str, content: Dict[str, Any]) -> bool:
        """Check if content satisfies a monitoring rule."""
        if rule == "has_metrics":
            return bool(content.get("metrics", []))
        elif rule == "has_thresholds":
            return bool(content.get("thresholds", {}))
        elif rule == "has_trends":
            return bool(content.get("trends", {}))
        elif rule == "has_status":
            return bool(content.get("status", []))
        elif rule == "has_diagnostics":
            return bool(content.get("diagnostics", {}))
        elif rule == "has_recovery":
            return bool(content.get("recovery", {}))
        elif rule == "has_usage":
            return bool(content.get("usage", {}))
        elif rule == "has_limits":
            return bool(content.get("limits", {}))
        elif rule == "has_allocation":
            return bool(content.get("allocation", {}))
        return False
        
    def _extract_monitoring(self, monitoring: Dict) -> Dict:
        """Extract and validate monitoring result."""
        result = monitoring.get("monitoring", {})
        valid_monitoring = {}
        
        if isinstance(result, dict):
            # Extract core monitoring fields
            valid_monitoring["type"] = str(result.get("type", "unknown"))
            valid_monitoring["agents"] = {}
            
            # Extract and validate agents
            agents = result.get("agents", {})
            if isinstance(agents, dict):
                for name, agent in agents.items():
                    if isinstance(agent, dict):
                        valid_agent = {
                            "type": str(agent.get("type", "unknown")),
                            "priority": float(agent.get("priority", 0.5))
                        }
                        
                        # Add optional agent attributes
                        if "description" in agent:
                            valid_agent["description"] = str(agent["description"])
                        if "metrics" in agent:
                            valid_agent["metrics"] = agent["metrics"]
                        if "metadata" in agent:
                            valid_agent["metadata"] = agent["metadata"]
                            
                        valid_monitoring["agents"][str(name)] = valid_agent
                        
            # Add optional monitoring sections
            if "metrics" in result:
                valid_monitoring["metrics"] = result["metrics"]
            if "metadata" in result:
                valid_monitoring["metadata"] = result["metadata"]
            if "similar_monitoring" in result:
                valid_monitoring["similar_monitoring"] = result["similar_monitoring"]
                
        return valid_monitoring
        
    def _extract_metrics(self, monitoring: Dict) -> List[Dict]:
        """Extract and validate monitoring metrics."""
        metrics = monitoring.get("metrics", [])
        valid_metrics = []
        
        for metric in metrics:
            if isinstance(metric, dict) and "type" in metric:
                valid_metric = {
                    "type": str(metric["type"]),
                    "description": str(metric.get("description", "Unknown metric")),
                    "confidence": float(metric.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "details" in metric:
                    valid_metric["details"] = str(metric["details"])
                if "domain_relevance" in metric:
                    valid_metric["domain_relevance"] = float(metric["domain_relevance"])
                if "importance" in metric:
                    valid_metric["importance"] = float(metric["importance"])
                if "agents" in metric:
                    valid_metric["agents"] = [str(a) for a in metric["agents"]]
                    
                valid_metrics.append(valid_metric)
                
        return valid_metrics
        
    def _extract_issues(self, monitoring: Dict) -> List[Dict]:
        """Extract and validate monitoring issues."""
        issues = monitoring.get("issues", [])
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
                if "related_agents" in issue:
                    valid_issue["related_agents"] = [str(a) for a in issue["related_agents"]]
                    
                valid_issues.append(valid_issue)
                
        return valid_issues
        
    def _calculate_confidence(
        self,
        monitoring: Dict,
        metrics: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall monitoring confidence."""
        if not monitoring or not metrics:
            return 0.0
            
        # Monitoring completeness confidence
        monitoring_conf = 0.0
        if monitoring.get("agents"):
            agent_count = len(monitoring["agents"])
            agent_conf = min(1.0, agent_count * 0.1)  # Cap at 1.0
            monitoring_conf += agent_conf
            
        if monitoring.get("metrics"):
            metric_count = len(monitoring["metrics"])
            metric_conf = min(1.0, metric_count * 0.1)
            monitoring_conf += metric_conf
            
        monitoring_conf = monitoring_conf / 2 if monitoring_conf > 0 else 0.0
        
        # Metric confidence
        metric_conf = sum(m.get("confidence", 0.5) for m in metrics) / len(metrics)
        
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
        base_conf = (monitoring_conf + metric_conf) / 2
        return max(0.0, base_conf - issue_impact)
        
    def _determine_validity(
        self,
        monitoring: Dict,
        metrics: List[Dict],
        issues: List[Dict],
        confidence: float
    ) -> bool:
        """Determine overall monitoring validity."""
        if not monitoring or not metrics:
            return False
            
        # Check for critical issues
        has_critical_issues = any(
            i.get("severity") == "high"
            for i in issues
        )
        if has_critical_issues:
            return False
            
        # Check metric confidence
        high_confidence_metrics = sum(
            1 for m in metrics
            if m.get("confidence", 0.0) > 0.7
        )
        metric_ratio = high_confidence_metrics / len(metrics)
        
        # Check monitoring completeness
        has_agents = bool(monitoring.get("agents"))
        has_metrics = bool(monitoring.get("metrics"))
        
        # Consider all factors
        return (
            metric_ratio >= 0.7 and
            confidence >= 0.6 and
            has_agents and
            has_metrics
        )
