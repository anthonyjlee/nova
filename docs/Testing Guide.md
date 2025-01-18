# Testing Guide

This guide documents the testing infrastructure and patterns used in the Nova project.

## Testing Architecture

### 1. End-to-End Tests (frontend/e2e/)

The e2e tests use Playwright to test full user flows and WebSocket interactions:

#### WebSocket Testing (websocket-endpoints.test.ts)
- Tests WebSocket connection lifecycle
- Validates authentication flows
- Tests channel operations (join/leave)
- Verifies message delivery and handling
- Tests domain-specific channels (NovaTeam, NovaSupport)

#### Test Helpers (frontend/e2e/test-helpers/)
- WebSocket test helper for simulating WebSocket events
- Connection status management
- Authentication flow helpers
- Channel operation helpers

### 2. Test Data Attributes

Important data-testid attributes used in tests:
```html
data-testid="connection-status"    <!-- WebSocket connection status -->
data-testid="auth-status"         <!-- Authentication status -->
data-testid="error-message"       <!-- Error message display -->
data-testid="reconnect-info"      <!-- Reconnection attempt info -->
data-testid="error-details"       <!-- Detailed error information -->
data-testid="message-content"     <!-- Message content in channels -->
```

### 3. Test Patterns

#### Connection Testing
```typescript
// Test connection lifecycle
test('should handle successful connection', async ({ page, wsHelper }) => {
    await wsHelper.setConnectionStatus('connecting');
    await expect(page.locator('[data-testid="connection-status"]'))
        .toHaveText('Connecting');

    await wsHelper.setConnectionStatus('connected');
    await expect(page.locator('[data-testid="connection-status"]'))
        .toHaveText('Connected');
});
```

#### Authentication Testing
```typescript
// Test auth persistence
test('should maintain auth status during connection changes', async ({ page, wsHelper }) => {
    await wsHelper.authenticate('valid-test-key');
    await wsHelper.waitForAuthStatus('Authenticated');
    
    // Test reconnection
    await wsHelper.setConnectionStatus('error');
    await wsHelper.setConnectionStatus('connected');
    await wsHelper.authenticate('valid-test-key');
    await wsHelper.waitForAuthStatus('Authenticated');
});
```

#### Channel Testing
```typescript
// Test channel operations
test('should handle NovaTeam channel messaging', async ({ page, wsHelper }) => {
    await wsHelper.joinChannel('NovaTeam');
    await wsHelper.waitForMessage('subscription_success');

    await wsHelper.sendMessage({
        type: 'chat_message',
        data: {
            content: 'Test message',
            thread_id: 'test-thread',
            message_type: 'task_detection'
        },
        channel: 'NovaTeam'
    });

    await expect(page.locator('[data-testid="message-content"]'))
        .toContainText('Test message');
});
```

### 4. Test Configuration

#### Playwright Config (playwright.config.ts)
```typescript
{
    testDir: './e2e',
    use: {
        baseURL: 'http://localhost:5173',
        trace: 'on-first-retry',
    },
    webServer: {
        command: 'npm run dev',
        port: 5173,
        reuseExistingServer: !process.env.CI,
    }
}
```

### 5. Test Environment

#### Required Services
- Frontend dev server (port 5173)
- WebSocket server (port 8000)
- Test API keys:
  * 'valid-test-key' for test authentication
  * 'development' for main app

#### Environment Setup
```bash
# Start all services
python scripts/manage.py start

# Run tests
cd frontend
npm run test:e2e
```

### 6. Test Data Management

#### Channel Test Data
```typescript
const testChannel = {
    id: 'test-channel',
    name: 'NovaTeam',
    type: 'PUBLIC',
    status: 'ACTIVE',
    settings: {
        name: 'NovaTeam',
        type: 'PUBLIC',
        is_public: true,
        allow_threads: true
    }
};
```

#### Message Test Data
```typescript
const testMessage = {
    type: 'chat_message',
    data: {
        content: 'Test message',
        thread_id: `thread-${Date.now()}`,
        message_type: 'task_detection',
        workspace: 'professional'
    },
    channel: 'NovaTeam'
};
```

### 7. Error Testing

#### Connection Errors
```typescript
test('should handle connection errors', async ({ page, wsHelper }) => {
    await wsHelper.setConnectionStatus('error');
    await expect(page.locator('[data-testid="connection-status"]'))
        .toHaveText('Error');
    await expect(page.locator('[data-testid="error-message"]'))
        .toBeVisible();
});
```

#### Authentication Errors
```typescript
test('should handle auth errors', async ({ page, wsHelper }) => {
    await wsHelper.authenticate('invalid-key');
    await expect(page.locator('[data-testid="auth-status"]'))
        .toHaveText('Not Authenticated');
    await expect(page.locator('[data-testid="error-message"]'))
        .toContainText('Invalid API key');
});
```

### 8. Best Practices

1. **Test Organization**
   - Group related tests using describe blocks
   - Use clear, descriptive test names
   - Keep tests focused and atomic

2. **Test Data**
   - Use unique identifiers for test data
   - Clean up test data after tests
   - Use helper functions for common operations

3. **Assertions**
   - Use explicit assertions
   - Check both positive and negative cases
   - Verify error states and edge cases

4. **Test Isolation**
   - Reset state between tests
   - Don't rely on test ordering
   - Clean up resources after tests

5. **Error Handling**
   - Test error scenarios
   - Verify error messages
   - Check error recovery

### 9. Adding New Tests

1. Create test file in appropriate directory:
   - E2E tests in frontend/e2e/
   - Component tests in src/components/\_\_tests\_\_/
   - Unit tests alongside source files

2. Import test helpers and fixtures:
   ```typescript
   import { test, expect } from './fixtures/websocket';
   import { wsHelper } from './test-helpers/websocket';
   ```

3. Write tests following existing patterns:
   ```typescript
   test.describe('Feature Name', () => {
       test('should do something', async ({ page, wsHelper }) => {
           // Test implementation
       });
   });
   ```

4. Run tests:
   ```bash
   npm run test:e2e        # Run all e2e tests
   npm run test:e2e:ui     # Run with UI
   npm run test:unit       # Run unit tests
   ```

### 10. Debugging Tests

1. **Using UI Mode**
   ```bash
   npm run test:e2e:ui
   ```
   - Shows test execution in browser
   - Allows stepping through tests
   - Provides detailed logs

2. **Using Debug Logs**
   ```typescript
   test.describe.configure({ mode: 'debug' });
   console.log('Debug info:', someValue);
   ```

3. **Using Screenshots**
   ```typescript
   await page.screenshot({ path: 'debug.png' });
   ```

4. **Using Traces**
   ```typescript
   await page.context().tracing.start();
   // Test code
   await page.context().tracing.stop({ path: 'trace.zip' });
