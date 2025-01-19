import { test as base, expect } from '@playwright/test';
import { WebSocketTestHelper } from '../test-helpers/websocket';

export type WebSocketFixtures = {
    wsHelper: WebSocketTestHelper;
};

export const test = base.extend<WebSocketFixtures>({
    wsHelper: async ({ page }, use) => {
        // Create a new WebSocket helper
        const wsHelper = new WebSocketTestHelper(page);

        try {
            // Initialize WebSocket code and ensure clean initial state
            await wsHelper.initialize();
            
            // Wait for initial not authenticated state
            await wsHelper.waitForAuthStatus('Not Authenticated', 30000);

            // Use the helper in the test
            await use(wsHelper);
        } catch (error) {
            console.error('Error in WebSocket test:', error);
            throw error;
        } finally {
            try {
                // Always attempt cleanup and verify clean state
                if (wsHelper && !page.isClosed()) {
                    await wsHelper.cleanup();
                    await wsHelper.waitForAuthStatus('Not Authenticated', 30000);
                }
            } catch (cleanupError) {
                console.error('Error during cleanup:', cleanupError);
                // Even if cleanup fails, try to force a clean state
                if (!page.isClosed()) {
                    await wsHelper?.setConnectionStatus('error');
                    await wsHelper?.waitForAuthStatus('Not Authenticated', 30000);
                }
            }
        }
    },
});

export { expect };
