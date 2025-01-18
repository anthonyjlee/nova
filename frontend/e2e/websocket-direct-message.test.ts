import { test, expect } from './fixtures/websocket';

test.describe('Direct Agent Messaging', () => {
    test('should send direct message to belief agent', async ({ page, wsHelper }) => {
        // Connect and authenticate
        await wsHelper.waitForConnection();
        await wsHelper.authenticate('test-key');

        // Wait for successful connection
        await wsHelper.waitForMessage('connection_success');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Send message to belief agent
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Hello belief agent',
                workspace: 'personal',
                metadata: {
                    type: 'direct_message',
                    agent_id: 'belief-agent',
                    domain: 'general'
                }
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Wait for and verify belief agent's response
        await wsHelper.waitForBeliefAnalysis();
        await expect(page.locator('[data-testid="message-content"]')).toContainText('Hello belief agent');

        // Verify belief agent's emotional state
        await wsHelper.waitForEmotionalState();

        // Verify belief agent's confidence level is high for this simple greeting
        const confidenceLevel = await page.locator('[data-testid="confidence-level"]').textContent();
        expect(parseFloat(confidenceLevel || '0')).toBeGreaterThan(0.8);
    });
});
