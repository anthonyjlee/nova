import { test as base } from '@playwright/test';
import { WebSocketTestHelper } from '../test-helpers/websocket';

// Declare the fixture type
type WebSocketFixture = {
    wsHelper: WebSocketTestHelper;
};

// Create a test fixture that includes the WebSocket helper
export const test = base.extend<WebSocketFixture>({
    wsHelper: async ({ page }, use) => {
        // Create a new WebSocket helper
        const wsHelper = new WebSocketTestHelper(page);

        try {
            // Initialize WebSocket code and ensure clean initial state
            await wsHelper.initialize();
            
            // Wait for initial not authenticated state
            await wsHelper.waitForAuthStatus('Not Authenticated');

            // Use the helper in the test
            await use(wsHelper);
        } catch (error) {
            console.error('Error in WebSocket test:', error);
            throw error;
        } finally {
            try {
                // Always attempt cleanup and verify clean state
                if (wsHelper) {
                    await wsHelper.cleanup();
                    await wsHelper.waitForAuthStatus('Not Authenticated');
                }
            } catch (cleanupError) {
                console.error('Error during cleanup:', cleanupError);
                // Even if cleanup fails, try to force a clean state
                await wsHelper?.setConnectionStatus('error');
                await wsHelper?.waitForAuthStatus('Not Authenticated');
            }
        }
    }
});

// Export expect from playwright
export { expect } from '@playwright/test';
