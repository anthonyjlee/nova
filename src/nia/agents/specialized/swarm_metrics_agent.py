"""Swarm Metrics Agent for tracking swarm performance and behavior."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import json

from ..tinytroupe_agent import TinyTroupeAgent
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.neo4j.base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)

class SwarmMetricsAgent(TinyTroupeAgent):
    """Tracks swarm performance metrics."""
    
    def __init__(
        self,
        name: str = "swarm_metrics",
        memory_system: Optional[TwoLayerMemorySystem] = None,
        domain: str = "swarm_management",
        **kwargs
    ):
        """Initialize SwarmMetricsAgent."""
        super().__init__(name=name, memory_system=memory_system, domain=domain, **kwargs)
        self.store = self.memory_system.semantic.store if memory_system else None
    
    async def collect_metrics(
        self,
        swarm_id: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect swarm performance data.
        
        Args:
            swarm_id: ID of the swarm
            metrics: Dictionary of performance metrics
            
        Returns:
            Dict containing collection status
        """
        try:
            # Prepare metrics data
            metrics_data = {
                "id": str(uuid.uuid4()),
                "swarm_id": swarm_id,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in Neo4j
            query = """
            MATCH (s:Swarm {id: $swarm_id})
            CREATE (m:SwarmMetrics {
                id: $id,
                metrics: $metrics,
                timestamp: $timestamp
            })
            CREATE (s)-[:HAS_METRICS]->(m)
            RETURN m
            """
            
            await self.store.run_query(
                query,
                parameters=metrics_data
            )
            
            # Store in vector store for temporal analysis
            await self.memory_system.vector_store.store_vector(
                content=metrics_data,
                metadata={"type": "swarm_metrics"},
                layer="episodic"
            )
            
            return {
                "metrics_id": metrics_data["id"],
                "collection_status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            return {
                "metrics_id": None,
                "collection_status": "failed",
                "error": str(e)
            }
    
    async def analyze_patterns(
        self,
        swarm_id: str,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Analyze swarm behavior patterns.
        
        Args:
            swarm_id: ID of the swarm to analyze
            time_window: Optional time window for analysis
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Build time window condition
            time_condition = ""
            parameters = {"swarm_id": swarm_id}
            
            if time_window:
                cutoff = datetime.now() - time_window
                time_condition = "AND m.timestamp >= $cutoff"
                parameters["cutoff"] = cutoff.isoformat()
            
            # Get metrics data
            query = f"""
            MATCH (s:Swarm {{id: $swarm_id}})-[:HAS_METRICS]->(m:SwarmMetrics)
            WHERE true {time_condition}
            RETURN m
            ORDER BY m.timestamp DESC
            """
            
            result = await self.store.run_query(query, parameters=parameters)
            metrics_data = [dict(row["m"]) for row in result]
            
            # Analyze patterns
            patterns = {
                "performance_trends": self._analyze_performance_trends(metrics_data),
                "resource_utilization": self._analyze_resource_utilization(metrics_data),
                "error_patterns": self._analyze_error_patterns(metrics_data),
                "optimization_opportunities": self._identify_optimization_opportunities(metrics_data)
            }
            
            return {
                "analysis_status": "success",
                "patterns": patterns,
                "metrics_analyzed": len(metrics_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {str(e)}")
            return {
                "analysis_status": "failed",
                "error": str(e)
            }
    
    def _analyze_performance_trends(
        self,
        metrics_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze performance trends from metrics data."""
        try:
            trends = {
                "response_time": [],
                "throughput": [],
                "success_rate": []
            }
            
            for metric in metrics_data:
                if "metrics" in metric:
                    m = metric["metrics"]
                    if "response_time" in m:
                        trends["response_time"].append(m["response_time"])
                    if "throughput" in m:
                        trends["throughput"].append(m["throughput"])
                    if "success_rate" in m:
                        trends["success_rate"].append(m["success_rate"])
            
            # Calculate trend statistics
            stats = {}
            for key, values in trends.items():
                if values:
                    stats[key] = {
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "trend": "improving" if values[-1] > values[0] else "declining"
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {str(e)}")
            return {}
    
    def _analyze_resource_utilization(
        self,
        metrics_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze resource utilization patterns."""
        try:
            utilization = {
                "memory": [],
                "cpu": [],
                "network": []
            }
            
            for metric in metrics_data:
                if "metrics" in metric:
                    m = metric["metrics"]
                    if "memory_usage" in m:
                        utilization["memory"].append(m["memory_usage"])
                    if "cpu_usage" in m:
                        utilization["cpu"].append(m["cpu_usage"])
                    if "network_usage" in m:
                        utilization["network"].append(m["network_usage"])
            
            # Calculate utilization statistics
            stats = {}
            for key, values in utilization.items():
                if values:
                    stats[key] = {
                        "average": sum(values) / len(values),
                        "peak": max(values),
                        "bottleneck": max(values) > 0.9  # Flag if utilization exceeds 90%
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error analyzing resource utilization: {str(e)}")
            return {}
    
    def _analyze_error_patterns(
        self,
        metrics_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze error patterns and frequencies."""
        try:
            error_counts = {}
            total_operations = 0
            
            for metric in metrics_data:
                if "metrics" in metric and "errors" in metric["metrics"]:
                    errors = metric["metrics"]["errors"]
                    for error in errors:
                        error_type = error.get("type", "unknown")
                        error_counts[error_type] = error_counts.get(error_type, 0) + 1
                
                if "metrics" in metric and "total_operations" in metric["metrics"]:
                    total_operations += metric["metrics"]["total_operations"]
            
            # Calculate error statistics
            if total_operations > 0:
                error_stats = {
                    "total_errors": sum(error_counts.values()),
                    "error_rate": sum(error_counts.values()) / total_operations,
                    "error_distribution": error_counts,
                    "most_common_error": max(error_counts.items(), key=lambda x: x[1])[0] if error_counts else None
                }
            else:
                error_stats = {
                    "total_errors": 0,
                    "error_rate": 0,
                    "error_distribution": {},
                    "most_common_error": None
                }
            
            return error_stats
            
        except Exception as e:
            logger.error(f"Error analyzing error patterns: {str(e)}")
            return {}
    
    def _identify_optimization_opportunities(
        self,
        metrics_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify potential optimization opportunities."""
        try:
            opportunities = []
            
            # Analyze performance bottlenecks
            perf_trends = self._analyze_performance_trends(metrics_data)
            for metric, stats in perf_trends.items():
                if stats.get("trend") == "declining":
                    opportunities.append({
                        "type": "performance",
                        "metric": metric,
                        "description": f"Declining {metric} trend detected",
                        "priority": "high"
                    })
            
            # Analyze resource bottlenecks
            resource_stats = self._analyze_resource_utilization(metrics_data)
            for resource, stats in resource_stats.items():
                if stats.get("bottleneck"):
                    opportunities.append({
                        "type": "resource",
                        "resource": resource,
                        "description": f"High {resource} utilization detected",
                        "priority": "medium"
                    })
            
            # Analyze error patterns
            error_stats = self._analyze_error_patterns(metrics_data)
            if error_stats.get("error_rate", 0) > 0.1:  # Error rate > 10%
                opportunities.append({
                    "type": "reliability",
                    "description": "High error rate detected",
                    "error_type": error_stats.get("most_common_error"),
                    "priority": "high"
                })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error identifying optimization opportunities: {str(e)}")
            return []
    
    async def generate_insights(
        self,
        swarm_id: str,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate performance insights.
        
        Args:
            swarm_id: ID of the swarm
            analysis_results: Results from pattern analysis
            
        Returns:
            Dict containing insights
        """
        try:
            insights = []
            
            # Performance insights
            if "patterns" in analysis_results:
                patterns = analysis_results["patterns"]
                
                # Performance trend insights
                if "performance_trends" in patterns:
                    perf_trends = patterns["performance_trends"]
                    for metric, stats in perf_trends.items():
                        if stats.get("trend") == "declining":
                            insights.append({
                                "type": "performance_alert",
                                "severity": "high",
                                "description": f"Declining {metric} performance detected",
                                "recommendation": f"Investigate causes of {metric} degradation"
                            })
                
                # Resource utilization insights
                if "resource_utilization" in patterns:
                    resources = patterns["resource_utilization"]
                    for resource, stats in resources.items():
                        if stats.get("bottleneck"):
                            insights.append({
                                "type": "resource_alert",
                                "severity": "medium",
                                "description": f"High {resource} utilization",
                                "recommendation": f"Consider scaling {resource} allocation"
                            })
                
                # Error pattern insights
                if "error_patterns" in patterns:
                    error_stats = patterns["error_patterns"]
                    if error_stats.get("error_rate", 0) > 0.1:
                        insights.append({
                            "type": "reliability_alert",
                            "severity": "high",
                            "description": "High error rate detected",
                            "recommendation": "Investigate and address common error patterns"
                        })
            
            # Store insights
            insight_data = {
                "id": str(uuid.uuid4()),
                "swarm_id": swarm_id,
                "insights": insights,
                "timestamp": datetime.now().isoformat()
            }
            
            query = """
            MATCH (s:Swarm {id: $swarm_id})
            CREATE (i:SwarmInsights {
                id: $id,
                insights: $insights,
                timestamp: $timestamp
            })
            CREATE (s)-[:HAS_INSIGHTS]->(i)
            RETURN i
            """
            
            await self.store.run_query(
                query,
                parameters=insight_data
            )
            
            return {
                "insight_id": insight_data["id"],
                "insights": insights,
                "generation_status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {
                "insight_id": None,
                "insights": [],
                "generation_status": "failed",
                "error": str(e)
            }
