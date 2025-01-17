"""Test WebSocket debugging and error handling scenarios."""

import pytest
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from nia.nova.core.websocket_server import WebSocketServer
from nia.memory.two_layer import TwoLayerMemorySystem
from .utils.mock_websocket import MockWebSocket
from .utils.websocket_test_utils import WebSocketTestSession

# Configure logging
LOGS_DIR = Path("logs/tests")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / f"test_websocket_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logger = logging.getLogger("test-websocket-debug")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(log_file)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

@pytest.mark.asyncio
class TestWebSocketDebug:
    """Test WebSocket debugging scenarios."""

    @pytest.fixture
    async def memory_system(self):
        """Create memory system fixture."""
        system = TwoLayerMemorySystem()
        await system.initialize()
        return system

    @pytest.fixture
    def websocket_server(self, memory_system):
        """Create WebSocket server fixture."""
        return WebSocketServer(lambda: memory_system)

    async def create_message(
        self,
        msg_type: str,
        data: Dict[str, Any],
        client_id: str = "test-client",
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create properly formatted WebSocket message."""
        return {
            "type": msg_type,
            "timestamp": datetime.now().isoformat(),
            "client_id": client_id,
            "channel": channel,
            "data": data
        }

    async def test_schema_validation(self, websocket_server):
        """Test schema validation for different message types."""
        logger.info("Starting schema validation test")

        try:
            websocket = MockWebSocket()
            client_id = "test-client"

            async with WebSocketTestSession(websocket) as session:
                # Test missing required fields
                invalid_message = {
                    "type": "chat_message",
                    # Missing timestamp
                    "client_id": client_id,
                    "data": {"content": "test"}
                }
                
                # Add message to websocket queue
                websocket.add_message(invalid_message)
                # Handle connection
                await websocket_server.handle_chat_connection(websocket, client_id)
            
                # Verify error response
                responses = session.get_received_messages()
                assert len(responses) == 1
                response = responses[0]
                assert response["type"] == "error"
                assert "schema validation" in response["data"]["message"].lower()

                # Test invalid field types
                invalid_types = await self.create_message(
                    "chat_message",
                    {
                        "content": 123,  # Should be string
                        "thread_id": ["invalid"],  # Should be string
                    }
                )
                
                # Add message to websocket queue
                websocket.add_message(invalid_types)
                # Handle connection
                await websocket_server.handle_chat_connection(websocket, client_id)
            
                # Verify error response
                responses = session.get_received_messages()
                assert len(responses) == 2  # Including previous error
                response = responses[-1]  # Get latest response
                assert response["type"] == "error"
                assert "invalid field type" in response["data"]["message"].lower()

            logger.info("Schema validation test completed successfully")
            
        except Exception as e:
            logger.error(f"Schema validation test failed: {str(e)}")
            raise

    async def test_connection_states(self, websocket_server):
        """Test WebSocket connection state handling."""
        logger.info("Starting connection state test")

        try:
            websocket = MockWebSocket()
            client_id = "test-client"

            async with WebSocketTestSession(websocket) as session:
                # 1. Initial connection without auth
                chat_message = await self.create_message(
                    "chat_message",
                    {"content": "test"}
                )
                
                # Add message to websocket queue
                websocket.add_message(chat_message)
                # Handle connection
                await websocket_server.handle_chat_connection(websocket, client_id)
                
                # Verify unauthorized error
                responses = session.get_received_messages()
                assert len(responses) == 1
                response = responses[0]
                assert response["type"] == "error"
                assert "authentication required" in response["data"]["message"].lower()

                # 2. Successful auth flow
                auth_message = await self.create_message(
                    "auth",
                    {"api_key": "test-key"}
                )
                
                # Add message to websocket queue
                websocket.add_message(auth_message)
                # Handle connection
                await websocket_server.handle_chat_connection(websocket, client_id)
                
                # Verify success response
                responses = session.get_received_messages()
                assert len(responses) == 2  # Including previous error
                response = responses[-1]
                assert response["type"] == "connection_success"

                # 3. Test connection timeout
                await asyncio.sleep(61)  # Wait past timeout
                
                chat_after_timeout = await self.create_message(
                    "chat_message",
                    {"content": "test"}
                )
                
                # Add message to websocket queue
                websocket.add_message(chat_after_timeout)
                # Handle connection
                await websocket_server.handle_chat_connection(websocket, client_id)
                
                # Verify timeout error
                responses = session.get_received_messages()
                assert len(responses) == 3  # Including previous messages
                response = responses[-1]
                assert response["type"] == "error"
                assert "connection timeout" in response["data"]["message"].lower()

            logger.info("Connection state test completed successfully")
            
        except Exception as e:
            logger.error(f"Connection state test failed: {str(e)}")
            raise

    async def test_channel_validation(self, websocket_server):
        """Test channel subscription validation."""
        logger.info("Starting channel validation test")

        try:
            websocket = MockWebSocket()
            client_id = "test-client"

            async with WebSocketTestSession(websocket) as session:
                # 1. Auth first
                auth_message = await self.create_message(
                    "auth",
                    {"api_key": "test-key"}
                )
                
                # Add message to websocket queue
                websocket.add_message(auth_message)
                # Handle connection
                await websocket_server.handle_chat_connection(websocket, client_id)
                
                # Verify auth success
                responses = session.get_received_messages()
                assert len(responses) == 1
                response = responses[0]
                assert response["type"] == "connection_success"

                # 2. Subscribe to invalid channel
                subscribe_invalid = await self.create_message(
                    "subscribe",
                    {"channel": "invalid-channel"}
                )
                
                # Add message to websocket queue
                websocket.add_message(subscribe_invalid)
                # Handle connection
                await websocket_server.handle_chat_connection(websocket, client_id)
                
                # Verify error response
                responses = session.get_received_messages()
                assert len(responses) == 2  # Including previous success
                response = responses[-1]
                assert response["type"] == "error"
                assert "invalid channel" in response["data"]["message"].lower()

                # 3. Subscribe to valid channel
                subscribe_valid = await self.create_message(
                    "subscribe",
                    {"channel": "test-channel"}
                )
                
                # Add message to websocket queue
                websocket.add_message(subscribe_valid)
                # Handle connection
                await websocket_server.handle_chat_connection(websocket, client_id)
                
                # Verify success response
                responses = session.get_received_messages()
                assert len(responses) == 3  # Including previous messages
                response = responses[-1]
                assert response["type"] == "subscription_success"

                # 4. Send message to channel
                channel_message = await self.create_message(
                    "chat_message",
                    {"content": "test"},
                    channel="test-channel"
                )
                
                # Add message to websocket queue
                websocket.add_message(channel_message)
                # Handle connection
                await websocket_server.handle_chat_connection(websocket, client_id)
                
                # Verify message broadcast
                responses = session.get_received_messages()
                assert len(responses) == 4  # Including previous messages
                response = responses[-1]
                assert response["type"] == "chat_message"
                assert response["channel"] == "test-channel"

            logger.info("Channel validation test completed successfully")
            
        except Exception as e:
            logger.error(f"Channel validation test failed: {str(e)}")
            raise

    async def test_message_validation(self, websocket_server):
        """Test message content validation."""
        logger.info("Starting message validation test")

        try:
            websocket = MockWebSocket()
            client_id = "test-client"

            async with WebSocketTestSession(websocket) as session:
                # 1. Auth first
                auth_message = await self.create_message(
                    "auth",
                    {"api_key": "test-key"}
                )
                
                # Add message to websocket queue
                websocket.add_message(auth_message)
                # Handle connection
                await websocket_server.handle_chat_connection(websocket, client_id)
                
                # Verify auth success
                responses = session.get_received_messages()
                assert len(responses) == 1
                response = responses[0]
                assert response["type"] == "connection_success"

                # 2. Test empty content
                empty_message = await self.create_message(
                    "chat_message",
                    {"content": ""}
                )
                
                # Add message to websocket queue
                websocket.add_message(empty_message)
                # Handle connection
                await websocket_server.handle_chat_connection(websocket, client_id)
                
                # Verify error response
                responses = session.get_received_messages()
                assert len(responses) == 2  # Including previous success
                response = responses[-1]
                assert response["type"] == "error"
                assert "empty content" in response["data"]["message"].lower()

                # 3. Test content too long
                long_content = "x" * 10001  # Over 10000 char limit
                long_message = await self.create_message(
                    "chat_message",
                    {"content": long_content}
                )
                
                # Add message to websocket queue
                websocket.add_message(long_message)
                # Handle connection
                await websocket_server.handle_chat_connection(websocket, client_id)
                
                # Verify error response
                responses = session.get_received_messages()
                assert len(responses) == 3  # Including previous messages
                response = responses[-1]
                assert response["type"] == "error"
                assert "content too long" in response["data"]["message"].lower()

            logger.info("Message validation test completed successfully")
            
        except Exception as e:
            logger.error(f"Message validation test failed: {str(e)}")
            raise
