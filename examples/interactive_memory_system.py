"""
Interactive memory system example.
"""

import asyncio
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from nia.memory import MemorySystem, LLMInterface, Neo4jMemoryStore, VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ANSI color codes
COLORS = {
    'blue': '\033[94m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'red': '\033[91m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
    'bold': '\033[1m',
    'underline': '\033[4m',
    'end': '\033[0m'
}

def print_colored(text: str, color: str = 'white', bold: bool = False, underline: bool = False) -> None:
    """Print colored text."""
    style = ''
    if bold:
        style += COLORS['bold']
    if underline:
        style += COLORS['underline']
    print(f"{style}{COLORS[color]}{text}{COLORS['end']}")

def print_header(text: str) -> None:
    """Print a header."""
    width = 60
    padding = (width - len(text)) // 2
    print()
    print_colored('=' * width, 'blue', bold=True)
    print_colored(' ' * padding + text + ' ' * padding, 'blue', bold=True)
    print_colored('=' * width, 'blue', bold=True)
    print()

async def get_system_status(memory_system: MemorySystem) -> Dict[str, Any]:
    """Get system status information."""
    try:
        # Get Neo4j stats
        query = """
        // Get node counts by label
        MATCH (n)
        WITH labels(n) as labels, count(n) as count
        RETURN collect({label: labels[0], count: count}) as nodes
        """
        nodes_result = await memory_system.store.query_graph(query)
        node_counts = nodes_result[0]["nodes"] if nodes_result else []
        
        # Get relationship counts by type
        query = """
        MATCH ()-[r]->()
        WITH type(r) as type, count(r) as count
        RETURN collect({type: type, count: count}) as relationships
        """
        rels_result = await memory_system.store.query_graph(query)
        rel_counts = rels_result[0]["relationships"] if rels_result else []
        
        # Get recent memories from Neo4j
        query = """
        MATCH (m:Memory)
        WITH m
        ORDER BY m.created_at DESC
        LIMIT 5
        RETURN collect({
            type: m.type,
            created_at: toString(m.created_at)
        }) as memories
        """
        memories_result = await memory_system.store.query_graph(query)
        recent_graph_memories = memories_result[0]["memories"] if memories_result else []
        
        # Get recent memories from vector store
        recent_vector_memories = await memory_system.vector_store.search_vectors(
            content="",  # Empty query to get most recent
            limit=5
        )
        
        # Get system capabilities
        capabilities = await memory_system.store.get_capabilities()
        
        # Get vector store stats
        collection_info = memory_system.vector_store.client.get_collection(
            collection_name=memory_system.vector_store.collection_name
        )
        vector_stats = {
            'vectors_count': collection_info.vectors_count,
            'indexed_vectors_count': collection_info.indexed_vectors_count,
            'points_count': collection_info.points_count,
            'segments_count': collection_info.segments_count,
            'status': collection_info.status
        }
        
        return {
            "graph_store": {
                "nodes": node_counts,
                "relationships": rel_counts,
                "recent_memories": recent_graph_memories
            },
            "vector_store": {
                "stats": vector_stats,
                "recent_memories": recent_vector_memories
            },
            "capabilities": capabilities
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {}

async def process_interaction(
    memory_system: MemorySystem,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Process an interaction through the memory system."""
    try:
        # Check for commands
        if content.startswith('!'):
            command = content[1:].strip()
            
            # Handle special commands
            if command == 'reset':
                print_colored("\nResetting memory system...", 'yellow')
                await memory_system.cleanup()
                print_colored("Memory system reset complete.", 'green')
                return
            
            elif command == 'status':
                print_colored("\nGetting system status...", 'yellow')
                status = await get_system_status(memory_system)
                
                # Print Neo4j stats
                print_colored("\nGraph Store:", 'cyan', bold=True)
                print_colored("Node Counts:", 'cyan')
                for node in status.get('graph_store', {}).get('nodes', []):
                    print_colored(f"  {node['label']}: {node['count']}", 'cyan')
                
                print_colored("\nRelationship Counts:", 'magenta')
                for rel in status.get('graph_store', {}).get('relationships', []):
                    print_colored(f"  {rel['type']}: {rel['count']}", 'magenta')
                
                print_colored("\nRecent Graph Memories:", 'yellow')
                for memory in status.get('graph_store', {}).get('recent_memories', []):
                    print_colored(f"  {memory['type']} ({memory['created_at']})", 'yellow')
                
                # Print vector store stats
                print_colored("\nVector Store:", 'green', bold=True)
                vector_stats = status.get('vector_store', {}).get('stats', {})
                print_colored(f"  Total Vectors: {vector_stats.get('vectors_count', 0)}", 'green')
                print_colored(f"  Indexed Vectors: {vector_stats.get('indexed_vectors_count', 0)}", 'green')
                print_colored(f"  Points: {vector_stats.get('points_count', 0)}", 'green')
                print_colored(f"  Segments: {vector_stats.get('segments_count', 0)}", 'green')
                print_colored(f"  Status: {vector_stats.get('status', 'unknown')}", 'green')
                
                print_colored("\nRecent Vector Memories:", 'blue')
                for memory in status.get('vector_store', {}).get('recent_memories', []):
                    print_colored(f"  {memory['id']} (score: {memory['score']:.2f})", 'blue')
                    print_colored(f"    Created: {memory['created_at']}", 'blue')
                
                print_colored("\nSystem Capabilities:", 'white', bold=True)
                for cap in status.get('capabilities', []):
                    print_colored(f"  {cap['description']} ({cap['type']})", 'white')
                    if cap.get('systems'):
                        systems = [s['name'] for s in cap['systems']]
                        print_colored(f"    Used by: {', '.join(systems)}", 'white')
                
                print()
                return
            
            elif command == 'help':
                print_colored("\nAvailable Commands:", 'cyan', bold=True)
                print_colored("  !reset    - Reset the memory system", 'cyan')
                print_colored("  !status   - Show system status", 'cyan')
                print_colored("  !help     - Show this help message", 'cyan')
                print_colored("  !clear    - Clear the terminal", 'cyan')
                print_colored("  !exit     - End the session", 'cyan')
                print()
                return
            
            elif command == 'clear':
                print('\033[2J\033[H')  # Clear screen
                print_header("Nova - AI Assistant")
                return
            
            elif command == 'exit':
                print_colored("\nGoodbye!", 'green')
                return
        
        # Format interaction content
        interaction = {
            'content': content,
            'type': 'user_interaction',
            'timestamp': datetime.now().isoformat()
        }
        
        # Process through memory system
        response = await memory_system.process_interaction(
            content=interaction,
            metadata=metadata or {'importance': 1.0}
        )
        
        # Display response
        print()
        print_colored("Nova:", 'green', bold=True)
        print_colored(response.response, 'white')
        print()
        
    except Exception as e:
        logger.error(f"Error processing interaction: {str(e)}")
        print_colored("\nNova: I need to process that differently", 'red')

async def interactive_session(reset: bool = False):
    """Run interactive memory system session."""
    try:
        # Initialize components
        llm = LLMInterface()
        store = Neo4jMemoryStore(llm=llm)
        vector_store = VectorStore()
        
        # Clean up if requested
        if reset:
            await store.cleanup()
            await vector_store.cleanup()
            logger.info("Reset memory system")
        
        # Initialize memory system
        memory_system = MemorySystem(llm, store, vector_store)
        logger.info("Initialized memory system")
        
        # Print welcome message
        print_header("Nova - AI Assistant")
        print_colored("Hello! I'm Nova, an AI assistant focused on self-discovery and growth.", 'green')
        print_colored("Type !help to see available commands or 'exit' to end our conversation.", 'cyan')
        print()
        
        # Interactive loop
        while True:
            try:
                # Get user input
                user_input = input(f"{COLORS['yellow']}You:{COLORS['end']} ").strip()
                if not user_input:
                    continue
                
                if user_input.lower() == 'exit':
                    break
                
                print_colored("\nProcessing interaction...", 'magenta')
                
                # Process interaction
                await process_interaction(
                    memory_system,
                    user_input,
                    metadata={'source': 'user_input'}
                )
                
            except Exception as e:
                logger.error(f"Error in interaction loop: {str(e)}")
                print_colored("\nNova: I need to process that differently", 'red')
        
        # Clean up
        memory_system.close()
        logger.info("Closed memory system")
        
        # Print goodbye message
        print_header("Session Ended")
        print_colored("Thank you for the interaction! Goodbye!", 'green')
        print()
        
    except Exception as e:
        logger.error(f"Error in interactive session: {str(e)}")
        raise

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Interactive Memory System")
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset memory system before starting'
    )
    args = parser.parse_args()
    
    # Run interactive session
    asyncio.run(interactive_session(args.reset))
