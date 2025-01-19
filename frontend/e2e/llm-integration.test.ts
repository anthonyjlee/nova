import { test, expect } from './fixtures/websocket';

test.describe('LLM Integration', () => {
    test('should handle direct LLM request', async ({ page, wsHelper }) => {
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

        // Wait for response
        await wsHelper.waitForMessage('llm_stream');
        await expect(page.locator('[data-testid="llm-response"]')).toBeVisible();
    });

    test('should handle template processing', async ({ page, wsHelper }) => {
        // Test with different templates
        const templates = ['parsing_analysis', 'analytics_processing'];

        for (const template of templates) {
            await wsHelper.sendMessage({
                type: 'llm_analysis',
                data: {
                    content: 'Test query',
                    template
                },
                timestamp: new Date().toISOString(),
                client_id: 'test'
            });

            // Wait for response
            await wsHelper.waitForMessage('llm_stream');
            await expect(page.locator('[data-testid="llm-response"]')).toBeVisible();
        }
    });

    test('should handle streaming responses', async ({ page, wsHelper }) => {
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
        
        // Wait for initial chunk
        await wsHelper.waitForMessage('llm_stream');
        await expect(page.locator('[data-testid="llm-chunk"]')).toBeVisible();
        chunkCount++;

        // Wait for final chunk
        await wsHelper.waitForMessage('llm_stream');
        await expect(page.locator('[data-testid="llm-chunk"]')).toBeVisible();
        chunkCount++;

        // Should have received at least 2 chunks
        expect(chunkCount).toBeGreaterThan(1);
    });

    test('should handle error recovery', async ({ page, wsHelper }) => {
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

        // Verify error handling
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
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

        // Verify successful recovery
        await wsHelper.waitForMessage('llm_stream');
        await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible();
    });

    test('should handle agent coordination', async ({ page, wsHelper }) => {
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Complex query requiring multiple agents',
                workspace: 'test'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Verify agent actions
        await wsHelper.waitForMessage('agent_action');
        await expect(page.locator('[data-testid="active-agents"]')).toBeVisible();

        // Verify LLM chunks
        await wsHelper.waitForMessage('llm_stream');
        await expect(page.locator('[data-testid="llm-chunk"]')).toBeVisible();

        // Wait for final response
        await wsHelper.waitForMessage('chat_message');
        await expect(page.locator('[data-testid="message-content"]')).toBeVisible();
    });
});
