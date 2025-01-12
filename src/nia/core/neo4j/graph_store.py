"""Graph store implementation."""

from typing import Dict, Any, List, Optional
from .base_store import Neo4jBaseStore
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class GraphStore(Neo4jBaseStore):
    """Store for graph operations."""
    
    async def initialize(self):
        """Initialize graph store."""
        logger.info("Initializing graph store...")
        await self.connect()
        logger.info("Graph store initialized successfully")
        
    async def create_node(self, labels: List[str], properties: Dict[str, Any]):
        """Create a node with given labels and properties."""
        labels_str = ':'.join(labels)
        query = f"""
        CREATE (n:{labels_str})
        SET n = $properties
        RETURN n
        """
        return await self.run_query(query, {"properties": properties})
        
    async def create_relationship(self, from_id: str, to_id: str, rel_type: str, properties: Optional[Dict[str, Any]] = None):
        """Create a relationship between nodes."""
        query = f"""
        MATCH (from), (to)
        WHERE from.id = $from_id AND to.id = $to_id
        CREATE (from)-[r:{rel_type}]->(to)
        SET r = $properties
        RETURN r
        """
        return await self.run_query(query, {
            "from_id": from_id,
            "to_id": to_id,
            "properties": properties or {}
        })
        
    async def get_node(self, node_id: str):
        """Get node by ID."""
        query = """
        MATCH (n)
        WHERE n.id = $node_id
        RETURN n
        """
        return await self.run_query(query, {"node_id": node_id})
        
    async def update_node(self, node_id: str, properties: Dict[str, Any]):
        """Update node properties."""
        query = """
        MATCH (n)
        WHERE n.id = $node_id
        SET n += $properties
        RETURN n
        """
        return await self.run_query(query, {
            "node_id": node_id,
            "properties": properties
        })
        
    async def delete_node(self, node_id: str):
        """Delete node by ID."""
        query = """
        MATCH (n)
        WHERE n.id = $node_id
        DETACH DELETE n
        """
        return await self.run_query(query, {"node_id": node_id})
        
    async def get_relationships(self, node_id: str, rel_type: Optional[str] = None, direction: str = "BOTH"):
        """Get node relationships."""
        if direction not in ["INCOMING", "OUTGOING", "BOTH"]:
            raise ValueError("Invalid direction. Must be INCOMING, OUTGOING, or BOTH")
            
        if direction == "INCOMING":
            pattern = "<-[r]-"
        elif direction == "OUTGOING":
            pattern = "-[r]->"
        else:
            pattern = "-[r]-"
            
        rel_type_str = f":{rel_type}" if rel_type else ""
        
        query = f"""
        MATCH (n)
        WHERE n.id = $node_id
        MATCH (n){pattern}(other){rel_type_str}
        RETURN r, other
        """
        return await self.run_query(query, {"node_id": node_id})
        
    async def search_nodes(self, label: Optional[str] = None, properties: Optional[Dict[str, Any]] = None):
        """Search nodes by label and properties."""
        label_str = f":{label}" if label else ""
        where_clause = " AND ".join(f"n.{k} = ${k}" for k in (properties or {}).keys())
        where_str = f"WHERE {where_clause}" if where_clause else ""
        
        query = f"""
        MATCH (n{label_str})
        {where_str}
        RETURN n
        """
        return await self.run_query(query, properties or {})

    async def get_graph_data(self) -> Dict[str, Any]:
        """Get all nodes and relationships in the graph."""
        try:
            logger.info("Fetching graph data...")
            
            # Get all nodes with their properties
            logger.debug("Fetching nodes...")
            nodes_query = """
            MATCH (n)
            RETURN 
                n.id as id,
                labels(n) as labels,
                properties(n) as properties,
                CASE
                    WHEN 'Agent' IN labels(n) THEN 'agent'
                    WHEN 'Concept' IN labels(n) THEN 'concept'
                    ELSE 'default'
                END as type
            """
            nodes_result = await self.run_query(nodes_query)
            logger.debug(f"Found {len(nodes_result)} nodes")
            
            # Get all relationships with their properties
            logger.debug("Fetching relationships...")
            edges_query = """
            MATCH (n)-[r]->(m)
            RETURN 
                id(r) as id,
                type(r) as type,
                n.id as source,
                m.id as target,
                properties(r) as properties
            """
            edges_result = await self.run_query(edges_query)
            logger.debug(f"Found {len(edges_result)} relationships")
            
            # Format nodes
            nodes = []
            for record in nodes_result:
                if not record.get("id"):
                    logger.warning(f"Skipping node without id: {record}")
                    continue
                    
                node = {
                    "id": record["id"],
                    "type": record["type"],
                    "labels": record["labels"]
                }
                
                # Add properties
                properties = record.get("properties", {})
                if isinstance(properties, dict):
                    for key, value in properties.items():
                        if key != "id":  # Skip id as it's already included
                            node[key] = value
                            
                # Add label if available
                if "name" in properties:
                    node["label"] = properties["name"]
                elif "title" in properties:
                    node["label"] = properties["title"]
                else:
                    node["label"] = str(record["id"])
                    
                nodes.append(node)
                
            # Format edges
            edges = []
            for record in edges_result:
                if not (record.get("source") and record.get("target")):
                    logger.warning(f"Skipping edge without source or target: {record}")
                    continue
                    
                edge = {
                    "id": str(record["id"]),
                    "type": record["type"],
                    "source": record["source"],
                    "target": record["target"]
                }
                
                # Add properties
                properties = record.get("properties", {})
                if isinstance(properties, dict):
                    for key, value in properties.items():
                        edge[key] = value
                        
                # Add label if available
                if "label" in properties:
                    edge["label"] = properties["label"]
                else:
                    edge["label"] = record["type"]
                    
                edges.append(edge)
                
            logger.info(f"Successfully fetched graph data: {len(nodes)} nodes, {len(edges)} edges")
            return {
                "nodes": nodes,
                "edges": edges
            }
        except Exception as e:
            logger.error(f"Error getting graph data: {str(e)}")
            raise
