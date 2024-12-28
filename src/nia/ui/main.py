"""Main entry point for NIA UI."""

import os
import sys
import logging
from pathlib import Path
import asyncio
from typing import Optional

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
        import networkx
        import matplotlib
        import anthropic
        import neo4j
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {str(e)}")
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
    
    # Check for API keys
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not found in environment")
        logger.warning("System-1 features will require manual key entry")
    
    return True

def setup_paths():
    """Set up Python path to include NIA modules."""
    # Add project root to Python path
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Create required directories
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    return project_root

async def main():
    """Main entry point."""
    try:
        # Set up paths
        project_root = setup_paths()
        logger.info(f"Project root: {project_root}")
        
        # Check dependencies
        if not check_dependencies():
            logger.error("Missing required dependencies")
            sys.exit(1)
        
        # Check environment
        if not check_environment():
            logger.error("Environment setup incomplete")
            sys.exit(1)
        
        # Import UI components
        from .mobile import MobileUI
        from .desktop import DesktopUI
        
        # Determine if running on mobile
        def is_mobile() -> bool:
            """Check if the request is coming from a mobile device."""
            try:
                import user_agents
                from gradio.routes import Request
                request = Request.get_current()
                if request and request.headers.get("User-Agent"):
                    user_agent = user_agents.parse(request.headers["User-Agent"])
                    return user_agent.is_mobile
            except:
                pass
            return False
        
        # Launch appropriate interface
        if is_mobile():
            logger.info("Launching mobile interface")
            ui = MobileUI()
        else:
            logger.info("Launching desktop interface")
            ui = DesktopUI()
        
        # Set API key from environment
        api_key = os.getenv("ANTHROPIC_API_KEY", "IGA3zJxd3AtXLWyVUq9fyNDev7xHD4UGbpwSWW8UejHeuUwO")
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
            logger.info("API key set from environment")
        
        # Launch UI
        ui.launch()
        
    except Exception as e:
        logger.error(f"Error starting UI: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
