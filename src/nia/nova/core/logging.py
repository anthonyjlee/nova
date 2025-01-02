"""Nova's core logging functionality."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class LoggingResult:
    """Container for logging results."""
    
    def __init__(
        self,
        is_valid: bool,
        logging: Dict,
        logs: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.logging = logging
        self.logs = logs
        self.confidence = confidence
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class LoggingAgent:
    """Core logging functionality for Nova's ecosystem."""
    
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
        
    async def process_logs(
        self,
        content: Dict[str, Any],
        logging_type: str,
        metadata: Optional[Dict] = None
    ) -> LoggingResult:
        """Process logs with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar logging if vector store available
            similar_logging = []
            if self.vector_store:
                similar_logging = await self._get_similar_logging(
                    content,
                    logging_type
                )
            
            # Analyze with LLM if available
            if self.llm:
                logging = await self.llm.analyze(
                    {
                        "content": content,
                        "logging_type": logging_type,
                        "metadata": metadata,
                        "similar_logging": similar_logging
                    },
                    template="log_processing",
                    max_tokens=1000
                )
            else:
                logging = self._basic_logging(
                    content,
                    logging_type,
                    similar_logging
                )
                
            # Extract and validate components
            logging_result = self._extract_logging(logging)
            logs = self._extract_logs(logging)
            issues = self._extract_issues(logging)
            
            # Calculate confidence and validity
            confidence = self._calculate_confidence(logging_result, logs, issues)
            is_valid = self._determine_validity(logging_result, logs, issues, confidence)
            
            return LoggingResult(
                is_valid=is_valid,
                logging=logging_result,
                logs=logs,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "logging_type": logging_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Logging error: {str(e)}")
            return LoggingResult(
                is_valid=False,
                logging={},
                logs=[],
                confidence=0.0,
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_similar_logging(
        self,
        content: Dict[str, Any],
        logging_type: str
    ) -> List[Dict]:
        """Get similar logging from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "logging",
                        "logging_type": logging_type
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar logging: {str(e)}")
        return []
            
    def _basic_logging(
        self,
        content: Dict[str, Any],
        logging_type: str,
        similar_logging: List[Dict]
    ) -> Dict:
        """Basic log processing without LLM."""
        logging = {}
        logs = []
        issues = []
        
        # Basic logging rules
        logging_rules = {
            "debug": {
                "has_message": 0.8,
                "has_level": 0.7,
                "has_context": 0.6
            },
            "info": {
                "has_message": 0.8,
                "has_level": 0.7,
                "has_metadata": 0.7
            },
            "error": {
                "has_message": 0.8,
                "has_stacktrace": 0.7,
                "has_context": 0.6
            }
        }
        
        # Check logging type rules
        if logging_type in logging_rules:
            type_rules = logging_rules[logging_type]
            
            # Extract basic logging structure
            if isinstance(content, dict):
                logging = {
                    "type": logging_type,
                    "logs": {},
                    "metadata": {}
                }
                
                # Add logs from content
                for key, value in content.items():
                    if isinstance(value, dict):
                        logging["logs"][key] = {
                            "type": value.get("type", "unknown"),
                            "level": value.get("level", "info"),
                            "message": value.get("message", "")
                        }
                        
                # Add basic logs
                for rule, confidence in type_rules.items():
                    if self._check_rule(rule, content):
                        logs.append({
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
                
            # Add similar logging as reference
            if similar_logging:
                logging["similar_logging"] = [
                    {
                        "content": s.get("content", {}).get("content", ""),
                        "similarity": s.get("similarity", 0.0),
                        "timestamp": s.get("timestamp", "")
                    }
                    for s in similar_logging
                ]
                
        return {
            "logging": logging,
            "logs": logs,
            "issues": issues
        }
        
    def _check_rule(self, rule: str, content: Dict[str, Any]) -> bool:
        """Check if content satisfies a logging rule."""
        if rule == "has_message":
            return bool(content.get("message", ""))
        elif rule == "has_level":
            return bool(content.get("level", ""))
        elif rule == "has_context":
            return bool(content.get("context", {}))
        elif rule == "has_metadata":
            return bool(content.get("metadata", {}))
        elif rule == "has_stacktrace":
            return bool(content.get("stacktrace", ""))
        return False
        
    def _extract_logging(self, logging: Dict) -> Dict:
        """Extract and validate logging result."""
        result = logging.get("logging", {})
        valid_logging = {}
        
        if isinstance(result, dict):
            # Extract core logging fields
            valid_logging["type"] = str(result.get("type", "unknown"))
            valid_logging["logs"] = {}
            
            # Extract and validate logs
            logs = result.get("logs", {})
            if isinstance(logs, dict):
                for name, log in logs.items():
                    if isinstance(log, dict):
                        valid_log = {
                            "type": str(log.get("type", "unknown")),
                            "level": str(log.get("level", "info")),
                            "message": str(log.get("message", ""))
                        }
                        
                        # Add optional log attributes
                        if "context" in log:
                            valid_log["context"] = log["context"]
                        if "metadata" in log:
                            valid_log["metadata"] = log["metadata"]
                        if "stacktrace" in log:
                            valid_log["stacktrace"] = str(log["stacktrace"])
                            
                        valid_logging["logs"][str(name)] = valid_log
                        
            # Add optional logging sections
            if "metadata" in result:
                valid_logging["metadata"] = result["metadata"]
            if "similar_logging" in result:
                valid_logging["similar_logging"] = result["similar_logging"]
                
        return valid_logging
        
    def _extract_logs(self, logging: Dict) -> List[Dict]:
        """Extract and validate logging logs."""
        logs = logging.get("logs", [])
        valid_logs = []
        
        for log in logs:
            if isinstance(log, dict) and "type" in log:
                valid_log = {
                    "type": str(log["type"]),
                    "description": str(log.get("description", "Unknown log")),
                    "confidence": float(log.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "details" in log:
                    valid_log["details"] = str(log["details"])
                if "domain_relevance" in log:
                    valid_log["domain_relevance"] = float(log["domain_relevance"])
                if "importance" in log:
                    valid_log["importance"] = float(log["importance"])
                if "context" in log:
                    valid_log["context"] = log["context"]
                    
                valid_logs.append(valid_log)
                
        return valid_logs
        
    def _extract_issues(self, logging: Dict) -> List[Dict]:
        """Extract and validate logging issues."""
        issues = logging.get("issues", [])
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
                if "context" in issue:
                    valid_issue["context"] = issue["context"]
                    
                valid_issues.append(valid_issue)
                
        return valid_issues
        
    def _calculate_confidence(
        self,
        logging: Dict,
        logs: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall logging confidence."""
        if not logging or not logs:
            return 0.0
            
        # Logging completeness confidence
        logging_conf = 0.0
        if logging.get("logs"):
            log_count = len(logging["logs"])
            log_conf = min(1.0, log_count * 0.1)  # Cap at 1.0
            logging_conf += log_conf
            
        if logging.get("metadata"):
            meta_count = len(logging["metadata"])
            meta_conf = min(1.0, meta_count * 0.1)
            logging_conf += meta_conf
            
        logging_conf = logging_conf / 2 if logging_conf > 0 else 0.0
        
        # Log confidence
        log_conf = sum(l.get("confidence", 0.5) for l in logs) / len(logs)
        
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
        base_conf = (logging_conf + log_conf) / 2
        return max(0.0, base_conf - issue_impact)
        
    def _determine_validity(
        self,
        logging: Dict,
        logs: List[Dict],
        issues: List[Dict],
        confidence: float
    ) -> bool:
        """Determine overall logging validity."""
        if not logging or not logs:
            return False
            
        # Check for critical issues
        has_critical_issues = any(
            i.get("severity") == "high"
            for i in issues
        )
        if has_critical_issues:
            return False
            
        # Check log confidence
        high_confidence_logs = sum(
            1 for l in logs
            if l.get("confidence", 0.0) > 0.7
        )
        log_ratio = high_confidence_logs / len(logs)
        
        # Check logging completeness
        has_logs = bool(logging.get("logs"))
        has_metadata = bool(logging.get("metadata"))
        
        # Consider all factors
        return (
            log_ratio >= 0.7 and
            confidence >= 0.6 and
            has_logs and
            has_metadata
        )
