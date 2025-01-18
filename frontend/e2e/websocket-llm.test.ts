import { test, expect } from './fixtures/websocket';

test.describe('WebSocket LLM Integration', () => {
    test('should handle direct LLM request', async ({ page, wsHelper }) => {
        await wsHelper.waitForConnection();
        await wsHelper.authenticate('test-key');

        await wsHelper.sendMessage({
            type: 'llm_analysis',
            data: {
                content: {
                    query: 'Test query',
                    type: 'analysis'
                },
                template: 'parsing_analysis'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        await wsHelper.waitForMessage('llm_stream');
        await expect(page.locator('[data-testid="llm-response"]')).toBeVisible();
    });

    test('should handle streaming responses', async ({ page, wsHelper }) => {
        await wsHelper.waitForConnection();
        await wsHelper.authenticate('test-key');

        await wsHelper.sendMessage({
            type: 'llm_analysis',
            data: {
                content: 'Long query requiring streaming',
                template: 'analytics_processing'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Monitor chunks
        let chunkCount = 0;
        let isFinal = false;

        while (!isFinal) {
            await wsHelper.waitForMessage('llm_stream');
            chunkCount++;
            await expect(page.locator('[data-testid="llm-chunk"]')).toBeVisible();

            // Check if this is the final chunk
            const isFinalText = await page.getAttribute('[data-testid="llm-chunk"]', 'data-final');
            isFinal = isFinalText === 'true';
        }

        expect(chunkCount).toBeGreaterThan(1);
    });

    test('should validate templates', async ({ page, wsHelper }) => {
        await wsHelper.waitForConnection();
        await wsHelper.authenticate('test-key');

        // Test invalid template
        await wsHelper.sendMessage({
            type: 'llm_analysis',
            data: {
                content: 'Test query',
                template: 'invalid_template'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        await wsHelper.waitForMessage('error');
        await expect(page.locator('[data-testid="error-message"]')).toContainText('template not found');

        // Test valid template
        await wsHelper.sendMessage({
            type: 'llm_analysis',
            data: {
                content: 'Test query',
                template: 'parsing_analysis'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        await wsHelper.waitForMessage('llm_stream');
        await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible();
    });

    test('should handle error recovery', async ({ page, wsHelper }) => {
        await wsHelper.waitForConnection();
        await wsHelper.authenticate('test-key');

        // Test with invalid API base
        await wsHelper.sendMessage({
            type: 'llm_analysis',
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
            type: 'llm_analysis',
            data: {
                content: 'Test query',
                template: 'parsing_analysis',
                api_base: 'http://localhost:1234/v1'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        await wsHelper.waitForMessage('llm_stream');
        await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible();
    });

    test('should handle agent coordination patterns', async ({ page, wsHelper }) => {
        await wsHelper.waitForConnection();
        await wsHelper.authenticate('test-key');

        // Test sequential pattern
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Sequential task requiring parser then orchestrator',
                pattern: 'sequential',
                workspace: 'test'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Verify parser runs first
        await wsHelper.waitForMessage('agent_action');
        await expect(page.locator('[data-testid="active-agent"]')).toHaveText('parser');

        // Then orchestrator
        await wsHelper.waitForMessage('agent_action');
        await expect(page.locator('[data-testid="active-agent"]')).toHaveText('orchestrator');

        // Test parallel pattern
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Parallel task for multiple agents',
                pattern: 'parallel',
                workspace: 'test'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Verify multiple agents are active
        await wsHelper.waitForMessage('agent_action');
        await expect(page.locator('[data-testid="active-agents"]')).toContainText('analytics');
        await expect(page.locator('[data-testid="active-agents"]')).toContainText('parser');

        // Test hierarchical pattern
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Hierarchical task with coordinator managing others',
                pattern: 'hierarchical',
                workspace: 'test'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Verify coordinator delegates
        await wsHelper.waitForMessage('agent_action');
        await expect(page.locator('[data-testid="coordinator-status"]')).toHaveText('delegating');

        // Verify other agents are coordinated
        const activeAgents = await page.locator('[data-testid="active-agents"]').allTextContents();
        expect(activeAgents.length).toBeGreaterThanOrEqual(2);
    });

    test('should maintain connection stability', async ({ page, wsHelper }) => {
        await wsHelper.waitForConnection();
        await wsHelper.authenticate('test-key');

        // Send long-running query
        await wsHelper.sendMessage({
            type: 'llm_analysis',
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
            await wsHelper.waitForMessage('llm_stream', 5000);
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
});
