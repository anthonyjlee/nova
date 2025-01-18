import json
from datetime import datetime
import random
import string
import uvicorn
import threading
import time
from websockets.sync.client import connect
from nia.nova.core.app import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

def test_auth():
    # Generate client ID like frontend
    client_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
    uri = f"ws://localhost:8000/debug/client_{client_id}"
    
    try:
        print(f"\nAttempting to connect to: {uri}")
        
        with connect(uri, additional_headers={"Origin": "http://localhost:5173"}) as ws:
            print("\nConnected to WebSocket server")
            
            # Wait for connection established message
            response = json.loads(ws.recv())
            print("\nReceived:", response)
            
            if response["type"] != "connection_established":
                print(f"Expected connection_established, got {response['type']}")
                return
                
            # Send connect message with API key
            auth_msg = {
                "type": "connect",
                "data": {
                    "api_key": "valid-test-key",  # Using the designated test key from WebSocket Guide
                    "connection_type": "chat",
                    "domain": "personal",
                    "workspace": "personal"
                },
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id
            }
            print("\nSending auth message:", auth_msg)
            ws.send(json.dumps(auth_msg))
            
            # Wait for auth response and delivery confirmation
            response = json.loads(ws.recv())
            print("\nReceived:", response)
            
            if response["type"] == "error":
                print(f"Auth error: {response['data']['message']}")
                return
                
            if response["type"] != "connection_success":
                print(f"Expected connection_success, got {response['type']}")
                return

            # Wait for delivery confirmation
            delivery = json.loads(ws.recv())
            print("\nReceived delivery confirmation:", delivery)
            
            if delivery["type"] != "message_delivered" or delivery["data"]["original_type"] != "connect":
                print(f"Expected message_delivered for connect, got {delivery}")
                return
                
            print("\nAuthentication successful!")
            
            # Send a test message
            test_msg = {
                "type": "chat_message",
                "data": {
                    "content": "Hello server!",
                    "thread_id": "test",
                    "workspace": "personal"
                },
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id
            }
            print("\nSending test message:", test_msg)
            ws.send(json.dumps(test_msg))
            
            # Wait for echo response and delivery confirmation
            response = json.loads(ws.recv())
            print("\nReceived:", response)
            
            if response["type"] != "chat_message":
                print(f"Expected chat_message, got {response['type']}")
                return

            # Wait for delivery confirmation
            delivery = json.loads(ws.recv())
            print("\nReceived delivery confirmation:", delivery)
            
            if delivery["type"] != "message_delivered" or delivery["data"]["original_type"] != "chat_message":
                print(f"Expected message_delivered for chat_message, got {delivery}")
                return
                
            print("\nTest message echoed successfully with delivery confirmation!")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give the server a moment to start
    time.sleep(2)
    
    # Run the test
    test_auth()
