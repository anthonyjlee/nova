"""Neo4j graph visualization components for NIA chat interface."""

import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

class GraphVisualizer:
    """Handles Neo4j graph visualization."""
    
    def __init__(self, system2, state, neo4j_driver=None):
        """Initialize visualizer with system2, state and Neo4j driver."""
        self.system2 = system2
        self.state = state
        self.neo4j_driver = neo4j_driver
    
    async def handle_cypher_query(
        self,
        query: str
    ) -> Tuple[str, Dict]:
        """Handle Cypher query and update graph view."""
        try:
            if not query:
                return self.get_default_graph(), {}
            
            if self.neo4j_driver:
                # Execute query through Neo4j driver
                with self.neo4j_driver.session() as session:
                    results = list(session.run(query))
                
                # Convert results to Cytoscape.js format
                elements = []
                
                # Process nodes
                nodes = set()
                for record in results:
                    for value in record.values():
                        if hasattr(value, 'id') and hasattr(value, 'labels'):
                            # This is a node
                            node_id = str(value.id)
                            if node_id not in nodes:
                                nodes.add(node_id)
                                elements.append({
                                    'data': {
                                        'id': node_id,
                                        'label': value.get('name', ''),
                                        'type': list(value.labels)[0],
                                        'properties': dict(value)
                                    }
                                })
                        elif hasattr(value, 'type'):
                            # This is a relationship
                            elements.append({
                                'data': {
                                    'id': f"e{value.id}",
                                    'source': str(value.start_node.id),
                                    'target': str(value.end_node.id),
                                    'label': value.type
                                }
                            })
                
                # Generate Cytoscape.js initialization code
                graph_data = {
                    'elements': elements
                }
                
                # Update graph view
                graph_js = f"""
                    <script>
                        window.updateGraph({graph_data});
                    </script>
                """
                
                return graph_js, {'query': query, 'results': len(results)}
            
            return self.get_default_graph(), {'error': 'Neo4j driver not available'}
            
        except Exception as e:
            logger.error(f"Error executing Cypher query: {str(e)}")
            return self.get_default_graph(), {'error': str(e)}
    
    async def refresh_graph_view(
        self,
        layout: str = "cose"
    ) -> str:
        """Refresh the graph view with current data."""
        try:
            if self.neo4j_driver:
                # Get all nodes and relationships
                query = """
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN n, r, m
                """
                return await self.handle_cypher_query(query)
            
            return self.get_default_graph()
            
        except Exception as e:
            logger.error(f"Error refreshing graph: {str(e)}")
            return self.get_default_graph()
    
    def get_default_graph(self) -> str:
        """Return default empty graph view."""
        return """
            <div id="cy" style="width: 100%; height: 500px; border: 1px solid #ccc;"></div>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    var cy = cytoscape({
                        container: document.getElementById('cy'),
                        elements: [],
                        style: [
                            {
                                selector: 'node',
                                style: {
                                    'label': 'data(label)',
                                    'background-color': '#666',
                                    'color': '#fff'
                                }
                            },
                            {
                                selector: 'edge',
                                style: {
                                    'label': 'data(label)',
                                    'curve-style': 'bezier',
                                    'target-arrow-shape': 'triangle'
                                }
                            }
                        ]
                    });
                });
            </script>
        """
    
    def get_graph_component_html(self) -> str:
        """Get HTML for graph component."""
        return """
            <div id="cy" style="width: 100%; height: 500px; border: 1px solid #ccc;"></div>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    var cy = cytoscape({
                        container: document.getElementById('cy'),
                        style: [
                            {
                                selector: 'node',
                                style: {
                                    'label': 'data(label)',
                                    'background-color': '#666',
                                    'color': '#fff'
                                }
                            },
                            {
                                selector: 'edge',
                                style: {
                                    'label': 'data(label)',
                                    'curve-style': 'bezier',
                                    'target-arrow-shape': 'triangle'
                                }
                            }
                        ]
                    });
                    
                    // Function to update graph data
                    window.updateGraph = function(data) {
                        cy.json(data);
                        cy.layout({name: 'cose'}).run();
                    };
                });
            </script>
        """
