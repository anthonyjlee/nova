"""Script to run the Nova FastAPI server."""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the FastAPI server."""
    try:
        # Log startup information
        logger.info("Starting Nova FastAPI server...")
        logger.info(f"Project root: {project_root}")
        logger.info(f"Python path: {sys.path}")
        
        # Get configuration from environment
        host = os.getenv("NOVA_HOST", "127.0.0.1")
        port = int(os.getenv("NOVA_PORT", "8000"))
        reload = os.getenv("NOVA_RELOAD", "true").lower() == "true"
        
        # Log configuration
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Reload: {reload}")
        
        # Run server
        uvicorn.run(
            "nia.nova.core.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
