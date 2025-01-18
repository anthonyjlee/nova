import { test, expect } from './fixtures/websocket';

test.describe('WebSocket Message Flow', () => {
    test('should handle connection lifecycle', async ({ page, wsHelper }) => {
        // Initial connection should be established by fixture
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Test disconnection
        await wsHelper.sendMessage({
            type: 'disconnect',
            data: {},
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connecting');

        // Test reconnection
        await wsHelper.sendMessage({
            type: 'connection_success',
            data: {},
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');
    });

    test('should handle channel operations', async ({ page, wsHelper }) => {
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Join channel
        await wsHelper.sendMessage({
            type: 'join_channel',
            data: {
                channel: 'NovaTeam'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Send message to channel
        await wsHelper.sendMessage({
            type: 'chat_message',
            data: {
                content: 'Channel message',
                thread_id: 'test-thread',
                workspace: 'test'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test',
            channel: 'NovaTeam'
        });

        // Verify message appears
        await expect(page.locator('[data-testid="message-content"]')).toContainText('Channel message');

        // Leave channel
        await wsHelper.sendMessage({
            type: 'leave_channel',
            data: {
                channel: 'NovaTeam'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });
    });

    test('should handle task updates', async ({ page, wsHelper }) => {
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Create task
        await wsHelper.sendMessage({
            type: 'task_update',
            data: {
                task_id: 'test-task',
                status: 'created',
                changes: {
                    workspace: 'test',
                    domain: 'analysis'
                }
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Verify task appears
        await expect(page.locator('[data-testid="task-item"][data-task-id="test-task"]')).toBeVisible();

        // Update task status
        await wsHelper.sendMessage({
            type: 'task_update',
            data: {
                task_id: 'test-task',
                status: 'in_progress',
                changes: {}
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Verify status update
        await expect(page.locator('[data-testid="task-item"][data-task-id="test-task"]'))
            .toHaveAttribute('data-status', 'in_progress');

        // Complete task
        await wsHelper.sendMessage({
            type: 'task_update',
            data: {
                task_id: 'test-task',
                status: 'completed',
                changes: {
                    result: 'Task completed successfully'
                }
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Verify completion
        await expect(page.locator('[data-testid="task-item"][data-task-id="test-task"]'))
            .toHaveAttribute('data-status', 'completed');
    });

    test('should handle graph updates', async ({ page, wsHelper }) => {
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Send graph update
        await wsHelper.sendMessage({
            type: 'graph_update',
            data: {
                nodes: [
                    { id: 'node1', label: 'Node 1' },
                    { id: 'node2', label: 'Node 2' }
                ],
                edges: [
                    { source: 'node1', target: 'node2', label: 'connects to' }
                ]
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });

        // Verify graph elements
        await expect(page.locator('[data-testid="graph-node"][data-node-id="node1"]')).toBeVisible();
        await expect(page.locator('[data-testid="graph-node"][data-node-id="node2"]')).toBeVisible();
        await expect(page.locator('[data-testid="graph-edge"][data-source="node1"][data-target="node2"]')).toBeVisible();
    });
});
