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
            // Set up test
            await page.goto('/');  // Use baseURL from playwright config
            await page.waitForLoadState('networkidle');
            await wsHelper.waitForConnection();
            await wsHelper.setConnectionStatus('connected');

            // Use the helper in the test
            await use(wsHelper);
        } catch (error) {
            console.error('Error in WebSocket test:', error);
            throw error;
        } finally {
            try {
                // Always attempt cleanup
                if (wsHelper) {
                    await wsHelper.cleanup();
                }
            } catch (cleanupError) {
                console.error('Error during cleanup:', cleanupError);
            }
        }
    }
});

// Export expect from playwright
export { expect } from '@playwright/test';
