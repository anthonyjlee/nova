"""Nova's core execution functionality."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class ExecutionResult:
    """Container for execution results."""
    
    def __init__(
        self,
        is_valid: bool,
        execution: Dict,
        actions: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.execution = execution
        self.actions = actions
        self.confidence = confidence
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class ExecutionAgent:
    """Core execution functionality for Nova's ecosystem."""
    
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
        
    async def execute_actions(
        self,
        content: Dict[str, Any],
        execution_type: str,
        metadata: Optional[Dict] = None
    ) -> ExecutionResult:
        """Execute actions with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar executions if vector store available
            similar_executions = []
            if self.vector_store:
                similar_executions = await self._get_similar_executions(
                    content,
                    execution_type
                )
            
            # Analyze with LLM if available
            if self.llm:
                execution = await self.llm.analyze(
                    {
                        "content": content,
                        "execution_type": execution_type,
                        "metadata": metadata,
                        "similar_executions": similar_executions
                    },
                    template="action_execution",
                    max_tokens=1000
                )
            else:
                execution = self._basic_execution(
                    content,
                    execution_type,
                    similar_executions
                )
                
            # Extract and validate components
            execution_result = self._extract_execution(execution)
            actions = self._extract_actions(execution)
            issues = self._extract_issues(execution)
            
            # Calculate confidence and validity
            confidence = self._calculate_confidence(execution_result, actions, issues)
            is_valid = self._determine_validity(execution_result, actions, issues, confidence)
            
            return ExecutionResult(
                is_valid=is_valid,
                execution=execution_result,
                actions=actions,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "execution_type": execution_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Execution error: {str(e)}")
            return ExecutionResult(
                is_valid=False,
                execution={},
                actions=[],
                confidence=0.0,
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_similar_executions(
        self,
        content: Dict[str, Any],
        execution_type: str
    ) -> List[Dict]:
        """Get similar executions from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "execution",
                        "execution_type": execution_type
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar executions: {str(e)}")
        return []
            
    def _basic_execution(
        self,
        content: Dict[str, Any],
        execution_type: str,
        similar_executions: List[Dict]
    ) -> Dict:
        """Basic action execution without LLM."""
        execution = {}
        actions = []
        issues = []
        
        # Basic execution rules
        execution_rules = {
            "sequential": {
                "has_steps": 0.8,
                "has_dependencies": 0.7,
                "has_transitions": 0.6
            },
            "parallel": {
                "has_tasks": 0.8,
                "has_coordination": 0.7,
                "has_synchronization": 0.7
            },
            "adaptive": {
                "has_conditions": 0.8,
                "has_fallbacks": 0.7,
                "has_adaptations": 0.6
            }
        }
        
        # Check execution type rules
        if execution_type in execution_rules:
            type_rules = execution_rules[execution_type]
            
            # Extract basic execution structure
            if isinstance(content, dict):
                execution = {
                    "type": execution_type,
                    "steps": {},
                    "actions": {},
                    "metadata": {}
                }
                
                # Add steps from content
                for key, value in content.items():
                    if isinstance(value, dict):
                        execution["steps"][key] = {
                            "type": value.get("type", "unknown"),
                            "priority": value.get("priority", 0.5),
                            "actions": value.get("actions", [])
                        }
                        
                # Add basic actions
                for rule, confidence in type_rules.items():
                    if self._check_rule(rule, content):
                        actions.append({
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
                
            # Add similar executions as reference
            if similar_executions:
                execution["similar_executions"] = [
                    {
                        "content": s.get("content", {}).get("content", ""),
                        "similarity": s.get("similarity", 0.0),
                        "timestamp": s.get("timestamp", "")
                    }
                    for s in similar_executions
                ]
                
        return {
            "execution": execution,
            "actions": actions,
            "issues": issues
        }
        
    def _check_rule(self, rule: str, content: Dict[str, Any]) -> bool:
        """Check if content satisfies an execution rule."""
        if rule == "has_steps":
            return bool(content.get("steps", []))
        elif rule == "has_dependencies":
            return bool(content.get("dependencies", {}))
        elif rule == "has_transitions":
            return bool(content.get("transitions", {}))
        elif rule == "has_tasks":
            return bool(content.get("tasks", []))
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
        
    def _extract_execution(self, execution: Dict) -> Dict:
        """Extract and validate execution result."""
        result = execution.get("execution", {})
        valid_execution = {}
        
        if isinstance(result, dict):
            # Extract core execution fields
            valid_execution["type"] = str(result.get("type", "unknown"))
            valid_execution["steps"] = {}
            
            # Extract and validate steps
            steps = result.get("steps", {})
            if isinstance(steps, dict):
                for name, step in steps.items():
                    if isinstance(step, dict):
                        valid_step = {
                            "type": str(step.get("type", "unknown")),
                            "priority": float(step.get("priority", 0.5))
                        }
                        
                        # Add optional step attributes
                        if "description" in step:
                            valid_step["description"] = str(step["description"])
                        if "actions" in step:
                            valid_step["actions"] = step["actions"]
                        if "metadata" in step:
                            valid_step["metadata"] = step["metadata"]
                            
                        valid_execution["steps"][str(name)] = valid_step
                        
            # Add optional execution sections
            if "actions" in result:
                valid_execution["actions"] = result["actions"]
            if "metadata" in result:
                valid_execution["metadata"] = result["metadata"]
            if "similar_executions" in result:
                valid_execution["similar_executions"] = result["similar_executions"]
                
        return valid_execution
        
    def _extract_actions(self, execution: Dict) -> List[Dict]:
        """Extract and validate execution actions."""
        actions = execution.get("actions", [])
        valid_actions = []
        
        for action in actions:
            if isinstance(action, dict) and "type" in action:
                valid_action = {
                    "type": str(action["type"]),
                    "description": str(action.get("description", "Unknown action")),
                    "confidence": float(action.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "details" in action:
                    valid_action["details"] = str(action["details"])
                if "domain_relevance" in action:
                    valid_action["domain_relevance"] = float(action["domain_relevance"])
                if "importance" in action:
                    valid_action["importance"] = float(action["importance"])
                if "steps" in action:
                    valid_action["steps"] = [str(s) for s in action["steps"]]
                    
                valid_actions.append(valid_action)
                
        return valid_actions
        
    def _extract_issues(self, execution: Dict) -> List[Dict]:
        """Extract and validate execution issues."""
        issues = execution.get("issues", [])
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
                if "related_steps" in issue:
                    valid_issue["related_steps"] = [str(s) for s in issue["related_steps"]]
                    
                valid_issues.append(valid_issue)
                
        return valid_issues
        
    def _calculate_confidence(
        self,
        execution: Dict,
        actions: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall execution confidence."""
        if not execution or not actions:
            return 0.0
            
        # Execution completeness confidence
        execution_conf = 0.0
        if execution.get("steps"):
            step_count = len(execution["steps"])
            step_conf = min(1.0, step_count * 0.1)  # Cap at 1.0
            execution_conf += step_conf
            
        if execution.get("actions"):
            action_count = len(execution["actions"])
            action_conf = min(1.0, action_count * 0.1)
            execution_conf += action_conf
            
        execution_conf = execution_conf / 2 if execution_conf > 0 else 0.0
        
        # Action confidence
        action_conf = sum(a.get("confidence", 0.5) for a in actions) / len(actions)
        
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
        base_conf = (execution_conf + action_conf) / 2
        return max(0.0, base_conf - issue_impact)
        
    def _determine_validity(
        self,
        execution: Dict,
        actions: List[Dict],
        issues: List[Dict],
        confidence: float
    ) -> bool:
        """Determine overall execution validity."""
        if not execution or not actions:
            return False
            
        # Check for critical issues
        has_critical_issues = any(
            i.get("severity") == "high"
            for i in issues
        )
        if has_critical_issues:
            return False
            
        # Check action confidence
        high_confidence_actions = sum(
            1 for a in actions
            if a.get("confidence", 0.0) > 0.7
        )
        action_ratio = high_confidence_actions / len(actions)
        
        # Check execution completeness
        has_steps = bool(execution.get("steps"))
        has_actions = bool(execution.get("actions"))
        
        # Consider all factors
        return (
            action_ratio >= 0.7 and
            confidence >= 0.6 and
            has_steps and
            has_actions
        )
