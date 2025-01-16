"""Nova's core alerting functionality."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel

from .validation import ValidationPattern, ValidationResult, ValidationTracker

logger = logging.getLogger(__name__)

class AlertValidationPattern(ValidationPattern):
    """Alert-specific validation pattern."""
    alert_type: str
    rule_type: Optional[str] = None
    channel_type: Optional[str] = None

class AlertingResult(BaseModel):
    """Container for alerting results."""
    is_valid: bool
    alerting: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any] = {}
    issues: List[Dict[str, Any]] = []
    validation: Optional[ValidationResult] = None
    timestamp: str = datetime.now().isoformat()

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
        self.validation_tracker = ValidationTracker()
        
    async def process_alerts(
        self,
        content: Dict[str, Any],
        alerting_type: str,
        metadata: Optional[Dict] = None
    ) -> AlertingResult:
        """Process alerts with domain and validation awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            logger.debug(f"Processing alerts - type: {alerting_type}, content: {content}")
                
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
                alerting = await self._basic_alerting(
                    content,
                    alerting_type,
                    similar_alerting
                )
                
            # Extract and validate components with validation tracking
            alerting_result = await self._extract_alerting(alerting)
            alerts = await self._extract_alerts(alerting)
            issues = await self._extract_issues(alerting)
            
            # Track validation patterns
            validation_issues = []
            
            # Validate alerts
            if not alerts:
                issue = {
                    "type": "missing_alerts",
                    "severity": "high",
                    "description": "No valid alerts found"
                }
                validation_issues.append(issue)
                
                logger.warning(f"Missing alerts detected: {issue}")
                    
            # Validate alerting structure
            required_structure = ["rules", "channels"]
            for req in required_structure:
                if req not in alerting_result:
                    issue = {
                        "type": "missing_structure",
                        "severity": "medium",
                        "description": f"Alerting missing required structure: {req}"
                    }
                    validation_issues.append(issue)
                    
                    logger.warning(f"Missing structure detected: {issue}")
                        
            # Create validation result
            validation_result = ValidationResult(
                is_valid=len(validation_issues) == 0,
                issues=validation_issues,
                metadata={
                    "alert_type": alerting_type,
                    "domain": self.domain,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Calculate confidence with validation awareness
            confidence = self._calculate_confidence(alerting_result, alerts, issues)
            
            # Determine validity with validation awareness
            is_valid = self._determine_validity(alerting_result, alerts, issues, confidence)
            
            # Create alerting result
            result = AlertingResult(
                is_valid=is_valid,
                alerting=alerting_result,
                alerts=alerts,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "alerting_type": alerting_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown"),
                    "validation_timestamp": datetime.now().isoformat()
                },
                issues=issues,
                validation=validation_result
            )
            
            logger.debug(f"Alerting result: {result.dict()}")
                    
            # Log critical patterns
            critical_patterns = self.validation_tracker.get_critical_patterns()
            if critical_patterns:
                logger.warning(f"Critical alerting patterns detected: {critical_patterns}")
                        
            if not result.validation.is_valid:
                raise ValueError(f"Alerting validation failed: {validation_issues}")
                    
            return result
            
        except Exception as e:
            error_msg = f"Alerting error: {str(e)}"
            logger.error(error_msg)
                
            return AlertingResult(
                is_valid=False,
                alerting={},
                alerts=[],
                confidence=0.0,
                metadata={
                    "error": str(e),
                    "domain": self.domain
                },
                issues=[{
                    "type": "error",
                    "severity": "high",
                    "description": str(e)
                }],
                validation=ValidationResult(
                    is_valid=False,
                    issues=[{
                        "type": "error",
                        "severity": "high",
                        "description": str(e)
                    }]
                )
            )
            
    async def _get_similar_alerting(
        self,
        content: Dict[str, Any],
        alerting_type: str
    ) -> List[Dict]:
        """Get similar alerting from vector store with validation."""
        try:
            logger.debug(f"Finding similar alerting for type: {alerting_type}")
                
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
                
                logger.debug(f"Found {len(results)} similar alerting patterns")
                    
                return results
                
        except Exception as e:
            error_msg = f"Error getting similar alerting: {str(e)}"
            logger.error(error_msg)
                
        return []
            
    async def _basic_alerting(
        self,
        content: Dict[str, Any],
        alerting_type: str,
        similar_alerting: List[Dict]
    ) -> Dict:
        """Basic alert processing with validation tracking."""
        alerting = {}
        alerts = []
        validation_issues = []
        
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
        
        # Check alerting type rules with validation
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
                
                # Add alerts from content with validation
                for key, value in content.items():
                    if isinstance(value, dict):
                        # Validate alert type
                        alert_type = value.get("type", "unknown")
                        if alert_type == "unknown":
                            issue = {
                                "type": "invalid_alert_type",
                                "severity": "high",
                                "description": "Alert type is unknown",
                                "alert_id": key
                            }
                            validation_issues.append(issue)
                            continue
                            
                        # Validate priority
                        priority = value.get("priority", 0.5)
                        if not isinstance(priority, (int, float)) or priority < 0 or priority > 1:
                            issue = {
                                "type": "invalid_priority",
                                "severity": "medium",
                                "description": "Priority must be between 0 and 1",
                                "alert_id": key
                            }
                            validation_issues.append(issue)
                            priority = max(0, min(1, float(priority)))
                            
                        alerting["alerts"][key] = {
                            "type": alert_type,
                            "priority": priority,
                            "rules": value.get("rules", [])
                        }
                        
                # Add basic alerts with validation
                for rule, confidence in type_rules.items():
                    if await self._check_rule(rule, content):
                        alerts.append({
                            "type": rule,
                            "description": f"Content satisfies {rule}",
                            "confidence": confidence
                        })
                    else:
                        issue = {
                            "type": f"missing_{rule}",
                            "severity": "medium",
                            "description": f"Content is missing {rule}",
                            "rule_type": rule
                        }
                        validation_issues.append(issue)
                        
                        logger.warning(f"Missing rule detected: {issue}")
                        
            else:
                issue = {
                    "type": "invalid_format",
                    "severity": "high",
                    "description": "Content must be a dictionary"
                }
                validation_issues.append(issue)
                
                logger.error(f"Invalid format detected: {issue}")
                
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
                
        # Track validation patterns
        for issue in validation_issues:
            pattern = AlertValidationPattern(
                type=issue["type"],
                description=issue["description"],
                severity=issue["severity"],
                alert_type=alerting_type,
                rule_type=issue.get("rule_type"),
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
                metadata={
                    "domain": self.domain
                }
            )
            self.validation_tracker.add_issue(pattern.dict())
                
        return {
            "alerting": alerting,
            "alerts": alerts,
            "validation_issues": validation_issues
        }
        
    async def _check_rule(self, rule: str, content: Dict[str, Any]) -> bool:
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
        
    async def _extract_alerting(
        self,
        alerting: Dict
    ) -> Dict:
        """Extract and validate alerting result with debug logging."""
        try:
            result = alerting.get("alerting", {})
            valid_alerting = {}
            validation_issues = []
            
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
                        else:
                            issue = {
                                "type": "invalid_alert",
                                "severity": "medium",
                                "description": "Alert has invalid format",
                                "alert_id": name
                            }
                            validation_issues.append(issue)
                            
                # Add optional alerting sections
                if "rules" in result:
                    valid_alerting["rules"] = result["rules"]
                if "metadata" in result:
                    valid_alerting["metadata"] = result["metadata"]
                if "similar_alerting" in result:
                    valid_alerting["similar_alerting"] = result["similar_alerting"]
                    
            # Track validation patterns
            for issue in validation_issues:
                pattern = AlertValidationPattern(
                    type=issue["type"],
                    description=issue["description"],
                    severity=issue["severity"],
                    alert_type=valid_alerting.get("type", "unknown"),
                    first_seen=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    metadata={
                        "domain": self.domain
                    }
                )
                self.validation_tracker.add_issue(pattern.dict())
                
            if validation_issues:
                logger.warning(f"Alerting validation issues: {validation_issues}")
                    
            return valid_alerting
            
        except Exception as e:
            error_msg = f"Error extracting alerting: {str(e)}"
            logger.error(error_msg)
                
            return {}
        
    async def _extract_alerts(
        self,
        alerting: Dict
    ) -> List[Dict]:
        """Extract and validate alerting alerts with debug logging."""
        try:
            alerts = alerting.get("alerts", [])
            valid_alerts = []
            validation_issues = []
            
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
                else:
                    issue = {
                        "type": "invalid_alert",
                        "severity": "medium",
                        "description": "Alert missing required fields"
                    }
                    validation_issues.append(issue)
                    
            # Track validation patterns
            for issue in validation_issues:
                pattern = AlertValidationPattern(
                    type=issue["type"],
                    description=issue["description"],
                    severity=issue["severity"],
                    alert_type="alert",
                    first_seen=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    metadata={
                        "domain": self.domain
                    }
                )
                self.validation_tracker.add_issue(pattern.dict())
                
            if validation_issues:
                logger.warning(f"Alert validation issues: {validation_issues}")
                    
            return valid_alerts
            
        except Exception as e:
            error_msg = f"Error extracting alerts: {str(e)}"
            logger.error(error_msg)
                
            return []
        
    async def _extract_issues(
        self,
        alerting: Dict
    ) -> List[Dict]:
        """Extract and validate alerting issues with debug logging."""
        try:
            issues = alerting.get("issues", [])
            valid_issues = []
            validation_issues = []
            
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
                else:
                    validation_issues.append({
                        "type": "invalid_issue",
                        "severity": "medium",
                        "description": "Issue missing required fields"
                    })
                    
            # Track validation patterns
            for issue in validation_issues:
                pattern = AlertValidationPattern(
                    type=issue["type"],
                    description=issue["description"],
                    severity=issue["severity"],
                    alert_type="issue",
                    first_seen=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    metadata={
                        "domain": self.domain
                    }
                )
                self.validation_tracker.add_issue(pattern.dict())
                
            if validation_issues:
                logger.warning(f"Issue validation issues: {validation_issues}")
                    
            return valid_issues
            
        except Exception as e:
            error_msg = f"Error extracting issues: {str(e)}"
            logger.error(error_msg)
                
            return []
        
    def _calculate_confidence(
        self,
        alerting: Dict,
        alerts: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall alerting confidence with validation."""
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
        """Determine overall alerting validity with validation."""
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
