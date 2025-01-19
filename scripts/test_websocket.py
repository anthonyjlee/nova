"""WebSocket test server with auth and validation."""

import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient
from nia.nova.core.websocket import websocket_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint with auth and validation."""
    client_id = None
    
    try:
        # Accept connection first
        await websocket.accept()
        
        # Wait for auth message
        message = await websocket.receive_json()
        logger.info(f"Received: {message}")
        
        if message['type'] != 'auth':
            logger.error("First message must be auth")
            return
            
        # Extract auth info
        client_id = message.get('client_id')
        api_key = message['data'].get('api_key')
        
        if not client_id or not api_key:
            logger.error("Missing client_id or api_key")
            return
            
        # Connect using WebSocket manager (skip accept since we already accepted)
        await websocket_manager.connect(websocket, client_id)
        
        # Send auth success
        await websocket.send_json({
            'type': 'auth_success',
            'timestamp': datetime.now().isoformat(),
            'client_id': client_id,
            'channel': None,
            'data': {}
        })
            
        # Handle messages
        while True:
            message = await websocket.receive_json()
            logger.info(f"Received: {message}")
            
            msg_type = message['type']
            
            if msg_type == 'chat_message':
                await websocket_manager.broadcast_chat_message(
                    message['data'],
                    channel=message.get('channel')
                )
            elif msg_type == 'task_update':
                await websocket_manager.broadcast_task_update(
                    message['data'],
                    channel=message.get('channel')
                )
            elif msg_type == 'agent_status':
                await websocket_manager.broadcast_agent_status(
                    message['data'],
                    channel=message.get('channel')
                )
            elif msg_type == 'channel_subscribe':
                channel = message['data']['channel']
                await websocket_manager.join_channel(client_id, channel)
                await websocket.send_json({
                    'type': 'channel_subscribed',
                    'timestamp': datetime.now().isoformat(),
                    'client_id': client_id,
                    'channel': channel,
                    'data': {}
                })
            elif msg_type == 'channel_unsubscribe':
                channel = message['data']['channel']
                await websocket_manager.leave_channel(client_id, channel)
                await websocket.send_json({
                    'type': 'channel_unsubscribed',
                    'timestamp': datetime.now().isoformat(),
                    'client_id': client_id,
                    'channel': channel,
                    'data': {}
                })
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if client_id:
            await websocket_manager.disconnect(client_id)

async def test_websocket():
    """Test WebSocket functionality with auth."""
    client = TestClient(app)
    
    with client.websocket_connect("/ws") as ws:
        # Test auth
        auth_message = {
            'type': 'auth',
            'timestamp': datetime.now().isoformat(),
            'client_id': 'test-client',
            'channel': None,
            'data': {
                'api_key': 'test-key'
            }
        }
        ws.send_json(auth_message)
        response = ws.receive_json()
        assert response['type'] == 'auth_success'
        logger.info("Auth successful")
        
        # Test channel subscription
        channel_sub = {
            'type': 'channel_subscribe',
            'timestamp': datetime.now().isoformat(),
            'client_id': 'test-client',
            'channel': None,
            'data': {
                'channel': 'test-channel'
            }
        }
        ws.send_json(channel_sub)
        response = ws.receive_json()
        assert response['type'] == 'channel_subscribed'
        logger.info("Channel subscription successful")
        
        # Test chat message in channel
        chat_message = {
            'type': 'chat_message',
            'timestamp': datetime.now().isoformat(),
            'client_id': 'test-client',
            'channel': 'test-channel',
            'data': {
                'content': 'Hello channel',
                'thread_id': 'test-thread'
            }
        }
        ws.send_json(chat_message)
        response = ws.receive_json()
        assert response['type'] == 'chat_message'
        assert response['data']['content'] == 'Hello channel'
        assert response['channel'] == 'test-channel'
        logger.info("Channel message successful")
        
        # Test channel unsubscribe
        channel_unsub = {
            'type': 'channel_unsubscribe',
            'timestamp': datetime.now().isoformat(),
            'client_id': 'test-client',
            'channel': None,
            'data': {
                'channel': 'test-channel'
            }
        }
        ws.send_json(channel_unsub)
        response = ws.receive_json()
        assert response['type'] == 'channel_unsubscribed'
        logger.info("Channel unsubscribe successful")
        
        logger.info("All WebSocket tests passed!")

if __name__ == '__main__':
    asyncio.run(test_websocket())
