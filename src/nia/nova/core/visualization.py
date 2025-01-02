"""Nova's core visualization functionality."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class VisualizationResult:
    """Container for visualization results."""
    
    def __init__(
        self,
        is_valid: bool,
        visualization: Dict,
        elements: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.visualization = visualization
        self.elements = elements
        self.confidence = confidence
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class VisualizationAgent:
    """Core visualization functionality for Nova's ecosystem."""
    
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
        
    async def process_visualization(
        self,
        content: Dict[str, Any],
        visualization_type: str,
        metadata: Optional[Dict] = None
    ) -> VisualizationResult:
        """Process visualization with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar visualization if vector store available
            similar_visualization = []
            if self.vector_store:
                similar_visualization = await self._get_similar_visualization(
                    content,
                    visualization_type
                )
            
            # Analyze with LLM if available
            if self.llm:
                visualization = await self.llm.analyze(
                    {
                        "content": content,
                        "visualization_type": visualization_type,
                        "metadata": metadata,
                        "similar_visualization": similar_visualization
                    },
                    template="visualization_processing",
                    max_tokens=1000
                )
            else:
                visualization = self._basic_visualization(
                    content,
                    visualization_type,
                    similar_visualization
                )
                
            # Extract and validate components
            visualization_result = self._extract_visualization(visualization)
            elements = self._extract_elements(visualization)
            issues = self._extract_issues(visualization)
            
            # Calculate confidence and validity
            confidence = self._calculate_confidence(visualization_result, elements, issues)
            is_valid = self._determine_validity(visualization_result, elements, issues, confidence)
            
            return VisualizationResult(
                is_valid=is_valid,
                visualization=visualization_result,
                elements=elements,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "visualization_type": visualization_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Visualization error: {str(e)}")
            return VisualizationResult(
                is_valid=False,
                visualization={},
                elements=[],
                confidence=0.0,
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_similar_visualization(
        self,
        content: Dict[str, Any],
        visualization_type: str
    ) -> List[Dict]:
        """Get similar visualization from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "visualization",
                        "visualization_type": visualization_type
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar visualization: {str(e)}")
        return []
            
    def _basic_visualization(
        self,
        content: Dict[str, Any],
        visualization_type: str,
        similar_visualization: List[Dict]
    ) -> Dict:
        """Basic visualization processing without LLM."""
        visualization = {}
        elements = []
        issues = []
        
        # Basic visualization rules
        visualization_rules = {
            "chart": {
                "has_data": 0.8,
                "has_axes": 0.7,
                "has_labels": 0.6
            },
            "graph": {
                "has_nodes": 0.8,
                "has_edges": 0.7,
                "has_layout": 0.7
            },
            "diagram": {
                "has_shapes": 0.8,
                "has_connections": 0.7,
                "has_annotations": 0.6
            }
        }
        
        # Check visualization type rules
        if visualization_type in visualization_rules:
            type_rules = visualization_rules[visualization_type]
            
            # Extract basic visualization structure
            if isinstance(content, dict):
                visualization = {
                    "type": visualization_type,
                    "visualization": {},
                    "metadata": {}
                }
                
                # Add visualization from content
                for key, value in content.items():
                    if isinstance(value, dict):
                        visualization["visualization"][key] = {
                            "type": value.get("type", "unknown"),
                            "data": value.get("data", {}),
                            "style": value.get("style", {})
                        }
                        
                # Add basic elements
                for rule, confidence in type_rules.items():
                    if self._check_rule(rule, content):
                        elements.append({
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
                
            # Add similar visualization as reference
            if similar_visualization:
                visualization["similar_visualization"] = [
                    {
                        "content": s.get("content", {}).get("content", ""),
                        "similarity": s.get("similarity", 0.0),
                        "timestamp": s.get("timestamp", "")
                    }
                    for s in similar_visualization
                ]
                
        return {
            "visualization": visualization,
            "elements": elements,
            "issues": issues
        }
        
    def _check_rule(self, rule: str, content: Dict[str, Any]) -> bool:
        """Check if content satisfies a visualization rule."""
        if rule == "has_data":
            return bool(content.get("data", []))
        elif rule == "has_axes":
            return bool(content.get("axes", {}))
        elif rule == "has_labels":
            return bool(content.get("labels", {}))
        elif rule == "has_nodes":
            return bool(content.get("nodes", {}))
        elif rule == "has_edges":
            return bool(content.get("edges", {}))
        elif rule == "has_layout":
            return bool(content.get("layout", {}))
        elif rule == "has_shapes":
            return bool(content.get("shapes", {}))
        elif rule == "has_connections":
            return bool(content.get("connections", {}))
        elif rule == "has_annotations":
            return bool(content.get("annotations", {}))
        return False
        
    def _extract_visualization(self, visualization: Dict) -> Dict:
        """Extract and validate visualization result."""
        result = visualization.get("visualization", {})
        valid_visualization = {}
        
        if isinstance(result, dict):
            # Extract core visualization fields
            valid_visualization["type"] = str(result.get("type", "unknown"))
            valid_visualization["visualization"] = {}
            
            # Extract and validate visualization
            visualization_data = result.get("visualization", {})
            if isinstance(visualization_data, dict):
                for name, visual in visualization_data.items():
                    if isinstance(visual, dict):
                        valid_visual = {
                            "type": str(visual.get("type", "unknown")),
                            "data": visual.get("data", {}),
                            "style": visual.get("style", {})
                        }
                        
                        # Add optional visual attributes
                        if "description" in visual:
                            valid_visual["description"] = str(visual["description"])
                        if "layout" in visual:
                            valid_visual["layout"] = visual["layout"]
                        if "metadata" in visual:
                            valid_visual["metadata"] = visual["metadata"]
                            
                        valid_visualization["visualization"][str(name)] = valid_visual
                        
            # Add optional visualization sections
            if "metadata" in result:
                valid_visualization["metadata"] = result["metadata"]
            if "similar_visualization" in result:
                valid_visualization["similar_visualization"] = result["similar_visualization"]
                
        return valid_visualization
        
    def _extract_elements(self, visualization: Dict) -> List[Dict]:
        """Extract and validate visualization elements."""
        elements = visualization.get("elements", [])
        valid_elements = []
        
        for element in elements:
            if isinstance(element, dict) and "type" in element:
                valid_element = {
                    "type": str(element["type"]),
                    "description": str(element.get("description", "Unknown element")),
                    "confidence": float(element.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "details" in element:
                    valid_element["details"] = str(element["details"])
                if "domain_relevance" in element:
                    valid_element["domain_relevance"] = float(element["domain_relevance"])
                if "importance" in element:
                    valid_element["importance"] = float(element["importance"])
                if "layout" in element:
                    valid_element["layout"] = element["layout"]
                    
                valid_elements.append(valid_element)
                
        return valid_elements
        
    def _extract_issues(self, visualization: Dict) -> List[Dict]:
        """Extract and validate visualization issues."""
        issues = visualization.get("issues", [])
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
                if "layout" in issue:
                    valid_issue["layout"] = issue["layout"]
                    
                valid_issues.append(valid_issue)
                
        return valid_issues
        
    def _calculate_confidence(
        self,
        visualization: Dict,
        elements: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall visualization confidence."""
        if not visualization or not elements:
            return 0.0
            
        # Visualization completeness confidence
        visualization_conf = 0.0
        if visualization.get("visualization"):
            visual_count = len(visualization["visualization"])
            visual_conf = min(1.0, visual_count * 0.1)  # Cap at 1.0
            visualization_conf += visual_conf
            
        if visualization.get("metadata"):
            meta_count = len(visualization["metadata"])
            meta_conf = min(1.0, meta_count * 0.1)
            visualization_conf += meta_conf
            
        visualization_conf = visualization_conf / 2 if visualization_conf > 0 else 0.0
        
        # Element confidence
        element_conf = sum(e.get("confidence", 0.5) for e in elements) / len(elements)
        
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
        base_conf = (visualization_conf + element_conf) / 2
        return max(0.0, base_conf - issue_impact)
        
    def _determine_validity(
        self,
        visualization: Dict,
        elements: List[Dict],
        issues: List[Dict],
        confidence: float
    ) -> bool:
        """Determine overall visualization validity."""
        if not visualization or not elements:
            return False
            
        # Check for critical issues
        has_critical_issues = any(
            i.get("severity") == "high"
            for i in issues
        )
        if has_critical_issues:
            return False
            
        # Check element confidence
        high_confidence_elements = sum(
            1 for e in elements
            if e.get("confidence", 0.0) > 0.7
        )
        element_ratio = high_confidence_elements / len(elements)
        
        # Check visualization completeness
        has_visualization = bool(visualization.get("visualization"))
        has_metadata = bool(visualization.get("metadata"))
        
        # Consider all factors
        return (
            element_ratio >= 0.7 and
            confidence >= 0.6 and
            has_visualization and
            has_metadata
        )
