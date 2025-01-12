import { expect, test } from '@playwright/test';

test.describe('Task Management System', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/tasks');
    });

    test('shows task board with all columns', async ({ page }) => {
        // Check column headers
        await expect(page.getByText('Pending')).toBeVisible();
        await expect(page.getByText('In Progress')).toBeVisible();
        await expect(page.getByText('Blocked')).toBeVisible();
        await expect(page.getByText('Completed')).toBeVisible();
    });

    test('handles task state transitions', async ({ page }) => {
        // Wait for board to load
        await expect(page.getByTestId('column')).toHaveCount(4);

        // Find a task in Pending
        const pendingTask = page.locator('[data-testid="column"]').first().locator('[draggable="true"]').first();
        const taskId = await pendingTask.getAttribute('data-task-id');
        
        // Drag to In Progress
        const inProgressColumn = page.locator('[data-testid="column"]').nth(1);
        await pendingTask.dragTo(inProgressColumn);

        // Verify task moved
        await expect(inProgressColumn.locator(`[data-task-id="${taskId}"]`)).toBeVisible();
    });

    test('shows initialization states correctly', async ({ page }) => {
        // Force uninitialized state
        await page.route('/api/system/status', async (route) => {
            await route.fulfill({
                status: 200,
                body: JSON.stringify({ initialization: 'uninitialized' })
            });
        });

        await page.reload();

        // Check initialization message
        await expect(page.getByText('System needs initialization')).toBeVisible();

        // Click retry and verify success
        await page.route('/api/system/initialize', async (route) => {
            await route.fulfill({
                status: 200,
                body: JSON.stringify({ initialization: 'initialized' })
            });
        });

        await page.getByRole('button', { name: 'Retry' }).click();
        await expect(page.getByText('System needs initialization')).not.toBeVisible();
    });

    test('handles error states appropriately', async ({ page }) => {
        // Force error state
        await page.route('/api/tasks/board', async (route) => {
            await route.fulfill({ status: 500 });
        });

        await page.reload();

        // Verify error message
        await expect(page.getByText('Failed to fetch task board')).toBeVisible();
    });

    test('enforces domain access controls', async ({ page }) => {
        // Try to move task to unauthorized domain
        await page.route('/api/tasks/*/transition', async (route) => {
            await route.fulfill({
                status: 403,
                body: JSON.stringify({
                    detail: 'Domain access denied: Insufficient permissions'
                })
            });
        });

        const task = page.locator('[data-testid="column"]').first().locator('[draggable="true"]').first();
        const targetColumn = page.locator('[data-testid="column"]').nth(1);
        await task.dragTo(targetColumn);

        // Verify error message
        await expect(page.getByText('Domain access denied: Insufficient permissions')).toBeVisible();
    });

    test('preserves task state during page navigation', async ({ page }) => {
        // Get initial task state
        const taskId = await page.locator('[data-testid="column"]')
            .first()
            .locator('[draggable="true"]')
            .first()
            .getAttribute('data-task-id');

        // Navigate away and back
        await page.goto('/agents');
        await page.goto('/tasks');

        // Verify task position preserved
        await expect(page.locator(`[data-task-id="${taskId}"]`)).toBeVisible();
    });
});
