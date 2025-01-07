"""Integration tests for demo functionality."""

import pytest
from fastapi.testclient import TestClient
import json
from datetime import datetime
import websockets
import asyncio
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

from nia.nova.core.app import app
from nia.nova.core.auth import API_KEYS
from nia.nova.core.endpoints import (
    get_memory_system,
    get_analytics_agent,
    get_llm_interface,
    get_tiny_factory,
    get_world
)
from nia.core.types.memory_types import Memory, MemoryType

# Test API key
TEST_API_KEY = "test-key"
assert TEST_API_KEY in API_KEYS, "Test API key not found in API_KEYS"

@pytest.fixture
async def llm_interface():
    """Create mock LLM interface for testing."""
    return LLMInterface(use_mock=True)

@pytest.fixture
async def analytics_agent(memory_system, llm_interface, request):
    """Create analytics agent for testing."""
    # Generate unique name based on test name
    agent_name = f"test-analytics-agent-{request.node.name}"
    agent = AnalyticsAgent(
        name=agent_name,
        memory_system=memory_system,
        domain="test"
    )
    return agent

@pytest.fixture
async def tiny_factory(memory_system):
    """Create TinyFactory instance for testing."""
    return TinyFactory(memory_system=memory_system)

@pytest.fixture
async def world():
    """Create world instance for testing."""
    from nia.world.environment import NIAWorld
    return NIAWorld()

@pytest.mark.integration
class TestDemoFunctionality:
    """Test demo script functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_coordination_setup(self, memory_system, analytics_agent, llm_interface, world):
        """Test agent coordination setup."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            # Test analytics agent initialization
            assert analytics_agent is not None
            assert analytics_agent.memory_system is not None
            assert analytics_agent.domain == "test"
            
            # Test WebSocket connection
            ws_url = f"ws://testserver/api/analytics/ws"
            with client.websocket_connect(
                ws_url,
                headers={"X-API-Key": TEST_API_KEY}
            ) as websocket:
                assert websocket is not None
                
        finally:
            app.dependency_overrides.clear()
            
    @pytest.mark.asyncio
    async def test_agent_coordination_messaging(self, memory_system, analytics_agent, llm_interface, world):
        """Test agent coordination messaging."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            ws_url = f"ws://testserver/api/analytics/ws"
            
            with client.websocket_connect(
                ws_url,
                headers={"X-API-Key": TEST_API_KEY}
            ) as websocket:
                logger.info("WebSocket connected, preparing to send coordination request")
                
                request_data = {
                    "type": "agent_coordination",
                    "content": "Why is the sky blue?",
                    "domain": "science",
                    "llm_config": {
                        "chat_model": "test-chat-model",
                        "embedding_model": "test-embedding-model"
                    }
                }
                logger.info(f"Request data prepared: {request_data}")
                
                # Send coordination request
                await websocket.send_json(request_data)
                logger.info("Coordination request sent successfully")
                
                # Wait for first response with timeout
                try:
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
                    logger.info(f"Received response: {data}")
                    assert data is not None
                    assert "type" in data
                except asyncio.TimeoutError:
                    logger.error("Timeout waiting for first response")
                    raise
                    
        finally:
            app.dependency_overrides.clear()
            
    @pytest.mark.asyncio
    async def test_agent_coordination_updates(self, memory_system, analytics_agent, llm_interface, world):
        """Test agent coordination updates."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            ws_url = f"ws://testserver/api/analytics/ws"
            
            with client.websocket_connect(
                ws_url,
                headers={"X-API-Key": TEST_API_KEY}
            ) as websocket:
                logger.info("WebSocket connected, preparing coordination request")
                
                request_data = {
                    "type": "agent_coordination",
                    "content": "Why is the sky blue?",
                    "domain": "science",
                    "llm_config": {
                        "chat_model": "test-chat-model",
                        "embedding_model": "test-embedding-model"
                    }
                }
                logger.info(f"Request data prepared: {request_data}")
                
                # Send coordination request
                try:
                    await websocket.send_json(request_data)
                    logger.info("Coordination request sent successfully")
                except Exception as e:
                    logger.error(f"Failed to send coordination request: {str(e)}")
                    raise
                
                logger.info("Starting to track agent updates")
                updates_received = 0
                response_received = False
                start_time = datetime.now()
                timeout = 10.0  # 10 second timeout
                logger.info(f"Timeout set to {timeout} seconds")
                
                while (datetime.now() - start_time).total_seconds() < timeout:
                    try:
                        logger.info("Waiting for response...")
                        data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                        logger.info(f"Received data: {data}")
                        
                        if data["type"] == "analytics_update":
                            updates_received += 1
                            assert "analytics" in data
                            for agent, update in data["analytics"].items():
                                assert "message" in update
                                
                        elif data["type"] == "response":
                            response_received = True
                            assert "content" in data
                            break
                            
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        logger.error("WebSocket connection closed unexpectedly")
                        break
                        
                logger.info(f"Updates received: {updates_received}")
                logger.info(f"Response received: {response_received}")
                assert updates_received > 0, "No updates were received"
                assert response_received, "No final response was received"
                
        finally:
            app.dependency_overrides.clear()
