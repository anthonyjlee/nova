import { test, expect } from './fixtures/websocket';
import type { 
    AgentType,
    AgentStatusType,
    WebSocketMessage
} from '../src/lib/schemas/websocket';

test.describe('WebSocket Direct Messaging', () => {
    test.beforeEach(async ({ wsHelper }) => {
        // Initialize with clean state
        await wsHelper.initialize();
        await wsHelper.waitForAuthStatus('Not Authenticated');
    });

    test.afterEach(async ({ wsHelper }) => {
        // Clean up and verify state reset
        await wsHelper.cleanup();
        await wsHelper.waitForAuthStatus('Not Authenticated');
    });

    test('should handle successful connection', async ({ page, wsHelper }) => {
        // Set connecting status
        await wsHelper.setConnectionStatus('connecting');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connecting');

        // Set connected status
        await wsHelper.setConnectionStatus('connected');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Authenticate
        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');
    });

    test('should handle agent status changes while maintaining auth', async ({ page, wsHelper }) => {
        // Set connecting status
        await wsHelper.setConnectionStatus('connecting');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connecting');

        // Set connected status
        await wsHelper.setConnectionStatus('connected');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Authenticate
        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');

        // Send agent status updates
        const statusMessage: WebSocketMessage = {
            type: 'agent_status',
            data: {
                agent_id: 'test_agent',
                status: 'active' as AgentStatusType
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        };
        await wsHelper.sendMessage(statusMessage);

        // Verify auth status maintained after agent updates
        await wsHelper.waitForAuthStatus('Authenticated');
    });

    test('should list core agents in NovaTeam channel', async ({ page, wsHelper }) => {
        // Set connecting status
        await wsHelper.setConnectionStatus('connecting');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connecting');

        // Set connected status
        await wsHelper.setConnectionStatus('connected');
        await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

        // Authenticate
        await wsHelper.authenticate('valid-test-key');
        await wsHelper.waitForAuthStatus('Authenticated');

        // Join NovaTeam channel
        await wsHelper.joinChannel('NovaTeam');

        // Create core agent team
        const message: WebSocketMessage = {
            type: 'agent_team_created',
            data: {
                agents: [
                    {
                        id: 'meta_agent_1',
                        name: 'Meta Agent',
                        type: 'meta' as AgentType,
                        status: 'active' as AgentStatusType,
                        domain: 'professional'
                    },
                    {
                        id: 'orchestration_agent_1',
                        name: 'Orchestration Agent',
                        type: 'orchestration' as AgentType,
                        status: 'active' as AgentStatusType,
                        domain: 'professional'
                    },
                    {
                        id: 'coordination_agent_1',
                        name: 'Coordination Agent',
                        type: 'coordination' as AgentType,
                        status: 'active' as AgentStatusType,
                        domain: 'professional'
                    }
                ],
                team_type: 'core'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test',
            channel: 'NovaTeam'
        };
        await wsHelper.sendMessage(message);

        // Wait for agent elements to be created
        await page.waitForSelector('[data-testid="agent-meta_agent_1"]');
        await page.waitForSelector('[data-testid="agent-orchestration_agent_1"]');
        await page.waitForSelector('[data-testid="agent-coordination_agent_1"]');

        // Verify core agents are listed
        await expect(page.locator('[data-testid="agent-meta_agent_1"]')).toBeVisible();
        await expect(page.locator('[data-testid="agent-orchestration_agent_1"]')).toBeVisible();
        await expect(page.locator('[data-testid="agent-coordination_agent_1"]')).toBeVisible();
    });
});
