# WebSocket Schema Debug Guide

## Overview

This guide explains how to debug and fix WebSocket schema validation issues between the frontend and backend.

## Required Message Flow

1. Initial Connection (CRITICAL)
```typescript
// 1. Connect with API key in headers
ws = new WebSocket(`/api/nova/ws/${clientId}`);

// 2. Send auth message immediately after connection
ws.send({
    type: "auth",
    timestamp: new Date().toISOString(),
    client_id: clientId,
    channel: null,
    data: {
        api_key: apiKey
    }
});

// 3. Wait for auth success response
{
    type: "connection_success",
    timestamp: "...",
    client_id: clientId,
    channel: null,
    data: {
        connection_type: "chat"
    }
}
```

2. Channel Subscription (REQUIRED BEFORE SENDING CHANNEL MESSAGES)
```typescript
// Subscribe to channel
ws.send({
    type: "subscribe",
    timestamp: new Date().toISOString(),
    client_id: clientId,
    channel: null,
    data: {
        channel: "nova-team" // or "nova-support"
    }
});

// Wait for subscription success
{
    type: "subscription_success",
    timestamp: "...",
    client_id: clientId,
    channel: null,
    data: {
        channel: "nova-team"
    }
}

// Unsubscribe from channel
ws.send({
    type: "unsubscribe",
    timestamp: "...",
    client_id: clientId,
    channel: null,
    data: {
        channel: "nova-team"
    }
});

// Wait for unsubscription success
{
    type: "unsubscription_success",
    timestamp: "...",
    client_id: clientId,
    channel: null,
    data: {
        channel: "nova-team"
    }
}
```

3. Channel Messages (MUST BE SUBSCRIBED FIRST)
```typescript
// Send message to nova-team channel
ws.send({
    type: "chat_message",
    timestamp: new Date().toISOString(),
    client_id: clientId,
    channel: null,
    data: {
        content: "Hello team",
        channel: "nova-team",
        message_type: "task_detection" // or "cognitive_processing"
    }
});

// Send message to nova-support channel
ws.send({
    type: "chat_message",
    timestamp: new Date().toISOString(),
    client_id: clientId,
    channel: null,
    data: {
        content: "System alert",
        channel: "nova-support",
        message_type: "resource_allocation" // or "system_health"
    }
});

// Receive channel message
{
    type: "message",
    timestamp: "...",
    client_id: senderId,
    channel: null,
    data: {
        content: "Hello team",
        channel: "nova-team",
        message_type: "task_detection"
    }
}

// Receive delivery confirmation
{
    type: "message_delivered",
    timestamp: "...",
    client_id: clientId,
    channel: null,
    data: {
        message: "Chat message received and processed",
        original_type: "chat_message",
        status: "success"
    }
}
```

4. Error Messages
```typescript
// Invalid channel
{
    type: "error",
    timestamp: "...",
    client_id: clientId,
    channel: null,
    data: {
        error: "Invalid channel: unknown-channel"
    }
}

// Invalid message type for channel
{
    type: "error",
    timestamp: "...",
    client_id: clientId,
    channel: null,
    data: {
        error: "Invalid message type for nova-team channel"
    }
}

// Not subscribed to channel
{
    type: "error",
    timestamp: "...",
    client_id: clientId,
    channel: null,
    data: {
        error: "Failed to join channel nova-team"
    }
}
```

5. Ping/Pong Messages
```typescript
// Send ping
ws.send({
    type: "ping",
    timestamp: new Date().toISOString(),
    client_id: clientId,
    channel: null,
    data: {}
});

// Receive pong
{
    type: "pong",
    timestamp: "...",
    client_id: clientId,
    channel: null,
    data: {}
}
```

## Current Issues

1. Missing Auth Message (CRITICAL)
- Backend requires auth message immediately after connection
- Without auth, all other messages will fail
- Check WebSocket connection logs for auth failures

2. Schema Validation Errors (BLOCKING)
- Frontend uses strict Zod validation
- Backend expects simpler format
- Common validation failures:
  - Extra metadata fields
  - Missing required fields
  - Wrong field types
  - Invalid date formats

3. Channel Subscription Issues (BLOCKING)
- Messages to channels require subscription first
- Subscribe before sending channel messages:
```typescript
// Join channel
ws.send({
    type: "subscribe",
    timestamp: new Date().toISOString(),
    client_id: clientId,
    channel: null,
    data: {
        channel: "channel-name"
    }
});

// Wait for subscription success
{
    type: "subscription_success",
    timestamp: "...",
    client_id: clientId,
    channel: null,
    data: {
        channel: "channel-name"
    }
}
```

## Required Message Flow Order

1. Connect to WebSocket
2. Send auth message immediately
3. Wait for auth success
4. Subscribe to channels if needed
5. Wait for subscription success
6. Begin sending messages

## Exact Message Type Mapping (MUST MATCH)

Backend expects these specific message types:

1. Chat Messages
```typescript
{
    type: "chat_message",
    data: {
        thread_id: string;
        content: string;
        sender?: string;
    }
}
```

2. Task Updates
```typescript
{
    type: "task_update",
    data: {
        task_id: string;
        status?: string;
        metadata?: Record<string, any>;
    }
}
```

3. Agent Status
```typescript
{
    type: "agent_status",
    data: {
        agent_id: string;
        status: string;
        metadata?: Record<string, any>;
    }
}
```

4. Graph Updates
```typescript
{
    type: "graph_update",
    data: {
        nodes: Array<{
            id: string;
            type: string;
            metadata?: Record<string, any>;
        }>;
        edges: Array<{
            from: string;
            to: string;
            type: string;
            metadata?: Record<string, any>;
        }>;
    }
}
```

## Debugging Steps

1. Enable WebSocket Logging
```typescript
// Frontend
ws.onmessage = (event) => {
    console.log('Received:', JSON.parse(event.data));
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

// Backend logs in: logs/websocket.log
```

2. Validate Message Format
- Check message matches base format
- Verify required fields present
- Ensure correct field types
- Validate ISO date format

3. Test Connection Flow
```typescript
// 1. Connect with headers
const headers = {
    'X-API-Key': apiKey
};

// 2. Send auth immediately
ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'auth',
        timestamp: new Date().toISOString(),
        client_id: clientId,
        channel: null,
        data: { api_key: apiKey }
    }));
};

// 3. Handle auth response
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'connection_success') {
        // Connection ready
    }
};
```

4. Check Channel Subscriptions
- Verify channel subscription before sending channel messages
- Check channel exists and client has access
- Confirm subscription success response

## Frontend Schema Updates

Update frontend schemas to match backend expectations:

```typescript
// Base WebSocket message schema
export const WebSocketMessageBaseSchema = z.object({
    type: z.string(),
    timestamp: z.string().refine(isValidISODate),
    client_id: z.string(),
    channel: z.string().nullable(),
    data: z.record(z.unknown())
});

// Auth message schema
export const AuthMessageSchema = WebSocketMessageBaseSchema.extend({
    type: z.literal('auth'),
    data: z.object({
        api_key: z.string()
    })
});

// Chat message schema
export const ChatMessageSchema = WebSocketMessageBaseSchema.extend({
    type: z.literal('chat_message'),
    data: z.object({
        thread_id: z.string(),
        content: z.string(),
        sender: z.string().optional()
    })
});
```

## Testing WebSocket Connection

Use the test client to verify connection:

```typescript
import { WebSocket } from 'ws';

const ws = new WebSocket('ws://localhost:8000/ws/test-client');

// Enable logging
ws.on('message', (data) => {
    console.log('Received:', JSON.parse(data));
});

// Send auth message
ws.on('open', () => {
    ws.send(JSON.stringify({
        type: 'auth',
        timestamp: new Date().toISOString(),
        client_id: 'test-client',
        channel: null,
        data: {
            api_key: 'test-key'
        }
    }));
});

// Handle errors
ws.on('error', console.error);
```

## Common Error Messages

1. Authentication Errors
```
Error: Authentication required
Solution: Send auth message after connection
```

2. Schema Validation Errors
```
Error: Invalid message format
Solution: Check message matches base format
```

3. Channel Errors
```
Error: Not subscribed to channel
Solution: Subscribe to channel before sending messages
```

4. Connection Timeout
```
Error: Connection timeout
Solution: Check connection is alive and sending ping/pong
```

## Best Practices

1. Always send auth message first
2. Validate messages against schemas before sending
3. Handle reconnection with exponential backoff
4. Subscribe to channels before sending channel messages
5. Log WebSocket traffic for debugging
6. Use typed message interfaces
7. Handle connection errors gracefully
8. Clean up subscriptions on disconnect

## Testing Tools

1. WebSocket Test Client
```bash
# Install wscat
npm install -g wscat

# Connect and send messages
wscat -c ws://localhost:8000/ws/test-client
```

2. Browser DevTools
- Network tab > WS
- Console logging
- Message inspection

3. Backend Logs
- Check logs/websocket.log
- Enable debug logging
- Monitor connection status

## Next Steps

1. Update frontend schemas to match backend
2. Add auth message handling
3. Implement proper channel subscription
4. Add connection error handling
5. Enable WebSocket logging
6. Test with example messages
7. Monitor for validation errors
