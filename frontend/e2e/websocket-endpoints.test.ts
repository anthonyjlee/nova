import { test, expect } from './fixtures/websocket';

test.describe('WebSocket Endpoints', () => {
    test('should handle successful connection', async ({ page, wsHelper }) => {
        // Initial connecting state
        await wsHelper.setConnectionStatus('connecting');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connecting');

        // Transition to connected state
        await wsHelper.setConnectionStatus('connected');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');
        await wsHelper.waitForAuthStatus('Not Authenticated');
    });

    test('should maintain auth status during connection changes', async ({ page, wsHelper }) => {
        // Initial connection and auth
        await wsHelper.setConnectionStatus('connecting');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connecting');
        await wsHelper.setConnectionStatus('connected');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');
        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');

        // Simulate connection error
        await wsHelper.setConnectionStatus('error');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Error');
        await wsHelper.setAuthStatus('not_authenticated');
        await wsHelper.waitForAuthStatus('Not Authenticated');

        // Reconnect
        await wsHelper.setConnectionStatus('connecting');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connecting');
        await wsHelper.setConnectionStatus('connected');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');
        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');
    });

    test('should handle NovaTeam channel messaging', async ({ page, wsHelper }) => {
        // Initial connection and auth
        await wsHelper.setConnectionStatus('connecting');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connecting');
        await wsHelper.setConnectionStatus('connected');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');
        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');

        // Join NovaTeam channel
        await wsHelper.joinChannel('NovaTeam');
        await wsHelper.waitForMessage('subscription_success');

        // Generate unique thread ID
        const threadId = 'nova-thread-' + Date.now();

        // Send message in NovaTeam channel with thread
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Task detection message',
                thread_id: threadId,
                message_type: 'task_detection',
                workspace: 'professional'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test',
            channel: 'NovaTeam'
        });

        // Verify message in channel
        await expect(page.locator('[data-testid="message-content"]')).toContainText('Task detection message');

        // Send cognitive processing reply in same thread
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Processing task',
                thread_id: threadId,
                message_type: 'cognitive_processing',
                workspace: 'professional'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test',
            channel: 'NovaTeam'
        });

        // Leave channel and verify auth status maintained
        await wsHelper.leaveChannel('NovaTeam');
        await wsHelper.waitForMessage('unsubscription_success');
        await wsHelper.waitForAuthStatus('Authenticated');

        // Verify no more messages received after leaving
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Should not receive',
                thread_id: threadId,
                message_type: 'task_detection',
                workspace: 'professional'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test',
            channel: 'NovaTeam'
        });

        await expect(page.locator('[data-testid="message-content"]')).not.toContainText('Should not receive');
    });

    test('should handle NovaSupport channel operations', async ({ page, wsHelper }) => {
        // Initial connection and auth
        await wsHelper.setConnectionStatus('connecting');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connecting');
        await wsHelper.setConnectionStatus('connected');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');
        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');

        // Subscribe to NovaSupport channel
        await wsHelper.joinChannel('NovaSupport');
        await wsHelper.waitForMessage('subscription_success');

        // Generate unique thread ID
        const threadId = 'support-thread-' + Date.now();

        // Send resource allocation message
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Resource allocation request',
                thread_id: threadId,
                message_type: 'resource_allocation',
                workspace: 'system'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test',
            channel: 'NovaSupport'
        });

        // Verify message in channel
        await expect(page.locator('[data-testid="message-content"]')).toContainText('Resource allocation request');

        // Leave channel and verify auth status maintained
        await wsHelper.leaveChannel('NovaSupport');
        await wsHelper.waitForMessage('unsubscription_success');
        await wsHelper.waitForAuthStatus('Authenticated');

        // Verify no more messages received after leaving
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Should not receive',
                thread_id: threadId,
                message_type: 'resource_allocation',
                workspace: 'system'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test',
            channel: 'NovaSupport'
        });

        await expect(page.locator('[data-testid="message-content"]')).not.toContainText('Should not receive');
    });
});
