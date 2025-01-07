"""Tests for analytics update functionality."""

import pytest
from fastapi.testclient import TestClient
import logging
from datetime import datetime
import asyncio

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
async def test_analytics_basic_update(memory_system, mock_analytics_agent, llm_interface, world):
    """Test basic analytics update flow."""
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
        
        # Connect WebSocket
        with client.websocket_connect(
            "ws://testserver/api/analytics/ws",
            headers={"X-API-Key": TEST_API_KEY}
        ) as websocket:
            # Send analytics request
            request_data = {
                "type": "analytics_request",
                "content": "Test analytics content",
                "domain": "test",
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }
            await websocket.send_json(request_data)
            
            # Wait for update with timeout
            try:
                response = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
                assert response is not None
                assert response["type"] == "analytics_update"
                assert "analytics" in response
                assert "insights" in response
                assert "confidence" in response
                assert "timestamp" in response
            except asyncio.TimeoutError:
                pytest.fail("Timeout waiting for analytics update")
                
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_analytics_update_sequence(memory_system, mock_analytics_agent, llm_interface, world):
    """Test sequence of analytics updates."""
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
        
        with client.websocket_connect(
            "ws://testserver/api/analytics/ws",
            headers={"X-API-Key": TEST_API_KEY}
        ) as websocket:
            # Send request that triggers multiple updates
            request_data = {
                "type": "analytics_request",
                "content": "Test sequential analytics",
                "domain": "test",
                "update_interval": 1,  # Request frequent updates
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }
            await websocket.send_json(request_data)
            
            # Track updates
            updates_received = 0
            start_time = datetime.now()
            timeout = 10.0  # 10 second timeout
            
            while (datetime.now() - start_time).total_seconds() < timeout:
                try:
                    response = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                    if response["type"] == "analytics_update":
                        updates_received += 1
                        # Verify update structure
                        assert "analytics" in response
                        assert "insights" in response
                        assert "confidence" in response
                        assert "timestamp" in response
                        # Break after receiving enough updates
                        if updates_received >= 3:
                            break
                except asyncio.TimeoutError:
                    continue
                    
            assert updates_received >= 3, f"Only received {updates_received} updates"
            
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_analytics_update_memory(memory_system, mock_analytics_agent, llm_interface, world):
    """Test analytics updates with memory integration."""
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
        
        # Store test memory
        memory = Memory(
            content={"text": "Test analytics memory"},
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
        
        with client.websocket_connect(
            "ws://testserver/api/analytics/ws",
            headers={"X-API-Key": TEST_API_KEY}
        ) as websocket:
            # Request analytics for stored memory
            request_data = {
                "type": "analytics_request",
                "memory_id": memory_id,
                "domain": "test",
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }
            await websocket.send_json(request_data)
            
            # Wait for update
            try:
                response = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
                assert response is not None
                assert response["type"] == "analytics_update"
                assert "analytics" in response
                # Verify memory-specific analytics
                assert "memory_analysis" in response["analytics"]
                assert memory_id in str(response["analytics"]["memory_analysis"])
            except asyncio.TimeoutError:
                pytest.fail("Timeout waiting for memory analytics")
                
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_analytics_update_error_handling(memory_system, mock_analytics_agent, llm_interface, world):
    """Test error handling in analytics updates."""
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
        
        with client.websocket_connect(
            "ws://testserver/api/analytics/ws",
            headers={"X-API-Key": TEST_API_KEY}
        ) as websocket:
            # Test invalid memory ID
            request_data = {
                "type": "analytics_request",
                "memory_id": "invalid_id",
                "domain": "test",
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }
            await websocket.send_json(request_data)
            
            # Should receive error response
            try:
                response = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
                assert response is not None
                assert response["type"] == "error"
                assert "error" in response
                assert "code" in response["error"]
                assert "message" in response["error"]
            except asyncio.TimeoutError:
                pytest.fail("Timeout waiting for error response")
                
            # Test invalid analytics type
            request_data = {
                "type": "invalid_type",
                "content": "Test content",
                "domain": "test",
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }
            await websocket.send_json(request_data)
            
            # Should receive error response
            try:
                response = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
                assert response is not None
                assert response["type"] == "error"
                assert "error" in response
                assert "code" in response["error"]
                assert "message" in response["error"]
            except asyncio.TimeoutError:
                pytest.fail("Timeout waiting for error response")
                
    finally:
        app.dependency_overrides.clear()
