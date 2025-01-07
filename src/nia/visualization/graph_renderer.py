"""Graph visualization implementation."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class GraphRenderer:
    """Renders graph visualizations for UI."""
    
    def __init__(self):
        """Initialize renderer."""
        self.layout_config = {
            "dag": {
                "rankdir": "TB",  # Top to bottom
                "node_spacing": 50,
                "rank_spacing": 50,
                "edge_routing": "orthogonal"
            },
            "pattern": {
                "layout": "force",  # Force-directed
                "node_spacing": 100,
                "edge_length": 200,
                "charge": -400
            }
        }
    
    def render_dag(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Render DAG visualization."""
        try:
            # Apply configuration
            layout = {
                **self.layout_config["dag"],
                **(config or {})
            }
            
            # Process nodes
            processed_nodes = []
            for node in nodes:
                processed_nodes.append({
                    "id": node["id"],
                    "label": node.get("label", node["id"]),
                    "type": node.get("type", "default"),
                    "status": node.get("status", "pending"),
                    "data": {
                        "start_time": node.get("start_time"),
                        "end_time": node.get("end_time"),
                        "duration": self._calculate_duration(
                            node.get("start_time"),
                            node.get("end_time")
                        ),
                        "error": node.get("error")
                    },
                    "style": self._get_node_style(node)
                })
            
            # Process edges
            processed_edges = []
            for edge in edges:
                processed_edges.append({
                    "id": f"{edge['from']}-{edge['to']}",
                    "source": edge["from"],
                    "target": edge["to"],
                    "type": edge.get("type", "default"),
                    "style": self._get_edge_style(edge)
                })
            
            return {
                "type": "dag",
                "layout": layout,
                "nodes": processed_nodes,
                "edges": processed_edges,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error rendering DAG: {str(e)}")
            raise
    
    def render_pattern(
        self,
        pattern: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Render pattern visualization."""
        try:
            # Apply configuration
            layout = {
                **self.layout_config["pattern"],
                **(config or {})
            }
            
            # Extract nodes and edges from pattern
            nodes = []
            edges = []
            
            # Process tasks as nodes
            tasks = pattern.get("config", {}).get("tasks", [])
            for task in tasks:
                nodes.append({
                    "id": task["id"],
                    "label": task.get("label", task["id"]),
                    "type": task["type"],
                    "data": {
                        "config": task.get("config", {}),
                        "metadata": task.get("metadata", {})
                    },
                    "style": self._get_pattern_node_style(task)
                })
                
                # Process dependencies as edges
                for dep_id in task.get("dependencies", []):
                    edges.append({
                        "id": f"{dep_id}-{task['id']}",
                        "source": dep_id,
                        "target": task["id"],
                        "type": "dependency",
                        "style": self._get_pattern_edge_style("dependency")
                    })
            
            return {
                "type": "pattern",
                "layout": layout,
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "pattern_id": pattern.get("id"),
                    "pattern_type": pattern.get("type"),
                    "created_at": pattern.get("created_at"),
                    "updated_at": pattern.get("updated_at")
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error rendering pattern: {str(e)}")
            raise
    
    def render_integrated_view(
        self,
        pattern: Dict[str, Any],
        execution: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Render integrated pattern and execution view."""
        try:
            # Render both views
            pattern_view = self.render_pattern(pattern, config)
            
            # Extract nodes and edges from execution
            execution_nodes = []
            execution_edges = []
            
            graph_state = execution.get("graph_state", {})
            nodes = graph_state.get("nodes", {})
            edges = graph_state.get("edges", {})
            
            # Process execution nodes
            for node_id, node in nodes.items():
                execution_nodes.append({
                    "id": node_id,
                    "label": node.get("label", node_id),
                    "type": node["task_type"],
                    "status": node["status"],
                    "data": {
                        "start_time": node.get("start_time"),
                        "end_time": node.get("end_time"),
                        "duration": self._calculate_duration(
                            node.get("start_time"),
                            node.get("end_time")
                        ),
                        "error": node.get("error")
                    },
                    "style": self._get_node_style(node)
                })
            
            # Process execution edges
            for source, targets in edges.items():
                for target in targets:
                    execution_edges.append({
                        "id": f"{source}-{target}",
                        "source": source,
                        "target": target,
                        "type": "execution",
                        "style": self._get_edge_style({"type": "execution"})
                    })
            
            # Combine views
            return {
                "type": "integrated",
                "pattern_view": pattern_view,
                "execution_view": {
                    "type": "execution",
                    "layout": self.layout_config["dag"],
                    "nodes": execution_nodes,
                    "edges": execution_edges,
                    "metadata": {
                        "execution_id": execution.get("id"),
                        "status": execution.get("status"),
                        "created_at": execution.get("created_at"),
                        "completed_at": execution.get("completed_at")
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error rendering integrated view: {str(e)}")
            raise
    
    def _calculate_duration(
        self,
        start_time: Optional[str],
        end_time: Optional[str]
    ) -> Optional[float]:
        """Calculate duration between timestamps."""
        try:
            if start_time and end_time:
                start = datetime.fromisoformat(start_time)
                end = datetime.fromisoformat(end_time)
                return (end - start).total_seconds()
            return None
        except Exception as e:
            logger.error(f"Error calculating duration: {str(e)}")
            return None
    
    def _get_node_style(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Get node styling based on state."""
        status_colors = {
            "pending": "#gray",
            "running": "#blue",
            "completed": "#green",
            "failed": "#red"
        }
        
        return {
            "shape": "circle",
            "size": 40,
            "color": status_colors.get(node.get("status", "pending"), "#gray"),
            "border_color": "#black",
            "border_width": 2,
            "font_size": 12,
            "font_color": "#black"
        }
    
    def _get_edge_style(self, edge: Dict[str, Any]) -> Dict[str, Any]:
        """Get edge styling based on type."""
        return {
            "line_style": "solid",
            "line_color": "#black",
            "line_width": 2,
            "arrow_size": 10,
            "arrow_color": "#black"
        }
    
    def _get_pattern_node_style(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get pattern node styling based on type."""
        type_colors = {
            "supervisor": "#purple",
            "worker": "#blue",
            "voter": "#orange",
            "default": "#gray"
        }
        
        return {
            "shape": "rectangle",
            "size": 50,
            "color": type_colors.get(task.get("type", "default"), "#gray"),
            "border_color": "#black",
            "border_width": 2,
            "font_size": 14,
            "font_color": "#white"
        }
    
    def _get_pattern_edge_style(self, edge_type: str) -> Dict[str, Any]:
        """Get pattern edge styling based on type."""
        type_styles = {
            "dependency": {
                "line_style": "solid",
                "line_color": "#black",
                "line_width": 2
            },
            "communication": {
                "line_style": "dashed",
                "line_color": "#blue",
                "line_width": 1
            },
            "default": {
                "line_style": "solid",
                "line_color": "#gray",
                "line_width": 1
            }
        }
        
        return type_styles.get(edge_type, type_styles["default"])
