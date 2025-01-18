import { type Page, expect } from '@playwright/test';

interface BaseMessage {
    timestamp: string;
    client_id: string;
    channel?: string;
}

interface LLMStreamMessage extends BaseMessage {
    type: 'llm_stream' | 'llm_analysis';
    data: {
        stream_id?: string;
        chunk?: string;
        is_final?: boolean;
        template_id?: string;
        template?: string;
        content?: string | { query: string; type: string };
        api_base?: string;
    };
}

interface AgentStatusMessage extends BaseMessage {
    type: 'agent_status';
    data: {
        agent_id: string;
        status: string;
    };
}

interface ChatMessage extends BaseMessage {
    type: 'chat_message';
    data: {
        content: string;
        agent_id?: string;
        message_type?: string;
        workspace?: string;
        pattern?: string;
        metadata?: {
            type?: string;
            agent_id?: string;
            domain?: string;
        };
    };
}

interface TaskMessage extends BaseMessage {
    type: 'task_update';
    data: {
        task_id: string;
        status: string;
        changes: {
            type?: string;
            priority?: string;
            progress?: number;
            result?: string;
            error?: string;
            error_details?: string;
            retry_count?: number;
        };
    };
}

interface ChannelMessage extends BaseMessage {
    type: 'join_channel' | 'leave_channel';
    data: {
        channel: string;
    };
}

interface AuthMessage extends BaseMessage {
    type: 'connect';
    data: {
        api_key: string;
    };
}

interface TeamMessage extends BaseMessage {
    type: 'agent_team_created';
    data: {
        team_type: string;
    };
}

interface DisconnectMessage extends BaseMessage {
    type: 'disconnect';
    data: Record<string, never>;
}

interface ConnectionMessage extends BaseMessage {
    type: 'connection_success';
    data: Record<string, never>;
}

type WebSocketMessage = 
    | LLMStreamMessage 
    | AgentStatusMessage 
    | ChatMessage 
    | TaskMessage 
    | ChannelMessage 
    | AuthMessage 
    | TeamMessage
    | DisconnectMessage
    | ConnectionMessage;

/**
 * Helper class to manage WebSocket interactions in e2e tests
 */
export class WebSocketTestHelper {
    private page: Page;
    private clientId: string;

    constructor(page: Page) {
        this.page = page;
        // Generate one client ID for the entire test session
        this.clientId = 'test-' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Wait for WebSocket connection to be established
     */
    async waitForConnection(apiKey = 'development', timeout = 10000) {
        try {
            // Add WebSocket code to the page
            const clientId = this.clientId;
            await this.page.addScriptTag({
                content: `
                    interface ExtendedWindow extends Window {
                        connectWebSocket?: (apiKey: string, timeout: number, clientId: string) => Promise<void>;
                        __testWebSocket?: WebSocket;
                    }
                    declare const window: ExtendedWindow;

                    window.connectWebSocket = (apiKey: string, timeout: number, clientId: string) => {
                        return new Promise((resolve, reject) => {
                            // Set up timeout using passed parameter
                            const timeoutId = setTimeout(() => {
                                reject(new Error('WebSocket connection timeout'));
                            }, timeout);

                            // Clean up any existing connection
                            if (window.__testWebSocket) {
                                window.__testWebSocket.close();
                                delete window.__testWebSocket;
                            }

                            const wsUrl = 'ws://localhost:8000/api/ws/debug/client_' + clientId;
                            const ws = new WebSocket(wsUrl);
                            
                            // Set up message handler first
                            ws.onmessage = (event) => {
                                try {
                                    const message = JSON.parse(event.data);
                                    console.log('Received message:', message);
                                    
                                    if (message.type === 'connection_established') {
                                        console.log('Received connection_established, sending auth');
                                        ws.send(JSON.stringify({
                                            type: 'connect',
                                            data: {
                                                api_key: apiKey
                                            },
                                            timestamp: new Date().toISOString(),
                                            client_id: clientId
                                        }));
                                    } else if (message.type === 'connection_success') {
                                        console.log('Authentication successful');
                                        clearTimeout(timeoutId);
                                        resolve();
                                    } else if (message.type === 'error') {
                                        console.error('WebSocket error:', message.data.message);
                                        clearTimeout(timeoutId);
                                        reject(new Error(message.data.message));
                                    }
                                    
                                    window.dispatchEvent(new CustomEvent('websocket-message', {
                                        detail: message
                                    }));
                                } catch (error) {
                                    console.error('Error processing message:', error);
                                    clearTimeout(timeoutId);
                                    reject(error);
                                }
                            };

                            // Then set up open handler and store WebSocket instance
                            ws.onopen = () => {
                                window.__testWebSocket = ws;
                                console.log('WebSocket connection opened');
                            };

                            ws.onerror = (error) => {
                                console.error('WebSocket error:', error);
                                //Emit a message indicating an error in the socket connection
                                window.dispatchEvent(new CustomEvent('websocket-status', {
                                    detail: {
                                        type: 'disconnect',
                                        data: {},
                                        timestamp: new Date().toISOString(),
                                        client_id: 'test',
                                        error: error.message
                                    }
                                }));
                                clearTimeout(timeoutId);
                                reject(error);
                            };

                            ws.onclose = () => {
                                window.dispatchEvent(new CustomEvent('websocket-status', {
                                    detail: {
                                        type: 'disconnect',
                                        data: {},
                                        timestamp: new Date().toISOString(),
                                        client_id: 'test'
                                    }
                                }));
                            };
                        });
                    };
                `
            });

            // Call the WebSocket connection function and wait for result
            await this.page.evaluate(({ apiKey, timeout, clientId }) => {
                interface ExtendedWindow extends Window {
                    connectWebSocket?: (apiKey: string, timeout: number, clientId: string) => Promise<void>;
                }
                const win = window as ExtendedWindow;
                return win.connectWebSocket?.(apiKey, timeout, clientId);
            }, { apiKey, timeout, clientId });
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            throw error;
        }
    }

    /**
     * Send a WebSocket message from the test
     */
    async sendMessage(message: WebSocketMessage) {
        await this.page.evaluate((msg) => {
            interface ExtendedWindow extends Window {
                __testWebSocket?: WebSocket;
            }
            const ws = (window as ExtendedWindow).__testWebSocket;
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify(msg));
            }
        }, message);
    }

    /**
     * Simulate a WebSocket connection status change
     */
    async setConnectionStatus(status: 'connected' | 'connecting' | 'error') {
        const clientId = this.clientId;
        await this.page.evaluate(({ newStatus, clientId }) => {
            return new Promise<void>((resolve) => {
                interface ExtendedWindow extends Window {
                    __testWebSocket?: WebSocket;
                }
                const ws = (window as ExtendedWindow).__testWebSocket;
                if (!ws) {
                    throw new Error('WebSocket not initialized');
                }

                if (newStatus === 'connecting') {
                    ws.close();
                    resolve();
                } else if (newStatus === 'connected') {
                    // Use the test session's client ID
                    const newWs = new WebSocket('ws://localhost:8000/api/ws/debug/client_' + clientId);
                    
                    newWs.onopen = () => {
                        (window as ExtendedWindow).__testWebSocket = newWs;
                        console.log('WebSocket connection opened');
                    };

                    newWs.onmessage = (event) => {
                        try {
                            const message = JSON.parse(event.data);
                            console.log('Received message:', message);
                            
                            if (message.type === 'connection_established') {
                                console.log('Received connection_established, sending auth');
                                newWs.send(JSON.stringify({
                                    type: 'connect',
                                    data: {
                                        api_key: 'valid-test-key'
                                    },
                                    timestamp: new Date().toISOString(),
                                            client_id: clientId
                                }));
                            } else if (message.type === 'connection_success') {
                                console.log('Authentication successful');
                                resolve();
                            } else if (message.type === 'error') {
                                console.error('WebSocket error:', message.data.message);
                                newWs.close();
                            }
                        } catch (error) {
                            console.error('Error processing message:', error);
                        }
                    };
                } else {
                    // Error state
                    ws.close();
                    resolve();
                }
            });
        }, { newStatus: status, clientId });

        // Wait for status to update in the UI
        if (status === 'connected') {
            await this.page.waitForSelector('[data-testid="connection-status"]', { state: 'visible' });
            await this.page.waitForFunction(
                (expectedStatus) => document.querySelector('[data-testid="connection-status"]')?.textContent === expectedStatus,
                status.charAt(0).toUpperCase() + status.slice(1),
                { timeout: 5000 }
            );
        }
    }

    /**
     * Simulate an agent status update
     */
    async updateAgentStatus(agentId: string, status: string) {
        await this.sendMessage({
            type: 'agent_status',
            data: {
                agent_id: agentId,
                status
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });
    }

    /**
     * Simulate an LLM stream message
     */
    async sendLLMStreamChunk(streamId: string, chunk: string, isFinal = false) {
        await this.sendMessage({
            type: 'llm_stream',
            data: {
                stream_id: streamId,
                chunk,
                is_final: isFinal,
                template_id: 'test'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });
    }

    /**
     * Simulate a task update
     */
    async updateTask(taskId: string, status: string, changes: TaskMessage['data']['changes'] = {}) {
        await this.sendMessage({
            type: 'task_update',
            data: {
                task_id: taskId,
                status,
                changes
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });
    }

    /**
     * Wait for a specific message type to be processed
     */
    async waitForMessage(type: string, timeout = 5000) {
        // Create promise to wait for message
        const messagePromise = this.page.evaluate((messageType) => {
            return new Promise<void>((resolve) => {
                interface ExtendedWindow extends Window {
                    __testWebSocket?: WebSocket;
                }
                const ws = (window as ExtendedWindow).__testWebSocket;
                if (!ws) {
                    throw new Error('WebSocket not initialized');
                }

                const handler = (event: MessageEvent) => {
                    const message = JSON.parse(event.data);
                    if (message.type === messageType) {
                        ws.removeEventListener('message', handler);
                        resolve();
                    }
                };
                ws.addEventListener('message', handler);
            });
        }, type);

        // Create timeout promise
        const timeoutPromise = new Promise<void>((_, reject) => {
            setTimeout(() => reject(new Error(`Timeout waiting for message type: ${type}`)), timeout);
        });

        // Wait for message or timeout
        await Promise.race([messagePromise, timeoutPromise]);

        // Allow time for the message to be processed
        await this.page.waitForTimeout(100);
    }

    /**
     * Simulate joining a channel
     */
    async joinChannel(channel: string) {
        await this.sendMessage({
            type: 'join_channel',
            data: {
                channel
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });
    }

    /**
     * Simulate leaving a channel
     */
    async leaveChannel(channel: string) {
        await this.sendMessage({
            type: 'leave_channel',
            data: {
                channel
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });
    }

    /**
     * Simulate authentication attempt
     */
    async authenticate(apiKey: string) {
        // Use waitForConnection which handles the full auth flow
        await this.waitForConnection(apiKey);

        // Wait for auth status to update in UI
        const expectedStatus = apiKey === 'valid-test-key' ? 'Authenticated' : 'Not Authenticated';
        await this.waitForAuthStatus(expectedStatus);

        // For invalid or expired keys, wait for error message
        if (apiKey === 'expired-key') {
            await this.page.waitForSelector('[data-testid="error-message"]', { state: 'visible', timeout: 5000 });
            await expect(this.page.locator('[data-testid="error-message"]')).toContainText('Token expired');
        } else if (apiKey === 'invalid-key') {
            await this.page.waitForSelector('[data-testid="error-message"]', { state: 'visible', timeout: 5000 });
            await expect(this.page.locator('[data-testid="error-message"]')).toContainText('Invalid API key');
        }
    }

    /**
     * Wait for authentication status
     */
    async waitForAuthStatus(expectedStatus: 'Authenticated' | 'Not Authenticated', timeout = 10000) {
        // Create promise to wait for auth status
        const statusPromise = this.page.evaluate((status) => {
            return new Promise<void>((resolve) => {
                const checkStatus = () => {
                    const authStatus = document.querySelector('[data-testid="auth-status"]')?.textContent;
                    if (authStatus === status) {
                        resolve();
                    } else {
                        requestAnimationFrame(checkStatus);
                    }
                };
                checkStatus();
            });
        }, expectedStatus);

        // Create timeout promise
        const timeoutPromise = new Promise<void>((_, reject) => {
            setTimeout(() => reject(new Error(`Timeout waiting for auth status: ${expectedStatus}`)), timeout);
        });

        // Wait for status or timeout
        await Promise.race([statusPromise, timeoutPromise]);
    }

    /**
     * List available agents for direct messaging
     */
    async listAgents() {
        await this.sendMessage({
            type: 'agent_team_created',
            data: {
                team_type: 'direct_message'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });
        await this.waitForMessage('agent_team_created');
    }

    /**
     * Send a direct message to an agent
     */
    async sendDirectMessage(agentId: string, content: string) {
        await this.sendMessage({
            type: 'chat_message',
            data: {
                content,
                agent_id: agentId,
                message_type: 'direct'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        });
    }

    /**
     * Wait for belief agent's analysis
     */
    async waitForBeliefAnalysis() {
        await this.waitForMessage('chat_message');
        await this.page.locator('[data-testid="belief-analysis"]').waitFor({ state: 'visible' });
        await this.page.locator('[data-testid="evidence"]').waitFor({ state: 'visible' });
        await this.page.locator('[data-testid="confidence-level"]').waitFor({ state: 'visible' });
    }

    /**
     * Wait for agent's emotional state
     */
    async waitForEmotionalState() {
        await this.waitForMessage('chat_message');
        await this.page.locator('[data-testid="agent-emotions"]').waitFor({ state: 'visible' });
        await this.page.locator('[data-testid="agent-goals"]').waitFor({ state: 'visible' });
    }

    async cleanup() {
        try {
            // First try to close any existing connection
            await this.page.evaluate(() => {
                interface ExtendedWindow extends Window {
                    __testWebSocket?: WebSocket;
                }
                const ws = (window as ExtendedWindow).__testWebSocket;
                if (ws) {
                    if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
                        ws.close();
                    }
                    delete (window as ExtendedWindow).__testWebSocket;
                }
                window.dispatchEvent(new Event('websocket-cleanup'));
            }).catch(error => {
                console.error('Error during WebSocket cleanup:', error);
            });
        } catch (error) {
            console.error('Error during WebSocket cleanup:', error);
        } finally {
            // Ensure we always try to clean up the page context
            try {
                await this.page.evaluate(() => {
                    interface ExtendedWindow extends Window {
                        __testWebSocket?: WebSocket;
                    }
                    delete (window as ExtendedWindow).__testWebSocket;
                });
            } catch (error) {
                console.error('Error during final cleanup:', error);
            }
        }
    }
}
