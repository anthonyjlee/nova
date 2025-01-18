"""Tests for Nova WebSocket endpoints.

This test suite verifies the functionality of Nova's WebSocket endpoints, including:
- Connection establishment and authentication
- Message handling and validation
- Channel subscription operations
- Error handling and timeouts
- Connection cleanup

Each test case focuses on a specific aspect of the WebSocket functionality
to ensure robust and reliable real-time communication.
"""

import pytest
import logging
import asyncio
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.testclient import TestClient
from datetime import datetime
from pathlib import Path

from nia.nova.endpoints.nova_endpoints import nova_router

# Configure logging
LOGS_DIR = Path("logs/tests")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / f"test_nova_endpoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger = logging.getLogger("test-nova-endpoints")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.propagate = False  # Prevent propagation to root logger

# Constants for test configuration
TEST_API_KEY = "test-key"
TEST_CLIENT_ID = "test-client"
TEST_CHANNEL = "test-channel"
WEBSOCKET_TIMEOUT = 61  # 60 seconds + 1 second buffer


def validate_message_schema(message: dict) -> None:
    """Validate WebSocket message schema."""
    assert "type" in message, "Message should have type"
    assert "timestamp" in message, "Message should have timestamp"
    assert "client_id" in message, "Message should have client_id"
    assert "data" in message, "Message should have data"
    # channel is optional, so we don't assert it


@pytest.fixture
def test_app() -> FastAPI:
    """Create FastAPI test application."""
    app = FastAPI()
    app.include_router(nova_router)
    return app

@pytest.mark.asyncio
async def test_websocket_success(test_app: FastAPI) -> None:
    """Test successful WebSocket connection and message handling."""
    logger.info("Testing successful WebSocket connection")
    
    client = TestClient(test_app)
    with client.websocket_connect(
        f"/api/nova/ws/{TEST_CLIENT_ID}",
        headers={"X-API-Key": TEST_API_KEY}
    ) as websocket:
        # Send auth message
        websocket.send_json({
            "type": "auth",
            "timestamp": datetime.now().isoformat(),
            "client_id": TEST_CLIENT_ID,
            "channel": None,
            "data": {
                "api_key": TEST_API_KEY
            }
        })
        
        # Get auth response
        auth_response = websocket.receive_json()
        validate_message_schema(auth_response)
        assert auth_response["type"] == "connection_success"
        
        # Send test message
        websocket.send_json({
            "type": "chat_message",
            "timestamp": datetime.now().isoformat(),
            "client_id": TEST_CLIENT_ID,
            "channel": None,
            "data": {
                "content": "test query",
                "workspace": "personal"
            }
        })
        
        # Get response
        response = websocket.receive_json()
        logger.debug(f"Response content: {response}")
        
        # Verify response structure
        validate_message_schema(response)
        assert response["type"] == "chat_message", "Response type should be chat_message"
        
        data = response["data"]
        assert "content" in data, "Response data should have content"
        assert "metadata" in data, "Response data should have metadata"
        assert "agent_actions" in data["metadata"], "Response metadata should have agent_actions"

@pytest.mark.asyncio
async def test_websocket_invalid_auth(test_app: FastAPI) -> None:
    """Test WebSocket connection with invalid auth."""
    logger.info("Testing invalid auth")
    
    client = TestClient(test_app)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            f"/api/nova/ws/{TEST_CLIENT_ID}",
            headers={"X-API-Key": "invalid-key"}
        ) as websocket:
            websocket.send_json({
                "type": "auth",
                "timestamp": datetime.now().isoformat(),
                "client_id": TEST_CLIENT_ID,
                "channel": None,
                "data": {
                    "api_key": "invalid-key"
                }
            })

@pytest.mark.asyncio
async def test_websocket_missing_auth(test_app: FastAPI) -> None:
    """Test WebSocket connection without auth message."""
    logger.info("Testing missing auth")
    
    client = TestClient(test_app)
    with client.websocket_connect(
        f"/api/nova/ws/{TEST_CLIENT_ID}",
        headers={"X-API-Key": TEST_API_KEY}
    ) as websocket:
        # Skip auth message
        websocket.send_json({
            "type": "chat_message",
            "timestamp": datetime.now().isoformat(),
            "client_id": TEST_CLIENT_ID,
            "channel": None,
            "data": {
                "content": "test query"
            }
        })
        
        # Should get error response
        response = websocket.receive_json()
        validate_message_schema(response)
        assert response["type"] == "error"
        assert "authentication required" in response["data"]["message"].lower()

@pytest.mark.asyncio
async def test_websocket_channel_operations(test_app: FastAPI) -> None:
    """Test WebSocket channel subscription operations."""
    logger.info("Testing channel operations")
    
    client = TestClient(test_app)
    with client.websocket_connect(
        f"/api/nova/ws/{TEST_CLIENT_ID}",
        headers={"X-API-Key": TEST_API_KEY}
    ) as websocket:
        # Authenticate
        websocket.send_json({
            "type": "auth",
            "timestamp": datetime.now().isoformat(),
            "client_id": TEST_CLIENT_ID,
            "channel": None,
            "data": {
                "api_key": TEST_API_KEY
            }
        })
        response = websocket.receive_json()
        validate_message_schema(response)
        assert response["type"] == "connection_success"
        
        # Join channel
        websocket.send_json({
            "type": "subscribe",
            "timestamp": datetime.now().isoformat(),
            "client_id": TEST_CLIENT_ID,
            "channel": None,
            "data": {
                "channel": TEST_CHANNEL
            }
        })
        response = websocket.receive_json()
        validate_message_schema(response)
        assert response["type"] == "subscription_success"
        
        # Leave channel
        websocket.send_json({
            "type": "unsubscribe",
            "timestamp": datetime.now().isoformat(),
            "client_id": TEST_CLIENT_ID,
            "channel": None,
            "data": {
                "channel": TEST_CHANNEL
            }
        })
        response = websocket.receive_json()
        validate_message_schema(response)
        assert response["type"] == "unsubscription_success"

@pytest.mark.asyncio
async def test_websocket_invalid_message(test_app: FastAPI) -> None:
    """Test handling of invalid message types."""
    logger.info("Testing invalid message type")
    
    client = TestClient(test_app)
    with client.websocket_connect(
        f"/api/nova/ws/{TEST_CLIENT_ID}",
        headers={"X-API-Key": TEST_API_KEY}
    ) as websocket:
        # Authenticate first
        websocket.send_json({
            "type": "auth",
            "timestamp": datetime.now().isoformat(),
            "client_id": TEST_CLIENT_ID,
            "channel": None,
            "data": {
                "api_key": TEST_API_KEY
            }
        })
        response = websocket.receive_json()
        validate_message_schema(response)
        assert response["type"] == "connection_success"
        
        # Send invalid message type
        websocket.send_json({
            "type": "invalid_type",
            "timestamp": datetime.now().isoformat(),
            "client_id": TEST_CLIENT_ID,
            "channel": None,
            "data": {
                "content": "test"
            }
        })
        
        # Should get error response
        response = websocket.receive_json()
        validate_message_schema(response)
        assert response["type"] == "error"
        assert "invalid message type" in response["data"]["message"].lower()

@pytest.mark.asyncio
async def test_websocket_timeout(test_app: FastAPI) -> None:
    """Test WebSocket connection timeout handling."""
    logger.info("Testing connection timeout")
    
    client = TestClient(test_app)
    with client.websocket_connect(
        f"/api/nova/ws/{TEST_CLIENT_ID}",
        headers={"X-API-Key": TEST_API_KEY}
    ) as websocket:
        # Authenticate
        websocket.send_json({
            "type": "auth",
            "timestamp": datetime.now().isoformat(),
            "client_id": TEST_CLIENT_ID,
            "channel": None,
            "data": {
                "api_key": TEST_API_KEY
            }
        })
        response = websocket.receive_json()
        validate_message_schema(response)
        assert response["type"] == "connection_success"
        
        # Wait longer than the timeout period
        await asyncio.sleep(WEBSOCKET_TIMEOUT)
        
        # Next message should fail
        with pytest.raises(WebSocketDisconnect) as exc_info:
            websocket.send_json({
                "type": "chat_message",
                "timestamp": datetime.now().isoformat(),
                "client_id": TEST_CLIENT_ID,
                "channel": None,
                "data": {
                    "content": "test"
                }
            })
            
        assert exc_info.value.code == 1000  # Normal closure
