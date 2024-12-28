"""Main entry point for NIA chat interface."""

import os
import sys
import logging
from pathlib import Path
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies() -> bool:
    """Check if all required dependencies are available."""
    try:
        import gradio
        import neo4j
        import aiohttp
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {str(e)}")
        return False

def check_lmstudio() -> bool:
    """Check if LMStudio is running."""
    import requests
    try:
        response = requests.get("http://localhost:1234/v1/models", timeout=2.0)
        return response.status_code == 200
    except:
        return False

def check_environment() -> bool:
    """Check if required environment variables and services are set up."""
    # Check Neo4j
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    try:
        from neo4j import GraphDatabase
        with GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password)) as driver:
            with driver.session() as session:
                session.run("RETURN 1")
        logger.info("Neo4j connection successful")
    except Exception as e:
        logger.error(f"Neo4j connection failed: {str(e)}")
        logger.error("Please ensure Neo4j is running and credentials are correct")
        return False
    
    # Check LMStudio
    if not check_lmstudio():
        logger.warning("LMStudio is not running")
        logger.warning("Chat functionality will be limited until LMStudio is started")
        # Don't return False since LMStudio is optional at startup
    else:
        logger.info("LMStudio connection successful")
    
    return True

def setup_paths():
    """Set up Python path and required directories."""
    # Add project root to Python path
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Create required directories
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create state directory
    state_dir = Path(os.path.expanduser("~/.nia/state"))
    state_dir.mkdir(parents=True, exist_ok=True)
    
    return project_root, state_dir

async def main():
    """Main entry point."""
    try:
        # Set up paths and directories
        project_root, state_dir = setup_paths()
        logger.info(f"Project root: {project_root}")
        logger.info(f"State directory: {state_dir}")
        
        # Check dependencies
        if not check_dependencies():
            logger.error("Missing required dependencies")
            sys.exit(1)
        
        # Check environment
        if not check_environment():
            logger.error("Environment setup incomplete")
            sys.exit(1)
        
        # Import UI components
        from .chat import ChatUI
        
        # Launch chat interface with state persistence
        logger.info("Launching chat interface")
        ui = ChatUI(state_dir=str(state_dir))
        await ui.launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,
            state_dir=str(state_dir)
        )
        
    except Exception as e:
        logger.error(f"Error starting UI: {str(e)}")
        sys.exit(1)

def run():
    """Run the main function in an async context."""
    asyncio.run(main())

if __name__ == "__main__":
    run()
