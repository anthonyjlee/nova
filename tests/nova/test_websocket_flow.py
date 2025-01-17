"""Test complete WebSocket flow including auth, messaging, and cleanup."""

import pytest
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from nia.nova.core.websocket_server import WebSocketServer
from nia.memory.two_layer import TwoLayerMemorySystem

# Configure logging
LOGS_DIR = Path("logs/tests")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / f"test_websocket_flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logger = logging.getLogger("test-websocket-flow")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(log_file)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class TestWebSocketFlow:
    """Test complete WebSocket flow."""

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

    async def test_complete_flow(self, websocket_server):
        """Test complete WebSocket flow including auth and messaging."""
        logger.info("Starting complete WebSocket flow test")

        try:
            # 1. Setup WebSocket connection
            websocket = Mock(spec=WebSocket)
            websocket.send_json = Mock()
            client_id = "test-client"
            api_key = "test-key"

            # 2. Connect and authenticate
            auth_message = await self.create_message(
                "auth",
                {"api_key": api_key}
            )
            
            # Mock receive_json to return auth message
            websocket.receive_json = Mock(return_value=auth_message)
            
            await websocket_server.handle_chat_connection(websocket, client_id)
            
            # Verify auth response
            websocket.send_json.assert_called_once()
            response = websocket.send_json.call_args[0][0]
            assert response["type"] == "connection_success"
            assert response["client_id"] == client_id
            
            # 3. Send chat message
            chat_message = await self.create_message(
                "chat_message",
                {
                    "thread_id": "test-thread",
                    "content": "Test message",
                    "sender": "test-user"
                }
            )
            
            # Reset mock and set new receive value
            websocket.receive_json.reset_mock()
            websocket.receive_json = Mock(return_value=chat_message)
            websocket.send_json.reset_mock()
            
            # Handle chat message
            await websocket_server.handle_chat_connection(websocket, client_id)
            
            # Verify message handling
            websocket.send_json.assert_called_once()
            response = websocket.send_json.call_args[0][0]
            assert response["type"] == "chat_message"
            assert "thread_id" in response["data"]
            assert response["data"]["content"] == "Test message"
            
            # 4. Join channel
            join_message = await self.create_message(
                "subscribe",
                {"channel": "test-channel"}
            )
            
            websocket.receive_json.reset_mock()
            websocket.receive_json = Mock(return_value=join_message)
            websocket.send_json.reset_mock()
            
            await websocket_server.handle_chat_connection(websocket, client_id)
            
            # Verify channel subscription
            websocket.send_json.assert_called_once()
            response = websocket.send_json.call_args[0][0]
            assert response["type"] == "subscription_success"
            
            # 5. Send channel message
            channel_message = await self.create_message(
                "chat_message",
                {
                    "thread_id": "test-thread",
                    "content": "Channel message",
                    "sender": "test-user"
                },
                channel="test-channel"
            )
            
            websocket.receive_json.reset_mock()
            websocket.receive_json = Mock(return_value=channel_message)
            websocket.send_json.reset_mock()
            
            await websocket_server.handle_chat_connection(websocket, client_id)
            
            # Verify channel message
            websocket.send_json.assert_called_once()
            response = websocket.send_json.call_args[0][0]
            assert response["type"] == "chat_message"
            assert response["channel"] == "test-channel"
            assert response["data"]["content"] == "Channel message"
            
            # 6. Leave channel
            leave_message = await self.create_message(
                "unsubscribe",
                {"channel": "test-channel"}
            )
            
            websocket.receive_json.reset_mock()
            websocket.receive_json = Mock(return_value=leave_message)
            websocket.send_json.reset_mock()
            
            await websocket_server.handle_chat_connection(websocket, client_id)
            
            # Verify channel unsubscription
            websocket.send_json.assert_called_once()
            response = websocket.send_json.call_args[0][0]
            assert response["type"] == "unsubscription_success"
            
            logger.info("WebSocket flow test completed successfully")
            
        except Exception as e:
            logger.error(f"WebSocket flow test failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def test_error_handling(self, websocket_server):
        """Test WebSocket error handling."""
        logger.info("Starting WebSocket error handling test")

        try:
            websocket = Mock(spec=WebSocket)
            websocket.send_json = Mock()
            client_id = "test-client"

            # 1. Test missing auth
            chat_message = await self.create_message(
                "chat_message",
                {
                    "thread_id": "test-thread",
                    "content": "Test message"
                }
            )
            
            websocket.receive_json = Mock(return_value=chat_message)
            
            await websocket_server.handle_chat_connection(websocket, client_id)
            
            # Verify error response
            websocket.send_json.assert_called_once()
            response = websocket.send_json.call_args[0][0]
            assert response["type"] == "error"
            assert "authentication required" in response["data"]["message"].lower()

            # 2. Test invalid message type
            invalid_message = await self.create_message(
                "invalid_type",
                {"content": "test"}
            )
            
            websocket.receive_json.reset_mock()
            websocket.receive_json = Mock(return_value=invalid_message)
            websocket.send_json.reset_mock()
            
            await websocket_server.handle_chat_connection(websocket, client_id)
            
            # Verify error response
            websocket.send_json.assert_called_once()
            response = websocket.send_json.call_args[0][0]
            assert response["type"] == "error"
            assert "invalid message type" in response["data"]["message"].lower()

            # 3. Test invalid channel operation
            leave_message = await self.create_message(
                "unsubscribe",
                {"channel": "nonexistent-channel"}
            )
            
            websocket.receive_json.reset_mock()
            websocket.receive_json = Mock(return_value=leave_message)
            websocket.send_json.reset_mock()
            
            await websocket_server.handle_chat_connection(websocket, client_id)
            
            # Verify error response
            websocket.send_json.assert_called_once()
            response = websocket.send_json.call_args[0][0]
            assert response["type"] == "error"
            assert "channel" in response["data"]["message"].lower()

            logger.info("WebSocket error handling test completed successfully")
            
        except Exception as e:
            logger.error(f"WebSocket error handling test failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def test_reconnection(self, websocket_server):
        """Test WebSocket reconnection handling."""
        logger.info("Starting WebSocket reconnection test")

        try:
            websocket = Mock(spec=WebSocket)
            websocket.send_json = Mock()
            client_id = "test-client"
            api_key = "test-key"

            # 1. Initial connection and auth
            auth_message = await self.create_message(
                "auth",
                {"api_key": api_key}
            )
            
            websocket.receive_json = Mock(return_value=auth_message)
            
            await websocket_server.handle_chat_connection(websocket, client_id)
            
            # Verify initial connection
            websocket.send_json.assert_called_once()
            response = websocket.send_json.call_args[0][0]
            assert response["type"] == "connection_success"

            # 2. Simulate disconnect and reconnect
            await websocket_server.handle_disconnect(websocket, client_id)
            
            # Create new connection
            new_websocket = Mock(spec=WebSocket)
            new_websocket.send_json = Mock()
            
            # Reconnect with same auth
            new_websocket.receive_json = Mock(return_value=auth_message)
            
            await websocket_server.handle_chat_connection(new_websocket, client_id)
            
            # Verify reconnection
            new_websocket.send_json.assert_called_once()
            response = new_websocket.send_json.call_args[0][0]
            assert response["type"] == "connection_success"

            logger.info("WebSocket reconnection test completed successfully")
            
        except Exception as e:
            logger.error(f"WebSocket reconnection test failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise
