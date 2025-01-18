import { type Page } from '@playwright/test';
import type { WebSocketMessage } from '../../src/lib/schemas/websocket';

/**
 * Helper class to manage WebSocket interactions in e2e tests
 * Uses the main app's WebSocket store and event handlers
 */
export class WebSocketTestHelper {
    private page: Page;
    private clientId: string;

    constructor(page: Page) {
        this.page = page;
        this.clientId = 'test-' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Initialize WebSocket code in the browser context
     */
    public async initialize() {
        try {
            // Navigate to the app and wait for it to be ready
            await this.page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
            await this.page.waitForSelector('[data-testid="connection-status"]', { timeout: 30000 });
            
            // Mock threads API
            await this.page.route('**/api/chat/threads', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        threads: [],
                        total: 0,
                        timestamp: new Date().toISOString()
                    })
                });
            });

            // Initial auth status
            await this.page.evaluate(() => {
                window.dispatchEvent(new CustomEvent('websocket-message', {
                    detail: {
                        type: 'auth_status',
                        data: {
                            status: 'not_authenticated'
                        },
                        timestamp: new Date().toISOString(),
                        client_id: 'test'
                    }
                }));
            });

            // Wait for auth status to update
            await this.page.waitForFunction(
                () => {
                    const element = document.querySelector('[data-testid="auth-status"]');
                    return element && element.textContent === 'Not Authenticated';
                },
                { timeout: 30000 }
            );
        } catch (error) {
            console.error('Error during initialization:', error);
            throw error;
        }
    }

    /**
     * Wait for WebSocket connection
     */
    async waitForConnection(timeout = 5000) {
        await this.page.waitForSelector('[data-testid="connection-status"]', { timeout });
        await this.page.waitForFunction(
            () => {
                const element = document.querySelector('[data-testid="connection-status"]');
                return element && element.textContent === 'Connected';
            },
            { timeout }
        );
    }

    /**
     * Set connection status
     */
    async setConnectionStatus(status: 'connected' | 'connecting' | 'error', domain: string = 'personal') {
        if (status === 'connecting') {
            // Send connecting status
            const message = {
                type: 'connecting',
                data: {
                    message: 'Connecting to WebSocket server',
                    status: 'connecting',
                    domain: domain,
                    connection_type: 'chat'
                },
                timestamp: new Date().toISOString(),
                client_id: 'test'
            };
            await this.page.evaluate((msg) => {
                window.dispatchEvent(new CustomEvent('websocket-status', { detail: msg }));
            }, message);
        } else if (status === 'error') {
            // Send error message
            const message = {
                type: 'error',
                data: {
                    message: 'Connection error',
                    status: 'error',
                    domain: domain,
                    code: 1011
                },
                timestamp: new Date().toISOString(),
                client_id: 'test'
            };
            await this.page.evaluate((msg) => {
                window.dispatchEvent(new CustomEvent('websocket-status', { detail: msg }));
            }, message);
        } else {
            // Send connection established first
            const message = {
                type: 'connection_success',
                data: {
                    message: 'WebSocket connection established',
                    status: 'connected',
                    domain: domain,
                    connection_type: 'chat'
                },
                timestamp: new Date().toISOString(),
                client_id: 'test'
            };
            await this.page.evaluate((msg) => {
                window.dispatchEvent(new CustomEvent('websocket-status', { detail: msg }));
            }, message);
        }

        // Wait for status to update in UI
        const expectedStatus = status.charAt(0).toUpperCase() + status.slice(1);
        await this.page.waitForSelector('[data-testid="connection-status"]');
        await this.page.waitForFunction(
            (expected: string) => {
                const element = document.querySelector('[data-testid="connection-status"]');
                return element && element.textContent === expected;
            },
            expectedStatus,
            { timeout: 5000 }
        );
    }

    /**
     * Authenticate with the WebSocket server
     */
    async authenticate(apiKey: string, domain: string = 'personal') {
        // Initial connection with API key
        const message = {
            type: 'connect',
            data: {
                api_key: apiKey,
                connection_type: 'chat',
                domain: domain,
                workspace: domain
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        };
        await this.page.evaluate((msg) => {
            window.dispatchEvent(new CustomEvent('websocket-message', { detail: msg }));
        }, message);

        if (apiKey === 'valid-test-key') {
            // Message delivery confirmation
            const deliveryMessage = {
                type: 'message_delivered',
                data: {
                    message: 'Authentication request received',
                    original_type: 'connect',
                    status: 'success'
                },
                timestamp: new Date().toISOString(),
                client_id: 'test'
            };
            await this.page.evaluate((msg) => {
                window.dispatchEvent(new CustomEvent('websocket-message', { detail: msg }));
            }, deliveryMessage);

            // Auth status update
            const authMessage = {
                type: 'auth_status',
                data: {
                    status: 'authenticated',
                    domain: domain,
                    workspace: domain
                },
                timestamp: new Date().toISOString(),
                client_id: 'test'
            };
            await this.page.evaluate((msg) => {
                window.dispatchEvent(new CustomEvent('websocket-message', { detail: msg }));
            }, authMessage);

            // Wait for auth status to update
            await this.page.waitForFunction(
            () => {
                const element = document.querySelector('[data-testid="auth-status"]');
                return element && element.textContent === 'Authenticated';
            },
            { timeout: 5000 }
            );

            // Mock threads response
            await this.page.route('**/api/chat/threads', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        threads: [],
                        total: 0,
                        domain: domain,
                        workspace: domain,
                        timestamp: new Date().toISOString()
                    })
                });
            });
        } else {
            // Message delivery with error
            const errorDeliveryMessage = {
                type: 'message_delivered',
                data: {
                    message: 'Authentication failed',
                    original_type: 'connect',
                    status: 'error',
                    error: {
                        message: 'Invalid API key',
                        error_type: 'invalid_key',
                        code: 403
                    }
                },
                timestamp: new Date().toISOString(),
                client_id: 'test'
            };
            await this.page.evaluate((msg) => {
                window.dispatchEvent(new CustomEvent('websocket-message', { detail: msg }));
            }, errorDeliveryMessage);

            // Error status
            const errorMessage = {
                type: 'error',
                data: {
                    message: 'Invalid API key',
                    status: 'error',
                    error_type: 'invalid_key',
                    code: 403,
                    domain: domain
                },
                timestamp: new Date().toISOString(),
                client_id: 'test'
            };
            await this.page.evaluate((msg) => {
                window.dispatchEvent(new CustomEvent('websocket-message', { detail: msg }));
            }, errorMessage);

            // Auth status update
            const authMessage = {
                type: 'auth_status',
                data: {
                    status: 'not_authenticated',
                    domain: domain,
                    workspace: domain
                },
                timestamp: new Date().toISOString(),
                client_id: 'test'
            };
            await this.page.evaluate((msg) => {
                window.dispatchEvent(new CustomEvent('websocket-message', { detail: msg }));
            }, authMessage);

            // Wait for auth status to update
            await this.page.waitForFunction(
            () => {
                const element = document.querySelector('[data-testid="auth-status"]');
                return element && element.textContent === 'Not Authenticated';
            },
            { timeout: 5000 }
            );
        }
    }

    /**
     * Wait for authentication status
     */
    async waitForAuthStatus(expectedStatus: 'Authenticated' | 'Not Authenticated', timeout = 5000) {
        await this.page.waitForSelector('[data-testid="auth-status"]', { timeout });
        await this.page.waitForFunction(
            () => {
                const element = document.querySelector('[data-testid="auth-status"]');
                return element && element.textContent === expectedStatus;
            },
            { timeout }
        );
    }

    /**
     * Join a channel
     */
    async joinChannel(channel: string) {
        // Send join request
        const joinMessage = {
            type: 'join_channel',
            data: {
                channel: channel
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        };
        await this.page.evaluate((msg) => {
            window.dispatchEvent(new CustomEvent('websocket-message', { detail: msg }));
        }, joinMessage);

        // Message delivery confirmation
        const deliveryMessage = {
            type: 'message_delivered',
            data: {
                message: 'Join channel request received',
                original_type: 'join_channel',
                status: 'success'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        };
        await this.page.evaluate((msg) => {
            window.dispatchEvent(new CustomEvent('websocket-message', { detail: msg }));
        }, deliveryMessage);

        // Subscription success
        const successMessage = {
            type: 'subscription_success',
            data: {
                channel: channel,
                status: 'success',
                message: 'Successfully joined channel'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test',
            channel: channel
        };
        await this.page.evaluate((msg) => {
            window.dispatchEvent(new CustomEvent('websocket-message', { detail: msg }));
        }, successMessage);
    }

    /**
     * Leave a channel
     */
    async leaveChannel(channel: string) {
        // Send leave request
        const leaveMessage = {
            type: 'leave_channel',
            data: {
                channel: channel
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        };
        await this.page.evaluate((msg) => {
            window.dispatchEvent(new CustomEvent('websocket-message', { detail: msg }));
        }, leaveMessage);

        // Message delivery confirmation
        const deliveryMessage = {
            type: 'message_delivered',
            data: {
                message: 'Leave channel request received',
                original_type: 'leave_channel',
                status: 'success'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test'
        };
        await this.page.evaluate((msg) => {
            window.dispatchEvent(new CustomEvent('websocket-message', { detail: msg }));
        }, deliveryMessage);

        // Unsubscription success
        const successMessage = {
            type: 'unsubscription_success',
            data: {
                channel: channel,
                status: 'success',
                message: 'Successfully left channel'
            },
            timestamp: new Date().toISOString(),
            client_id: 'test',
            channel: channel
        };
        await this.page.evaluate((msg) => {
            window.dispatchEvent(new CustomEvent('websocket-message', { detail: msg }));
        }, successMessage);
    }

    /**
     * Send a WebSocket message
     */
    async sendMessage(message: WebSocketMessage) {
        await this.page.evaluate((msg) => {
            window.dispatchEvent(new CustomEvent('websocket-message', {
                detail: msg
            }));
        }, message);
    }

    /**
     * Wait for a specific message type
     */
    async waitForMessage(type: string, timeout = 5000) {
        let timeoutHandle: NodeJS.Timeout;
        
        interface ExtendedWindow extends Window {
            onWebSocketMessage?: (messageType: string) => boolean;
        }
        
        try {
            await this.page.exposeBinding('onWebSocketMessage', (_, messageType: string) => {
                return messageType === type;
            });

            await Promise.race([
                this.page.evaluate((expectedType) => {
                    return new Promise<void>((resolve) => {
                        function handler(event: Event) {
                            const customEvent = event as CustomEvent<{ type: string }>;
                            const win = window as ExtendedWindow;
                            if (customEvent.detail.type === expectedType && win.onWebSocketMessage?.(customEvent.detail.type)) {
                                window.removeEventListener('websocket-message', handler);
                                resolve();
                            }
                        }
                        window.addEventListener('websocket-message', handler);
                    });
                }, type),
                new Promise((_, reject) => {
                    timeoutHandle = setTimeout(() => {
                        reject(new Error('Timeout waiting for message'));
                    }, timeout);
                })
            ]);
        } finally {
            clearTimeout(timeoutHandle!);
            await this.page.evaluate(() => {
                const win = window as ExtendedWindow;
                delete win.onWebSocketMessage;
            });
        }
    }

    /**
     * Simulate a connection error
     */
    async simulateError(error: string) {
        // Send error message
        await this.page.evaluate((errorMessage) => {
            window.dispatchEvent(new CustomEvent('websocket-message', {
                detail: {
                    type: 'error',
                    data: {
                        message: errorMessage,
                        status: 'error',
                        code: 1011,
                        error_type: 'server_error'
                    },
                    timestamp: new Date().toISOString(),
                    client_id: 'test'
                }
            }));
        }, error);

        // Wait for error message to be displayed
        await this.page.waitForSelector('[data-testid="error-message"]');
        await this.page.waitForFunction(
            () => {
                const element = document.querySelector('[data-testid="error-message"]');
                return element && element.textContent && element.textContent.includes(error);
            },
            { timeout: 5000 }
        );

        // Verify connection status changed to error
        await this.page.waitForFunction(
            () => {
                const element = document.querySelector('[data-testid="connection-status"]');
                return element && element.textContent === 'Error';
            },
            { timeout: 5000 }
        );

        // Verify auth status reset
        await this.page.waitForFunction(
            () => {
                const element = document.querySelector('[data-testid="auth-status"]');
                return element && element.textContent === 'Not Authenticated';
            },
            { timeout: 5000 }
        );
    }

    /**
     * Wait for reconnection info
     */
    async waitForReconnectInfo(expectedAttempts: number, timeout = 5000) {
        await this.page.waitForSelector('[data-testid="reconnect-info"]', { timeout });
        await this.page.waitForFunction(
            () => {
                const element = document.querySelector('[data-testid="reconnect-info"]');
                return element && element.textContent && element.textContent.includes(`Reconnection attempts: ${expectedAttempts}`);
            },
            { timeout }
        );
    }

    /**
     * Set authentication status
     */
    async setAuthStatus(status: 'authenticated' | 'not_authenticated') {
        await this.page.evaluate((authStatus) => {
            window.dispatchEvent(new CustomEvent('websocket-message', {
                detail: {
                    type: 'auth_status',
                    data: {
                        status: authStatus
                    },
                    timestamp: new Date().toISOString(),
                    client_id: 'test'
                }
            }));
        }, status);

        // Wait for auth status to update
        const expectedStatus = status === 'authenticated' ? 'Authenticated' : 'Not Authenticated';
        await this.page.waitForFunction(
            () => {
                const element = document.querySelector('[data-testid="auth-status"]');
                return element && element.textContent === expectedStatus;
            },
            { timeout: 5000 }
        );
    }

    /**
     * Wait for error message
     */
    async waitForErrorMessage(expectedMessage: string, timeout = 5000) {
        await this.page.waitForSelector('[data-testid="error-message"]', { timeout });
        await this.page.waitForFunction(
            () => {
                const element = document.querySelector('[data-testid="error-message"]');
                return element && element.textContent && element.textContent.includes(expectedMessage);
            },
            { timeout }
        );
    }

    /**
     * Clean up WebSocket connection
     */
    async cleanup() {
        // Reset connection status
        await this.page.evaluate(() => {
            window.dispatchEvent(new CustomEvent('websocket-status', {
                detail: {
                    type: 'connection_success',
                    data: {
                        message: 'Connection established',
                        status: 'connected',
                        domain: 'personal'
                    },
                    timestamp: new Date().toISOString(),
                    client_id: 'test'
                }
            }));
        });

        // Wait for connection status to update
        await this.page.waitForFunction(
            () => {
                const element = document.querySelector('[data-testid="connection-status"]');
                return element && element.textContent === 'Connected';
            },
            { timeout: 5000 }
        );

        // Reset auth status
        await this.page.evaluate(() => {
            window.dispatchEvent(new CustomEvent('websocket-message', {
                detail: {
                    type: 'auth_status',
                    data: {
                        status: 'not_authenticated'
                    },
                    timestamp: new Date().toISOString(),
                    client_id: 'test'
                }
            }));
        });

        // Wait for auth status to update
        await this.page.waitForFunction(
            () => {
                const element = document.querySelector('[data-testid="auth-status"]');
                return element && element.textContent === 'Not Authenticated';
            },
            { timeout: 5000 }
        );

        // Clean up WebSocket connection
        await this.page.evaluate(() => {
            window.dispatchEvent(new Event('websocket-cleanup'));
        });
    }
}
