"""Pytest configuration and shared fixtures."""

import os
import sys
import pytest
from typing import Dict, List
import asyncio
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Configure pytest
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def base_memory_data():
    """Provide base memory data for testing."""
    return {
        "content": "Test memory content",
        "source": "test",
        "timestamp": datetime.now(),
        "importance": 0.5,
        "metadata": {
            "test": True
        }
    }

@pytest.fixture
def memory_batch_data():
    """Provide test data for memory batches."""
    return [
        {
            "content": f"Memory {i}",
            "importance": 0.5 + (i * 0.1),
            "metadata": {"batch": "test"}
        }
        for i in range(3)
    ]

@pytest.fixture
def concept_data():
    """Provide test concept data."""
    return {
        "name": "Test Concept",
        "category": "Test Category",
        "attributes": {
            "key": "value"
        }
    }

@pytest.fixture
def relationship_data():
    """Provide test relationship data."""
    return {
        "from_concept": "Concept A",
        "to_concept": "Concept B",
        "type": "TEST_RELATION",
        "properties": {
            "strength": 0.8
        }
    }

@pytest.fixture
def consolidation_config():
    """Provide test consolidation configuration."""
    return {
        "time_based": {
            "enabled": True,
            "interval": 3600  # 1 hour
        },
        "volume_based": {
            "enabled": True,
            "threshold": 100
        },
        "importance_based": {
            "enabled": True,
            "threshold": 0.8
        }
    }

@pytest.fixture
def mock_logger():
    """Provide a mock logger for testing."""
    class MockLogger:
        def __init__(self):
            self.logs = []
            
        def info(self, msg):
            self.logs.append(("INFO", msg))
            
        def error(self, msg):
            self.logs.append(("ERROR", msg))
            
        def warning(self, msg):
            self.logs.append(("WARNING", msg))
            
        def debug(self, msg):
            self.logs.append(("DEBUG", msg))
            
    return MockLogger()
