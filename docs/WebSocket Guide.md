# WebSocket Implementation Guide

## Overview

This guide outlines the WebSocket implementation for real-time communication between frontend and backend, focusing on critical features needed for MVP.

## MVP Tasks (Prioritized)

### 1. Critical Path (Must Have)
- [ ] Fix frontend schema validation
  * Remove extra metadata fields
  * Match backend message format exactly
  * Update Zod schemas in schemas.ts
  * Test with basic messages

- [ ] Implement auth flow
  * Add auth message on connect
  * Handle auth response
  * Manage connection state
  * Test auth success/failure

- [ ] Add basic chat messaging
  * Implement chat message format
  * Handle message delivery
  * Add basic error handling
  * Test message flow

### 2. Important Features
- [ ] Add task updates
  * Implement task status messages
  * Handle task state changes
  * Update task board UI
  * Test task flow

- [ ] Add agent status
  * Implement agent status format
  * Handle status updates
  * Update agent UI
  * Test agent flow

### 3. Nice to Have
- [ ] Add channel system
  * Basic channel subscription
  * Simple message routing
  * Test channel flow

- [ ] Add reconnection
  * Basic reconnect logic
  * Connection health check
  * Test reconnection

- [x] Add LLM streaming
  * Stream message format
  * Handle stream chunks
  * Test streaming

### LLM Integration

The WebSocket system integrates with LM Studio for real-time LLM responses:

### 1. Message Format
```typescript
// LLM Request Message
{
    type: "llm_request",
    timestamp: "2025-01-20T12:34:56.789Z",
    client_id: "user-123",
    channel: "llm-channel",
    data: {
        content: "User query text",
        template: "parsing_analysis",
        metadata: {
            domain: "test",
            type: "analysis"
        }
    }
}

// LLM Response Chunk
{
    type: "llm_chunk",
    timestamp: "2025-01-20T12:34:56.789Z",
    client_id: "user-123",
    channel: "llm-channel",
    data: {
        chunk: "Response text chunk",
        is_final: false
    }
}
```

### 2. Backend Implementation
```python
# src/nia/nova/core/websocket.py
class WebSocketManager:
    async def handle_llm_request(
        self,
        websocket: WebSocket,
        message: dict
    ):
        """Handle LLM request through WebSocket."""
        try:
            # Initialize LLM
            llm = LMStudioLLM(
                chat_model="llama-3.2-3b-instruct",
                embedding_model="text-embedding-nomic-embed-text-v1.5@f16",
                api_base="http://localhost:1234/v1"
            )
            
            # Stream response chunks
            async for chunk in llm.stream_response(
                content=message['data']['content'],
                template=message['data']['template']
            ):
                await websocket.send_json({
                    'type': 'llm_chunk',
                    'timestamp': datetime.now().isoformat(),
                    'client_id': message['client_id'],
                    'channel': message['channel'],
                    'data': {
                        'chunk': chunk,
                        'is_final': False
                    }
                })
                
            # Send final chunk
            await websocket.send_json({
                'type': 'llm_chunk',
                'timestamp': datetime.now().isoformat(),
                'client_id': message['client_id'],
                'channel': message['channel'],
                'data': {
                    'chunk': '',
                    'is_final': True
                }
            })
            
        except Exception as e:
            await self.send_error(
                websocket,
                f"LLM error: {str(e)}"
            )
```

### 3. Frontend Integration
```typescript
// frontend/src/lib/llm.ts
export class LLMClient {
    constructor(private ws: WebSocketClient) {}
    
    async analyze(
        content: string,
        template: string,
        metadata: Record<string, unknown>
    ) {
        return new Promise((resolve, reject) => {
            let response = '';
            
            // Handle response chunks
            const handleMessage = (msg: WebSocketMessage) => {
                if (msg.type === 'llm_chunk') {
                    if (msg.data.is_final) {
                        this.ws.off('message', handleMessage);
                        resolve(response);
                    } else {
                        response += msg.data.chunk;
                    }
                } else if (msg.type === 'error') {
                    this.ws.off('message', handleMessage);
                    reject(new Error(msg.data.message));
                }
            };
            
            // Listen for chunks
            this.ws.on('message', handleMessage);
            
            // Send request
            this.ws.send({
                type: 'llm_request',
                timestamp: new Date().toISOString(),
                client_id: this.ws.clientId,
                channel: 'llm-channel',
                data: { content, template, metadata }
            });
        });
    }
}
```

### 4. Testing
```python
# tests/nova/test_websocket_llm.py
async def test_llm_streaming():
    """Test LLM streaming through WebSocket."""
    async with client.websocket_connect("/ws/test") as ws:
        # Send LLM request
        await ws.send_json({
            "type": "llm_request",
            "data": {
                "content": "Test query",
                "template": "parsing_analysis",
                "metadata": {
                    "domain": "test",
                    "type": "analysis"
                }
            }
        })
        
        # Collect chunks
        response = ""
        while True:
            msg = await ws.receive_json()
            if msg["type"] == "llm_chunk":
                if msg["data"]["is_final"]:
                    break
                response += msg["data"]["chunk"]
        
        # Verify response
        assert len(response) > 0
```

This integration enables:
1. Real-time LLM responses through WebSocket
2. Streaming response chunks for better UX
3. Template-based analysis
4. Error handling and recovery

## Implementation Plan

### Phase 1: Schema Fix (Day 1)
1. Update frontend schemas
```typescript
// frontend/src/lib/validation/schemas.ts
export const WebSocketMessageBaseSchema = z.object({
    type: z.string(),
    timestamp: z.string(),
    client_id: z.string(),
    channel: z.string().nullable(),
    data: z.record(z.unknown())
});
```

2. Update backend models
```python
# src/nia/nova/core/websocket.py
class BaseMessage(BaseModel):
    type: str
    timestamp: datetime
    client_id: str
    channel: Optional[str]
    data: Dict[str, Any]
```

### Phase 2: Auth Flow (Day 1-2)
1. Add auth handling
```python
# src/nia/nova/core/websocket.py
async def handle_auth(self, websocket: WebSocket, message: dict):
    api_key = message['data']['api_key']
    if await self.validate_api_key(api_key):
        await self.send_auth_success(websocket, message['client_id'])
        return True
    await self.send_auth_failure(websocket, message['client_id'])
    return False
```

2. Update frontend connection
```typescript
// frontend/src/lib/websocket.ts
class WebSocketClient {
    connect() {
        this.ws = new WebSocket(this.url);
        this.ws.onopen = () => this.sendAuth();
    }
}
```

### Phase 3: Chat Messages (Day 2-3)
1. Implement chat handling
```python
# src/nia/nova/core/websocket.py
async def handle_chat(self, websocket: WebSocket, message: dict):
    try:
        await self.store_message(message['data'])
        await self.broadcast_message(message)
    except Exception as e:
        await self.send_error(websocket, str(e))
```

2. Add frontend chat
```typescript
// frontend/src/lib/chat.ts
export const sendChatMessage = (content: string, threadId: string) => {
    ws.send({
        type: 'chat_message',
        data: { content, thread_id: threadId }
    });
};
```

### 1. Message Flow
```
Client                              Server
  |                                   |
  |-- WS Connect ------------------>  |
  |                                   |
  |-- Auth Message ---------------->  |
  |                                   |
  |<- Auth Success/Failure ---------- |
  |                                   |
  |-- Subscribe Channel ----------->  |
  |                                   |
  |<- Subscription Success --------- -|
  |                                   |
  |-- Message ------------------->    |
  |                                   |
  |<- Message Response ------------- -|
```

### 2. Required Message Formats

```typescript
// Base Message Format
{
    type: string;
    timestamp: string;
    client_id: string;
    channel: string | null;
    data: any;
}

// Auth Message
{
    type: "auth",
    timestamp: "2025-01-20T12:34:56.789Z",
    client_id: "user-123",
    channel: null,
    data: {
        api_key: "key-123"
    }
}

// Chat Message
{
    type: "chat_message",
    timestamp: "2025-01-20T12:34:56.789Z",
    client_id: "user-123",
    channel: "channel-123",
    data: {
        content: "Hello",
        thread_id: "thread-123"
    }
}

// Task Update
{
    type: "task_update",
    timestamp: "2025-01-20T12:34:56.789Z",
    client_id: "user-123",
    channel: null,
    data: {
        task_id: "task-123",
        status: "in_progress"
    }
}

// Agent Status
{
    type: "agent_status",
    timestamp: "2025-01-20T12:34:56.789Z",
    client_id: "user-123",
    channel: null,
    data: {
        agent_id: "agent-123",
        status: "active"
    }
}
```

### 3. Frontend Implementation

```typescript
// websocket.ts
class WebSocketClient {
    private ws: WebSocket;
    private reconnectAttempts = 0;
    
    constructor(private url: string, private apiKey: string) {}
    
    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
            // Send auth message immediately
            this.sendAuth();
            this.reconnectAttempts = 0;
        };
        
        this.ws.onclose = () => {
            this.handleReconnect();
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    private sendAuth() {
        this.send({
            type: 'auth',
            timestamp: new Date().toISOString(),
            client_id: this.clientId,
            channel: null,
            data: { api_key: this.apiKey }
        });
    }
    
    private handleReconnect() {
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
        this.reconnectAttempts++;
        
        setTimeout(() => this.connect(), delay);
    }
}
```

### 4. Backend Implementation

```python
# websocket_server.py
class WebSocketServer:
    def __init__(self):
        self.active_connections = {}
        self.channel_subscribers = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
    async def handle_auth(self, websocket: WebSocket, message: dict):
        api_key = message['data']['api_key']
        if await self.validate_api_key(api_key):
            await websocket.send_json({
                'type': 'auth_success',
                'timestamp': datetime.now().isoformat(),
                'client_id': message['client_id'],
                'channel': None,
                'data': {}
            })
            return True
        return False
        
    async def handle_message(self, websocket: WebSocket, message: dict):
        msg_type = message['type']
        if msg_type == 'chat_message':
            await self.handle_chat(websocket, message)
        elif msg_type == 'task_update':
            await self.handle_task(websocket, message)
        elif msg_type == 'agent_status':
            await self.handle_agent(websocket, message)
```

## Integration Points

### 1. Redis/Celery Integration
- Use Redis as message broker
- Store WebSocket state
- Handle task queues
- Manage channel subscriptions

### 2. Frontend Store Integration
```typescript
// store/websocket.ts
export const createWebSocketStore = () => {
    const { subscribe, set, update } = writable({
        connected: false,
        messages: [],
        errors: []
    });
    
    const client = new WebSocketClient(WS_URL, API_KEY);
    
    return {
        subscribe,
        connect: () => client.connect(),
        send: (message) => client.send(message),
        disconnect: () => client.disconnect()
    };
};
```

### 3. Agent Integration
- Agent status updates
- Task coordination
- Real-time responses
- LLM streaming

## Testing Strategy

### 1. Basic WebSocket Tests
```python
# tests/nova/core/test_nova_endpoints.py

@pytest.mark.asyncio
async def test_websocket_success(test_app: FastAPI) -> None:
    """Test successful WebSocket connection and message handling."""
    with client.websocket_connect("/api/nova/ws/test-client") as ws:
        # Auth flow
        await ws.send_json({
            "type": "auth",
            "timestamp": datetime.now().isoformat(),
            "client_id": "test-client",
            "data": {"api_key": "test-key"}
        })
        response = await ws.receive_json()
        assert response["type"] == "connection_success"

@pytest.mark.asyncio
async def test_channel_operations(test_app: FastAPI) -> None:
    """Test channel subscription and messaging."""
    with client.websocket_connect("/api/nova/ws/test-client") as ws:
        # Subscribe to channel
        await ws.send_json({
            "type": "subscribe",
            "data": {"channel": "test-channel"}
        })
        response = await ws.receive_json()
        assert response["type"] == "subscription_success"
```

### 2. LLM Integration Tests
```python
# tests/nova/test_websocket_llm.py

class AsyncWebSocketSession(AsyncContextManager):
    """Async context manager for WebSocket sessions."""
    
    def __init__(self, session: WebSocketTestSession):
        self.session = session
        
    async def __aenter__(self) -> WebSocketTestSession:
        return self.session
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

class WebSocketTestClient:
    """Helper class for WebSocket LLM testing."""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.llm = LMStudioLLM(
            chat_model="llama-3.2-3b-instruct",
            embedding_model="text-embedding-nomic-embed-text-v1.5@f16",
            api_base="http://localhost:1234/v1"
        )
        
    async def connect_and_auth(self) -> AsyncWebSocketSession:
        """Connect and authenticate WebSocket."""
        session = WebSocketTestSession(self.app, "/api/nova/ws/test-client")
        await session.connect()
        await self.send_auth(session)
        return AsyncWebSocketSession(session)

@pytest.mark.asyncio
async def test_llm_direct_request(llm_test_client: WebSocketTestClient) -> None:
    """Test direct LLM request without WebSocket."""
    result = await llm_test_client.llm.analyze(
        content={
            "query": "Test query",
            "type": "analysis"
        },
        template="parsing_analysis"
    )
    assert "response" in result
    assert "concepts" in result

@pytest.mark.asyncio
async def test_llm_websocket_streaming(llm_test_client: WebSocketTestClient) -> None:
    """Test LLM streaming through WebSocket."""
    session = await llm_test_client.connect_and_auth()
    async with session as ws:
        # Send LLM request
        await ws.send_json({
            "type": "llm_request",
            "data": {
                "content": "Test query",
                "template": "parsing_analysis",
                "metadata": {
                    "domain": "test",
                    "type": "analysis"
                }
            }
        })
        
        # Collect streaming chunks
        chunks = await llm_test_client.collect_stream(
            ws,
            end_condition=lambda msg: (
                msg["type"] == "llm_chunk" and 
                msg["data"]["is_final"]
            )
        )
        
        # Verify streaming worked
        assert len(chunks) > 1
        assert all(c["type"] == "llm_chunk" for c in chunks)
        
        # Verify complete response
        complete_response = "".join(
            c["data"]["chunk"] for c in chunks 
            if not c["data"]["is_final"]
        )
        assert len(complete_response) > 0

@pytest.mark.asyncio
async def test_llm_agent_coordination(llm_test_client: WebSocketTestClient) -> None:
    """Test LLM coordination with agents."""
    session = await llm_test_client.connect_and_auth()
    async with session as ws:
        # Send complex query
        await ws.send_json({
            "type": "chat_message",
            "data": {
                "content": "Complex query requiring multiple agents",
                "workspace": "test"
            }
        })
        
        # Collect all messages
        messages = await llm_test_client.collect_stream(
            ws,
            end_condition=lambda msg: (
                msg["type"] == "chat_message" and 
                msg["data"].get("is_final")
            )
        )
        
        # Verify agent coordination
        agent_actions = [
            msg for msg in messages 
            if msg["type"] == "agent_action"
        ]
        assert len(agent_actions) > 0
        
        # Verify LLM usage
        llm_chunks = [
            msg for msg in messages 
            if msg["type"] == "llm_chunk"
        ]
        assert len(llm_chunks) > 0
        
        # Verify final response
        final_message = messages[-1]
        assert final_message["type"] == "chat_message"
        assert final_message["data"]["is_final"]
        assert "response" in final_message["data"]
```

This testing strategy ensures:
1. Proper WebSocket session management with async context managers
2. Correct LLM request/response formats
3. Robust error handling and recovery
4. Stable streaming for long operations
5. Effective agent coordination

### 3. Agent Integration Tests
```python
# tests/nova/test_websocket_agents.py

@pytest.mark.asyncio
async def test_agent_status_updates(test_app: FastAPI) -> None:
    """Test agent status updates through WebSocket."""
    with client.websocket_connect("/api/nova/ws/test-client") as ws:
        # Subscribe to agent updates
        await ws.send_json({
            "type": "subscribe",
            "data": {"channel": "agent-status"}
        })
        
        # Should receive agent status updates
        msg = await ws.receive_json()
        assert msg["type"] == "agent_status"
        assert "agent_id" in msg["data"]
        assert "status" in msg["data"]
        
@pytest.mark.asyncio
async def test_agent_task_coordination(test_app: FastAPI) -> None:
    """Test agent task coordination through WebSocket."""
    with client.websocket_connect("/api/nova/ws/test-client") as ws:
        # Create task
        await ws.send_json({
            "type": "create_task",
            "data": {
                "task_type": "analysis",
                "content": "Test task"
            }
        })
        
        # Should receive task updates
        updates = []
        for _ in range(3):  # Expect 3 updates: created, assigned, completed
            msg = await ws.receive_json()
            assert msg["type"] == "task_update"
            updates.append(msg["data"]["status"])
            
        assert "created" in updates
        assert "assigned" in updates
        assert "completed" in updates
        
@pytest.mark.asyncio
async def test_agent_llm_interaction(test_app: FastAPI) -> None:
    """Test agent interaction with LLM through WebSocket."""
    with client.websocket_connect("/api/nova/ws/test-client") as ws:
        # Send task requiring agent-LLM interaction
        await ws.send_json({
            "type": "chat_message",
            "data": {
                "content": "Complex query requiring multiple agents",
                "workspace": "test"
            }
        })
        
        # Collect all related messages
        messages = []
        while True:
            msg = await ws.receive_json()
            messages.append(msg)
            if msg["type"] == "chat_message" and msg["data"].get("is_final"):
                break
                
        # Verify agent coordination
        agent_actions = [
            msg for msg in messages 
            if msg["type"] == "agent_action"
        ]
        assert len(agent_actions) > 0
        
        # Verify LLM usage
        llm_chunks = [
            msg for msg in messages 
            if msg["type"] == "llm_chunk"
        ]
        assert len(llm_chunks) > 0
```

### 4. Integration Test Utilities
```python
# tests/nova/utils/websocket_test_utils.py

class WebSocketTestClient:
    """Helper class for WebSocket testing."""
    
    def __init__(self, app: FastAPI):
        self.client = TestClient(app)
        
    async def connect_and_auth(self) -> WebSocket:
        """Connect and authenticate WebSocket."""
        ws = self.client.websocket_connect("/api/nova/ws/test-client")
        await self.send_auth(ws)
        return ws
        
    async def send_auth(self, ws: WebSocket) -> None:
        """Send authentication message."""
        await ws.send_json({
            "type": "auth",
            "data": {"api_key": "test-key"}
        })
        response = await ws.receive_json()
        assert response["type"] == "connection_success"
        
    async def collect_stream(
        self,
        ws: WebSocket,
        end_condition: Callable[[dict], bool]
    ) -> List[dict]:
        """Collect streaming messages until condition met."""
        messages = []
        while True:
            msg = await ws.receive_json()
            messages.append(msg)
            if end_condition(msg):
                break
        return messages
```

This testing strategy ensures:
1. Basic WebSocket functionality works
2. LLM integration handles streaming and errors
3. Agents can coordinate through WebSocket
4. Complex interactions work end-to-end

## Running and Testing

### 1. Start Backend Server
```bash
# Start Neo4j and Redis
cd scripts/docker
docker-compose up -d

# Start FastAPI server
cd ../..
python scripts/run_server.py
```

### 2. Run Frontend Tests
```bash
cd frontend
npm test
```

### 3. Run End-to-End Tests
```bash
python scripts/test_websocket.py
```

### 4. Manual Testing
1. Start development server:
```bash
cd frontend
npm run dev
```

2. Open browser console and test WebSocket:
```javascript
const ws = new WebSocketClient({
    url: 'ws://localhost:8000/ws',
    apiKey: 'test-key',
    clientId: 'test-client',
    onMessage: console.log,
    onError: console.error,
    onStateChange: connected => console.log('Connected:', connected)
});

ws.connect();

// Send chat message
ws.sendChatMessage('Hello', 'thread-1');

// Subscribe to channel
ws.subscribeToChannel('test-channel');

// Send message to channel
ws.sendChatMessage('Channel message', 'thread-1');

// Unsubscribe from channel
ws.unsubscribeFromChannel('test-channel');

// Cleanup
ws.destroy();
```

## Troubleshooting

### Connection Issues
1. Check server logs:
```bash
tail -f logs/nova.log
```

2. Check WebSocket status:
```javascript
// In browser console
ws.ws.readyState  // Should be 1 (OPEN)
```

3. Common issues:
- Server not running
- Wrong WebSocket URL
- Invalid API key
- Network/firewall blocking WebSocket

### Message Issues
1. Check message validation:
```javascript
// In browser console
import { validateMessage } from './validation/websocket-schemas';

const message = {
    type: 'chat_message',
    timestamp: new Date().toISOString(),
    client_id: 'test-client',
    channel: null,
    data: {
        content: 'Hello',
        thread_id: 'thread-1'
    }
};

console.log(validateMessage(message));  // Should be true
```

2. Common issues:
- Missing required fields
- Wrong field types
- Invalid message format
- Not authenticated
- Wrong channel name

### Channel Issues
1. Check subscriptions:
```python
# In Python shell
from nia.nova.core.websocket import websocket_manager
print(websocket_manager.channel_subscribers)
print(websocket_manager.client_channels)
```

2. Common issues:
- Not subscribed to channel
- Channel doesn't exist
- Permission denied
- Wrong channel format

### Performance Issues
1. Monitor metrics:
```python
# In Python shell
from nia.nova.core.websocket import websocket_manager
print(len(websocket_manager.active_connections))
```

2. Common issues:
- Too many connections
- Message queue full
- High latency
- Memory leaks

## Debugging Guide

### 1. Connection Issues

#### Symptoms
- WebSocket fails to connect
- Frequent disconnections
- Auth failures
- Timeout errors

#### Debug Steps
1. Check WebSocket URL
```typescript
// Should match your environment
const WS_URL = process.env.NODE_ENV === 'development' 
    ? 'ws://localhost:8000/ws'
    : 'wss://your-domain.com/ws';
```

2. Verify API Key
```typescript
// Enable debug logging
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'auth_failure') {
        console.error('Auth failed:', msg.data.reason);
    }
};
```

3. Monitor Connection State
```typescript
// Add state logging
ws.onopen = () => console.log('Connected');
ws.onclose = () => console.log('Disconnected');
ws.onerror = (e) => console.error('Error:', e);
```

### 2. Message Issues

#### Symptoms
- Messages not being received
- Schema validation errors
- Missing responses
- Incorrect message order

#### Debug Steps
1. Check Message Format
```typescript
// Add message validation
const validateMessage = (msg: unknown) => {
    try {
        return WebSocketMessageSchema.parse(msg);
    } catch (e) {
        console.error('Invalid message:', e);
        return null;
    }
};
```

2. Monitor Message Flow
```python
# Add server-side logging
async def handle_message(self, websocket: WebSocket, message: dict):
    logger.debug(f"Received message: {message}")
    try:
        await self._handle_message(websocket, message)
        logger.debug(f"Handled message: {message}")
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await self.send_error(websocket, str(e))
```

3. Test Message Round-trip
```python
async def test_message_roundtrip():
    """Test complete message flow."""
    async with client.websocket_connect("/ws/test") as ws:
        # Send message
        await ws.send_json(test_message)
        
        # Wait for echo
        response = await ws.receive_json()
        
        # Verify round-trip
        assert response["data"] == test_message["data"]
```

### 3. Schema Issues

#### Symptoms
- Validation errors
- Missing fields
- Type mismatches
- Extra fields being sent

#### Debug Steps
1. Compare Schemas
```typescript
// Frontend schema
const frontendSchema = {
    type: z.string(),
    timestamp: z.string(),
    client_id: z.string(),
    channel: z.string().nullable(),
    data: z.record(z.unknown())
};

# Backend schema
class BackendSchema(BaseModel):
    type: str
    timestamp: datetime
    client_id: str
    channel: Optional[str]
    data: Dict[str, Any]
```

2. Validate Messages
```typescript
// Add validation wrapper
const sendMessage = (msg: unknown) => {
    try {
        const validated = MessageSchema.parse(msg);
        ws.send(JSON.stringify(validated));
    } catch (e) {
        console.error('Schema error:', e);
    }
};
```

### 4. Performance Issues

#### Symptoms
- High latency
- Message queuing
- Memory growth
- CPU spikes

#### Debug Steps
1. Monitor Message Rate
```python
class MessageStats:
    def __init__(self):
        self.message_count = 0
        self.start_time = time.time()
        
    def log_message(self):
        self.message_count += 1
        elapsed = time.time() - self.start_time
        if elapsed > 60:  # Log every minute
            logger.info(f"Messages/min: {self.message_count}")
            self.message_count = 0
            self.start_time = time.time()
```

2. Check Memory Usage
```python
async def monitor_memory():
    while True:
        process = psutil.Process()
        logger.info(f"Memory usage: {process.memory_info().rss / 1024 / 1024}MB")
        await asyncio.sleep(60)
```

3. Profile Message Handling
```python
async def handle_message(self, websocket: WebSocket, message: dict):
    start = time.time()
    try:
        await self._handle_message(websocket, message)
    finally:
        elapsed = time.time() - start
        if elapsed > 0.1:  # Log slow messages
            logger.warning(f"Slow message: {elapsed}s")
```

### Quick Fixes

1. Schema Mismatch
```typescript
// Simplify frontend schema
export const MessageSchema = z.object({
    type: z.string(),
    data: z.record(z.unknown())
}).passthrough();  // Allow extra fields
```

2. Connection Issues
```typescript
// Add retry logic
const connect = (retries = 3) => {
    try {
        ws = new WebSocket(WS_URL);
    } catch (e) {
        if (retries > 0) {
            setTimeout(() => connect(retries - 1), 1000);
        }
    }
};
```

3. Message Handling
```python
# Add timeout handling
async def handle_message(self, websocket: WebSocket, message: dict):
    try:
        async with asyncio.timeout(5.0):
            await self._handle_message(websocket, message)
    except asyncio.TimeoutError:
        logger.error("Message handling timeout")
        await self.send_error(websocket, "Timeout")
```
