"""
Main application entry point.
"""

import os
import sys
import logging
import argparse
import asyncio
from datetime import datetime
from typing import Optional

from nia.memory.llm_interface import LLMInterface
from nia.memory.neo4j_store import Neo4jMemoryStore
from nia.memory.vector_store import VectorStore
from nia.memory.memory_integration import MemorySystem

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def print_header():
    """Print application header."""
    print("\n" + "=" * 60)
    print(" " * 21 + "Nova AI Assistant")
    print("=" * 60 + "\n")
    print("Hello! I'm Nova focused on self-discovery and growth.")
    print("Type !help to see commands or !exit to end.\n")

def print_footer():
    """Print application footer."""
    print("\n" + "=" * 60)
    print(" " * 23 + "Session Ended")
    print("=" * 60 + "\n")
    print("Thank you for the interaction! Goodbye!")

def print_help():
    """Print help information."""
    print("\nAvailable Commands:")
    print("  !help     - Show this help message")
    print("  !exit     - Exit the application")
    print("  !reset    - Reset memory system")
    print("  !status   - Show memory system status")
    print("  !search   - Search memories")
    print("  !clear    - Clear screen\n")

async def get_user_input(prompt: str = "You: ") -> str:
    """Get user input asynchronously."""
    return await asyncio.get_event_loop().run_in_executor(
        None, lambda: input(prompt)
    )

async def process_command(
    command: str,
    memory: MemorySystem
) -> bool:
    """Process special commands."""
    if command == "!help":
        print_help()
        return True
        
    elif command == "!exit":
        return False
        
    elif command == "!reset":
        print("\nResetting memory system...")
        await memory.cleanup()
        print("Memory system reset complete.")
        return True
        
    elif command == "!status":
        status = await memory.get_status()
        print("\nMemory System Status:")
        print(f"Vector Store: {status['vector_store']}")
        print(f"Neo4j: {status['neo4j']}")
        print(f"Timestamp: {status['timestamp']}\n")
        return True
        
    elif command == "!search":
        query = input("Enter search query: ")
        results = await memory.search_memories(query)
        print("\nSearch Results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result['score']:.2f}")
            print(f"Content: {result['content']}")
            print(f"Metadata: {result['metadata']}")
        print()
        return True
        
    elif command == "!clear":
        os.system('cls' if os.name == 'nt' else 'clear')
        print_header()
        return True
        
    return False

async def run_session(reset: bool = False):
    """Run interactive session."""
    try:
        # Initialize components
        llm = LLMInterface()
        store = Neo4jMemoryStore()
        vector_store = VectorStore()
        
        # Initialize memory system
        memory = MemorySystem(llm, store, vector_store)
        
        # Reset if requested
        if reset:
            print("\nResetting memory system...")
            await memory.cleanup()
            print("Memory system reset complete.")
        
        logger.info("Initialized memory system")
        print_header()
        
        # Main interaction loop
        while True:
            # Get user input
            user_input = await get_user_input()
            
            # Check for commands
            if user_input.startswith("!"):
                should_continue = await process_command(user_input, memory)
                if not should_continue:
                    break
                continue
            
            # Process user input
            print("\nProcessing...")
            try:
                response = await memory.process_interaction(user_input)
                print(f"\nNova: {response.response}")
            except Exception as e:
                logger.error(f"Error processing interaction: {str(e)}")
                print(f"\nNova: I need to process that differently")
        
        # Clean up
        memory.close()
        logger.info("Closed memory system")
        print_footer()
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Nova AI Assistant")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset memory system on startup"
    )
    args = parser.parse_args()
    
    try:
        asyncio.run(run_session(args.reset))
    except KeyboardInterrupt:
        print_footer()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
