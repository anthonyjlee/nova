"""Graph store for managing knowledge graph operations."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

from ..core.neo4j.base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)

class GraphStore(Neo4jBaseStore):
    """Store for managing knowledge graph."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", **kwargs):
        """Initialize graph store."""
        super().__init__(uri=uri, **kwargs)
    
    async def prune_graph(
        self,
        min_relevance: float = 0.5,
        max_age_days: int = 30,
        exclude_domains: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """Prune knowledge graph based on criteria.
        
        Args:
            min_relevance: Minimum relevance score to keep
            max_age_days: Maximum age in days to keep
            exclude_domains: List of domains to exclude from pruning
            
        Returns:
            Dict containing counts of removed nodes and edges
        """
        try:
            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()
            
            # Build domain exclusion
            domain_condition = ""
            parameters = {
                "min_relevance": min_relevance,
                "cutoff_date": cutoff_date
            }
            
            if exclude_domains:
                domain_condition = "AND NOT n.domain IN $exclude_domains"
                parameters["exclude_domains"] = exclude_domains
            
            # Count nodes and edges to be removed
            count_query = f"""
            MATCH (n)
            WHERE (n.relevance < $min_relevance OR n.created_at < $cutoff_date)
            {domain_condition}
            WITH n, size((n)-[]->()) as outgoing, size((n)<-[]-()) as incoming
            RETURN count(n) as nodes, sum(outgoing + incoming) as edges
            """
            
            count_result = await self.run_query(count_query, parameters=parameters)
            
            # Perform pruning
            prune_query = f"""
            MATCH (n)
            WHERE (n.relevance < $min_relevance OR n.created_at < $cutoff_date)
            {domain_condition}
            DETACH DELETE n
            """
            
            await self.run_query(prune_query, parameters=parameters)
            
            if count_result and count_result[0]:
                return {
                    "nodes_removed": count_result[0]["nodes"],
                    "edges_removed": count_result[0]["edges"]
                }
            return {
                "nodes_removed": 0,
                "edges_removed": 0
            }
            
        except Exception as e:
            logger.error(f"Error pruning graph: {str(e)}")
            return {
                "nodes_removed": 0,
                "edges_removed": 0
            }
    
    async def check_health(self) -> Dict[str, Any]:
        """Check knowledge graph health.
        
        Returns:
            Dict containing health metrics
        """
        try:
            # Get basic counts
            counts_query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->()
            WITH count(DISTINCT n) as node_count,
                 count(DISTINCT r) as edge_count
            RETURN node_count, edge_count
            """
            
            counts_result = await self.run_query(counts_query)
            
            # Find orphaned nodes
            orphans_query = """
            MATCH (n)
            WHERE NOT (n)-[]-()
            RETURN count(n) as orphaned_nodes
            """
            
            orphans_result = await self.run_query(orphans_query)
            
            # Check for invalid edges
            invalid_edges_query = """
            MATCH ()-[r]->()
            WHERE r.created_at IS NULL
            OR r.type IS NULL
            RETURN count(r) as invalid_edges
            """
            
            invalid_edges_result = await self.run_query(invalid_edges_query)
            
            # Calculate consistency score
            if counts_result and counts_result[0]:
                node_count = counts_result[0]["node_count"]
                edge_count = counts_result[0]["edge_count"]
                orphaned_nodes = orphans_result[0]["orphaned_nodes"] if orphans_result and orphans_result[0] else 0
                invalid_edges = invalid_edges_result[0]["invalid_edges"] if invalid_edges_result and invalid_edges_result[0] else 0
                
                # Score based on:
                # - Ratio of orphaned nodes (lower is better)
                # - Ratio of invalid edges (lower is better)
                # - Edge to node ratio (higher is better, up to a point)
                if node_count > 0:
                    orphan_ratio = orphaned_nodes / node_count
                    edge_ratio = min(edge_count / node_count, 1.0)  # Cap at 1.0
                else:
                    orphan_ratio = 1.0
                    edge_ratio = 0.0
                    
                if edge_count > 0:
                    invalid_ratio = invalid_edges / edge_count
                else:
                    invalid_ratio = 1.0 if invalid_edges > 0 else 0.0
                
                consistency_score = (
                    (1.0 - orphan_ratio) * 0.4 +  # 40% weight
                    (1.0 - invalid_ratio) * 0.4 +  # 40% weight
                    edge_ratio * 0.2  # 20% weight
                )
                
                return {
                    "node_count": node_count,
                    "edge_count": edge_count,
                    "orphaned_nodes": orphaned_nodes,
                    "invalid_edges": invalid_edges,
                    "consistency_score": consistency_score
                }
            
            return {
                "node_count": 0,
                "edge_count": 0,
                "orphaned_nodes": 0,
                "invalid_edges": 0,
                "consistency_score": 0.0
            }
            
        except Exception as e:
            logger.error(f"Error checking health: {str(e)}")
            return {
                "node_count": 0,
                "edge_count": 0,
                "orphaned_nodes": 0,
                "invalid_edges": 0,
                "consistency_score": 0.0
            }
    
    async def optimize_structure(
        self,
        target_metrics: Optional[List[str]] = None,
        optimization_level: str = "moderate"
    ) -> Dict[str, Any]:
        """Optimize graph structure.
        
        Args:
            target_metrics: List of metrics to optimize for
            optimization_level: Level of optimization (conservative/moderate/aggressive)
            
        Returns:
            Dict containing optimization results
        """
        try:
            # Default metrics if none specified
            if not target_metrics:
                target_metrics = ["query_performance"]
            
            # Get initial metrics
            initial_metrics = await self.get_statistics()
            
            # Perform optimizations based on level
            improvements = {}
            
            if "query_performance" in target_metrics:
                # Create indexes based on optimization level
                if optimization_level == "aggressive":
                    # Create indexes on all frequently queried properties
                    await self.run_query(
                        "CREATE INDEX IF NOT EXISTS FOR (n:Node) ON (n.type, n.created_at, n.relevance)"
                    )
                elif optimization_level == "moderate":
                    # Create selective indexes
                    await self.run_query(
                        "CREATE INDEX IF NOT EXISTS FOR (n:Node) ON (n.type)"
                    )
                # Conservative level doesn't create additional indexes
                
                improvements["query_performance"] = {
                    "indexes_created": 1 if optimization_level == "moderate" else 3 if optimization_level == "aggressive" else 0
                }
            
            if "storage_efficiency" in target_metrics:
                # Remove duplicate relationships based on level
                if optimization_level == "aggressive":
                    # Remove all duplicates
                    dedup_query = """
                    MATCH (n)-[r1:RELATES_TO]->(m)
                    WITH n, m, type(r1) as rel_type, collect(r1) as rels
                    WHERE size(rels) > 1
                    WITH n, m, rel_type, rels[0] as kept, rels[1..] as duplicates
                    FOREACH (r in duplicates | DELETE r)
                    """
                elif optimization_level == "moderate":
                    # Remove duplicates older than 30 days
                    dedup_query = """
                    MATCH (n)-[r1:RELATES_TO]->(m)
                    WHERE r1.created_at < datetime() - duration('P30D')
                    WITH n, m, type(r1) as rel_type, collect(r1) as rels
                    WHERE size(rels) > 1
                    WITH n, m, rel_type, rels[0] as kept, rels[1..] as duplicates
                    FOREACH (r in duplicates | DELETE r)
                    """
                else:
                    # Conservative: only remove exact duplicates
                    dedup_query = """
                    MATCH (n)-[r1:RELATES_TO]->(m)
                    WITH n, m, type(r1) as rel_type, r1.properties as props, collect(r1) as rels
                    WHERE size(rels) > 1
                    WITH n, m, rel_type, props, rels[0] as kept, rels[1..] as duplicates
                    WHERE ALL(r in duplicates WHERE r.properties = props)
                    FOREACH (r in duplicates | DELETE r)
                    """
                
                await self.run_query(dedup_query)
                
                # Get space saved
                final_metrics = await self.get_statistics()
                edge_reduction = initial_metrics["edge_count"] - final_metrics["edge_count"]
                
                improvements["storage_efficiency"] = {
                    "edges_removed": edge_reduction,
                    "space_saved_bytes": edge_reduction * 100  # Rough estimate
                }
            
            # Calculate overall improvements
            performance_improvement = 0.0
            if "query_performance" in improvements:
                # Estimate performance improvement based on indexes
                index_count = improvements["query_performance"]["indexes_created"]
                performance_improvement = min(index_count * 0.2, 0.6)  # Cap at 60%
            
            space_saved = 0
            if "storage_efficiency" in improvements:
                space_saved = improvements["storage_efficiency"]["space_saved_bytes"]
            
            return {
                "performance_improvement": performance_improvement,
                "space_saved": space_saved,
                "improvements": improvements
            }
            
        except Exception as e:
            logger.error(f"Error optimizing structure: {str(e)}")
            return {
                "performance_improvement": 0.0,
                "space_saved": 0,
                "improvements": {}
            }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics.
        
        Returns:
            Dict containing graph statistics
        """
        try:
            # Get node distribution
            node_query = """
            MATCH (n)
            WITH labels(n) as node_type, count(n) as count
            RETURN collect({type: node_type, count: count}) as node_distribution
            """
            
            node_result = await self.run_query(node_query)
            
            # Get edge type distribution
            edge_query = """
            MATCH ()-[r]->()
            WITH type(r) as edge_type, count(r) as count
            RETURN collect({type: edge_type, count: count}) as edge_types
            """
            
            edge_result = await self.run_query(edge_query)
            
            # Get domain statistics
            domain_query = """
            MATCH (n)
            WITH n.domain as domain, count(n) as count
            WHERE domain IS NOT NULL
            RETURN collect({domain: domain, count: count}) as domain_stats
            """
            
            domain_result = await self.run_query(domain_query)
            
            # Get query performance metrics
            perf_query = """
            CALL db.stats.retrieve('GRAPH_STATS')
            YIELD stats
            RETURN stats
            """
            
            perf_result = await self.run_query(perf_query)
            
            # Get memory usage
            memory_query = """
            CALL db.stats.retrieve('MEMORY_STATS')
            YIELD stats
            RETURN stats
            """
            
            memory_result = await self.run_query(memory_query)
            
            return {
                "node_distribution": node_result[0]["node_distribution"] if node_result and node_result[0] else [],
                "edge_types": edge_result[0]["edge_types"] if edge_result and edge_result[0] else [],
                "domain_stats": domain_result[0]["domain_stats"] if domain_result and domain_result[0] else [],
                "query_performance": perf_result[0]["stats"] if perf_result and perf_result[0] else {},
                "memory_usage": memory_result[0]["stats"] if memory_result and memory_result[0] else {}
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {
                "node_distribution": [],
                "edge_types": [],
                "domain_stats": [],
                "query_performance": {},
                "memory_usage": {}
            }
    
    async def create_backup(
        self,
        include_domains: Optional[List[str]] = None,
        backup_format: str = "cypher",
        compression: bool = True
    ) -> Dict[str, Any]:
        """Create graph backup.
        
        Args:
            include_domains: List of domains to include (["all"] for everything)
            backup_format: Format of backup (cypher/graphml)
            compression: Whether to compress the backup
            
        Returns:
            Dict containing backup details
        """
        try:
            # Build domain filter
            domain_filter = ""
            parameters = {}
            
            if include_domains and "all" not in include_domains:
                domain_filter = "WHERE n.domain IN $domains"
                parameters["domains"] = include_domains
            
            # Get nodes and relationships to backup
            backup_query = f"""
            MATCH (n)
            {domain_filter}
            OPTIONAL MATCH (n)-[r]->(m)
            WHERE {domain_filter.replace('n.', 'm.')}
            RETURN n, r, m
            """
            
            result = await self.run_query(backup_query, parameters=parameters)
            
            # Generate backup in requested format
            backup_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            if backup_format == "cypher":
                # Convert to Cypher statements
                statements = []
                nodes_created = set()
                
                for row in result:
                    # Create node if not already created
                    if row["n"] and row["n"].id not in nodes_created:
                        node_props = dict(row["n"])
                        node_labels = ":".join(row["n"].labels)
                        statements.append(
                            f"CREATE (:{node_labels} {node_props})"
                        )
                        nodes_created.add(row["n"].id)
                    
                    # Create target node if exists
                    if row["m"] and row["m"].id not in nodes_created:
                        node_props = dict(row["m"])
                        node_labels = ":".join(row["m"].labels)
                        statements.append(
                            f"CREATE (:{node_labels} {node_props})"
                        )
                        nodes_created.add(row["m"].id)
                    
                    # Create relationship if exists
                    if row["r"]:
                        rel_props = dict(row["r"])
                        rel_type = type(row["r"]).__name__
                        statements.append(
                            f"MATCH (n), (m) WHERE id(n) = {row['n'].id} AND id(m) = {row['m'].id} "
                            f"CREATE (n)-[:{rel_type} {rel_props}]->(m)"
                        )
                
                backup_content = "\n".join(statements)
                
            else:  # GraphML format
                # Convert to GraphML XML
                nodes_xml = []
                edges_xml = []
                nodes_created = set()
                
                for row in result:
                    # Add node if not already added
                    if row["n"] and row["n"].id not in nodes_created:
                        node_props = dict(row["n"])
                        node_labels = " ".join(row["n"].labels)
                        nodes_xml.append(
                            f'<node id="{row["n"].id}">\n'
                            f'  <data key="labels">{node_labels}</data>\n'
                            f'  <data key="properties">{node_props}</data>\n'
                            f'</node>'
                        )
                        nodes_created.add(row["n"].id)
                    
                    # Add target node if exists
                    if row["m"] and row["m"].id not in nodes_created:
                        node_props = dict(row["m"])
                        node_labels = " ".join(row["m"].labels)
                        nodes_xml.append(
                            f'<node id="{row["m"].id}">\n'
                            f'  <data key="labels">{node_labels}</data>\n'
                            f'  <data key="properties">{node_props}</data>\n'
                            f'</node>'
                        )
                        nodes_created.add(row["m"].id)
                    
                    # Add relationship if exists
                    if row["r"]:
                        rel_props = dict(row["r"])
                        rel_type = type(row["r"]).__name__
                        edges_xml.append(
                            f'<edge source="{row["n"].id}" target="{row["m"].id}">\n'
                            f'  <data key="type">{rel_type}</data>\n'
                            f'  <data key="properties">{rel_props}</data>\n'
                            f'</edge>'
                        )
                
                backup_content = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n'
                    '  <key id="labels" for="node" attr.name="labels" attr.type="string"/>\n'
                    '  <key id="properties" for="node" attr.name="properties" attr.type="string"/>\n'
                    '  <key id="type" for="edge" attr.name="type" attr.type="string"/>\n'
                    '  <key id="properties" for="edge" attr.name="properties" attr.type="string"/>\n'
                    '  <graph id="G" edgedefault="directed">\n'
                    f'    {"".join(nodes_xml)}\n'
                    f'    {"".join(edges_xml)}\n'
                    '  </graph>\n'
                    '</graphml>'
                )
            
            # Compress if requested
            if compression:
                import gzip
                import base64
                
                compressed = gzip.compress(backup_content.encode())
                backup_content = base64.b64encode(compressed).decode()
            
            # Calculate statistics
            node_count = len(nodes_created)
            edge_count = sum(1 for row in result if row["r"])
            file_size = len(backup_content.encode())
            
            return {
                "backup_id": backup_id,
                "timestamp": timestamp,
                "format": backup_format,
                "compressed": compression,
                "file_size": file_size,
                "node_count": node_count,
                "edge_count": edge_count,
                "content": backup_content
            }
            
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return {
                "backup_id": None,
                "timestamp": datetime.now().isoformat(),
                "format": backup_format,
                "compressed": compression,
                "file_size": 0,
                "node_count": 0,
                "edge_count": 0,
                "content": None
            }
