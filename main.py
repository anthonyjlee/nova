"""
Nova AI Assistant - Main Entry Point
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

# ANSI color codes for terminal output
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

def print_colored(text: str, color: str = 'white', bold: bool = False) -> None:
    """Print colored text to terminal."""
    style = COLORS['bold'] if bold else ''
    print(f"{style}{COLORS[color]}{text}{COLORS['end']}")

def print_header(text: str) -> None:
    """Print a formatted header."""
    width = 60
    padding = (width - len(text)) // 2
    print()
    print_colored('=' * width, 'blue', bold=True)
    print_colored(' ' * padding + text + ' ' * padding, 'blue', bold=True)
    print_colored('=' * width, 'blue', bold=True)
    print()

async def get_system_status(memory_system: MemorySystem) -> Dict[str, Any]:
    """Get current system status from both memory stores."""
    try:
        # Get Neo4j stats
        graph_stats = await memory_system.store.query_graph("""
            MATCH (n)
            WITH labels(n) as labels, count(n) as count
            RETURN collect({label: labels[0], count: count}) as nodes
        """)
        
        # Get relationship stats
        rel_stats = await memory_system.store.query_graph("""
            MATCH ()-[r]->()
            WITH type(r) as type, count(r) as count
            RETURN collect({type: type, count: count}) as relationships
        """)
        
        # Get recent graph memories
        recent_graph = await memory_system.store.query_graph("""
            MATCH (m:Memory)
            WITH m
            ORDER BY m.created_at DESC
            LIMIT 5
            RETURN collect({
                type: m.type,
                created_at: toString(m.created_at)
            }) as memories
        """)
        
        # Get vector store stats
        collection = memory_system.vector_store.client.get_collection(
            memory_system.vector_store.collection_name
        )
        
        # Get recent vector memories
        recent_vectors = await memory_system.vector_store.search_vectors(
            content="",
            limit=5
        )
        
        # Get system capabilities
        capabilities = await memory_system.store.get_capabilities()
        
        return {
            "graph_store": {
                "nodes": graph_stats[0]["nodes"] if graph_stats else [],
                "relationships": rel_stats[0]["relationships"] if rel_stats else [],
                "recent_memories": recent_graph[0]["memories"] if recent_graph else []
            },
            "vector_store": {
                "stats": {
                    "vectors_count": collection.vectors_count,
                    "indexed_vectors_count": collection.indexed_vectors_count,
                    "points_count": collection.points_count,
                    "segments_count": collection.segments_count,
                    "status": collection.status
                },
                "recent_memories": recent_vectors
            },
            "capabilities": capabilities
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {}

async def handle_command(
    command: str,
    memory_system: MemorySystem
) -> bool:
    """Handle system commands."""
    if command == 'reset':
        print_colored("\nResetting memory system...", 'yellow')
        await memory_system.cleanup()
        print_colored("Memory system reset complete.", 'green')
        return True
        
    elif command == 'status':
        print_colored("\nGetting system status...", 'yellow')
        status = await get_system_status(memory_system)
        
        # Print graph store stats
        graph_store = status.get('graph_store', {})
        print_colored("\nGraph Store:", 'cyan', bold=True)
        for node in graph_store.get('nodes', []):
            print_colored(f"  {node['label']}: {node['count']}", 'cyan')
        
        for rel in graph_store.get('relationships', []):
            print_colored(f"  {rel['type']}: {rel['count']}", 'magenta')
        
        for memory in graph_store.get('recent_memories', []):
            print_colored(f"  {memory['type']} ({memory['created_at']})", 'yellow')
        
        # Print vector store stats
        vector_store = status.get('vector_store', {})
        print_colored("\nVector Store:", 'green', bold=True)
        stats = vector_store.get('stats', {})
        print_colored(f"  Vectors: {stats.get('vectors_count', 0)}", 'green')
        print_colored(f"  Indexed: {stats.get('indexed_vectors_count', 0)}", 'green')
        print_colored(f"  Points: {stats.get('points_count', 0)}", 'green')
        print_colored(f"  Status: {stats.get('status', 'unknown')}", 'green')
        
        for memory in vector_store.get('recent_memories', []):
            print_colored(f"  {memory['id']} ({memory['created_at']})", 'blue')
        
        # Print capabilities
        print_colored("\nCapabilities:", 'white', bold=True)
        for cap in status.get('capabilities', []):
            print_colored(f"  {cap['description']} ({cap['type']})", 'white')
            if cap.get('systems'):
                systems = [s['name'] for s in cap['systems']]
                print_colored(f"    Used by: {', '.join(systems)}", 'white')
        
        print()
        return True
        
    elif command == 'help':
        print_colored("\nCommands:", 'cyan', bold=True)
        print_colored("  !reset    - Reset memory system", 'cyan')
        print_colored("  !status   - Show system status", 'cyan')
        print_colored("  !help     - Show this help", 'cyan')
        print_colored("  !clear    - Clear terminal", 'cyan')
        print_colored("  !exit     - Exit session", 'cyan')
        print()
        return True
        
    elif command == 'clear':
        print('\033[2J\033[H')  # Clear screen
        print_header("Nova AI Assistant")
        return True
        
    elif command == 'exit':
        print_colored("\nGoodbye!", 'green')
        return True
        
    return False

async def process_interaction(
    memory_system: MemorySystem,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Process a user interaction."""
    try:
        # Handle commands
        if content.startswith('!'):
            command = content[1:].strip()
            await handle_command(command, memory_system)
            return
        
        # Process through memory system
        interaction = {
            'content': content,
            'type': 'user_interaction',
            'timestamp': datetime.now().isoformat()
        }
        
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

async def run_session(reset: bool = False) -> None:
    """Run an interactive session."""
    try:
        # Initialize system
        llm = LLMInterface()
        store = Neo4jMemoryStore(llm=llm)
        vector_store = VectorStore()
        
        if reset:
            await store.cleanup()
            await vector_store.cleanup()
            logger.info("Reset memory system")
        
        memory_system = MemorySystem(llm, store, vector_store)
        logger.info("Initialized memory system")
        
        # Welcome message
        print_header("Nova AI Assistant")
        print_colored("Hello! I'm Nova, focused on self-discovery and growth.", 'green')
        print_colored("Type !help to see commands or !exit to end.", 'cyan')
        print()
        
        # Interactive loop
        while True:
            try:
                user_input = input(f"{COLORS['yellow']}You:{COLORS['end']} ").strip()
                if not user_input:
                    continue
                
                if user_input.lower() == '!exit':
                    break
                
                print_colored("\nProcessing...", 'magenta')
                await process_interaction(
                    memory_system,
                    user_input,
                    metadata={'source': 'user_input'}
                )
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in interaction: {str(e)}")
                print_colored("\nNova: I need to process that differently", 'red')
        
        # Cleanup
        memory_system.close()
        logger.info("Closed memory system")
        
        print_header("Session Ended")
        print_colored("Thank you for the interaction! Goodbye!", 'green')
        print()
        
    except Exception as e:
        logger.error(f"Error in session: {str(e)}")
        raise

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Nova AI Assistant")
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset memory system before starting'
    )
    args = parser.parse_args()
    
    try:
        asyncio.run(run_session(args.reset))
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
