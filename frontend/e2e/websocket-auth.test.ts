import { test } from './fixtures/websocket';

test.describe('WebSocket Authentication', () => {
    test('should start in not authenticated state', async ({ wsHelper }) => {
        await wsHelper.waitForAuthStatus('Not Authenticated');
    });

    test('should handle successful authentication', async ({ wsHelper }) => {
        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');
    });

    test('should handle authentication failure', async ({ wsHelper }) => {
        await wsHelper.authenticate('invalid-key');
        await wsHelper.waitForErrorMessage('Invalid API key');
        await wsHelper.waitForAuthStatus('Not Authenticated');
    });

    test('should handle reconnection with auth', async ({ wsHelper }) => {
        // Initial connection failure
        await wsHelper.setConnectionStatus('error');
        await wsHelper.simulateError('Connection failed');
        await wsHelper.waitForErrorMessage('Connection failed');
        await wsHelper.waitForAuthStatus('Not Authenticated');

        // First reconnection attempt
        await wsHelper.setConnectionStatus('connecting');
        await wsHelper.waitForReconnectInfo(1);

        // Second reconnection attempt
        await wsHelper.setConnectionStatus('connecting');
        await wsHelper.waitForReconnectInfo(2);

        // Successful reconnection
        await wsHelper.setConnectionStatus('connected');
        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');
    });

    test('should handle expired auth token', async ({ wsHelper }) => {
        await wsHelper.authenticate('expired-key');
        await wsHelper.waitForAuthStatus('Not Authenticated');
        await wsHelper.waitForErrorMessage('Token expired');

        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');
    });

    test('should handle connection errors with backoff', async ({ wsHelper }) => {
        // Initial error
        await wsHelper.setConnectionStatus('error');
        await wsHelper.simulateError('Network error');
        await wsHelper.waitForErrorMessage('Network error');

        // Multiple reconnection attempts
        for (let i = 1; i <= 3; i++) {
            await wsHelper.setConnectionStatus('connecting');
            await wsHelper.waitForReconnectInfo(i);
            await wsHelper.setConnectionStatus('error');
            await wsHelper.simulateError(`Attempt ${i} failed`);
            await wsHelper.waitForErrorMessage(`Attempt ${i} failed`);
        }

        // Successful reconnection
        await wsHelper.setConnectionStatus('connected');
        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');
    });

    test('should reset to not authenticated state after cleanup', async ({ wsHelper }) => {
        // First authenticate
        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');

        // Then cleanup and verify reset
        await wsHelper.cleanup();
        await wsHelper.waitForAuthStatus('Not Authenticated');
    });
});
