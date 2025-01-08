"""Test utilities for Nova integration tests."""

import asyncio
import logging
from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)

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
