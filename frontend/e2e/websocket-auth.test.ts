import { test, expect } from './fixtures/websocket';

test.describe('WebSocket Authentication', () => {
    test('should handle successful authentication', async ({ wsHelper }) => {
        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');
    });

    test('should handle authentication failure', async ({ page, wsHelper }) => {
        await wsHelper.authenticate('invalid-key');
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
        await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid API key');
        await wsHelper.waitForAuthStatus('Not Authenticated');
    });

    test('should handle reconnection with auth', async ({ page, wsHelper }) => {
        await wsHelper.setConnectionStatus('connecting');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connecting');
        await wsHelper.waitForAuthStatus('Not Authenticated');

        await wsHelper.setConnectionStatus('connected');
        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');
    });

    test('should handle expired auth token', async ({ page, wsHelper }) => {
        await wsHelper.authenticate('expired-key');
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
        await expect(page.locator('[data-testid="error-message"]')).toContainText('Token expired');
        await wsHelper.waitForAuthStatus('Not Authenticated');

        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');
    });

});
