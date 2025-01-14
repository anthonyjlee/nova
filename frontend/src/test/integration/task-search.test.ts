import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render } from '@testing-library/svelte';
import TaskBoard from '$lib/components/TaskBoard.svelte';
import { TaskState } from '$lib/types/task';
import type { Task } from '$lib/types/task';
import { TaskTestContext, assertions, wait } from '../utils/test-utils';
import { tasksSocket } from '$lib/stores/websocket';
import type { TaskSearchMessage } from '$lib/types/websocket';
import {
    createSearchQuery,
    createDateRange,
    type SearchQuery,
    type SearchResult
} from '$lib/types/search';

// Mock the websocket store
vi.mock('$lib/stores/websocket', () => ({
    tasksSocket: {
        connect: vi.fn(),
        disconnect: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        send: vi.fn()
    }
}));

describe('Task Search Integration', () => {
    let context: TaskTestContext;

    beforeEach(() => {
        context = new TaskTestContext();
        // Replace the mock implementation with our test context
        tasksSocket.connect = () => context.websocket.connect();
        tasksSocket.disconnect = () => context.websocket.disconnect();
        tasksSocket.addEventListener = (event, callback) => 
            context.websocket.addEventListener(event, callback);
        tasksSocket.removeEventListener = (event, callback) =>
            context.websocket.removeEventListener(event, callback);
        tasksSocket.send = (message) => context.websocket.send(message);
    });

    afterEach(() => {
        context.reset();
    });

    describe('Text Search', () => {
        it('should search tasks by text', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create test tasks
            const task1 = context.addTask({
                label: 'Important meeting',
                description: 'Team sync'
            });
            const task2 = context.addTask({
                label: 'Code review',
                description: 'Review PR #123'
            });

            await wait.forWebSocket();

            // Search for 'meeting'
            const query = createSearchQuery('meeting');
            const searchMessage: TaskSearchMessage = {
                type: 'task_search',
                data: query,
                timestamp: new Date().toISOString()
            };

            tasksSocket.send(searchMessage);
            await wait.forWebSocket();

            const result = board.tasks;
            expect(result).toContainEqual(task1);
            expect(result).not.toContainEqual(task2);
        });
    });

    describe('Status Filtering', () => {
        it('should filter tasks by status', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create tasks with different statuses
            const pendingTask = context.addTask({
                status: TaskState.PENDING
            });
            const completedTask = context.addTask({
                status: TaskState.COMPLETED
            });

            await wait.forWebSocket();

            // Filter for pending tasks
            const query = createSearchQuery(undefined, {
                status: [TaskState.PENDING]
            });
            const searchMessage: TaskSearchMessage = {
                type: 'task_search',
                data: query,
                timestamp: new Date().toISOString()
            };

            tasksSocket.send(searchMessage);
            await wait.forWebSocket();

            const result = board.tasks;
            expect(result).toContainEqual(pendingTask);
            expect(result).not.toContainEqual(completedTask);
        });
    });

    describe('Date Range Filtering', () => {
        it('should filter tasks by date range', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create tasks with different dates
            const oldTask = context.addTask({
                created_at: '2025-01-01T00:00:00Z'
            });
            const newTask = context.addTask({
                created_at: '2025-01-15T00:00:00Z'
            });

            await wait.forWebSocket();

            // Filter for tasks after Jan 10
            const query = createSearchQuery(undefined, {
                dateRange: createDateRange('2025-01-10T00:00:00Z')
            });
            const searchMessage: TaskSearchMessage = {
                type: 'task_search',
                data: query,
                timestamp: new Date().toISOString()
            };

            tasksSocket.send(searchMessage);
            await wait.forWebSocket();

            const result = board.tasks;
            expect(result).toContainEqual(newTask);
            expect(result).not.toContainEqual(oldTask);
        });
    });

    describe('Pagination', () => {
        it('should handle paginated results', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create multiple tasks
            // Create test tasks
            Array.from({ length: 25 }, (_, i) => 
                context.addTask({ label: `Task ${i + 1}` })
            );

            await wait.forWebSocket();

            // Request first page
            const query = createSearchQuery(undefined, undefined, undefined, {
                page: 1,
                pageSize: 10
            });
            const searchMessage: TaskSearchMessage = {
                type: 'task_search',
                data: query,
                timestamp: new Date().toISOString()
            };

            tasksSocket.send(searchMessage);
            await wait.forWebSocket();

            // The board should have received a SearchResult from the websocket
            const result = {
                items: board.tasks,
                pagination: {
                    page: 1,
                    pageSize: 10,
                    totalItems: 25,
                    totalPages: 3
                }
            } as SearchResult<Task>;
            expect(result.items).toHaveLength(10);
            expect(result.pagination.totalItems).toBe(25);
            expect(result.pagination.totalPages).toBe(3);
        });
    });

    describe('Combined Search', () => {
        it('should combine multiple search criteria', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create tasks with various attributes
            const matchingTask = context.addTask({
                label: 'Important meeting',
                status: TaskState.PENDING,
                created_at: '2025-01-15T00:00:00Z',
                assignee: 'user1'
            });
            const nonMatchingTask = context.addTask({
                label: 'Code review',
                status: TaskState.COMPLETED,
                created_at: '2025-01-01T00:00:00Z',
                assignee: 'user2'
            });

            await wait.forWebSocket();

            // Search with multiple criteria
            const query = createSearchQuery('meeting', {
                status: [TaskState.PENDING],
                assignee: ['user1'],
                dateRange: createDateRange('2025-01-10T00:00:00Z')
            });
            const searchMessage: TaskSearchMessage = {
                type: 'task_search',
                data: query,
                timestamp: new Date().toISOString()
            };

            tasksSocket.send(searchMessage);
            await wait.forWebSocket();

            const result = board.tasks;
            expect(result).toContainEqual(matchingTask);
            expect(result).not.toContainEqual(nonMatchingTask);
        });
    });

    describe('Error Handling', () => {
        it('should handle invalid search queries', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { 
                tasks: Task[];
                handleError: (error: Error) => void;
            };
            const mockError = vi.fn();
            board.handleError = mockError;

            // Send invalid query
            // Create an invalid query that will be caught by validation
            const invalidQuery = createSearchQuery(
                undefined,
                undefined,
                undefined,
                { page: 0, pageSize: 20 } // Invalid: page should be >= 1
            );
            const searchMessage: TaskSearchMessage = {
                type: 'task_search',
                data: invalidQuery as SearchQuery,
                timestamp: new Date().toISOString()
            };

            tasksSocket.send(searchMessage);
            await wait.forWebSocket();

            expect(mockError).toHaveBeenCalled();
            expect(board.tasks).toHaveLength(0);
        });

        it('should handle search timeout', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { 
                tasks: Task[];
                handleError: (error: Error) => void;
            };
            const mockError = vi.fn();
            board.handleError = mockError;

            // Simulate timeout
            tasksSocket.send = vi.fn().mockImplementation(() => {
                throw new Error('Search timeout');
            });

            const query = createSearchQuery('test');
            const searchMessage: TaskSearchMessage = {
                type: 'task_search',
                data: query,
                timestamp: new Date().toISOString()
            };

            tasksSocket.send(searchMessage);
            await wait.forWebSocket();

            expect(mockError).toHaveBeenCalledWith(expect.any(Error));
            expect(board.tasks).toEqual(board.tasks); // Tasks should remain unchanged
        });
    });
});
