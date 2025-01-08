"""Test utilities for Nova integration tests."""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from functools import wraps, partial
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

# Configure test logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    )
)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Resource tracking
active_resources = set()

def track_resource(resource_id: str):
    """Track an active test resource."""
    active_resources.add(resource_id)
    logger.debug(f"Resource tracked: {resource_id}")

def untrack_resource(resource_id: str):
    """Untrack a test resource."""
    active_resources.discard(resource_id)
    logger.debug(f"Resource untracked: {resource_id}")

def get_active_resources() -> set:
    """Get set of currently tracked resources."""
    return active_resources.copy()

@contextmanager
def resource_tracking():
    """Context manager to verify all resources are cleaned up."""
    resources_before = get_active_resources()
    try:
        yield
    finally:
        resources_after = get_active_resources()
        leaked = resources_after - resources_before
        if leaked:
            logger.warning(f"Leaked resources detected: {leaked}")
            # Clean up leaked resources
            for resource_id in leaked:
                untrack_resource(resource_id)

# Test data generation
def generate_test_memory(
    content: str,
    domain: str,
    agent_name: Optional[str] = None,
    importance: float = 0.8,
    concepts: Optional[List[Dict[str, Any]]] = None,
    relationships: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Generate consistent test memory data."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    memory_id = f"test_memory_{uuid.uuid4()}"
    track_resource(memory_id)
    
    return {
        "id": memory_id,
        "content": content,
        "timestamp": timestamp,
        "domain": domain,
        "importance": importance,
        "agent": agent_name,
        "concepts": concepts or [],
        "relationships": relationships or [],
        "metadata": {
            "test": True,
            "generated": timestamp
        }
    }

def generate_test_agent(
    name: str,
    agent_type: str,
    domain: str,
    skills: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Generate consistent test agent data."""
    agent_id = f"test_agent_{uuid.uuid4()}"
    track_resource(agent_id)
    
    return {
        "id": agent_id,
        "name": name,
        "type": agent_type,
        "domain": domain,
        "skills": skills or [],
        "status": "active",
        "metadata": {
            "test": True,
            "created": datetime.now(timezone.utc).isoformat()
        }
    }

# Assertion helpers
async def assert_eventually(
    condition,
    timeout: float = 5.0,
    interval: float = 0.1,
    message: str = "Condition not met"
):
    """Assert that a condition becomes true within timeout."""
    deadline = asyncio.get_event_loop().time() + timeout
    
    while asyncio.get_event_loop().time() < deadline:
        try:
            if await condition():
                return
        except Exception as e:
            logger.debug(f"Condition check failed: {e}")
        await asyncio.sleep(interval)
    
    raise AssertionError(
        f"{message} within {timeout} seconds"
    )

async def assert_memory_stored(
    memory_system,
    memory_id: str,
    timeout: float = 5.0
):
    """Assert that a memory is stored in the system."""
    async def check_memory():
        try:
            memory = await memory_system.get_memory(memory_id)
            return memory is not None
        except Exception:
            return False
    
    await assert_eventually(
        check_memory,
        timeout=timeout,
        message=f"Memory {memory_id} not found"
    )

async def assert_agent_state(
    nova,
    agent_id: str,
    expected_state: str,
    timeout: float = 5.0
):
    """Assert that an agent reaches expected state."""
    async def check_state():
        try:
            agent = await nova.get_agent(agent_id)
            return agent and agent.state == expected_state
        except Exception:
            return False
    
    await assert_eventually(
        check_state,
        timeout=timeout,
        message=f"Agent {agent_id} did not reach {expected_state} state"
    )

# Vector store operation settings
VECTOR_STORE_TIMEOUT = 30  # seconds
VECTOR_STORE_MAX_RETRIES = 3
VECTOR_STORE_RETRY_MIN_WAIT = 1  # seconds
VECTOR_STORE_RETRY_MAX_WAIT = 10  # seconds

class VectorStoreError(Exception):
    """Base exception for vector store operations."""
    pass

class VectorStoreTimeout(VectorStoreError):
    """Exception raised when vector store operation times out."""
    pass

class VectorStoreOperationError(VectorStoreError):
    """Exception raised when vector store operation fails."""
    pass

def with_vector_store_retry(func):
    """Decorator to add retry logic to vector store operations."""
    @retry(
        stop=stop_after_attempt(VECTOR_STORE_MAX_RETRIES),
        wait=wait_exponential(
            multiplier=VECTOR_STORE_RETRY_MIN_WAIT,
            max=VECTOR_STORE_RETRY_MAX_WAIT
        ),
        retry=retry_if_exception_type(VectorStoreError),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            async with asyncio.timeout(VECTOR_STORE_TIMEOUT):
                return await func(*args, **kwargs)
        except asyncio.TimeoutError:
            logger.error(
                f"Vector store operation timed out after {VECTOR_STORE_TIMEOUT}s"
            )
            raise VectorStoreTimeout(
                f"Operation timed out after {VECTOR_STORE_TIMEOUT}s"
            )
        except Exception as e:
            logger.error(f"Vector store operation failed: {str(e)}")
            raise VectorStoreOperationError(str(e))
    return wrapper

async def cleanup_test_data(memory_system, domain: str):
    """Clean up test data from memory system."""
    try:
        # Clean vector store
        await memory_system.episodic.store.delete_vectors(
            query=f"domain:{domain}"
        )
        # Clean semantic store
        await memory_system.semantic.query(
            f"MATCH (n) WHERE n.domain = '{domain}' DETACH DELETE n"
        )
    except Exception as e:
        logger.error(f"Failed to cleanup test data: {str(e)}")
        raise

class TestContext:
    """Context manager for test setup and cleanup."""
    
    def __init__(self, memory_system, domain: str):
        self.memory_system = memory_system
        self.domain = domain
    
    async def __aenter__(self):
        """Set up test context."""
        # Clean any existing test data
        await cleanup_test_data(self.memory_system, self.domain)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up test context."""
        # Clean up test data
        await cleanup_test_data(self.memory_system, self.domain)
        # Clear dependency overrides
        from nia.nova.core.app import app
        app.dependency_overrides.clear()
