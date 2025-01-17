import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';

test.describe('WebSocket LLM Integration', () => {
    let page: Page;

    test.beforeEach(async ({ browser }) => {
        page = await browser.newPage();
        await page.goto('http://localhost:5173/llm');
    });

    test('should connect to websocket and stream LLM response', async () => {
        // Wait for WebSocket connection
        await page.waitForSelector('[data-testid="ws-status-connected"]');

        // Send LLM request
        await page.fill('[data-testid="llm-input"]', 'Test query');
        await page.selectOption('[data-testid="template-select"]', 'parsing_analysis');
        await page.click('[data-testid="send-button"]');

        // Verify streaming chunks appear
        const chunkElements = await page.$$('[data-testid="llm-chunk"]');
        expect(chunkElements.length).toBeGreaterThan(5); // Should have multiple chunks

        // Get chunk contents
        const chunks = await Promise.all(
            chunkElements.map(async el => {
                const text = await el.textContent();
                return text || '';
            })
        );
        expect(chunks.some(text => text.length > 0)).toBeTruthy();

        // Wait for final response
        await page.waitForSelector('[data-testid="llm-complete"]');
        const response = await page.textContent('[data-testid="llm-response"]') || '';
        expect(response.length).toBeGreaterThan(0);
    });

    test('should handle invalid template error', async () => {
        await page.waitForSelector('[data-testid="ws-status-connected"]');

        // Try invalid template
        await page.fill('[data-testid="llm-input"]', 'Test query');
        await page.selectOption('[data-testid="template-select"]', 'invalid_template');
        await page.click('[data-testid="send-button"]');

        // Verify error message
        await page.waitForSelector('[data-testid="error-message"]');
        const error = await page.textContent('[data-testid="error-message"]') || '';
        expect(error.toLowerCase()).toContain('template not found');
    });

    test('should handle connection error', async () => {
        await page.waitForSelector('[data-testid="ws-status-connected"]');

        // Simulate connection error by using wrong port
        await page.evaluate(() => {
            window.localStorage.setItem('llm_api_base', 'http://localhost:9999/v1');
        });

        // Send request
        await page.fill('[data-testid="llm-input"]', 'Test query');
        await page.selectOption('[data-testid="template-select"]', 'parsing_analysis');
        await page.click('[data-testid="send-button"]');

        // Verify error message
        await page.waitForSelector('[data-testid="error-message"]');
        const error = await page.textContent('[data-testid="error-message"]') || '';
        expect(error.toLowerCase()).toContain('failed to connect');

        // Reset API base
        await page.evaluate(() => {
            window.localStorage.setItem('llm_api_base', 'http://localhost:1234/v1');
        });
    });

    test('should maintain stable connection during streaming', async () => {
        await page.waitForSelector('[data-testid="ws-status-connected"]');

        // Send long query
        await page.fill('[data-testid="llm-input"]', 'Very long query requiring extensive processing');
        await page.selectOption('[data-testid="template-select"]', 'analytics_processing');
        await page.click('[data-testid="send-button"]');

        // Monitor chunks over time
        const startTime = Date.now();
        const seenChunks = new Set<string>();
        
        while (Date.now() - startTime < 5000) { // Monitor for 5 seconds
            const newChunks = await page.$$('[data-testid="llm-chunk"]');
            for (const chunk of newChunks) {
                const text = await chunk.textContent();
                if (text) {
                    seenChunks.add(text);
                }
            }
            await page.waitForTimeout(100);
        }

        // Verify stable streaming
        expect(seenChunks.size).toBeGreaterThan(5);
        
        // Verify completion
        await page.waitForSelector('[data-testid="llm-complete"]');
        expect(await page.isVisible('[data-testid="ws-status-connected"]')).toBeTruthy();
    });
});
