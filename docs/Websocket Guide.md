# WebSocket Testing Guide (Updated 2025-01-21)

This guide documents the WebSocket testing infrastructure and current implementation status.

## Testing Architecture

The WebSocket tests use the main application's WebSocket infrastructure:

1. The main app's WebSocket store (`src/lib/stores/websocket.ts`) handles WebSocket connections and events
2. The ConnectionStatus component (`src/lib/components/shared/ConnectionStatus.svelte`) displays connection state
3. The WebSocket endpoints (`src/nia/nova/endpoints/websocket_endpoints.py`) include a debug endpoint for testing
4. The test helper (`frontend/e2e/test-helpers/websocket.ts`) uses the app's event system for testing

### Port Configuration
- Frontend app runs on port 5173 (Vite dev server)
- WebSocket server runs on port 8000
- Tests connect to frontend on 5173 and WebSocket on 8000
- API keys:
  * 'development' for main app
  * 'valid-test-key' for tests

## Current Test Status

### Passing Tests
1. Basic Connection (3 tests)
   - Successful connection in Chromium (583ms)
   - Successful connection in Firefox (1.0s)
   - Successful connection in WebKit (2.6s)

2. Authentication (2 tests in Firefox)
   - Successful authentication
   - Authentication failure handling

### Test Data Attributes
- `data-testid="connection-status"` - WebSocket connection status
- `data-testid="auth-status"` - Authentication status ('Authenticated' | 'Not Authenticated')
- `data-testid="error-message"` - Error message display
- `data-testid="reconnect-info"` - Reconnection attempt information
- `data-testid="error-details"` - Detailed error information

### Server Configuration

The WebSocket server is part of the main FastAPI application (`nia.nova.core.app`) and can be started in two ways:

1. Development Mode (manage.py):
   ```bash
   python scripts/manage.py start
   ```
   - Starts all services including Neo4j, Redis, FastAPI, etc.
   - Uses uvicorn with debug mode enabled
   - Provides comprehensive logging and monitoring

2. Server Only (run_server.py):
   ```bash
   python scripts/run_server.py
   ```
   - Focused on running the FastAPI server
   - Includes service verification and monitoring
   - More suitable for production-like environments

Both methods use the same FastAPI application and WebSocket endpoints, ensuring consistent behavior.

### Authentication Flow and Error Handling

The WebSocket authentication in this app follows a two-step process with comprehensive error handling:

1. Initial Connection
   - Client connects to `/debug/client_{client_id}` or `/client_{client_id}`
   - Server accepts connection without authentication
   - Server sends `connection_established` message
   ```json
   {
     "type": "connection_established",
     "data": {
       "message": "Connection established, waiting for authentication"
     }
   }
   ```

2. Authentication Message
   - Client sends `connect` message with API key
   ```json
   {
     "type": "connect",
     "data": {
       "api_key": "valid-test-key",
       "connection_type": "chat",
       "domain": "personal",
       "workspace": "personal"
     }
   }
   ```
   - Server validates API key using `ws_auth()` function
   - On success, server sends `connection_success` followed by `message_delivered`
   ```json
   {
     "type": "connection_success",
     "data": {
       "message": "Connected"
     }
   }
   {
     "type": "message_delivered",
     "data": {
       "message": "Authentication message received and processed",
       "original_type": "connect",
       "status": "success"
     }
   }
   ```
   - On failure, server sends error message and closes connection
   ```json
   {
     "type": "error",
     "data": {
       "message": "Invalid API key",
       "error_type": "invalid_key"
     }
   }
   {
     "type": "disconnect",
     "data": {
       "reason": "Invalid API key"
     }
   }
   ```

3. Post-Authentication
   - All subsequent messages require prior successful authentication
   - Connection is maintained until explicitly closed or error occurs
   - Server tracks authentication state per connection
   - Reconnection requires re-authentication

4. Error Handling
   - Authentication Errors (403/4000)
     ```json
     // Invalid API key
     {
       "type": "error",
       "data": {
         "message": "Invalid API key",
         "error_type": "invalid_key",
         "code": 403
       }
     }
     // Expired token
     {
       "type": "error",
       "data": {
         "message": "Token expired",
         "error_type": "token_expired",
         "code": 403
       }
     }
     ```
     Followed by disconnect message:
     ```json
     {
       "type": "disconnect",
       "data": {
         "reason": "Invalid API key"
       }
     }
     ```
     Connection closed with code 4000

   - Server Errors (500/1011)
     ```json
     {
       "type": "error",
       "data": {
         "message": "Internal server error",
         "error_type": "server_error",
         "code": 500
       }
     }
     ```
     Connection closed with code 1011

5. API Keys
   - Development: 'development' key for main app
   - Testing: 'valid-test-key' for automated tests
   - Keys are validated against TEST_API_KEYS in auth.py
   - Keys can have expiration and permission levels

6. WebSocket Close Codes
   - 1000: Normal closure
   - 1011: Server error
   - 4000: Authentication error
   - 4001: Rate limit exceeded
   - 4002: Invalid message format
   - 4003: Protocol violation

### Authentication States
The system maintains consistent authentication states:
1. Initial state: 'Not Authenticated'
2. After successful auth: 'Authenticated'
3. After connection error: 'Not Authenticated'
4. After reconnection: Requires re-authentication
5. After cleanup: 'Not Authenticated'

Authentication status is preserved during:
- Channel operations (join/leave)
- Agent status updates
- Message sending/receiving

## Implementation Status

1. Working Features
   - Basic WebSocket connection across browsers
   - Authentication with API key validation
   - Connection status display
   - Basic error message handling
   - Consistent auth state management
   - Auth status preservation during operations
   - Clean state reset after tests

2. Pending Implementation
   - Message delivery confirmation
   - Reconnection handling
   - Message broadcasting
   - Error recovery strategies
   - Performance monitoring
   - Load balancing

3. Known Issues
   - Message delivery unconfirmed
   - Reconnection scenarios need improvement
   - Performance under high load untested
   - Error recovery needs enhancement

## Next Steps

1. Debug Endpoint Updates
   - ✓ Fixed premature exit after auth by implementing two-step authentication
   - ✓ Added message delivery confirmation
   - Implement channel operations:
     * Need to implement `/api/chat/threads` endpoint (currently 404)
     * Need to fix message validation for channel operations
     * Need to implement channel subscription/unsubscription handlers
   - Add proper error handling:
     * Need to handle channel operation failures
     * Need to implement retry logic for failed operations
     * Need to add timeout handling for operations

2. Test Infrastructure
   - Add channel subscription tests
   - Add message delivery tests
   - Add reconnection tests
   - Add error recovery tests

3. Error Handling
   - Add retry logic
   - Add timeout handling
   - Add error recovery
   - Add error reporting

4. Performance Testing
   - Add load tests
   - Add stress tests
   - Add latency tests
   - Add connection limit tests
