"""
Main entry point for the memory system.
"""

import os
import sys
import json
import logging
import asyncio
import argparse
from datetime import datetime
from typing import Optional

from src.nia.memory.llm_interface import LLMInterface
from src.nia.memory.neo4j_store import Neo4jMemoryStore
from src.nia.memory.vector_store import VectorStore
from src.nia.memory.memory_integration import MemorySystem
from src.nia.memory.logging_config import configure_logging

logger = logging.getLogger(__name__)

HELP_TEXT = """
Available commands:
!help     - Show this help message
!status   - Show memory system status
!reset    - Reset memory system
!exit     - Exit the program

Type any message to interact with Nova.
"""

def format_status(status: dict) -> str:
    """Format status output."""
    lines = []
    lines.append("\n============================================================")
    lines.append("                    Memory System Status                    ")
    lines.append("============================================================\n")
    
    # Vector Store Status
    vector_status = status.get("vector_store", {})
    lines.append("Vector Store:")
    lines.append(f"  Collection: {vector_status.get('collection_name')}")
    lines.append(f"  Total Vectors: {vector_status.get('total_vectors', 0)}")
    lines.append(f"  Episodic Memories: {vector_status.get('episodic_memories', 0)}")
    lines.append(f"  Semantic Memories: {vector_status.get('semantic_memories', 0)}")
    lines.append(f"  Vector Size: {vector_status.get('vector_size')}")
    lines.append(f"  Embedding Model: {vector_status.get('embedding_model')}")
    lines.append(f"  Status: {vector_status.get('status', 'unknown')}")
    
    # Neo4j Status
    neo4j_status = status.get("neo4j", {})
    lines.append("\nNeo4j Store:")
    lines.append(f"  Connected: {neo4j_status.get('connected', False)}")
    if neo4j_status.get("error"):
        lines.append(f"  Error: {neo4j_status['error']}")
    
    # Timestamp
    lines.append(f"\nTimestamp: {status.get('timestamp', datetime.now().isoformat())}")
    lines.append("\n============================================================")
    
    return "\n".join(lines)

async def run_session(reset: bool = False) -> None:
    """Run an interactive session."""
    try:
        # Initialize components
        llm = LLMInterface()
        store = Neo4jMemoryStore(llm=llm)
        memory_system = MemorySystem(llm, store)
        logger.info("Initialized memory system")
        
        # Reset if requested
        if reset:
            await memory_system.cleanup()
            print("Memory system reset complete.")
        
        # Print welcome message
        print("\n============================================================")
        print("                     Nova AI Assistant                     ")
        print("============================================================\n")
        print("Hello! I'm Nova, focused on self-discovery and growth.")
        print("Type !help to see commands or !exit to end.\n")
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                # Handle commands
                if user_input.lower() == "!help":
                    print(HELP_TEXT)
                    continue
                elif user_input.lower() == "!status":
                    status = await memory_system.get_status()
                    print(format_status(status))
                    continue
                elif user_input.lower() == "!reset":
                    print("\nResetting memory system...")
                    await memory_system.cleanup()
                    print("Memory system reset complete.")
                    continue
                elif user_input.lower() == "!exit":
                    break
                
                # Process user input
                print("\nProcessing...")
                response = await memory_system.process_interaction(
                    content=user_input,
                    metadata={
                        'timestamp': datetime.now().isoformat(),
                        'type': 'user_input'
                    }
                )
                
                # Print response
                print("\nNova:", response.response)
                
            except KeyboardInterrupt:
                print("\nInterrupted by user")
                break
            except Exception as e:
                logger.error(f"Error processing interaction: {str(e)}")
                print("\nNova: I need to process that differently")
        
        # Close memory system
        memory_system.close()
        logger.info("Closed memory system")
        
        # Print goodbye message
        print("\n============================================================")
        print("                       Session Ended                       ")
        print("============================================================\n")
        print("Thank you for the interaction! Goodbye!")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run the memory system")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset memory system on startup"
    )
    args = parser.parse_args()
    
    # Configure logging
    configure_logging()
    
    # Run session
    asyncio.run(run_session(args.reset))

if __name__ == "__main__":
    main()
