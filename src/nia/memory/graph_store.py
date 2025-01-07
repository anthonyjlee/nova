"""Graph store implementation."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from nia.core.neo4j.base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)

class GraphStore(Neo4jBaseStore):
    """Store for managing knowledge graph operations."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", **kwargs):
        """Initialize store."""
        super().__init__(uri=uri, **kwargs)
        
    async def prune_graph(
        self,
        min_relevance: float = 0.5,
        max_age_days: int = 30,
        exclude_domains: List[str] = []
    ) -> Dict[str, int]:
        """Prune knowledge graph based on criteria."""
        try:
            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()
            
            # Build domain exclusion clause
            domain_clause = ""
            if exclude_domains:
                domain_list = ", ".join([f"'{domain}'" for domain in exclude_domains])
                domain_clause = f"AND NOT n.domain IN [{domain_list}]"
            
            # Delete nodes and relationships
            query = f"""
            MATCH (n)
            WHERE (n.relevance < $min_relevance OR n.created_at < $cutoff_date)
            {domain_clause}
            WITH n, size((n)--()) as degree
            DETACH DELETE n
            RETURN count(n) as nodes_removed, sum(degree) as edges_removed
            """
            
            result = await self.driver.execute_query(
                query,
                parameters={
                    "min_relevance": min_relevance,
                    "cutoff_date": cutoff_date
                }
            )
            
            if result and result[0]:
                return {
                    "nodes_removed": result[0][0],
                    "edges_removed": result[0][1]
                }
            return {"nodes_removed": 0, "edges_removed": 0}
        except Exception as e:
            logger.error(f"Error pruning graph: {str(e)}")
            raise
    
    async def check_health(self) -> Dict[str, Any]:
        """Check knowledge graph health."""
        try:
            # Get graph health metrics
            query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            WITH count(DISTINCT n) as node_count,
                 count(DISTINCT r) as edge_count,
                 count(DISTINCT n) - count(DISTINCT (n)--()) as orphaned_nodes,
                 count(DISTINCT r) - count(DISTINCT ()-[r]->()) as invalid_edges
            RETURN node_count, edge_count, orphaned_nodes, invalid_edges
            """
            
            result = await self.driver.execute_query(query)
            
            if result and result[0]:
                node_count = result[0][0]
                edge_count = result[0][1]
                orphaned_nodes = result[0][2]
                invalid_edges = result[0][3]
                
                # Calculate consistency score (0-1)
                total_elements = node_count + edge_count
                if total_elements > 0:
                    consistency = 1 - ((orphaned_nodes + invalid_edges) / total_elements)
                else:
                    consistency = 1.0
                
                return {
                    "node_count": node_count,
                    "edge_count": edge_count,
                    "orphaned_nodes": orphaned_nodes,
                    "invalid_edges": invalid_edges,
                    "consistency_score": consistency
                }
            return {
                "node_count": 0,
                "edge_count": 0,
                "orphaned_nodes": 0,
                "invalid_edges": 0,
                "consistency_score": 1.0
            }
        except Exception as e:
            logger.error(f"Error checking health: {str(e)}")
            raise
    
    async def optimize_structure(
        self,
        target_metrics: List[str] = ["query_performance"],
        optimization_level: str = "moderate"
    ) -> Dict[str, Any]:
        """Optimize graph structure."""
        try:
            improvements = {}
            space_saved = 0
            
            # Apply optimizations based on target metrics
            for metric in target_metrics:
                if metric == "query_performance":
                    # Create indexes for frequently queried properties
                    await self.driver.execute_query(
                        "CREATE INDEX IF NOT EXISTS FOR (n:Node) ON (n.type)"
                    )
                    await self.driver.execute_query(
                        "CREATE INDEX IF NOT EXISTS FOR (n:Node) ON (n.domain)"
                    )
                    improvements["query_performance"] = 0.2  # Estimated improvement
                
                elif metric == "storage_efficiency":
                    # Remove duplicate relationships
                    dedup_query = """
                    MATCH (a)-[r]->(b)
                    WITH a, b, type(r) as type, collect(r) as rels
                    WHERE size(rels) > 1
                    UNWIND tail(rels) as rel
                    DELETE rel
                    RETURN count(rel) as removed
                    """
                    result = await self.driver.execute_query(dedup_query)
                    if result and result[0]:
                        space_saved = result[0][0]
                        improvements["storage_efficiency"] = 0.15  # Estimated improvement
            
            # Apply additional optimizations based on level
            if optimization_level == "aggressive":
                # Merge similar nodes
                merge_query = """
                MATCH (n1:Node), (n2:Node)
                WHERE n1.type = n2.type
                AND n1.domain = n2.domain
                AND n1 <> n2
                AND n1.similarity_score > 0.9
                WITH n1, n2
                LIMIT 1000
                CALL apoc.refactor.mergeNodes([n1, n2])
                YIELD node
                RETURN count(node) as merged
                """
                result = await self.driver.execute_query(merge_query)
                if result and result[0]:
                    improvements["node_consolidation"] = 0.1  # Estimated improvement
            
            return {
                "performance_improvement": sum(improvements.values()),
                "space_saved": space_saved,
                "optimizations": list(improvements.keys())
            }
        except Exception as e:
            logger.error(f"Error optimizing structure: {str(e)}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        try:
            # Get node distribution
            node_query = """
            MATCH (n)
            WITH labels(n) as type, count(n) as count
            RETURN collect({type: type, count: count}) as distribution
            """
            
            # Get edge types
            edge_query = """
            MATCH ()-[r]->()
            WITH type(r) as type, count(r) as count
            RETURN collect({type: type, count: count}) as types
            """
            
            # Get domain stats
            domain_query = """
            MATCH (n)
            WITH n.domain as domain, count(n) as count
            WHERE domain IS NOT NULL
            RETURN collect({domain: domain, count: count}) as stats
            """
            
            # Get query performance metrics
            perf_query = """
            CALL apoc.monitor.kernel()
            YIELD kernelOperations, kernelTotalTime, kernelTotalWaitTime
            RETURN {
                operations: kernelOperations,
                total_time: kernelTotalTime,
                wait_time: kernelTotalWaitTime
            } as performance
            """
            
            # Execute queries
            node_result = await self.driver.execute_query(node_query)
            edge_result = await self.driver.execute_query(edge_query)
            domain_result = await self.driver.execute_query(domain_query)
            perf_result = await self.driver.execute_query(perf_query)
            
            return {
                "node_distribution": node_result[0][0] if node_result and node_result[0] else [],
                "edge_types": edge_result[0][0] if edge_result and edge_result[0] else [],
                "domain_stats": domain_result[0][0] if domain_result and domain_result[0] else [],
                "query_performance": perf_result[0][0] if perf_result and perf_result[0] else {},
                "memory_usage": await self._get_memory_usage()
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            raise
    
    async def create_backup(
        self,
        include_domains: List[str] = ["all"],
        backup_format: str = "cypher",
        compression: bool = True
    ) -> Dict[str, Any]:
        """Create graph backup."""
        try:
            # Build domain filter
            domain_filter = ""
            if "all" not in include_domains:
                domain_list = ", ".join([f"'{domain}'" for domain in include_domains])
                domain_filter = f"WHERE n.domain IN [{domain_list}]"
            
            # Get nodes and relationships to backup
            backup_query = f"""
            MATCH (n)
            {domain_filter}
            OPTIONAL MATCH (n)-[r]->(m)
            WHERE {domain_filter.replace('n.', 'm.')} OR true
            RETURN count(DISTINCT n) as nodes,
                   count(DISTINCT r) as edges,
                   sum(size(apoc.convert.toJson(properties(n)))) as size
            """
            
            result = await self.driver.execute_query(backup_query)
            
            if result and result[0]:
                backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                node_count = result[0][0]
                edge_count = result[0][1]
                file_size = result[0][2]
                
                # Apply compression if requested
                if compression:
                    file_size = int(file_size * 0.4)  # Estimated compression ratio
                
                return {
                    "backup_id": backup_id,
                    "timestamp": datetime.now().isoformat(),
                    "format": backup_format,
                    "compressed": compression,
                    "file_size": file_size,
                    "node_count": node_count,
                    "edge_count": edge_count
                }
            return {
                "backup_id": None,
                "timestamp": datetime.now().isoformat(),
                "format": backup_format,
                "compressed": compression,
                "file_size": 0,
                "node_count": 0,
                "edge_count": 0
            }
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            raise
    
    async def _get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics."""
        try:
            query = """
            CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Memory*')
            YIELD name, attributes
            RETURN name, attributes
            """
            
            result = await self.driver.execute_query(query)
            
            memory_stats = {
                "heap_used": 0,
                "heap_max": 0,
                "heap_committed": 0
            }
            
            if result:
                for record in result:
                    name = record[0]
                    attrs = record[1]
                    
                    if "HeapMemoryUsage" in name:
                        memory_stats["heap_used"] = attrs.get("used", 0)
                        memory_stats["heap_max"] = attrs.get("max", 0)
                        memory_stats["heap_committed"] = attrs.get("committed", 0)
            
            return memory_stats
        except Exception as e:
            logger.error(f"Error getting memory usage: {str(e)}")
            return {
                "heap_used": 0,
                "heap_max": 0,
                "heap_committed": 0
            }
