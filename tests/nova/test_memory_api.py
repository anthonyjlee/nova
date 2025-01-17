"""Tests for Nova memory API endpoints."""

import pytest
from fastapi.testclient import TestClient
import logging
from datetime import datetime, timezone

from nia.nova.core.app import app
from nia.nova.core.auth import API_KEYS
from nia.nova.core.endpoints import (
    get_memory_system,
    get_llm_interface,
    get_world
)
from nia.core.types.memory_types import Memory, MemoryType
from nia.core.interfaces.llm_interface import LLMInterface

logger = logging.getLogger(__name__)

# Test API key
TEST_API_KEY = "test-key"
assert TEST_API_KEY in API_KEYS, "Test API key not found in API_KEYS"

@pytest.fixture
async def llm_interface():
    """Create mock LLM interface for testing."""
    return LLMInterface(use_mock=True)

@pytest.mark.asyncio
async def test_memory_api_store(memory_system, llm_interface, world):
    """Test storing memory through the API."""
    # Get fixture results
    memory_sys = await memory_system
    llm = await llm_interface
    w = await world
    
    # Set up dependency overrides
    app.dependency_overrides[get_memory_system] = lambda: memory_sys
    app.dependency_overrides[get_llm_interface] = lambda: llm
    app.dependency_overrides[get_world] = lambda: w
    
    try:
        client = TestClient(app)
        
        # Test direct memory storage first
        memory = Memory(
            content={"text": "Test memory content"},
            type=MemoryType.SEMANTIC,
            importance=0.8,
            context={"domain": "test"},
            timestamp=datetime.now(timezone.utc)
        )
        
        # Initialize memory system
        await memory_sys.initialize()
        
        # Store using memory system directly
        memory_id = await memory_sys.store(
            content=memory.content,
            memory_type=memory.type,
            importance=memory.importance,
            context=memory.context,
            metadata={}
        )
        assert memory_id is not None
        
        # Verify storage
        stored_data = await memory_sys.query_episodic({
            "text": "Test memory content",
            "type": MemoryType.SEMANTIC.value
        })
        assert len(stored_data) > 0
        
        # Now test API endpoint
        response = client.post(
            "/api/orchestration/memory/store",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "content": "API test memory content",
                "type": "semantic",
                "importance": 0.9,
                "context": {"domain": "test"},
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "memory_id" in data
        
        # Verify API storage
        api_stored = await memory_sys.query_episodic({
            "text": "API test memory content",
            "type": "semantic"  # Match the type from the API request
        })
        assert len(api_stored) > 0
        
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_memory_api_query(memory_system, llm_interface, world):
    """Test querying memory through the API."""
    # Get fixture results
    memory_sys = await memory_system
    llm = await llm_interface
    w = await world
    
    # Set up dependency overrides
    app.dependency_overrides[get_memory_system] = lambda: memory_sys
    app.dependency_overrides[get_llm_interface] = lambda: llm
    app.dependency_overrides[get_world] = lambda: w
    
    try:
        client = TestClient(app)
        
        # Store test memory
        memory = Memory(
            content={"text": "Memory to be queried"},
            type=MemoryType.SEMANTIC,
            importance=0.8,
            context={"domain": "test"},
            timestamp=datetime.now(timezone.utc)
        )
        # Initialize memory system
        await memory_sys.initialize()
        
        await memory_sys.store(
            content=memory.content,
            memory_type=memory.type,
            importance=memory.importance,
            context=memory.context,
            metadata={}
        )
        
        # Test query endpoint
        response = client.post(
            "/api/orchestration/memory/query",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "query": "Memory to be queried",
                "type": "semantic",  # Match the memory type
                "domain": "test",
                "limit": 5
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "memories" in data
        assert len(data["memories"]) > 0
        
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_memory_api_consolidation(memory_system, llm_interface, world):
    """Test memory consolidation through the API."""
    # Get fixture results
    memory_sys = await memory_system
    llm = await llm_interface
    w = await world
    
    # Set up dependency overrides
    app.dependency_overrides[get_memory_system] = lambda: memory_sys
    app.dependency_overrides[get_llm_interface] = lambda: llm
    app.dependency_overrides[get_world] = lambda: w
    
    try:
        client = TestClient(app)
        
        # Store multiple related memories
        memories = [
            Memory(
                content={"text": "First related memory"},
                type=MemoryType.SEMANTIC,
                importance=0.8,
                context={"domain": "test"},
                timestamp=datetime.now(timezone.utc)
            ),
            Memory(
                content={"text": "Second related memory"},
                type=MemoryType.SEMANTIC,
                importance=0.8,
                context={"domain": "test"},
                timestamp=datetime.now(timezone.utc)
            )
        ]
        
        # Initialize memory system
        await memory_sys.initialize()
        
        for memory in memories:
            await memory_sys.store(
                content=memory.content,
                memory_type=memory.type,
                importance=memory.importance,
                context=memory.context,
                metadata={}
            )
        
        # Test consolidation endpoint
        response = client.post(
            "/api/orchestration/memory/consolidate",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "domain": "test",
                "force": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "consolidated_count" in data
        assert data["consolidated_count"] > 0
        
    finally:
        app.dependency_overrides.clear()
