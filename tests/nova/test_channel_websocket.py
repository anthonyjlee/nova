"""Tests for Nova's WebSocket channel functionality."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import json
import asyncio
from uuid import uuid4

from nia.nova.core.app import app
from nia.nova.core.auth import API_KEYS
from nia.nova.core.auth.token import verify_token
from nia.nova.core.endpoints import get_memory_system
from nia.nova.core.channel_types import (
    ChannelType, ChannelStatus, ChannelRole,
    ChannelDetails, ChannelSettings, ChannelState,
    ChannelEvent, ChannelEventType
)
from nia.nova.core.websocket_types import (
    WebSocketState, WebSocketError, WebSocketSession,
    WebSocketConfig, WebSocketEvent, WebSocketMessageType
)

# Test API key
TEST_API_KEY = "test-key"
assert TEST_API_KEY in API_KEYS, "Test API key not found in API_KEYS"

@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)

@pytest.fixture
async def memory_system():
    """Create memory system for testing."""
    from nia.memory.two_layer import TwoLayerMemorySystem
    memory = TwoLayerMemorySystem(
        neo4j_uri="bolt://localhost:7687",
        vector_store=None  # Not needed for channel tests
    )
    await memory.initialize()
    return memory

@pytest.fixture
def test_channel():
    """Create test channel data."""
    return {
        "id": str(uuid4()),
        "name": "test-channel",
        "type": ChannelType.PUBLIC,
        "status": ChannelStatus.ACTIVE,
        "created_by": "test-user",
        "settings": {
            "name": "test-channel",
            "type": ChannelType.PUBLIC,
            "description": "Test channel",
            "is_public": True
        }
    }

@pytest.mark.asyncio
class TestChannelWebSocket:
    """Test WebSocket channel functionality."""
    
    async def test_channel_connection(self, test_client, memory_system, test_channel):
        """Test WebSocket channel connection."""
        # Override dependencies
        app.dependency_overrides[get_memory_system] = lambda: memory_system
        
        try:
            # Connect to channel WebSocket
            async with test_client.websocket_connect(
                f"/api/channels/{test_channel['id']}/ws",
                headers={
                    "X-API-Key": TEST_API_KEY,
                    "X-Client-ID": "test-client",
                    "X-Workspace": "test",
                    "X-Domain": "test"
                }
            ) as websocket:
                # Should receive welcome message
                data = await websocket.receive_json()
                assert data["type"] == "connection_established"
                assert data["data"]["channel_id"] == test_channel["id"]
                
                # Test ping/pong
                await websocket.send_json({"type": "ping"})
                pong = await websocket.receive_json()
                assert pong["type"] == "pong"
                
        finally:
            app.dependency_overrides.clear()
    
    async def test_channel_events(self, test_client, memory_system, test_channel):
        """Test channel event handling."""
        app.dependency_overrides[get_memory_system] = lambda: memory_system
        
        try:
            # Connect two clients to same channel
            async with test_client.websocket_connect(
                f"/api/channels/{test_channel['id']}/ws",
                headers={
                    "X-API-Key": TEST_API_KEY,
                    "X-Client-ID": "client1",
                    "X-Workspace": "test",
                    "X-Domain": "test"
                }
            ) as ws1, test_client.websocket_connect(
                f"/api/channels/{test_channel['id']}/ws",
                headers={
                    "X-API-Key": TEST_API_KEY,
                    "X-Client-ID": "client2",
                    "X-Workspace": "test",
                    "X-Domain": "test"
                }
            ) as ws2:
                # Skip welcome messages
                await ws1.receive_json()
                await ws2.receive_json()
                
                # Send event from client1
                test_event = {
                    "type": "message_sent",
                    "data": {
                        "content": "Hello channel!",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                await ws1.send_json(test_event)
                
                # Both clients should receive the event
                event1 = await ws1.receive_json()
                event2 = await ws2.receive_json()
                
                assert event1["event_type"] == ChannelEventType.MESSAGE_SENT
                assert event2["event_type"] == ChannelEventType.MESSAGE_SENT
                assert event1["data"]["content"] == "Hello channel!"
                assert event2["data"]["content"] == "Hello channel!"
                
        finally:
            app.dependency_overrides.clear()
    
    async def test_channel_state(self, test_client, memory_system, test_channel):
        """Test channel state management."""
        app.dependency_overrides[get_memory_system] = lambda: memory_system
        
        try:
            # Get initial state
            response = test_client.get(
                f"/api/channels/{test_channel['id']}/state",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert response.status_code == 200
            state = response.json()
            assert state["status"] == ChannelStatus.ACTIVE
            assert state["connection_state"] == "disconnected"
            
            # Connect to channel
            async with test_client.websocket_connect(
                f"/api/channels/{test_channel['id']}/ws",
                headers={
                    "X-API-Key": TEST_API_KEY,
                    "X-Client-ID": "test-client",
                    "X-Workspace": "test",
                    "X-Domain": "test"
                }
            ) as websocket:
                # Skip welcome message
                await websocket.receive_json()
                
                # Check updated state
                response = test_client.get(
                    f"/api/channels/{test_channel['id']}/state",
                    headers={"X-API-Key": TEST_API_KEY}
                )
                state = response.json()
                assert state["connection_state"] == "connected"
            
            # Check state after disconnect
            response = test_client.get(
                f"/api/channels/{test_channel['id']}/state",
                headers={"X-API-Key": TEST_API_KEY}
            )
            state = response.json()
            assert state["connection_state"] == "disconnected"
            
        finally:
            app.dependency_overrides.clear()
    
    async def test_error_handling(self, test_client, memory_system, test_channel):
        """Test WebSocket error handling."""
        app.dependency_overrides[get_memory_system] = lambda: memory_system
        
        try:
            # Test invalid token
            with pytest.raises(Exception):
                async with test_client.websocket_connect(
                    f"/api/channels/{test_channel['id']}/ws",
                    headers={
                        "X-API-Key": "invalid-key",
                        "X-Client-ID": "test-client",
                        "X-Workspace": "test",
                        "X-Domain": "test"
                    }
                ):
                    pass
            
            # Test valid connection with invalid message
            async with test_client.websocket_connect(
                f"/api/channels/{test_channel['id']}/ws",
                headers={
                    "X-API-Key": TEST_API_KEY,
                    "X-Client-ID": "test-client",
                    "X-Workspace": "test",
                    "X-Domain": "test"
                }
            ) as websocket:
                # Skip welcome message
                await websocket.receive_json()
                
                # Send invalid event type
                await websocket.send_json({
                    "type": "invalid_type",
                    "data": {}
                })
                
                # Should receive error
                error = await websocket.receive_json()
                assert error["type"] == "error"
                assert error["error_type"] == "message_handling_error"
                
        finally:
            app.dependency_overrides.clear()
