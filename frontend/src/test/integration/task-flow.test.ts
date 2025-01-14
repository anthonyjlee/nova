import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render } from '@testing-library/svelte';
import TaskBoard from '$lib/components/TaskBoard.svelte';
import type { Task } from '$lib/types/task';
import { TaskState } from '$lib/types/task';
import { TaskTestContext, assertions, wait } from '../utils/test-utils';
import { tasksSocket } from '$lib/stores/websocket';
import { ValidationError } from '$lib/utils/validation';

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

describe('Task Flow Integration', () => {
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

    describe('Task Creation and Updates', () => {
        it('should handle new task creation', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create a new task
            const task = context.addTask({
                status: TaskState.PENDING
            });

            // Wait for WebSocket update
            await wait.forWebSocket();

            // Verify task was added to the board
            expect(board.tasks).toContainEqual(task);
            assertions.taskExists(board.tasks, task.id);
            assertions.taskHasStatus(board.tasks, task.id, TaskState.PENDING);
        });

        it('should handle task state transitions', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create a task in PENDING state
            const task = context.addTask({
                status: TaskState.PENDING
            });

            // Move to IN_PROGRESS
            context.updateTask(task.id, {
                status: TaskState.IN_PROGRESS
            });

            await wait.forWebSocket();
            assertions.taskHasStatus(board.tasks, task.id, TaskState.IN_PROGRESS);

            // Move to COMPLETED
            context.updateTask(task.id, {
                status: TaskState.COMPLETED
            });

            await wait.forWebSocket();
            assertions.taskHasStatus(board.tasks, task.id, TaskState.COMPLETED);
        });

        it('should handle invalid state transitions', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { 
                tasks: Task[];
                handleError: (error: Error | ValidationError) => void;
            };
            board.handleError = (error) => context.errorBoundary.handleError(error);

            // Create a task in PENDING state
            const task = context.addTask({
                status: TaskState.PENDING
            });

            // Try to move directly to COMPLETED (invalid transition)
            context.updateTask(task.id, {
                status: TaskState.COMPLETED
            });

            await wait.forWebSocket();

            // Task should remain in PENDING state
            assertions.taskHasStatus(board.tasks, task.id, TaskState.PENDING);
            assertions.errorBoundaryHasError(context.errorBoundary, ValidationError);
        });
    });

    describe('Task Validation', () => {
        it('should validate tasks on creation', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { 
                tasks: Task[];
                handleError: (error: Error | ValidationError) => void;
            };
            board.handleError = (error) => context.errorBoundary.handleError(error);

            // Try to create an invalid task
            const invalidTask = context.addTask({
                id: '', // Invalid: empty ID
                label: '' // Invalid: empty label
            });

            await wait.forWebSocket();

            // Task should not be added to the board
            expect(board.tasks).not.toContainEqual(invalidTask);
            assertions.errorBoundaryHasError(context.errorBoundary, ValidationError);
        });

        it('should validate task updates', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { 
                tasks: Task[];
                handleError: (error: Error | ValidationError) => void;
            };
            board.handleError = (error) => context.errorBoundary.handleError(error);

            // Create a valid task
            const task = context.addTask();

            // Try to update with invalid data
            context.updateTask(task.id, {
                label: '' // Invalid: empty label
            });

            await wait.forWebSocket();

            // Task should retain original values
            const originalTask = assertions.taskExists(board.tasks, task.id);
            expect(originalTask.label).toBe(task.label);
            assertions.errorBoundaryHasError(context.errorBoundary, ValidationError);
        });
    });

    describe('WebSocket Connection', () => {
        it('should handle connection loss and reconnection', async () => {
            render(TaskBoard);

            // Verify initial connection
            assertions.websocketIsConnected(context.websocket);

            // Simulate connection loss
            context.websocket.disconnect();
            expect(context.websocket.isConnected).toBe(false);

            // Simulate reconnection
            context.websocket.connect();
            assertions.websocketIsConnected(context.websocket);
        });

        it('should buffer updates during disconnection', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create initial task
            const task = context.addTask();
            await wait.forWebSocket();

            // Simulate connection loss
            context.websocket.disconnect();

            // Update task while disconnected
            const updatedTask = context.updateTask(task.id, {
                status: TaskState.IN_PROGRESS
            });

            // Reconnect and verify update was processed
            context.websocket.connect();
            await wait.forWebSocket();

            assertions.taskExists(board.tasks, task.id);
            expect(board.tasks).toContainEqual(updatedTask);
        });
    });

    describe('Error Recovery', () => {
        it('should recover from validation errors', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { 
                tasks: Task[];
                handleError: (error: Error | ValidationError) => void;
            };
            board.handleError = (error) => context.errorBoundary.handleError(error);

            // Create a valid task
            const task = context.addTask();
            await wait.forWebSocket();

            // Try invalid update
            context.updateTask(task.id, {
                label: '' // Invalid
            });
            await wait.forWebSocket();

            // Verify error was caught
            assertions.errorBoundaryHasError(context.errorBoundary, ValidationError);

            // Try valid update
            const validUpdate = context.updateTask(task.id, {
                label: 'Updated Task'
            });
            await wait.forWebSocket();

            // Verify recovery
            expect(board.tasks).toContainEqual(validUpdate);
        });

        it('should handle multiple errors gracefully', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { 
                tasks: Task[];
                handleError: (error: Error | ValidationError) => void;
            };
            board.handleError = (error) => context.errorBoundary.handleError(error);

            // Generate multiple errors
            for (let i = 0; i < 3; i++) {
                context.addTask({ id: '' }); // Invalid task
                await wait.forWebSocket();
            }

            // Verify all errors were caught
            expect(context.errorBoundary.errors).toHaveLength(3);
            expect(board.tasks).toHaveLength(0);

            // Verify can still add valid tasks
            const validTask = context.addTask();
            await wait.forWebSocket();

            expect(board.tasks).toContainEqual(validTask);
        });
    });
});
