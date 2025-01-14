import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest';
import { render } from '@testing-library/svelte';
import TaskBoard from '$lib/components/TaskBoard.svelte';
import { tasksSocket } from '$lib/stores/websocket';
import { ValidationError } from '$lib/utils/validation';
import type { TaskUpdate, TaskSearchMessage, TaskSearchResultMessage, WebSocketState } from '$lib/types/websocket';
import type { TaskFilter } from '$lib/types/search';
import { TaskState } from '$lib/types/task';
import { wait } from '../utils/test-utils';
import { createDefaultPagination, createDefaultSort } from '$lib/types/search';

// Mock the tasks socket
vi.mock('$lib/stores/websocket', () => ({
    tasksSocket: {
        connect: vi.fn(),
        disconnect: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        send: vi.fn(),
        subscribe: vi.fn()
    }
}));

describe('Task WebSocket Integration', () => {
    const now = new Date().toISOString();

    beforeEach(() => {
        vi.clearAllMocks();
    });

    function mockWebSocketState(state: Partial<WebSocketState>) {
        (tasksSocket.subscribe as Mock).mockImplementation((callback: (state: WebSocketState) => void) => {
            callback({
                connected: false,
                error: null,
                messages: [],
                ...state
            });
            return () => {};
        });
    }

    describe('Task Update Validation', () => {
        it('should validate task updates before sending', () => {
            mockWebSocketState({ connected: true });

            const { getByTestId } = render(TaskBoard);

            // Try to send an invalid task update
            const invalidUpdate: TaskUpdate = {
                type: 'task_update',
                data: {
                    id: '',  // Invalid: empty ID
                    label: '',  // Invalid: empty label
                    type: 'task',
                    status: TaskState.PENDING,
                    created_at: 'invalid-date',  // Invalid: not ISO format
                    updated_at: now,
                    metadata: {}
                },
                timestamp: now
            };

            tasksSocket.send = vi.fn().mockImplementation(() => {
                throw new ValidationError('Invalid task update format', { update: invalidUpdate });
            });

            // Attempt to send invalid update
            tasksSocket.send(invalidUpdate);

            expect(tasksSocket.send).toThrow(ValidationError);
            expect(getByTestId('error-message')).toBeTruthy();
        });

        it('should handle valid task updates correctly', async () => {
            const validUpdate: TaskUpdate = {
                type: 'task_update',
                data: {
                    id: 'task-123',
                    label: 'Test Task',
                    type: 'task',
                    status: TaskState.PENDING,
                    created_at: now,
                    updated_at: now,
                    metadata: {}
                },
                timestamp: now
            };

            mockWebSocketState({
                connected: true,
                messages: [validUpdate]
            });

            render(TaskBoard);

            // Send valid update
            tasksSocket.send(validUpdate);

            expect(tasksSocket.send).toHaveBeenCalledWith(validUpdate);
        });
    });

    describe('Task Search Validation', () => {
        it('should validate search queries before sending', () => {
            mockWebSocketState({ connected: true });

            const { getByTestId } = render(TaskBoard);

            // Try to send an invalid search query
            const invalidSearch = {
                type: 'task_search',
                data: {
                    text: 123 as unknown as string,  // Invalid: number instead of string
                    filter: null as unknown as Record<string, never>,  // Invalid: null instead of object
                    sort: {
                        field: 'invalid_field' as keyof TaskFilter | 'created_at' | 'updated_at' | 'label',  // Invalid field
                        direction: 'invalid' as unknown as 'asc' | 'desc'  // Invalid direction
                    },
                    pagination: { page: 0, pageSize: 0 }  // Invalid pagination
                },
                timestamp: 'invalid-date'  // Invalid: not ISO format
            } as TaskSearchMessage;

            tasksSocket.send = vi.fn().mockImplementation(() => {
                throw new ValidationError('Invalid search query format', { query: invalidSearch });
            });

            // Attempt to send invalid search
            tasksSocket.send(invalidSearch);

            expect(tasksSocket.send).toThrow(ValidationError);
            expect(getByTestId('error-message')).toBeTruthy();
        });

        it('should handle valid search queries correctly', async () => {
            const validSearch: TaskSearchMessage = {
                type: 'task_search',
                data: {
                    text: 'test',
                    filter: {},
                    sort: createDefaultSort(),
                    pagination: createDefaultPagination()
                },
                timestamp: now
            };

            mockWebSocketState({
                connected: true,
                messages: [validSearch]
            });

            render(TaskBoard);

            // Send valid search
            tasksSocket.send(validSearch);

            expect(tasksSocket.send).toHaveBeenCalledWith(validSearch);
        });
    });

    describe('Search Result Validation', () => {
        it('should validate search results', async () => {
            const invalidResult: TaskSearchResultMessage = {
                type: 'task_search_result',
                result: {
                    items: [
                        {
                            id: '',  // Invalid: empty ID
                            label: '',  // Invalid: empty label
                            type: 'task',
                            status: TaskState.PENDING,
                            created_at: 'invalid-date',  // Invalid: not ISO format
                            updated_at: now,
                            metadata: {}
                        }
                    ],
                    pagination: {
                        page: 0,  // Invalid: page must be >= 1
                        pageSize: 0,  // Invalid: pageSize must be >= 1
                        totalItems: -1,  // Invalid: must be >= 0
                        totalPages: -1  // Invalid: must be >= 0
                    }
                },
                timestamp: 'invalid-date'  // Invalid: not ISO format
            };

            mockWebSocketState({
                connected: true,
                messages: [invalidResult]
            });

            const { getByTestId } = render(TaskBoard);

            await wait.forNextTick();
            expect(getByTestId('error-message')).toBeTruthy();
        });

        it('should handle valid search results correctly', async () => {
            const validResult: TaskSearchResultMessage = {
                type: 'task_search_result',
                result: {
                    items: [
                        {
                            id: 'task-123',
                            label: 'Test Task',
                            type: 'task',
                            status: TaskState.PENDING,
                            created_at: now,
                            updated_at: now,
                            metadata: {}
                        }
                    ],
                    pagination: {
                        page: 1,
                        pageSize: 10,
                        totalItems: 1,
                        totalPages: 1
                    }
                },
                timestamp: now
            };

            mockWebSocketState({
                connected: true,
                messages: [validResult]
            });

            const { getByText } = render(TaskBoard);

            await wait.forNextTick();
            expect(getByText('Test Task')).toBeTruthy();
        });
    });

    describe('Error Handling', () => {
        it('should handle validation errors gracefully', async () => {
            mockWebSocketState({
                connected: true,
                error: new ValidationError('Invalid message format', { details: 'test' })
            });

            const { getByTestId } = render(TaskBoard);

            await wait.forNextTick();
            const errorMessage = getByTestId('error-message');
            expect(errorMessage.textContent).toContain('Invalid message format');
            expect(errorMessage.textContent).toContain('test');
        });

        it('should clear validation errors when valid messages are received', async () => {
            // Start with error
            mockWebSocketState({
                connected: true,
                error: new ValidationError('Invalid message format')
            });

            const { getByTestId, queryByTestId } = render(TaskBoard);

            await wait.forNextTick();
            expect(getByTestId('error-message')).toBeTruthy();

            // Receive valid message
            mockWebSocketState({
                connected: true,
                error: null,
                messages: [
                    {
                        type: 'task_update',
                        data: {
                            id: 'task-123',
                            label: 'Test Task',
                            type: 'task',
                            status: TaskState.PENDING,
                            created_at: now,
                            updated_at: now,
                            metadata: {}
                        },
                        timestamp: now
                    }
                ]
            });

            await wait.forNextTick();
            expect(queryByTestId('error-message')).toBeFalsy();
        });
    });
});
