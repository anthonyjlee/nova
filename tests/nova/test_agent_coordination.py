"""Tests for agent coordination functionality."""

import pytest
from fastapi.testclient import TestClient
import logging
from datetime import datetime

from nia.nova.core.app import app
from nia.nova.core.auth import API_KEYS
from nia.nova.core.endpoints import (
    get_memory_system,
    get_analytics_agent,
    get_llm_interface,
    get_world
)
from nia.core.types.memory_types import Memory, MemoryType

logger = logging.getLogger(__name__)

# Test API key
TEST_API_KEY = "test-key"
assert TEST_API_KEY in API_KEYS, "Test API key not found in API_KEYS"

@pytest.mark.asyncio
async def test_agent_initialization(memory_system, mock_analytics_agent, llm_interface, world):
    """Test agent initialization and setup."""
    # Get fixture results
    memory_sys = await memory_system
    llm = await llm_interface
    w = await world
    
    # Set up dependency overrides
    app.dependency_overrides[get_memory_system] = lambda: memory_sys
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_llm_interface] = lambda: llm
    app.dependency_overrides[get_world] = lambda: w
    
    try:
        # Initialize systems
        await memory_sys.initialize()
        
        # Verify agent setup
        assert mock_analytics_agent is not None
        assert mock_analytics_agent.memory_system is not None
        assert mock_analytics_agent.domain == "test"
        
        # Store test memory
        memory = Memory(
            content={"text": "Test coordination memory"},
            type=MemoryType.SEMANTIC,
            importance=0.8,
            context={"domain": "test"},
            timestamp=datetime.now().isoformat()
        )
        
        memory_id = await memory_sys.store(
            content=memory.content,
            memory_type=memory.type,
            importance=memory.importance,
            context=memory.context
        )
        assert memory_id is not None
        
        # Verify agent can access memory
        memories = await memory_sys.query_episodic({
            "text": "Test coordination memory",
            "type": "semantic"
        })
        assert len(memories) > 0
        
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_agent_coordination_flow(memory_system, mock_analytics_agent, llm_interface, world):
    """Test agent coordination message flow."""
    # Get fixture results
    memory_sys = await memory_system
    llm = await llm_interface
    w = await world
    
    # Set up dependency overrides
    app.dependency_overrides[get_memory_system] = lambda: memory_sys
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_llm_interface] = lambda: llm
    app.dependency_overrides[get_world] = lambda: w
    
    try:
        client = TestClient(app)
        
        # Initialize systems
        await memory_sys.initialize()
        
        # Test coordination request
        response = client.post(
            "/api/orchestration/coordinate",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "content": "Test coordination request",
                "type": "coordination",
                "domain": "test",
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "coordination_id" in data
        
        # Verify coordination memory was stored
        memories = await memory_system.query_episodic({
            "text": "Test coordination request",
            "type": "coordination"
        })
        assert len(memories) > 0
        
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_agent_coordination_patterns(memory_system, mock_analytics_agent, llm_interface, world):
    """Test different agent coordination patterns."""
    # Get fixture results
    memory_sys = await memory_system
    llm = await llm_interface
    w = await world
    
    # Set up dependency overrides
    app.dependency_overrides[get_memory_system] = lambda: memory_sys
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_llm_interface] = lambda: llm
    app.dependency_overrides[get_world] = lambda: w
    
    try:
        client = TestClient(app)
        
        # Initialize systems
        await memory_system.initialize()
        
        # Test sequential coordination
        response = client.post(
            "/api/orchestration/coordinate",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "content": "Sequential coordination test",
                "type": "coordination",
                "pattern": "sequential",
                "domain": "test",
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "coordination_id" in data
        assert data["pattern"] == "sequential"
        
        # Test parallel coordination
        response = client.post(
            "/api/orchestration/coordinate",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "content": "Parallel coordination test",
                "type": "coordination",
                "pattern": "parallel",
                "domain": "test",
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "coordination_id" in data
        assert data["pattern"] == "parallel"
        
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_agent_coordination_error_handling(memory_system, mock_analytics_agent, llm_interface, world):
    """Test error handling in agent coordination."""
    # Get fixture results
    memory_sys = await memory_system
    llm = await llm_interface
    w = await world
    
    # Set up dependency overrides
    app.dependency_overrides[get_memory_system] = lambda: memory_sys
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_llm_interface] = lambda: llm
    app.dependency_overrides[get_world] = lambda: w
    
    try:
        client = TestClient(app)
        
        # Initialize systems
        await memory_system.initialize()
        
        # Test invalid coordination pattern
        response = client.post(
            "/api/orchestration/coordinate",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "content": "Invalid pattern test",
                "type": "coordination",
                "pattern": "invalid_pattern",
                "domain": "test",
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        
        # Test missing required fields
        response = client.post(
            "/api/orchestration/coordinate",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "type": "coordination",
                "domain": "test"
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        
    finally:
        app.dependency_overrides.clear()
