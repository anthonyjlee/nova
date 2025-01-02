"""Nova's core orchestration functionality."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class OrchestrationResult:
    """Container for orchestration results."""
    
    def __init__(
        self,
        is_valid: bool,
        orchestration: Dict,
        decisions: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.orchestration = orchestration
        self.decisions = decisions
        self.confidence = confidence
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class OrchestrationAgent:
    """Core orchestration functionality for Nova's ecosystem."""
    
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
        
    async def orchestrate_agents(
        self,
        content: Dict[str, Any],
        orchestration_type: str,
        metadata: Optional[Dict] = None
    ) -> OrchestrationResult:
        """Orchestrate agents with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar orchestrations if vector store available
            similar_orchestrations = []
            if self.vector_store:
                similar_orchestrations = await self._get_similar_orchestrations(
                    content,
                    orchestration_type
                )
            
            # Analyze with LLM if available
            if self.llm:
                orchestration = await self.llm.analyze(
                    {
                        "content": content,
                        "orchestration_type": orchestration_type,
                        "metadata": metadata,
                        "similar_orchestrations": similar_orchestrations
                    },
                    template="agent_orchestration",
                    max_tokens=1000
                )
            else:
                orchestration = self._basic_orchestration(
                    content,
                    orchestration_type,
                    similar_orchestrations
                )
                
            # Extract and validate components
            orchestration_result = self._extract_orchestration(orchestration)
            decisions = self._extract_decisions(orchestration)
            issues = self._extract_issues(orchestration)
            
            # Calculate confidence and validity
            confidence = self._calculate_confidence(orchestration_result, decisions, issues)
            is_valid = self._determine_validity(orchestration_result, decisions, issues, confidence)
            
            return OrchestrationResult(
                is_valid=is_valid,
                orchestration=orchestration_result,
                decisions=decisions,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "orchestration_type": orchestration_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Orchestration error: {str(e)}")
            return OrchestrationResult(
                is_valid=False,
                orchestration={},
                decisions=[],
                confidence=0.0,
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_similar_orchestrations(
        self,
        content: Dict[str, Any],
        orchestration_type: str
    ) -> List[Dict]:
        """Get similar orchestrations from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "orchestration",
                        "orchestration_type": orchestration_type
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar orchestrations: {str(e)}")
        return []
            
    def _basic_orchestration(
        self,
        content: Dict[str, Any],
        orchestration_type: str,
        similar_orchestrations: List[Dict]
    ) -> Dict:
        """Basic agent orchestration without LLM."""
        orchestration = {}
        decisions = []
        issues = []
        
        # Basic orchestration rules
        orchestration_rules = {
            "sequential": {
                "has_order": 0.8,
                "has_dependencies": 0.7,
                "has_transitions": 0.6
            },
            "parallel": {
                "has_groups": 0.8,
                "has_coordination": 0.7,
                "has_synchronization": 0.7
            },
            "adaptive": {
                "has_conditions": 0.8,
                "has_fallbacks": 0.7,
                "has_adaptations": 0.6
            }
        }
        
        # Check orchestration type rules
        if orchestration_type in orchestration_rules:
            type_rules = orchestration_rules[orchestration_type]
            
            # Extract basic orchestration structure
            if isinstance(content, dict):
                orchestration = {
                    "type": orchestration_type,
                    "agents": {},
                    "flows": {},
                    "metadata": {}
                }
                
                # Add agents from content
                for key, value in content.items():
                    if isinstance(value, dict):
                        orchestration["agents"][key] = {
                            "type": value.get("type", "unknown"),
                            "priority": value.get("priority", 0.5),
                            "flows": value.get("flows", [])
                        }
                        
                # Add basic decisions
                for rule, confidence in type_rules.items():
                    if self._check_rule(rule, content):
                        decisions.append({
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
                
            # Add similar orchestrations as reference
            if similar_orchestrations:
                orchestration["similar_orchestrations"] = [
                    {
                        "content": s.get("content", {}).get("content", ""),
                        "similarity": s.get("similarity", 0.0),
                        "timestamp": s.get("timestamp", "")
                    }
                    for s in similar_orchestrations
                ]
                
        return {
            "orchestration": orchestration,
            "decisions": decisions,
            "issues": issues
        }
        
    def _check_rule(self, rule: str, content: Dict[str, Any]) -> bool:
        """Check if content satisfies an orchestration rule."""
        if rule == "has_order":
            return bool(content.get("order", []))
        elif rule == "has_dependencies":
            return bool(content.get("dependencies", {}))
        elif rule == "has_transitions":
            return bool(content.get("transitions", {}))
        elif rule == "has_groups":
            return bool(content.get("groups", []))
        elif rule == "has_coordination":
            return bool(content.get("coordination", {}))
        elif rule == "has_synchronization":
            return bool(content.get("synchronization", {}))
        elif rule == "has_conditions":
            return bool(content.get("conditions", {}))
        elif rule == "has_fallbacks":
            return bool(content.get("fallbacks", {}))
        elif rule == "has_adaptations":
            return bool(content.get("adaptations", {}))
        return False
        
    def _extract_orchestration(self, orchestration: Dict) -> Dict:
        """Extract and validate orchestration result."""
        result = orchestration.get("orchestration", {})
        valid_orchestration = {}
        
        if isinstance(result, dict):
            # Extract core orchestration fields
            valid_orchestration["type"] = str(result.get("type", "unknown"))
            valid_orchestration["agents"] = {}
            
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
                        if "flows" in agent:
                            valid_agent["flows"] = agent["flows"]
                        if "metadata" in agent:
                            valid_agent["metadata"] = agent["metadata"]
                            
                        valid_orchestration["agents"][str(name)] = valid_agent
                        
            # Add optional orchestration sections
            if "flows" in result:
                valid_orchestration["flows"] = result["flows"]
            if "metadata" in result:
                valid_orchestration["metadata"] = result["metadata"]
            if "similar_orchestrations" in result:
                valid_orchestration["similar_orchestrations"] = result["similar_orchestrations"]
                
        return valid_orchestration
        
    def _extract_decisions(self, orchestration: Dict) -> List[Dict]:
        """Extract and validate orchestration decisions."""
        decisions = orchestration.get("decisions", [])
        valid_decisions = []
        
        for decision in decisions:
            if isinstance(decision, dict) and "type" in decision:
                valid_decision = {
                    "type": str(decision["type"]),
                    "description": str(decision.get("description", "Unknown decision")),
                    "confidence": float(decision.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "details" in decision:
                    valid_decision["details"] = str(decision["details"])
                if "domain_relevance" in decision:
                    valid_decision["domain_relevance"] = float(decision["domain_relevance"])
                if "importance" in decision:
                    valid_decision["importance"] = float(decision["importance"])
                if "flows" in decision:
                    valid_decision["flows"] = [str(f) for f in decision["flows"]]
                    
                valid_decisions.append(valid_decision)
                
        return valid_decisions
        
    def _extract_issues(self, orchestration: Dict) -> List[Dict]:
        """Extract and validate orchestration issues."""
        issues = orchestration.get("issues", [])
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
                if "related_flows" in issue:
                    valid_issue["related_flows"] = [str(f) for f in issue["related_flows"]]
                    
                valid_issues.append(valid_issue)
                
        return valid_issues
        
    def _calculate_confidence(
        self,
        orchestration: Dict,
        decisions: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall orchestration confidence."""
        if not orchestration or not decisions:
            return 0.0
            
        # Orchestration completeness confidence
        orchestration_conf = 0.0
        if orchestration.get("agents"):
            agent_count = len(orchestration["agents"])
            agent_conf = min(1.0, agent_count * 0.1)  # Cap at 1.0
            orchestration_conf += agent_conf
            
        if orchestration.get("flows"):
            flow_count = len(orchestration["flows"])
            flow_conf = min(1.0, flow_count * 0.1)
            orchestration_conf += flow_conf
            
        orchestration_conf = orchestration_conf / 2 if orchestration_conf > 0 else 0.0
        
        # Decision confidence
        decision_conf = sum(d.get("confidence", 0.5) for d in decisions) / len(decisions)
        
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
        base_conf = (orchestration_conf + decision_conf) / 2
        return max(0.0, base_conf - issue_impact)
        
    def _determine_validity(
        self,
        orchestration: Dict,
        decisions: List[Dict],
        issues: List[Dict],
        confidence: float
    ) -> bool:
        """Determine overall orchestration validity."""
        if not orchestration or not decisions:
            return False
            
        # Check for critical issues
        has_critical_issues = any(
            i.get("severity") == "high"
            for i in issues
        )
        if has_critical_issues:
            return False
            
        # Check decision confidence
        high_confidence_decisions = sum(
            1 for d in decisions
            if d.get("confidence", 0.0) > 0.7
        )
        decision_ratio = high_confidence_decisions / len(decisions)
        
        # Check orchestration completeness
        has_agents = bool(orchestration.get("agents"))
        has_flows = bool(orchestration.get("flows"))
        
        # Consider all factors
        return (
            decision_ratio >= 0.7 and
            confidence >= 0.6 and
            has_agents and
            has_flows
        )
