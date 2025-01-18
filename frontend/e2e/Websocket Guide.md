# WebSocket Testing Guide (Updated 2025-01-21)

This guide documents the WebSocket testing infrastructure, message formats, and test cases. It serves as a comprehensive reference for WebSocket functionality in the application, including end-to-end tests using Playwright.

## LM Studio Integration

### Configuration
```typescript
const llm = new LMStudioLLM({
    chat_model: "llama-3.2-3b-instruct",
    embedding_model: "text-embedding-nomic-embed-text-v1.5@f16",
    api_base: "http://localhost:1234/v1"
});
```

### Message Types

#### LLM Request
```typescript
interface LLMRequest extends BaseMessage {
    type: "llm_request";
    data: {
        content: string;
        template: string;
        metadata?: {
            domain: string;
            type: string;
        };
    };
}
```

#### LLM Response
```typescript
interface LLMChunk extends BaseMessage {
    type: "llm_chunk";
    data: {
        chunk: string;
        is_final: boolean;
    };
}
```

### Test Examples

1. Basic LLM Request
```typescript
test('should handle direct LLM request', async ({ page, wsHelper }) => {
    await wsHelper.waitForConnection();
    await wsHelper.authenticate('test-key');

    await wsHelper.sendMessage({
        type: 'llm_request',
        data: {
            content: 'Test query',
            template: 'parsing_analysis',
            metadata: {
                domain: 'test',
                type: 'analysis'
            }
        },
        timestamp: new Date().toISOString(),
        client_id: 'test'
    });

    await wsHelper.waitForMessage('llm_chunk');
    await expect(page.locator('[data-testid="llm-response"]')).toBeVisible();
});
```

2. Streaming Response
```typescript
test('should handle streaming responses', async ({ page, wsHelper }) => {
    await wsHelper.waitForConnection();
    await wsHelper.authenticate('test-key');

    await wsHelper.sendMessage({
        type: 'llm_request',
        data: {
            content: 'Long query requiring streaming',
            template: 'analytics_processing'
        },
        timestamp: new Date().toISOString(),
        client_id: 'test'
    });

    let chunkCount = 0;
    let isFinal = false;

    while (!isFinal) {
        await wsHelper.waitForMessage('llm_chunk');
        chunkCount++;
        await expect(page.locator('[data-testid="llm-chunk"]')).toBeVisible();

        const isFinalText = await page.getAttribute('[data-testid="llm-chunk"]', 'data-final');
        isFinal = isFinalText === 'true';
    }

    expect(chunkCount).toBeGreaterThan(1);
});
```

3. Error Recovery
```typescript
test('should handle error recovery', async ({ page, wsHelper }) => {
    await wsHelper.waitForConnection();
    await wsHelper.authenticate('test-key');

    // Test with invalid API base
    await wsHelper.sendMessage({
        type: 'llm_request',
        data: {
            content: 'Test query',
            template: 'parsing_analysis',
            api_base: 'http://localhost:9999/v1'
        },
        timestamp: new Date().toISOString(),
        client_id: 'test'
    });

    await wsHelper.waitForMessage('error');
    await expect(page.locator('[data-testid="error-message"]')).toContainText('failed to connect');

    // Test recovery with correct API base
    await wsHelper.sendMessage({
        type: 'llm_request',
        data: {
            content: 'Test query',
            template: 'parsing_analysis',
            api_base: 'http://localhost:1234/v1'
        },
        timestamp: new Date().toISOString(),
        client_id: 'test'
    });

    await wsHelper.waitForMessage('llm_chunk');
    await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible();
});
```

4. Connection Stability
```typescript
test('should maintain connection stability', async ({ page, wsHelper }) => {
    await wsHelper.waitForConnection();
    await wsHelper.authenticate('test-key');

    // Send long-running query
    await wsHelper.sendMessage({
        type: 'llm_request',
        data: {
            content: 'Very long query requiring extensive processing',
            template: 'analytics_processing'
        },
        timestamp: new Date().toISOString(),
        client_id: 'test'
    });

    // Monitor connection status
    await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

    // Collect chunks with timeout monitoring
    const startTime = Date.now();
    let chunkCount = 0;

    while (true) {
        await wsHelper.waitForMessage('llm_chunk', 5000);
        chunkCount++;

        // Verify connection remains stable
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Check if this is the final chunk
        const isFinalText = await page.getAttribute('[data-testid="llm-chunk"]', 'data-final');
        if (isFinalText === 'true') break;
    }

    const elapsedTime = Date.now() - startTime;
    expect(elapsedTime).toBeGreaterThan(1000); // Should take some time
    expect(chunkCount).toBeGreaterThan(5); // Should have multiple chunks
});
```

## Test Data Attributes

### LLM Integration
- `data-testid="llm-chunk"` - Individual LLM response chunk
- `data-testid="llm-response"` - Complete LLM response
- `data-testid="error-message"` - Error message display
- `data-testid="connection-status"` - WebSocket connection status

## Implementation Status (2025-01-21)

1. ✓ LM Studio Integration
   - Configured models (llama-3.2-3b-instruct, text-embedding-nomic-embed-text-v1.5@f16)
   - Implemented WebSocket streaming
   - Added template-based analysis
   - Added error handling and recovery

2. ✓ Frontend Components
   - Created LLMChat component with WebSocket support
   - Added template selection dropdown
   - Implemented streaming response display
   - Added error handling and status indicators

3. ✓ Testing Infrastructure
   - Added end-to-end WebSocket tests
   - Added LLM integration tests
   - Added error recovery tests
   - Added performance tests

4. ✓ Documentation
   - Added message format documentation
   - Added troubleshooting guide
   - Added test data attributes
   - Added implementation examples

## Timeline

- Day 1: Configure LM Studio and implement backend handlers
- Day 2: Add frontend integration and basic testing
- Day 3: Complete end-to-end testing and agent coordination

## Next Steps

1. Complete remaining LM Studio configuration
   - Set up llama-3.2-3b-instruct model
   - Configure text-embedding-nomic-embed-text-v1.5@f16
   - Test model loading

2. Implement WebSocket handlers
   - Add LLM request handling
   - Add streaming response
   - Add error handling

3. Add frontend integration
   - Create LLMClient class
   - Add streaming support
   - Add error handling

4. Test end-to-end flow
   - Test with frontend
   - Verify streaming works
   - Check error handling

5. Additional Improvements
   - Add more templates for different analysis types
   - Improve error handling with retry logic
   - Add unit tests for edge cases
   - Document WebSocket message formats
