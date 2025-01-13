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

# Configure logging
LOGS_DIR = project_root / "logs" / "server"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOGS_DIR / f"server_{session_id}.log"
json_log = LOGS_DIR / f"server_{session_id}.json"

print(f"Logs will be written to:\n- {log_file}\n- {json_log}")

# Configure file handler for detailed logs
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Configure console handler for critical updates only
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    '%(levelname)s: %(message)s'
))

# Configure JSON handler for structured logging
class JsonLogHandler(logging.Handler):
    def __init__(self, log_file):
        super().__init__()
        self.log_file = log_file
        self.logs = []
        
    def emit(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno,
            "thread_id": record.thread,
            "process_id": record.process,
            "service": getattr(record, 'service', None),
            "status": getattr(record, 'status', None)
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        self.logs.append(log_entry)
        self._save_logs()
        
    def _save_logs(self):
        with open(self.log_file, 'w') as f:
            json.dump({
                "session_id": session_id,
                "logs": self.logs,
                "summary": {
                    "total_services": len(set(l.get("service") for l in self.logs if l.get("service"))),
                    "healthy_services": len(set(l.get("service") for l in self.logs 
                                             if l.get("service") and l.get("status") == "healthy")),
                    "failed_services": len(set(l.get("service") for l in self.logs 
                                            if l.get("service") and l.get("status") == "failed"))
                }
            }, f, indent=2)

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.addHandler(JsonLogHandler(json_log))

# Get module logger
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
                logger.info("Neo4j is ready!", extra={"service": "neo4j", "status": "healthy"})
                return
            
            logger.debug("Waiting for Neo4j to be ready...", extra={"service": "neo4j", "status": "waiting"})
            
        except Exception as e:
            logger.warning(f"Error checking Neo4j status: {str(e)}", 
                         extra={"service": "neo4j", "status": "error"})
            # If Neo4j container is not running, start services
            compose_dir = Path(__file__).parent / "docker"
            os.chdir(str(compose_dir))
            subprocess.run(["docker compose up -d"])
            
        retry_count += 1
        await asyncio.sleep(retry_interval)
        
    raise RuntimeError("Neo4j failed to become ready in time")

async def wait_for_qdrant(max_retries: int = 30, retry_interval: int = 1):
    """Wait for Qdrant to be ready."""
    retry_count = 0
    
    async with aiohttp.ClientSession() as session:
        while retry_count < max_retries:
            try:
                # Check Qdrant health via HTTP
                async with session.get('http://localhost:6333/healthz') as response:
                    if response.status == 200:
                        logger.info("Qdrant is ready!", extra={"service": "qdrant", "status": "healthy"})
                        return
                    
                logger.debug("Waiting for Qdrant to be ready...", extra={"service": "qdrant", "status": "waiting"})
                
            except Exception as e:
                logger.warning(f"Error checking Qdrant status: {str(e)}", 
                             extra={"service": "qdrant", "status": "error"})
                
            retry_count += 1
            await asyncio.sleep(retry_interval)
            
    raise RuntimeError("Qdrant failed to become ready in time")

async def main():
    """Run the FastAPI server."""
    try:
        # Log startup information
        logger.info("Starting Nova FastAPI server...", extra={"service": "fastapi", "status": "starting"})
        logger.debug(f"Project root: {project_root}")
        logger.debug(f"Python path: {sys.path}")
        
        # Wait for services
        await wait_for_neo4j()
        await wait_for_qdrant()
        
        # Get configuration from environment
        host = os.getenv("NOVA_HOST", "127.0.0.1")
        port = int(os.getenv("NOVA_PORT", "8000"))
        reload = os.getenv("NOVA_RELOAD", "true").lower() == "true"
        
        # Log configuration
        logger.debug(f"Host: {host}")
        logger.debug(f"Port: {port}")
        logger.debug(f"Reload: {reload}")
        
        # Configure uvicorn logging
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        log_config["handlers"]["access"]["filename"] = str(log_file)
        log_config["handlers"]["access"]["formatter"] = "access"
        
        # Run server
        logger.info("Starting uvicorn server...", extra={"service": "fastapi", "status": "starting"})
        try:
            config = uvicorn.Config(
                "nia.nova.core.app:app",
                host=host,
                port=port,
                reload=reload,
                log_level="debug",
                log_config=log_config,
                access_log=True,
                timeout_keep_alive=30
            )
            server = uvicorn.Server(config)
            logger.info("Server configuration complete, starting server...", 
                       extra={"service": "fastapi", "status": "configured"})
            await server.serve()
        except Exception as e:
            logger.error(f"Failed to start uvicorn server: {str(e)}", 
                        extra={"service": "fastapi", "status": "failed"})
            logger.debug(traceback.format_exc())
            raise
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", 
                    extra={"service": "fastapi", "status": "failed"})
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
