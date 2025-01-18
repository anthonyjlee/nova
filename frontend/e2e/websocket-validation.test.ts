import { test, expect } from './fixtures/websocket';
import type { WebSocketMessage, MessageType } from '../src/lib/schemas/websocket';

// Helper type for testing invalid messages
type InvalidMessage = {
    type: MessageType;
    data?: Record<string, unknown>;
    timestamp?: string;
    client_id?: string;
    channel?: string;
};

test.describe('WebSocket Message Validation', () => {
    test('should handle invalid message format', async ({ page, wsHelper }) => {
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Send message with missing required fields
        // Using Partial<WebSocketMessage> to indicate intentionally incomplete message
        const invalidMessage: InvalidMessage = {
            type: 'chat_message',
            data: {
                content: 'Test message'
            }
        };
        await wsHelper.sendMessage(invalidMessage as WebSocketMessage);

        // Verify error appears
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
        await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid message format');
    });

    test('should handle invalid channel name', async ({ page, wsHelper }) => {
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Try to join invalid channel
        await wsHelper.sendMessage({
            type: 'join_channel',
            data: {
                channel: 'InvalidChannel'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Verify error appears
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
        await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid channel');
    });

    test('should handle invalid task status', async ({ page, wsHelper }) => {
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Send task update with invalid status
        await wsHelper.sendMessage({
            type: 'task_update',
            data: {
                task_id: 'test-task',
                status: 'invalid_status',
                changes: {}
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Verify error appears
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
        await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid task status');
    });

    test('should handle invalid agent status', async ({ page, wsHelper }) => {
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Send agent status update with invalid status
        await wsHelper.sendMessage({
            type: 'agent_status',
            data: {
                agent_id: 'test-agent',
                status: 'invalid_status'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Verify error appears
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
        await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid agent status');
    });

    test('should handle invalid graph data', async ({ page, wsHelper }) => {
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Send graph update with invalid data
        await wsHelper.sendMessage({
            type: 'graph_update',
            data: {
                nodes: [
                    { invalid_field: 'value' } // Missing required id field
                ],
                edges: []
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Verify error appears
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
        await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid graph data');
    });
});
