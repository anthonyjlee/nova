"""Script to run the Nova FastAPI server."""

import os
import sys
import uvicorn
import logging
import asyncio
import aiohttp
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent.resolve()
sys.path.append(str(project_root))

# Configure logging - file only, no console output
LOGS_DIR = project_root / "logs" / "server"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / f"server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Configure logger
logger = logging.getLogger("nova-server")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.propagate = False  # Prevent propagation to root logger

async def start_docker_services():
    """Start all required Docker services."""
    try:
        compose_dir = Path(__file__).parent / "docker"
        os.chdir(str(compose_dir))
        subprocess.run(["docker", "compose", "up", "-d"], check=True)
        logger.info("Docker services started successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to start Docker services: {str(e)}")
        return False

async def wait_for_neo4j(max_retries: int = 30, retry_interval: int = 2):
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
                return True
        except Exception as e:
            if retry_count == 0:
                logger.warning(f"Waiting for Neo4j: {str(e)}")
        retry_count += 1
        await asyncio.sleep(retry_interval)
    logger.error("Neo4j failed to become ready")
    return False

async def wait_for_qdrant(max_retries: int = 30, retry_interval: int = 2):
    """Wait for Qdrant to be ready."""
    retry_count = 0
    async with aiohttp.ClientSession() as session:
        while retry_count < max_retries:
            try:
                async with session.get('http://localhost:6333/healthz') as response:
                    if response.status == 200:
                        logger.info("Qdrant is ready")
                        return True
            except Exception as e:
                if retry_count == 0:
                    logger.warning(f"Waiting for Qdrant: {str(e)}")
            retry_count += 1
            await asyncio.sleep(retry_interval)
    logger.error("Qdrant failed to become ready")
    return False

async def wait_for_redis(max_retries: int = 30, retry_interval: int = 2):
    """Wait for Redis to be ready."""
    retry_count = 0
    while retry_count < max_retries:
        try:
            result = subprocess.run(
                ["docker", "exec", "docker-redis-1", "redis-cli", "ping"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and "PONG" in result.stdout:
                logger.info("Redis is ready")
                return True
        except Exception as e:
            if retry_count == 0:
                logger.warning(f"Waiting for Redis: {str(e)}")
        retry_count += 1
        await asyncio.sleep(retry_interval)
    logger.error("Redis failed to become ready")
    return False

async def main():
    """Run the FastAPI server."""
    try:
        # Start Docker services
        if not await start_docker_services():
            print("❌ Failed to start Docker services")
            sys.exit(1)
        print("✓ Docker services started")

        # Wait for services
        if not await wait_for_neo4j():
            print("❌ Neo4j failed to start")
            sys.exit(1)
        print("✓ Neo4j ready")

        if not await wait_for_qdrant():
            print("❌ Qdrant failed to start")
            sys.exit(1)
        print("✓ Qdrant ready")

        if not await wait_for_redis():
            print("❌ Redis failed to start")
            sys.exit(1)
        print("✓ Redis ready")
        
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
            log_level="error",
            access_log=False,
            timeout_keep_alive=30
        )
        server = uvicorn.Server(config)
        print(f"✓ Server starting on http://{host}:{port}")
        await server.serve()
    except Exception as e:
        print(f"❌ Server failed to start: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
