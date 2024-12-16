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

from nia.memory.llm_interface import LLMInterface
from nia.memory.neo4j_store import Neo4jMemoryStore
from nia.memory.vector_store import VectorStore
from nia.memory.memory_integration import MemorySystem
from nia.memory.logging_config import configure_logging

logger = logging.getLogger(__name__)

# ANSI color codes
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
ENDC = "\033[0m"
BOLD = "\033[1m"

HELP_TEXT = f"""
Available commands:
{BLUE}!help{ENDC}     - Show this help message
{BLUE}!status{ENDC}   - Show memory system status
{BLUE}!reset{ENDC}    - Reset memory system
{BLUE}!exit{ENDC}     - Exit the program

Type any message to interact with Nova.
"""

def format_status(status: dict) -> str:
    """Format status output."""
    lines = []
    lines.append(f"\n{BOLD}============================================================{ENDC}")
    lines.append(f"{BOLD}                    Memory System Status                    {ENDC}")
    lines.append(f"{BOLD}============================================================{ENDC}\n")
    
    # Vector Store Status
    vector_status = status.get("vector_store", {})
    lines.append(f"{BOLD}Vector Store:{ENDC}")
    lines.append(f"  Collection: {BLUE}{vector_status.get('collection_name')}{ENDC}")
    lines.append(f"  Total Vectors: {vector_status.get('total_vectors', 0)}")
    lines.append(f"  Episodic Memories: {YELLOW}{vector_status.get('episodic_memories', 0)}{ENDC}")
    lines.append(f"  Semantic Memories: {GREEN}{vector_status.get('semantic_memories', 0)}{ENDC}")
    lines.append(f"  Vector Size: {vector_status.get('vector_size')}")
    lines.append(f"  Embedding Model: {vector_status.get('embedding_model')}")
    
    # Color status based on value
    status_value = vector_status.get('status', 'unknown')
    status_color = GREEN if status_value == 'green' else YELLOW if status_value == 'yellow' else RED
    lines.append(f"  Status: {status_color}{status_value}{ENDC}")
    
    # Neo4j Status
    neo4j_status = status.get("neo4j", {})
    lines.append(f"\n{BOLD}Neo4j Store:{ENDC}")
    connected = neo4j_status.get('connected', False)
    status_color = GREEN if connected else RED
    lines.append(f"  Connected: {status_color}{connected}{ENDC}")
    if neo4j_status.get("error"):
        lines.append(f"  Error: {RED}{neo4j_status['error']}{ENDC}")
    
    # Timestamp
    lines.append(f"\nTimestamp: {BLUE}{status.get('timestamp', datetime.now().isoformat())}{ENDC}")
    lines.append(f"{BOLD}============================================================{ENDC}")
    
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
            print(f"{GREEN}Memory system reset complete.{ENDC}")
        
        # Print welcome message
        print(f"\n{BOLD}============================================================{ENDC}")
        print(f"{BOLD}                     Nova AI Assistant                     {ENDC}")
        print(f"{BOLD}============================================================{ENDC}\n")
        print(f"{BLUE}Hello! I'm Nova, focused on self-discovery and growth.")
        print(f"Type !help to see commands or !exit to end.{ENDC}\n")
        
        while True:
            try:
                # Get user input
                user_input = input(f"{BOLD}You:{ENDC} ").strip()
                
                # Handle commands
                if user_input.lower() == "!help":
                    print(HELP_TEXT)
                    continue
                elif user_input.lower() == "!status":
                    status = await memory_system.get_status()
                    print(format_status(status))
                    continue
                elif user_input.lower() == "!reset":
                    print(f"\n{YELLOW}Resetting memory system...{ENDC}")
                    await memory_system.cleanup()
                    print(f"{GREEN}Memory system reset complete.{ENDC}")
                    continue
                elif user_input.lower() == "!exit":
                    break
                
                # Process user input
                print(f"\n{YELLOW}Processing...{ENDC}")
                response = await memory_system.process_interaction(
                    content=user_input,
                    metadata={
                        'timestamp': datetime.now().isoformat(),
                        'type': 'user_input'
                    }
                )
                
                # Print response
                print(f"\n{BOLD}Nova:{ENDC}", response.response)
                
            except KeyboardInterrupt:
                print("\nInterrupted by user")
                break
            except Exception as e:
                logger.error(f"Error processing interaction: {str(e)}")
                print(f"\n{BOLD}Nova:{ENDC} I need to process that differently")
        
        # Close memory system
        memory_system.close()
        logger.info("Closed memory system")
        
        # Print goodbye message
        print(f"\n{BOLD}============================================================{ENDC}")
        print(f"{BOLD}                       Session Ended                       {ENDC}")
        print(f"{BOLD}============================================================{ENDC}\n")
        print(f"{BLUE}Thank you for the interaction! Goodbye!{ENDC}")
        
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
