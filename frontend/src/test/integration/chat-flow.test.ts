import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest';
import { render } from '@testing-library/svelte';
import Chat from '$lib/components/Chat.svelte';
import { websocketStore } from '$lib/stores/websocket';
import { ValidationError } from '$lib/utils/validation';
import type { Message, WebSocketState } from '$lib/types/websocket';
import { wait } from '../utils/test-utils';

// Mock the websocket store
vi.mock('$lib/stores/websocket', () => ({
    websocketStore: {
        connect: vi.fn(),
        disconnect: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        sendMessage: vi.fn(),
        subscribe: vi.fn()
    }
}));

describe('Chat Flow Integration', () => {
    const apiKey = 'test-api-key';
    const clientId = crypto.randomUUID();
    const threadId = 'test-thread';

    beforeEach(() => {
        vi.clearAllMocks();
    });

    function mockWebSocketState(state: Partial<WebSocketState>) {
        (websocketStore.subscribe as Mock).mockImplementation((callback: (state: WebSocketState) => void) => {
            callback({
                connected: false,
                error: null,
                messages: [],
                ...state
            });
            return () => {};
        });
    }

    describe('Message Validation', () => {
        it('should validate messages before sending', () => {
            mockWebSocketState({ connected: true });

            const { getByText } = render(Chat, {
                props: { apiKey, clientId, threadId }
            });

            // Try to send an empty message
            websocketStore.sendMessage = vi.fn().mockImplementation(() => {
                throw new ValidationError('Message content cannot be empty', { content: '' });
            });

            const sendButton = getByText('Send');
            sendButton.click();

            expect(websocketStore.sendMessage).not.toHaveBeenCalled();
            expect(getByText('Message content cannot be empty')).toBeTruthy();
        });

        it('should validate received messages', async () => {
            const invalidMessage = {
                type: 'message' as const,
                id: '',  // Invalid: empty ID
                content: 'test',
                sender_type: 'user',
                sender_id: 'test',
                timestamp: 'invalid-date',  // Invalid: not ISO format
                metadata: {}
            };

            mockWebSocketState({
                connected: true,
                messages: [invalidMessage]
            });

            const { getByText } = render(Chat, {
                props: { apiKey, clientId, threadId }
            });

            await wait.forNextTick();
            expect(getByText(/Invalid message format/)).toBeTruthy();
        });

        it('should handle valid messages correctly', async () => {
            const validMessage: Message = {
                type: 'message',
                id: 'msg-123',
                content: 'Hello',
                sender_type: 'user',
                sender_id: 'test',
                timestamp: new Date().toISOString(),
                metadata: {}
            };

            mockWebSocketState({
                connected: true,
                messages: [validMessage]
            });

            const { getByText, getByPlaceholderText } = render(Chat, {
                props: { apiKey, clientId, threadId }
            });

            // Send message
            const input = getByPlaceholderText('Type a message...') as HTMLTextAreaElement;
            const sendButton = getByText('Send');

            input.value = 'Hello';
            sendButton.click();

            expect(websocketStore.sendMessage).toHaveBeenCalledWith('Hello', threadId);
            expect(input.value).toBe('');
        });
    });

    describe('Connection Handling', () => {
        it('should handle connection and disconnection', () => {
            mockWebSocketState({ connected: true });

            const { component } = render(Chat, {
                props: { apiKey, clientId, threadId }
            });

            // Test initial connection
            expect(websocketStore.connect).toHaveBeenCalledWith('chat', clientId, apiKey);

            // Test disconnection
            component.$destroy();
            expect(websocketStore.disconnect).toHaveBeenCalled();
        });

        it('should disable input when disconnected', async () => {
            mockWebSocketState({ connected: false });

            const { getByPlaceholderText } = render(Chat, {
                props: { apiKey, clientId, threadId }
            });

            const input = getByPlaceholderText('Type a message...') as HTMLTextAreaElement;
            expect(input.disabled).toBe(true);

            // Test connected state
            mockWebSocketState({ connected: true });
            await wait.forNextTick();
            expect(input.disabled).toBe(false);
        });
    });

    describe('Error Handling', () => {
        it('should display websocket errors', async () => {
            mockWebSocketState({
                connected: true,
                error: new Error('Connection failed')
            });

            const { getByText } = render(Chat, {
                props: { apiKey, clientId, threadId }
            });

            await wait.forNextTick();
            expect(getByText('Connection failed')).toBeTruthy();
        });

        it('should clear errors when connection is restored', async () => {
            // Start with error
            mockWebSocketState({
                connected: false,
                error: new Error('Connection failed')
            });

            const { getByText, queryByText } = render(Chat, {
                props: { apiKey, clientId, threadId }
            });

            await wait.forNextTick();
            expect(getByText('Connection failed')).toBeTruthy();

            // Restore connection
            mockWebSocketState({
                connected: true,
                error: null
            });

            await wait.forNextTick();
            expect(queryByText('Connection failed')).toBeFalsy();
        });
    });
});
