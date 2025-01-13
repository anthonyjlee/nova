"""Script to run the Nova FastAPI server."""

import os
import sys
import uvicorn
import logging
import asyncio
import subprocess
import traceback
from pathlib import Path
from typing import List, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def wait_for_neo4j(max_retries: int = 30, retry_interval: int = 1):
    """Wait for Neo4j to be ready."""
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Check Neo4j health using cypher-shell
            result = subprocess.run(
                ["docker", "exec", "docker-neo4j-1", "cypher-shell", "-u", "neo4j", "-p", "password", "RETURN 1"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("Neo4j is ready!")
                return
            
            logger.info("Waiting for Neo4j to be ready...")
            
        except Exception as e:
            logger.warning(f"Error checking Neo4j status: {str(e)}")
            # If Neo4j container is not running, start services
            compose_dir = Path(__file__).parent / "docker"
            os.chdir(str(compose_dir))
            subprocess.run(["docker-compose", "up", "-d"])
            
        retry_count += 1
        await asyncio.sleep(retry_interval)
        
    raise RuntimeError("Neo4j failed to become ready in time")

async def main():
    """Run the FastAPI server."""
    try:
        # Log startup information
        logger.info("Starting Nova FastAPI server...")
        logger.info(f"Project root: {project_root}")
        logger.info(f"Python path: {sys.path}")
        
        # Wait for Neo4j
        await wait_for_neo4j()
        
        # Get configuration from environment
        host = os.getenv("NOVA_HOST", "127.0.0.1")
        port = int(os.getenv("NOVA_PORT", "8000"))  # Changed to match manage.py health check
        reload = os.getenv("NOVA_RELOAD", "true").lower() == "true"
        
        # Log configuration
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Reload: {reload}")
        
        # Run server
        logger.info("Starting uvicorn server...")
        try:
            config = uvicorn.Config(
                "nia.nova.core.app:app",
                host=host,
                port=port,
                reload=reload,
                log_level="debug",  # Change to debug for more detailed logs
                access_log=True,
                timeout_keep_alive=30
            )
            server = uvicorn.Server(config)
            logger.info("Server configuration complete, starting server...")
            await server.serve()
        except Exception as e:
            logger.error(f"Failed to start uvicorn server: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
