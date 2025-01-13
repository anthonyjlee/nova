"""Script to run the Nova FastAPI server."""

import os
import sys
import json
import uvicorn
import logging
import asyncio
import aiohttp
import subprocess
import traceback
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent.resolve()
sys.path.append(str(project_root))

# Configure logging with rate limiting
class RateLimitedLogger:
    def __init__(self, name: str, rate_limit: float = 1.0):  # Increased rate limit to 1 second
        self.logger = logging.getLogger(name)
        self.rate_limit = rate_limit
        self.last_log = {}
        
        # Configure basic logging
        LOGS_DIR = project_root / "logs" / "server"
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        log_file = LOGS_DIR / f"server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # File handler for all logs
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Console handler for critical updates only
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        
        # Configure logger - Set base level to INFO for file logging
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _should_log(self, level: int, msg: str) -> bool:
        now = datetime.now().timestamp()
        key = f"{level}:{msg}"
        if key not in self.last_log or (now - self.last_log[key]) >= self.rate_limit:
            self.last_log[key] = now
            return True
        return False
    
    def debug(self, msg: str, *args, **kwargs):
        if self._should_log(logging.DEBUG, msg):
            self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        if self._should_log(logging.INFO, msg):
            self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        if self._should_log(logging.WARNING, msg):
            self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        if self._should_log(logging.ERROR, msg):
            self.logger.error(msg, *args, **kwargs)

# Create rate-limited logger instance
logger = RateLimitedLogger(__name__)

async def wait_for_neo4j(max_retries: int = 30, retry_interval: int = 2):  # Increased retry interval
    """Wait for Neo4j to be ready."""
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            result = subprocess.run(
                ["docker", "exec", "docker-neo4j-1", "cypher-shell", "-u", "neo4j", "-p", "password", "RETURN 1"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("Neo4j is ready")
                return
            
        except Exception as e:
            if retry_count == 0:  # Only log on first attempt
                logger.warning("Waiting for Neo4j...")
                compose_dir = Path(__file__).parent / "docker"
                os.chdir(str(compose_dir))
                subprocess.run(["docker compose up -d"])
            
        retry_count += 1
        await asyncio.sleep(retry_interval)
        
    raise RuntimeError("Neo4j failed to become ready in time")

async def wait_for_qdrant(max_retries: int = 30, retry_interval: int = 2):  # Increased retry interval
    """Wait for Qdrant to be ready."""
    retry_count = 0
    
    if retry_count == 0:  # Only log on first attempt
        logger.warning("Waiting for Qdrant...")
        
    async with aiohttp.ClientSession() as session:
        while retry_count < max_retries:
            try:
                async with session.get('http://localhost:6333/healthz') as response:
                    if response.status == 200:
                        logger.info("Qdrant is ready")
                        return
                    
            except Exception:
                pass
                
            retry_count += 1
            await asyncio.sleep(retry_interval)
            
    raise RuntimeError("Qdrant failed to become ready in time")

async def main():
    """Run the FastAPI server."""
    try:
        logger.warning("Starting Nova FastAPI server...")
        
        # Wait for services
        await wait_for_neo4j()
        await wait_for_qdrant()
        
        # Get configuration from environment
        host = os.getenv("NOVA_HOST", "127.0.0.1")
        port = int(os.getenv("NOVA_PORT", "8000"))
        reload = os.getenv("NOVA_RELOAD", "true").lower() == "true"
        
        # Run server with minimal logging
        config = uvicorn.Config(
            "nia.nova.core.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="error",  # Only show errors
            access_log=False,   # Disable access logs
            timeout_keep_alive=30
        )
        server = uvicorn.Server(config)
        logger.warning(f"Server starting on http://{host}:{port}")
        await server.serve()
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", 
                    extra={"service": "fastapi", "status": "failed"})
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
