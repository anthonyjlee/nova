"""Initialize test data in graph store."""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.nia.memory.graph_store import GraphStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_graph():
    """Initialize test data in graph store."""
    try:
        graph_store = GraphStore()
        await graph_store.connect()
        
        # Check existing nodes
        logger.info("Checking existing nodes...")
        result = await graph_store.run_query("""
        MATCH (n) 
        RETURN labels(n) as labels, n.name as name
        """)
        
        existing_nodes = {
            f"{r['labels'][0]}:{r['name']}" 
            for r in result 
            if r['labels'] and r['name']
        }
        logger.info(f"Found existing nodes: {existing_nodes}")
        
        # Create nodes if they don't exist
        logger.info("Creating missing nodes...")
        
        nodes_to_create = [
            ("Concept", "Belief", "concept"),
            ("Concept", "Desire", "concept"),
            ("Concept", "Emotion", "concept"),
            ("Agent", "Nova", "nova", "Core orchestration agent"),
            ("Agent", "BeliefAgent", "belief", "Handles belief processing"),
            ("Agent", "DesireAgent", "desire", "Handles desire processing")
        ]
        
        for node in nodes_to_create:
            node_key = f"{node[0]}:{node[1]}"
            if node_key not in existing_nodes:
                if node[0] == "Concept":
                    await graph_store.run_query(f"""
                    CREATE (n:{node[0]} {{
                        name: '{node[1]}',
                        type: '{node[2]}'
                    }})
                    """)
                    logger.info(f"Created {node_key}")
                else:
                    await graph_store.run_query(f"""
                    CREATE (n:{node[0]} {{
                        name: '{node[1]}',
                        type: '{node[2]}',
                        domain: 'general',
                        created_at: datetime(),
                        description: '{node[3]}'
                    }})
                    """)
                    logger.info(f"Created {node_key}")
            else:
                logger.info(f"Node {node_key} already exists")
        
        # Create relationships
        logger.info("Creating relationships...")
        
        # Concept relationships
        await graph_store.run_query("""
        MATCH (a:Concept {name: 'Belief'}), (b:Concept {name: 'Desire'})
        CREATE (a)-[:INFLUENCES]->(b)
        """)
        
        await graph_store.run_query("""
        MATCH (a:Concept {name: 'Desire'}), (b:Concept {name: 'Emotion'})
        CREATE (a)-[:AFFECTS]->(b)
        """)
        
        await graph_store.run_query("""
        MATCH (a:Concept {name: 'Emotion'}), (b:Concept {name: 'Belief'})
        CREATE (a)-[:IMPACTS]->(b)
        """)
        
        # Agent relationships
        await graph_store.run_query("""
        MATCH (a:Agent {name: 'BeliefAgent'}), (b:Concept {name: 'Belief'})
        CREATE (a)-[:MANAGES]->(b)
        """)
        
        await graph_store.run_query("""
        MATCH (a:Agent {name: 'DesireAgent'}), (b:Concept {name: 'Desire'})
        CREATE (a)-[:MANAGES]->(b)
        """)
        
        await graph_store.run_query("""
        MATCH (a:Agent {name: 'Nova'}), (b:Agent {name: 'BeliefAgent'})
        CREATE (a)-[:COORDINATES]->(b)
        """)
        
        await graph_store.run_query("""
        MATCH (a:Agent {name: 'Nova'}), (b:Agent {name: 'DesireAgent'})
        CREATE (a)-[:COORDINATES]->(b)
        """)
        logger.info("Test data created successfully")
        
        # Verify data was created
        result = await graph_store.get_graph_data()
        logger.info(f"Graph contains {len(result['nodes'])} nodes and {len(result['edges'])} edges")
        
    except Exception as e:
        logger.error(f"Error initializing graph: {str(e)}")
        raise
    finally:
        await graph_store.close()

if __name__ == "__main__":
    asyncio.run(initialize_graph())
