import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render } from '@testing-library/svelte';
import TaskBoard from '$lib/components/TaskBoard.svelte';
import { TaskState } from '$lib/types/task';
import type { Task } from '$lib/types/task';
import { TaskTestContext, assertions, wait } from '../utils/test-utils';
import { tasksSocket } from '$lib/stores/websocket';
import {
    createStateChangeEvent,
    createUpdateEvent,
    createCommentEvent,
    createAssignmentEvent,
    createAgentInteraction,
    initializeTaskHistory,
    type AgentInteraction
} from '$lib/types/history';

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

describe('Task History Integration', () => {
    let context: TaskTestContext;

    beforeEach(() => {
        context = new TaskTestContext();
        // Add generateId method to context
        context.generateId = () => Math.random().toString(36).substr(2, 9);
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

    describe('State Change History', () => {
        it('should track task state changes', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create task and track state changes
            const task = context.addTask({
                status: TaskState.PENDING,
                metadata: {
                    ...initializeTaskHistory(context.generateId())
                }
            });

            await wait.forWebSocket();

            // Move to IN_PROGRESS
            context.updateTask(task.id, {
                status: TaskState.IN_PROGRESS,
                metadata: {
                    ...initializeTaskHistory(task.id),
                    state_history: [
                        createStateChangeEvent(TaskState.PENDING, TaskState.IN_PROGRESS)
                    ]
                }
            });

            await wait.forWebSocket();

            // Move to COMPLETED
            context.updateTask(task.id, {
                status: TaskState.COMPLETED,
                metadata: {
                    ...initializeTaskHistory(task.id),
                    state_history: [
                        createStateChangeEvent(TaskState.PENDING, TaskState.IN_PROGRESS),
                        createStateChangeEvent(TaskState.IN_PROGRESS, TaskState.COMPLETED)
                    ]
                }
            });

            await wait.forWebSocket();

            // Verify history
            const updatedTask = assertions.taskExists(board.tasks, task.id);
            const history = updatedTask.metadata.state_history as Array<{from: TaskState, to: TaskState}>;
            expect(history).toHaveLength(2);
            expect(history[0].from).toBe(TaskState.PENDING);
            expect(history[1].to).toBe(TaskState.COMPLETED);
        });
    });

    describe('Update History', () => {
        it('should track task updates', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create task
            const task = context.addTask({
                label: 'Initial Label',
                metadata: {
                    ...initializeTaskHistory(context.generateId())
                }
            });

            await wait.forWebSocket();

            // Update label
            context.updateTask(task.id, {
                label: 'Updated Label',
                metadata: {
                    ...initializeTaskHistory(task.id),
                    update_history: [
                        createUpdateEvent('label', 'Initial Label', 'Updated Label')
                    ]
                }
            });

            await wait.forWebSocket();

            // Verify history
            const updatedTask = assertions.taskExists(board.tasks, task.id);
            const history = updatedTask.metadata.update_history as Array<{field: string, from: string, to: string}>;
            expect(history).toHaveLength(1);
            expect(history[0].field).toBe('label');
            expect(history[0].from).toBe('Initial Label');
            expect(history[0].to).toBe('Updated Label');
        });
    });

    describe('Comment History', () => {
        it('should track task comments', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create task
            const task = context.addTask({
                metadata: {
                    ...initializeTaskHistory(context.generateId())
                }
            });

            await wait.forWebSocket();

            // Add comment
            context.updateTask(task.id, {
                metadata: {
                    ...initializeTaskHistory(task.id),
                    comments: [
                        createCommentEvent('First comment', 'user1')
                    ]
                }
            });

            await wait.forWebSocket();

            // Add another comment
            context.updateTask(task.id, {
                metadata: {
                    ...initializeTaskHistory(task.id),
                    comments: [
                        createCommentEvent('First comment', 'user1'),
                        createCommentEvent('Second comment', 'user2')
                    ]
                }
            });

            await wait.forWebSocket();

            // Verify comments
            const updatedTask = assertions.taskExists(board.tasks, task.id);
            const comments = updatedTask.metadata.comments as Array<{id: string, content: string, author: string}>;
            expect(comments).toHaveLength(2);
            expect(comments[0].content).toBe('First comment');
            expect(comments[1].author).toBe('user2');
        });
    });

    describe('Assignment History', () => {
        it('should track task assignments', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create task
            const task = context.addTask({
                assignee: 'user1',
                metadata: {
                    ...initializeTaskHistory(context.generateId())
                }
            });

            await wait.forWebSocket();

            // Reassign task
            context.updateTask(task.id, {
                assignee: 'user2',
                metadata: {
                    ...initializeTaskHistory(task.id),
                    assignment_history: [
                        createAssignmentEvent('user1', 'user2')
                    ]
                }
            });

            await wait.forWebSocket();

            // Verify assignment history
            const updatedTask = assertions.taskExists(board.tasks, task.id);
            const history = updatedTask.metadata.assignment_history as Array<{from: string, to: string}>;
            expect(history).toHaveLength(1);
            expect(history[0].from).toBe('user1');
            expect(history[0].to).toBe('user2');
        });

        it('should handle unassignment', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create assigned task
            const task = context.addTask({
                assignee: 'user1',
                metadata: {
                    ...initializeTaskHistory(context.generateId())
                }
            });

            await wait.forWebSocket();

            // Unassign task
            context.updateTask(task.id, {
                assignee: undefined,
                metadata: {
                    ...initializeTaskHistory(task.id),
                    assignment_history: [
                        createAssignmentEvent('user1', null)
                    ]
                }
            });

            await wait.forWebSocket();

            // Verify unassignment
            const updatedTask = assertions.taskExists(board.tasks, task.id);
            expect(updatedTask.assignee).toBeUndefined();
            const history = updatedTask.metadata.assignment_history as Array<{from: string, to: string | null}>;
            expect(history[0].to).toBeNull();
        });
    });

    describe('Agent Interactions', () => {
        it('should track agent interactions', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create task
            const task = context.addTask({
                metadata: {
                    ...initializeTaskHistory(context.generateId())
                }
            });

            await wait.forWebSocket();

            // Add agent interaction
            context.updateTask(task.id, {
                metadata: {
                    ...initializeTaskHistory(task.id),
                    agent_interactions: [
                        createAgentInteraction('message', 'Agent response', { context: 'test' })
                    ]
                }
            });

            await wait.forWebSocket();

            // Add another interaction
            context.updateTask(task.id, {
                metadata: {
                    ...initializeTaskHistory(task.id),
                    agent_interactions: [
                        createAgentInteraction('message', 'Agent response', { context: 'test' }),
                        createAgentInteraction('task', 'Task update')
                    ]
                }
            });

            await wait.forWebSocket();

            // Verify interactions
            const updatedTask = assertions.taskExists(board.tasks, task.id);
            const interactions = updatedTask.metadata.agent_interactions as AgentInteraction[];
            expect(interactions).toHaveLength(2);
            expect(interactions[0].type).toBe('message');
            expect(interactions[1].type).toBe('task');
            expect(interactions[0].context).toEqual({ context: 'test' });
        });
    });
});
