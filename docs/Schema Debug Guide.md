# Schema Debug Guide

## Current Problem
Messages aren't validating correctly between frontend and backend. We need to:
1. Debug validation issues
2. Use feature flags to help identify problems
3. Get basic chat working

## Implementation

### 1. Redis Feature Flags (no longer implementing)
```python
# src/nia/core/feature_flags.py
class FeatureFlags:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "debug:"
        
    async def enable_debug(self, flag_name: str):
        """Enable debug flag."""
        key = f"{self.prefix}{flag_name}"
        await self.redis.set(key, "true")
        
    async def is_debug_enabled(self, flag_name: str) -> bool:
        """Check if debug flag is enabled."""
        key = f"{self.prefix}{flag_name}"
        return await self.redis.get(key) == b"true"

# Debug flags
DEBUG_FLAGS = {
    'log_validation': 'debug:log_validation',     # Log all validation attempts
    'log_websocket': 'debug:log_websocket',       # Log WebSocket messages
    'log_storage': 'debug:log_storage',           # Log storage operations
    'strict_mode': 'debug:strict_mode'            # Throw on any validation error
}
```

### 2. Backend Validation
```python
# src/nia/nova/core/validation.py
async def validate_message(data: dict, debug_flags: FeatureFlags) -> Message:
    """Validate message with debug logging."""
    try:
        if await debug_flags.is_debug_enabled('log_validation'):
            logger.debug(f"Validating message data: {data}")
            
        message = Message(**data)
        
        if await debug_flags.is_debug_enabled('log_validation'):
            logger.debug(f"Validation successful: {message}")
            
        return message
        
    except ValidationError as e:
        if await debug_flags.is_debug_enabled('log_validation'):
            logger.error(f"Validation failed: {str(e)}")
            
        if await debug_flags.is_debug_enabled('strict_mode'):
            raise
        
        logger.warning(f"Validation error (non-strict mode): {str(e)}")
        return None
```

### 3. Frontend Validation
```typescript
// frontend/src/lib/validation/debug.ts
export const debugFlags = {
    logValidation: false,
    logWebSocket: false,
    strictMode: false
};

// frontend/src/lib/validation/messages.ts
export const validateMessage = (data: unknown) => {
    if (debugFlags.logValidation) {
        console.log('Validating message:', data);
    }
    
    try {
        const result = messageSchema.parse(data);
        
        if (debugFlags.logValidation) {
            console.log('Validation successful:', result);
        }
        
        return result;
    } catch (error) {
        if (debugFlags.logValidation) {
            console.error('Validation failed:', error);
        }
        
        if (debugFlags.strictMode) {
            throw error;
        }
        
        console.warn('Validation error (non-strict):', error);
        return null;
    }
};
```

### 4. WebSocket Integration
```python
# Backend WebSocket
class WebSocketServer:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe("debug_updates")
        
    async def broadcast_debug_update(self, data: dict):
        """Broadcast debug info to all clients."""
        await self.redis.publish("debug_updates", 
            json.dumps({
                "type": "debug_update",
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
        )

# Frontend WebSocket
export class WebSocketClient {
    constructor(private debugFlags = debugFlags) {
        this.ws = new WebSocket('ws://localhost:8000/ws');
        this.setupDebugHandlers();
    }
    
    private setupDebugHandlers() {
        // Handle debug messages
        this.ws.addEventListener('message', (event) => {
            if (this.debugFlags.logWebSocket) {
                console.log('WS Received:', event.data);
            }
            
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'debug_update') {
                    this.handleDebugUpdate(data);
                }
            } catch (error) {
                if (this.debugFlags.logWebSocket) {
                    console.error('WS Parse error:', error);
                }
            }
        });
        
        // Handle connection issues
        this.ws.addEventListener('close', () => {
            if (this.debugFlags.logWebSocket) {
                console.log('WS Connection closed');
            }
            this.scheduleReconnect();
        });
    }
    
    private handleDebugUpdate(data: any) {
        if (data.data.type === 'validation') {
            this.handleValidationUpdate(data.data);
        } else if (data.data.type === 'websocket') {
            this.handleWebSocketUpdate(data.data);
        }
    }
    
    async send(message: unknown) {
        if (this.debugFlags.logWebSocket) {
            console.log('WS Sending:', message);
        }
        
        try {
            const validated = validateMessage(message);
            if (!validated) {
                throw new Error('Message validation failed');
            }
            
            await this.ws.send(JSON.stringify(validated));
            
        } catch (error) {
            if (this.debugFlags.logWebSocket) {
                console.error('WS Send error:', error);
            }
            throw error;
        }
    }
    
    private scheduleReconnect() {
        setTimeout(() => {
            if (this.debugFlags.logWebSocket) {
                console.log('WS Attempting reconnect...');
            }
            this.ws = new WebSocket('ws://localhost:8000/ws');
            this.setupDebugHandlers();
        }, 5000);
    }
}
```

### 5. Debug UI
```typescript
// frontend/src/lib/components/DebugPanel.svelte
<script lang="ts">
    import { debugFlags } from '../validation/debug';
    import { webSocket } from '../websocket/client';
    
    let messages: any[] = [];
    
    $: {
        if (debugFlags.logValidation) {
            // Subscribe to validation logs
            webSocket.on('validation', (data) => {
                messages = [...messages, {
                    type: 'validation',
                    ...data,
                    timestamp: new Date().toISOString()
                }];
            });
        }
        
        if (debugFlags.logWebSocket) {
            // Subscribe to WebSocket logs
            webSocket.on('websocket', (data) => {
                messages = [...messages, {
                    type: 'websocket',
                    ...data,
                    timestamp: new Date().toISOString()
                }];
            });
        }
    }
</script>

<div class="debug-panel">
    <div class="controls">
        <label>
            <input type="checkbox" bind:checked={debugFlags.logValidation}>
            Log Validation
        </label>
        <label>
            <input type="checkbox" bind:checked={debugFlags.logWebSocket}>
            Log WebSocket
        </label>
        <label>
            <input type="checkbox" bind:checked={debugFlags.strictMode}>
            Strict Mode
        </label>
    </div>
    
    <div class="logs">
        {#each messages as msg}
            <div class="log-entry">
                <span class="timestamp">{msg.timestamp}</span>
                <span class="type">{msg.type}</span>
                <pre class="data">{JSON.stringify(msg.data, null, 2)}</pre>
            </div>
        {/each}
    </div>
</div>
```

## Debug Process

### 1. Enable Debug Mode
```python
# In development
await feature_flags.enable_debug('log_validation')
await feature_flags.enable_debug('log_websocket')
await feature_flags.enable_debug('strict_mode')
```

### 2. Send Test Message
```typescript
// In browser console
debugFlags.logValidation = true;
debugFlags.logWebSocket = true;
debugFlags.strictMode = true;

// Send test message
const message = {
    content: "Test message",
    thread_id: "test-thread",
    sender: {
        id: "test-user",
        type: "user",
        name: "Test User"
    }
};

await chat.sendMessage(message);
```

### 3. Check Logs
1. Browser console for frontend validation/WebSocket logs
2. Backend logs for server validation/WebSocket logs
3. Compare data at each step

## Next Steps

1. Debug Current Issues
- [ ] Enable debug logging
- [ ] Send test messages
- [ ] Identify validation failures
- [ ] Fix schema mismatches

2. Get Basic Flow Working
- [ ] Test simple message flow
- [ ] Verify storage
- [ ] Check WebSocket updates
- [ ] Validate responses

3. Add Error Recovery
- [ ] Improve error messages
- [ ] Add retry logic
- [ ] Handle edge cases
- [ ] Add user feedback

The goal is to get basic messaging working first, then improve the validation and error handling once we understand where things are breaking.
