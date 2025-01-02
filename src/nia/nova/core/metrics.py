"""Nova's core metrics functionality."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class MetricsResult:
    """Container for metrics results."""
    
    def __init__(
        self,
        is_valid: bool,
        metrics: Dict,
        values: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.metrics = metrics
        self.values = values
        self.confidence = confidence
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class MetricsAgent:
    """Core metrics functionality for Nova's ecosystem."""
    
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
        
    async def process_metrics(
        self,
        content: Dict[str, Any],
        metrics_type: str,
        metadata: Optional[Dict] = None
    ) -> MetricsResult:
        """Process metrics with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar metrics if vector store available
            similar_metrics = []
            if self.vector_store:
                similar_metrics = await self._get_similar_metrics(
                    content,
                    metrics_type
                )
            
            # Analyze with LLM if available
            if self.llm:
                metrics = await self.llm.analyze(
                    {
                        "content": content,
                        "metrics_type": metrics_type,
                        "metadata": metadata,
                        "similar_metrics": similar_metrics
                    },
                    template="metrics_processing",
                    max_tokens=1000
                )
            else:
                metrics = self._basic_metrics(
                    content,
                    metrics_type,
                    similar_metrics
                )
                
            # Extract and validate components
            metrics_result = self._extract_metrics(metrics)
            values = self._extract_values(metrics)
            issues = self._extract_issues(metrics)
            
            # Calculate confidence and validity
            confidence = self._calculate_confidence(metrics_result, values, issues)
            is_valid = self._determine_validity(metrics_result, values, issues, confidence)
            
            return MetricsResult(
                is_valid=is_valid,
                metrics=metrics_result,
                values=values,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "metrics_type": metrics_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Metrics error: {str(e)}")
            return MetricsResult(
                is_valid=False,
                metrics={},
                values=[],
                confidence=0.0,
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_similar_metrics(
        self,
        content: Dict[str, Any],
        metrics_type: str
    ) -> List[Dict]:
        """Get similar metrics from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "metrics",
                        "metrics_type": metrics_type
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar metrics: {str(e)}")
        return []
            
    def _basic_metrics(
        self,
        content: Dict[str, Any],
        metrics_type: str,
        similar_metrics: List[Dict]
    ) -> Dict:
        """Basic metrics processing without LLM."""
        metrics = {}
        values = []
        issues = []
        
        # Basic metrics rules
        metrics_rules = {
            "performance": {
                "has_values": 0.8,
                "has_thresholds": 0.7,
                "has_trends": 0.6
            },
            "resource": {
                "has_usage": 0.8,
                "has_limits": 0.7,
                "has_allocation": 0.7
            },
            "quality": {
                "has_scores": 0.8,
                "has_criteria": 0.7,
                "has_benchmarks": 0.6
            }
        }
        
        # Check metrics type rules
        if metrics_type in metrics_rules:
            type_rules = metrics_rules[metrics_type]
            
            # Extract basic metrics structure
            if isinstance(content, dict):
                metrics = {
                    "type": metrics_type,
                    "metrics": {},
                    "metadata": {}
                }
                
                # Add metrics from content
                for key, value in content.items():
                    if isinstance(value, dict):
                        metrics["metrics"][key] = {
                            "type": value.get("type", "unknown"),
                            "value": value.get("value", 0.0),
                            "unit": value.get("unit", "")
                        }
                        
                # Add basic values
                for rule, confidence in type_rules.items():
                    if self._check_rule(rule, content):
                        values.append({
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
                
            # Add similar metrics as reference
            if similar_metrics:
                metrics["similar_metrics"] = [
                    {
                        "content": s.get("content", {}).get("content", ""),
                        "similarity": s.get("similarity", 0.0),
                        "timestamp": s.get("timestamp", "")
                    }
                    for s in similar_metrics
                ]
                
        return {
            "metrics": metrics,
            "values": values,
            "issues": issues
        }
        
    def _check_rule(self, rule: str, content: Dict[str, Any]) -> bool:
        """Check if content satisfies a metrics rule."""
        if rule == "has_values":
            return bool(content.get("values", []))
        elif rule == "has_thresholds":
            return bool(content.get("thresholds", {}))
        elif rule == "has_trends":
            return bool(content.get("trends", {}))
        elif rule == "has_usage":
            return bool(content.get("usage", {}))
        elif rule == "has_limits":
            return bool(content.get("limits", {}))
        elif rule == "has_allocation":
            return bool(content.get("allocation", {}))
        elif rule == "has_scores":
            return bool(content.get("scores", {}))
        elif rule == "has_criteria":
            return bool(content.get("criteria", {}))
        elif rule == "has_benchmarks":
            return bool(content.get("benchmarks", {}))
        return False
        
    def _extract_metrics(self, metrics: Dict) -> Dict:
        """Extract and validate metrics result."""
        result = metrics.get("metrics", {})
        valid_metrics = {}
        
        if isinstance(result, dict):
            # Extract core metrics fields
            valid_metrics["type"] = str(result.get("type", "unknown"))
            valid_metrics["metrics"] = {}
            
            # Extract and validate metrics
            metrics_data = result.get("metrics", {})
            if isinstance(metrics_data, dict):
                for name, metric in metrics_data.items():
                    if isinstance(metric, dict):
                        valid_metric = {
                            "type": str(metric.get("type", "unknown")),
                            "value": float(metric.get("value", 0.0)),
                            "unit": str(metric.get("unit", ""))
                        }
                        
                        # Add optional metric attributes
                        if "description" in metric:
                            valid_metric["description"] = str(metric["description"])
                        if "thresholds" in metric:
                            valid_metric["thresholds"] = metric["thresholds"]
                        if "metadata" in metric:
                            valid_metric["metadata"] = metric["metadata"]
                            
                        valid_metrics["metrics"][str(name)] = valid_metric
                        
            # Add optional metrics sections
            if "metadata" in result:
                valid_metrics["metadata"] = result["metadata"]
            if "similar_metrics" in result:
                valid_metrics["similar_metrics"] = result["similar_metrics"]
                
        return valid_metrics
        
    def _extract_values(self, metrics: Dict) -> List[Dict]:
        """Extract and validate metrics values."""
        values = metrics.get("values", [])
        valid_values = []
        
        for value in values:
            if isinstance(value, dict) and "type" in value:
                valid_value = {
                    "type": str(value["type"]),
                    "description": str(value.get("description", "Unknown value")),
                    "confidence": float(value.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "details" in value:
                    valid_value["details"] = str(value["details"])
                if "domain_relevance" in value:
                    valid_value["domain_relevance"] = float(value["domain_relevance"])
                if "importance" in value:
                    valid_value["importance"] = float(value["importance"])
                if "thresholds" in value:
                    valid_value["thresholds"] = value["thresholds"]
                    
                valid_values.append(valid_value)
                
        return valid_values
        
    def _extract_issues(self, metrics: Dict) -> List[Dict]:
        """Extract and validate metrics issues."""
        issues = metrics.get("issues", [])
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
                if "thresholds" in issue:
                    valid_issue["thresholds"] = issue["thresholds"]
                    
                valid_issues.append(valid_issue)
                
        return valid_issues
        
    def _calculate_confidence(
        self,
        metrics: Dict,
        values: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall metrics confidence."""
        if not metrics or not values:
            return 0.0
            
        # Metrics completeness confidence
        metrics_conf = 0.0
        if metrics.get("metrics"):
            metric_count = len(metrics["metrics"])
            metric_conf = min(1.0, metric_count * 0.1)  # Cap at 1.0
            metrics_conf += metric_conf
            
        if metrics.get("metadata"):
            meta_count = len(metrics["metadata"])
            meta_conf = min(1.0, meta_count * 0.1)
            metrics_conf += meta_conf
            
        metrics_conf = metrics_conf / 2 if metrics_conf > 0 else 0.0
        
        # Value confidence
        value_conf = sum(v.get("confidence", 0.5) for v in values) / len(values)
        
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
        base_conf = (metrics_conf + value_conf) / 2
        return max(0.0, base_conf - issue_impact)
        
    def _determine_validity(
        self,
        metrics: Dict,
        values: List[Dict],
        issues: List[Dict],
        confidence: float
    ) -> bool:
        """Determine overall metrics validity."""
        if not metrics or not values:
            return False
            
        # Check for critical issues
        has_critical_issues = any(
            i.get("severity") == "high"
            for i in issues
        )
        if has_critical_issues:
            return False
            
        # Check value confidence
        high_confidence_values = sum(
            1 for v in values
            if v.get("confidence", 0.0) > 0.7
        )
        value_ratio = high_confidence_values / len(values)
        
        # Check metrics completeness
        has_metrics = bool(metrics.get("metrics"))
        has_metadata = bool(metrics.get("metadata"))
        
        # Consider all factors
        return (
            value_ratio >= 0.7 and
            confidence >= 0.6 and
            has_metrics and
            has_metadata
        )
