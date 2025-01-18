import { test, expect } from './fixtures/websocket';

test.describe('WebSocket Endpoints', () => {
    test('should handle successful connection', async ({ page, wsHelper }) => {
        await wsHelper.waitForConnection();
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');
    });

    test('should handle WebSocket message flow', async ({ page, wsHelper }) => {
        // Auth flow
        await wsHelper.authenticate('test-key');
        await wsHelper.waitForAuthStatus('Authenticated');

        // Channel subscription
        await wsHelper.joinChannel('test-channel');
        await wsHelper.waitForMessage('subscription_success');

        // Message sending
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Test message',
                thread_id: 'test-thread'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test',
            channel: 'test-channel'
        });

        // Verify message received
        await expect(page.locator('[data-testid="message-content"]')).toContainText('Test message');
    });

    test('should handle channel operations', async ({ page, wsHelper }) => {
        await wsHelper.authenticate('test-key');
        await wsHelper.waitForAuthStatus('Authenticated');

        // Subscribe to channel
        await wsHelper.joinChannel('test-channel');
        await wsHelper.waitForMessage('subscription_success');

        // Send message to channel
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Channel message',
                thread_id: 'test-thread'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test',
            channel: 'test-channel'
        });

        // Verify message in channel
        await expect(page.locator('[data-testid="message-content"]')).toContainText('Channel message');

        // Leave channel
        await wsHelper.leaveChannel('test-channel');
        await wsHelper.waitForMessage('unsubscription_success');

        // Verify no more messages received
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Should not receive',
                thread_id: 'test-thread'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test',
            channel: 'test-channel'
        });

        await expect(page.locator('[data-testid="message-content"]')).not.toContainText('Should not receive');
    });
});
