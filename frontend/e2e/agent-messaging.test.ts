import { test, expect } from './fixtures/websocket';

test.describe('Agent Messaging', () => {

    test('should handle direct messages between agents', async ({ page, wsHelper }) => {

        // Wait for agents to be loaded
        await expect(page.locator('[data-testid="agent-list"]')).toBeVisible();

        // Get list of available agents
        const agents = await page.locator('[data-testid="agent-item"]').all();
        expect(agents.length).toBeGreaterThan(0);

        // Send a test message
        const testMessage = 'Hello from e2e test';
        await page.fill('[data-testid="message-input"]', testMessage);
        await page.click('[data-testid="send-button"]');

        // Verify message appears in chat
        await expect(page.locator(`[data-testid="message-content"]:has-text("${testMessage}")`)).toBeVisible();

        // Simulate agent response via LLM stream
        const streamId = 'test-response';
        await wsHelper.sendLLMStreamChunk(streamId, 'Hello! I received your message.');
        await wsHelper.sendLLMStreamChunk(streamId, ' How can I help you today?', true);

        // Verify agent response
        await expect(page.locator('[data-testid="agent-message"]')).toBeVisible();
        await expect(page.locator('[data-testid="agent-message"]')).toContainText('Hello! I received your message. How can I help you today?');

        // Verify connection remains stable
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');
    });

    test('should handle connection status changes', async ({ page, wsHelper }) => {
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Test connection state transitions
        await wsHelper.setConnectionStatus('error');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Error');

        await wsHelper.setConnectionStatus('connecting');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connecting');

        await wsHelper.setConnectionStatus('connected');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');
    });

    test('should handle agent status updates', async ({ page, wsHelper }) => {
        await expect(page.locator('[data-testid="agent-list"]')).toBeVisible();

        // Get initial active agents count
        const initialActiveAgents = await page.locator('[data-testid="agent-item"][data-status="active"]').count();

        // Test agent status transitions
        await wsHelper.updateAgentStatus('test-agent', 'active');
        await expect(page.locator('[data-testid="agent-item"][data-agent-id="test-agent"]')).toHaveAttribute('data-status', 'active');

        await wsHelper.updateAgentStatus('test-agent', 'busy');
        await expect(page.locator('[data-testid="agent-item"][data-agent-id="test-agent"]')).toHaveAttribute('data-status', 'busy');

        // Verify active agents count updated
        const updatedActiveAgents = await page.locator('[data-testid="agent-item"][data-status="active"]').count();
        expect(updatedActiveAgents).toBe(initialActiveAgents);
    });

    test('should handle task updates', async ({ page, wsHelper }) => {

        // Create a test task
        const taskId = 'test-task';
        await wsHelper.updateTask(taskId, 'created', {
            title: 'Test Task',
            description: 'This is a test task'
        });

        // Verify task appears in list
        await expect(page.locator(`[data-testid="task-item"][data-task-id="${taskId}"]`)).toBeVisible();
        await expect(page.locator(`[data-testid="task-item"][data-task-id="${taskId}"]`)).toContainText('Test Task');

        // Update task status
        await wsHelper.updateTask(taskId, 'in_progress');
        await expect(page.locator(`[data-testid="task-item"][data-task-id="${taskId}"]`)).toHaveAttribute('data-status', 'in_progress');

        await wsHelper.updateTask(taskId, 'completed');
        await expect(page.locator(`[data-testid="task-item"][data-task-id="${taskId}"]`)).toHaveAttribute('data-status', 'completed');
    });
});
