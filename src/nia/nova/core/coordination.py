"""Nova's core coordination functionality."""

import logging
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

logger = logging.getLogger(__name__)

class CoordinationResult:
    """Container for coordination results."""
    
    def __init__(
        self,
        is_valid: bool,
        groups: Dict[str, Dict],
        assignments: Dict[str, List[str]],
        resources: Dict[str, Any],
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.groups = groups
        self.assignments = assignments
        self.resources = resources
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class CoordinationAgent:
    """Core coordination functionality for Nova's ecosystem."""
    
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
        
        # Initialize coordination state
        self.active_groups: Dict[str, Dict] = {}
        self.agent_assignments: Dict[str, Set[str]] = {}
        self.resource_allocations: Dict[str, Dict] = {}
        self.task_dependencies: Dict[str, Set[str]] = {}
        
    async def process_coordination(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> CoordinationResult:
        """Process coordination with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get coordination history if vector store available
            coordination_history = []
            if self.vector_store:
                coordination_history = await self._get_coordination_history(content)
            
            # Analyze with LLM if available
            if self.llm:
                coordination = await self.llm.analyze(
                    {
                        "content": content,
                        "metadata": metadata,
                        "coordination_history": coordination_history
                    },
                    template="coordination_processing",
                    max_tokens=1000
                )
            else:
                coordination = self._basic_coordination(content, coordination_history)
                
            # Extract and validate components
            groups = self._extract_groups(coordination)
            assignments = self._extract_assignments(coordination)
            resources = self._extract_resources(coordination)
            issues = self._extract_issues(coordination)
            
            # Calculate validity
            is_valid = self._determine_validity(groups, assignments, resources, issues)
            
            return CoordinationResult(
                is_valid=is_valid,
                groups=groups,
                assignments=assignments,
                resources=resources,
                metadata={
                    "domain": self.domain,
                    "content_type": content.get("type", "coordination"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Coordination error: {str(e)}")
            return CoordinationResult(
                is_valid=False,
                groups={},
                assignments={},
                resources={},
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_coordination_history(self, content: Dict[str, Any]) -> List[Dict]:
        """Get coordination history from vector store."""
        try:
            if "group_id" in content:
                results = await self.vector_store.search(
                    content["group_id"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "coordination"
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting coordination history: {str(e)}")
        return []
            
    def _basic_coordination(
        self,
        content: Dict[str, Any],
        coordination_history: List[Dict]
    ) -> Dict:
        """Basic coordination processing without LLM."""
        groups = {}
        assignments = {}
        resources = {}
        issues = []
        
        # Extract group information
        if "groups" in content:
            for group_id, group_data in content["groups"].items():
                if isinstance(group_data, dict):
                    groups[group_id] = {
                        "name": group_data.get("name", group_id),
                        "type": group_data.get("type", "default"),
                        "status": group_data.get("status", "active"),
                        "metadata": group_data.get("metadata", {})
                    }
                    
        # Extract agent assignments
        if "assignments" in content:
            for agent_id, group_ids in content["assignments"].items():
                if isinstance(group_ids, (list, set)):
                    assignments[agent_id] = list(group_ids)
                    
        # Extract resource allocations
        if "resources" in content:
            for resource_id, allocation in content["resources"].items():
                if isinstance(allocation, dict):
                    resources[resource_id] = {
                        "type": allocation.get("type", "unknown"),
                        "amount": allocation.get("amount", 0),
                        "assigned_to": allocation.get("assigned_to", [])
                    }
                    
        # Add coordination history context
        if coordination_history:
            for entry in coordination_history:
                # Check for resource conflicts
                if "resources" in entry.get("content", {}):
                    for resource_id, allocation in entry["content"]["resources"].items():
                        if resource_id in resources:
                            issues.append({
                                "type": "resource_conflict",
                                "severity": "medium",
                                "description": f"Resource {resource_id} has conflicting allocations"
                            })
                            
        return {
            "groups": groups,
            "assignments": assignments,
            "resources": resources,
            "issues": issues
        }
        
    def _extract_groups(self, coordination: Dict) -> Dict[str, Dict]:
        """Extract and validate groups."""
        groups = coordination.get("groups", {})
        valid_groups = {}
        
        for group_id, group in groups.items():
            if isinstance(group, dict):
                valid_group = {
                    "name": str(group.get("name", group_id)),
                    "type": str(group.get("type", "default")),
                    "status": str(group.get("status", "active")),
                    "metadata": group.get("metadata", {})
                }
                
                # Add optional fields
                if "description" in group:
                    valid_group["description"] = str(group["description"])
                if "priority" in group:
                    valid_group["priority"] = float(group["priority"])
                if "dependencies" in group:
                    valid_group["dependencies"] = list(group["dependencies"])
                    
                valid_groups[str(group_id)] = valid_group
                
        return valid_groups
        
    def _extract_assignments(self, coordination: Dict) -> Dict[str, List[str]]:
        """Extract and validate assignments."""
        assignments = coordination.get("assignments", {})
        valid_assignments = {}
        
        for agent_id, group_ids in assignments.items():
            if isinstance(group_ids, (list, set)):
                valid_assignments[str(agent_id)] = [
                    str(group_id) for group_id in group_ids
                ]
                
        return valid_assignments
        
    def _extract_resources(self, coordination: Dict) -> Dict[str, Any]:
        """Extract and validate resources."""
        resources = coordination.get("resources", {})
        valid_resources = {}
        
        for resource_id, allocation in resources.items():
            if isinstance(allocation, dict):
                valid_allocation = {
                    "type": str(allocation.get("type", "unknown")),
                    "amount": float(allocation.get("amount", 0)),
                    "assigned_to": list(allocation.get("assigned_to", []))
                }
                
                # Add optional fields
                if "priority" in allocation:
                    valid_allocation["priority"] = float(allocation["priority"])
                if "constraints" in allocation:
                    valid_allocation["constraints"] = allocation["constraints"]
                if "metadata" in allocation:
                    valid_allocation["metadata"] = allocation["metadata"]
                    
                valid_resources[str(resource_id)] = valid_allocation
                
        return valid_resources
        
    def _extract_issues(self, coordination: Dict) -> List[Dict]:
        """Extract and validate issues."""
        issues = coordination.get("issues", [])
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
                if "impact" in issue:
                    valid_issue["impact"] = float(issue["impact"])
                if "suggested_fix" in issue:
                    valid_issue["suggested_fix"] = str(issue["suggested_fix"])
                    
                valid_issues.append(valid_issue)
                
        return valid_issues
        
    def _determine_validity(
        self,
        groups: Dict[str, Dict],
        assignments: Dict[str, List[str]],
        resources: Dict[str, Any],
        issues: List[Dict]
    ) -> bool:
        """Determine overall coordination validity."""
        if not groups:
            return False
            
        # Check for critical issues
        has_critical_issues = any(
            i.get("severity") == "high"
            for i in issues
        )
        if has_critical_issues:
            return False
            
        # Verify group assignments
        for agent_id, group_ids in assignments.items():
            if not all(group_id in groups for group_id in group_ids):
                return False
                
        # Verify resource allocations
        for resource_id, allocation in resources.items():
            if allocation["amount"] < 0:
                return False
            if not all(
                agent_id in assignments
                for agent_id in allocation["assigned_to"]
            ):
                return False
                
        return True
