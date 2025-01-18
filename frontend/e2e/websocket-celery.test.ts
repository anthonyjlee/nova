import { test, expect } from './fixtures/websocket';

test.describe('WebSocket Celery Integration', () => {
    test('should handle task creation and updates', async ({ page, wsHelper }) => {
        await wsHelper.waitForConnection();
        await wsHelper.authenticate('test-key');

        // Create task
        await wsHelper.updateTask('test-task', 'pending', {
            type: 'analysis',
            priority: 'high'
        });

        // Verify task creation
        await wsHelper.waitForMessage('task_update');
        await expect(page.locator('[data-testid="task-status"]')).toHaveText('pending');
        await expect(page.locator('[data-testid="task-priority"]')).toHaveText('high');

        // Update task status
        await wsHelper.updateTask('test-task', 'in_progress', {
            progress: 0.5
        });

        // Verify task update
        await wsHelper.waitForMessage('task_update');
        await expect(page.locator('[data-testid="task-status"]')).toHaveText('in_progress');
        await expect(page.locator('[data-testid="task-progress"]')).toHaveText('50%');

        // Complete task
        await wsHelper.updateTask('test-task', 'completed', {
            result: 'Analysis complete',
            progress: 1.0
        });

        // Verify task completion
        await wsHelper.waitForMessage('task_update');
        await expect(page.locator('[data-testid="task-status"]')).toHaveText('completed');
        await expect(page.locator('[data-testid="task-progress"]')).toHaveText('100%');
        await expect(page.locator('[data-testid="task-result"]')).toContainText('Analysis complete');
    });

    test('should handle task error states', async ({ page, wsHelper }) => {
        await wsHelper.waitForConnection();
        await wsHelper.authenticate('test-key');

        // Create task that will fail
        await wsHelper.updateTask('error-task', 'pending', {
            type: 'analysis',
            priority: 'high'
        });

        // Verify task creation
        await wsHelper.waitForMessage('task_update');
        await expect(page.locator('[data-testid="task-status"]')).toHaveText('pending');

        // Task fails
        await wsHelper.updateTask('error-task', 'error', {
            error: 'Analysis failed',
            error_details: 'Connection timeout'
        });

        // Verify error state
        await wsHelper.waitForMessage('task_update');
        await expect(page.locator('[data-testid="task-status"]')).toHaveText('error');
        await expect(page.locator('[data-testid="task-error"]')).toContainText('Analysis failed');
        await expect(page.locator('[data-testid="task-error-details"]')).toContainText('Connection timeout');
    });

    test('should handle task retry', async ({ page, wsHelper }) => {
        await wsHelper.waitForConnection();
        await wsHelper.authenticate('test-key');

        // Create task
        await wsHelper.updateTask('retry-task', 'pending', {
            type: 'analysis',
            priority: 'high'
        });

        // Task fails first attempt
        await wsHelper.updateTask('retry-task', 'error', {
            error: 'Temporary failure',
            retry_count: 1
        });

        // Verify retry state
        await wsHelper.waitForMessage('task_update');
        await expect(page.locator('[data-testid="task-status"]')).toHaveText('error');
        await expect(page.locator('[data-testid="retry-count"]')).toHaveText('1');

        // Task succeeds on retry
        await wsHelper.updateTask('retry-task', 'completed', {
            result: 'Analysis complete after retry',
            retry_count: 2
        });

        // Verify successful retry
        await wsHelper.waitForMessage('task_update');
        await expect(page.locator('[data-testid="task-status"]')).toHaveText('completed');
        await expect(page.locator('[data-testid="retry-count"]')).toHaveText('2');
        await expect(page.locator('[data-testid="task-result"]')).toContainText('Analysis complete after retry');
    });
});
