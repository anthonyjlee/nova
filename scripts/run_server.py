"""Script to run the Nova FastAPI server with comprehensive initialization and monitoring."""

import os
import sys
import uvicorn
import logging
import asyncio
import aiohttp
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Set

from nia.memory.two_layer import TwoLayerMemorySystem
from nia.memory.vector_store import VectorStore
from nia.nova.core.thread_manager import ThreadManager

# Add src directory to Python path
project_root = Path(__file__).parent.parent.resolve()
sys.path.append(str(project_root / "src"))

# Configure logging with both file and console handlers
LOGS_DIR = project_root / "test_results" / "initialization_logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / f"server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for logging."""
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            'phase': getattr(record, 'phase', 'unknown'),
            'timestamp': datetime.utcnow().isoformat(),
            'name': record.name,
            'level': record.levelname,
            'file': record.filename,
            'line': record.lineno,
            'message': record.getMessage(),
            'exc_info': record.exc_info and str(record.exc_info),
        }, default=str) + '\n'

# Configure JSON file handler
json_handler = logging.FileHandler(log_file)
json_handler.setLevel(logging.DEBUG)
json_handler.setFormatter(JsonFormatter())

# Configure console handler with minimal formatting
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter('%(message)s'))

# Configure main logger
logger = logging.getLogger("nova-server")
logger.setLevel(logging.DEBUG)
logger.addHandler(json_handler)
logger.addHandler(console_handler)
logger.propagate = False

# Configure uvicorn logger
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.setLevel(logging.DEBUG)
uvicorn_logger.addHandler(json_handler)
uvicorn_logger.propagate = False

# Constants
MAX_RETRIES = 30
RETRY_INTERVAL = 2
REQUIRED_SYSTEM_THREADS = ["nova-team", "system-logs", "agent-communication"]

class ServiceStatus:
    """Track service health status with proper cleanup."""
    def __init__(self):
        self._services: Dict[str, bool] = {
            "neo4j": False,
            "qdrant": False,
            "redis": False,
            "celery": False,
            "memory_system": False,
            "thread_manager": False
        }
        self._initialized: Set[str] = set()
        
    def set_status(self, service: str, status: bool) -> None:
        """Update service status with proper tracking."""
        self._services[service] = status
        if status:
            self._initialized.add(service)
        status_symbol = "✓" if status else "❌"
        logger.warning(f"{status_symbol} {service.capitalize()}: {'ready' if status else 'failed'}")
    
    def all_ready(self) -> bool:
        """Check if all services are ready."""
        return all(self._services.values())
        
    def get_initialized(self) -> Set[str]:
        """Get set of initialized services for cleanup."""
        return self._initialized

async def start_docker_services(status: ServiceStatus):
    """Start all required Docker services with proper cleanup."""
    try:
        compose_dir = Path(__file__).parent / "docker"
        os.chdir(str(compose_dir))
        
        # Stop any existing services first
        subprocess.run(["docker", "compose", "down"], check=True)
        
        # Start services
        subprocess.run(["docker", "compose", "up", "-d"], check=True)
        logger.warning("Docker services started")
        return True
    except Exception as e:
        logger.error(f"Failed to start Docker services: {str(e)}")
        return False

async def wait_for_neo4j(status: ServiceStatus, max_retries: int = MAX_RETRIES, retry_interval: int = RETRY_INTERVAL):
    """Wait for Neo4j to be ready with proper error handling."""
    retry_count = 0
    while retry_count < max_retries:
        try:
            result = subprocess.run(
                ["docker", "exec", "docker-neo4j-1", "cypher-shell", "-u", "neo4j", "-p", "password", "RETURN 1"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.warning("Neo4j is ready")
                status.set_status("neo4j", True)
                return True
        except Exception as e:
            if retry_count == 0:
                logger.warning(f"Waiting for Neo4j: {str(e)}")
        retry_count += 1
        await asyncio.sleep(retry_interval)
    logger.error("Neo4j failed to become ready")
    return False

async def wait_for_qdrant(status: ServiceStatus, max_retries: int = MAX_RETRIES, retry_interval: int = RETRY_INTERVAL):
    """Wait for Qdrant to be ready with proper error handling."""
    retry_count = 0
    async with aiohttp.ClientSession() as session:
        while retry_count < max_retries:
            try:
                async with session.get('http://localhost:6333/healthz') as response:
                    if response.status == 200:
                        logger.warning("Qdrant is ready")
                        status.set_status("qdrant", True)
                        return True
            except Exception as e:
                if retry_count == 0:
                    logger.warning(f"Waiting for Qdrant: {str(e)}")
            retry_count += 1
            await asyncio.sleep(retry_interval)
    logger.error("Qdrant failed to become ready")
    return False

async def wait_for_redis(status: ServiceStatus, max_retries: int = MAX_RETRIES, retry_interval: int = RETRY_INTERVAL):
    """Wait for Redis to be ready with proper error handling."""
    retry_count = 0
    while retry_count < max_retries:
        try:
            result = subprocess.run(
                ["docker", "exec", "docker-redis-1", "redis-cli", "ping"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and "PONG" in result.stdout:
                logger.warning("Redis is ready")
                status.set_status("redis", True)
                return True
        except Exception as e:
            if retry_count == 0:
                logger.warning(f"Waiting for Redis: {str(e)}")
        retry_count += 1
        await asyncio.sleep(retry_interval)
    logger.error("Redis failed to become ready")
    return False

async def verify_memory_system(status: ServiceStatus) -> Optional[TwoLayerMemorySystem]:
    """Initialize and verify memory system with proper cleanup."""
    try:
        # Initialize memory system with memory pools
        memory_system = TwoLayerMemorySystem()
        await memory_system.initialize()
        
        # Verify vector store with connection pooling
        if memory_system.vector_store:
            await memory_system.vector_store.connect()
            await memory_system.vector_store.inspect_collection()
        
        # Verify episodic store with minimal serialization
        from nia.core.types.memory_types import EpisodicMemory, MemoryType
        test_memory = EpisodicMemory(
            content="Memory system test",
            type=MemoryType.EPISODIC,
            metadata={
                "type": "test",
                "timestamp": datetime.utcnow().isoformat()
            },
            importance=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        if memory_system.episodic:
            # Use direct layer access
            await memory_system.episodic.store_memory(test_memory)
        
        status.set_status("memory_system", True)
        return memory_system
    except Exception as e:
        logger.error(f"Memory system verification failed: {str(e)}")
        status.set_status("memory_system", False)
        return None

async def verify_thread_manager(status: ServiceStatus, memory_system: TwoLayerMemorySystem) -> Optional[ThreadManager]:
    """Initialize and verify thread manager with proper cleanup."""
    try:
        thread_manager = ThreadManager(memory_system)
        
        # Verify system threads exist with direct layer access
        for thread_name in REQUIRED_SYSTEM_THREADS:
            thread = await thread_manager.get_thread(thread_name)
            if not thread:
                logger.warning(f"System thread {thread_name} missing, creating...")
                await thread_manager.create_thread(
                    title=thread_name,
                    domain="system",
                    metadata={
                        "type": "system-thread",
                        "system": True,
                        "pinned": True
                    }
                )
        
        status.set_status("thread_manager", True)
        return thread_manager
    except Exception as e:
        logger.error(f"Thread manager verification failed: {str(e)}")
        status.set_status("thread_manager", False)
        return None

async def start_celery_worker(status: ServiceStatus):
    """Start Celery worker with proper monitoring."""
    try:
        worker_process = subprocess.Popen(
            ["celery", "-A", "nia.nova.core.celery_app", "worker", "--loglevel=info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait briefly and check if process is still running
        await asyncio.sleep(5)
        if worker_process.poll() is None:
            status.set_status("celery", True)
            return worker_process
        else:
            logger.error("Celery worker failed to start")
            status.set_status("celery", False)
            return None
    except Exception as e:
        logger.error(f"Failed to start Celery worker: {str(e)}")
        status.set_status("celery", False)
        return None

async def cleanup_services(status: ServiceStatus, worker_process: Optional[subprocess.Popen] = None):
    """Clean up services on shutdown."""
    try:
        if worker_process:
            worker_process.terminate()
            try:
                worker_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                worker_process.kill()
        
        # Stop Docker services
        compose_dir = Path(__file__).parent / "docker"
        os.chdir(str(compose_dir))
        subprocess.run(["docker", "compose", "down"], check=True)
        
        logger.warning("Services cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

async def main():
    """Run the FastAPI server with comprehensive initialization and monitoring."""
    status = ServiceStatus()
    worker_process = None
    
    try:
        # Start and verify all services
        if not await start_docker_services(status):
            raise RuntimeError("Failed to start Docker services")

        if not await wait_for_neo4j(status):
            raise RuntimeError("Neo4j failed to start")

        if not await wait_for_qdrant(status):
            raise RuntimeError("Qdrant failed to start")

        if not await wait_for_redis(status):
            raise RuntimeError("Redis failed to start")
        
        # Initialize memory system with proper cleanup
        memory_system = await verify_memory_system(status)
        if not memory_system:
            raise RuntimeError("Memory system verification failed")
        
        # Initialize thread manager with proper cleanup
        thread_manager = await verify_thread_manager(status, memory_system)
        if not thread_manager:
            raise RuntimeError("Thread manager verification failed")
        
        # Start Celery worker with proper cleanup
        worker_process = await start_celery_worker(status)
        if not worker_process:
            raise RuntimeError("Failed to start Celery worker")
        
        if not status.all_ready():
            raise RuntimeError("Not all services are ready")
        
        logger.warning("All services initialized successfully")
        
        # Get configuration from environment
        host = os.getenv("NOVA_HOST", "127.0.0.1")
        port = int(os.getenv("NOVA_PORT", "8000"))
        reload = os.getenv("NOVA_RELOAD", "true").lower() == "true"
        
        # Run server with comprehensive logging
        config = uvicorn.Config(
            "nia.nova.core.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="debug",
            access_log=True,
            timeout_keep_alive=30,
            log_config=None
        )
        server = uvicorn.Server(config)
        logger.warning(f"Server starting on http://{host}:{port}")
        
        try:
            await server.serve()
        except Exception as e:
            logger.error(f"Server error: {str(e)}", exc_info=True)
            raise
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        await cleanup_services(status, worker_process)

if __name__ == "__main__":
    asyncio.run(main())
