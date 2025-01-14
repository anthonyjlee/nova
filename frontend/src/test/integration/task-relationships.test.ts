import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render } from '@testing-library/svelte';
import TaskBoard from '$lib/components/TaskBoard.svelte';
import type { Task } from '$lib/types/task';
import { TaskState } from '$lib/types/task';
import type { SubTask } from '$lib/types/subtask';
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

describe('Task Relationships Integration', () => {
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

    describe('Parent-Child Relationships', () => {
        it('should handle parent task creation with subtasks', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create parent task
            const parentTask = context.addTask({
                status: TaskState.PENDING,
                sub_tasks: [
                    { id: 'sub1', description: 'Subtask 1', completed: false, created_at: new Date().toISOString() } as SubTask,
                    { id: 'sub2', description: 'Subtask 2', completed: false, created_at: new Date().toISOString() } as SubTask
                ]
            });

            await wait.forWebSocket();

            // Verify parent task was added
            const task = assertions.taskExists(board.tasks, parentTask.id);
            expect(task.sub_tasks).toHaveLength(2);
            expect(task.sub_tasks?.[0].id).toBe('sub1');
        });

        it('should update parent task when all subtasks complete', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create parent task with subtasks
            const parentTask = context.addTask({
                status: TaskState.IN_PROGRESS,
                sub_tasks: [
                    { id: 'sub1', description: 'Subtask 1', completed: false, created_at: new Date().toISOString() } as SubTask,
                    { id: 'sub2', description: 'Subtask 2', completed: false, created_at: new Date().toISOString() } as SubTask
                ]
            });

            await wait.forWebSocket();

            // Complete all subtasks
            context.updateTask(parentTask.id, {
                sub_tasks: [
                    { id: 'sub1', description: 'Subtask 1', completed: true, created_at: new Date().toISOString() } as SubTask,
                    { id: 'sub2', description: 'Subtask 2', completed: true, created_at: new Date().toISOString() } as SubTask
                ]
            });

            await wait.forWebSocket();

            // Parent should be marked as completed
            assertions.taskHasStatus(board.tasks, parentTask.id, TaskState.COMPLETED);
        });
    });

    describe('Task Dependencies', () => {
        it('should handle dependent task creation', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create tasks with dependency
            const dependentOn = context.addTask();
            const dependentTask = context.addTask({
                dependencies: [dependentOn.id]
            });

            await wait.forWebSocket();

            // Verify dependency relationship
            const task = assertions.taskExists(board.tasks, dependentTask.id);
            expect(task.dependencies).toContain(dependentOn.id);
        });

        it('should prevent completing task with incomplete dependencies', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { 
                tasks: Task[];
                handleError: (error: Error | ValidationError) => void;
            };
            board.handleError = (error) => context.errorBoundary.handleError(error);

            // Create dependent tasks
            const dependentOn = context.addTask({
                status: TaskState.IN_PROGRESS
            });
            const dependentTask = context.addTask({
                status: TaskState.IN_PROGRESS,
                dependencies: [dependentOn.id]
            });

            await wait.forWebSocket();

            // Try to complete dependent task before dependency
            context.updateTask(dependentTask.id, {
                status: TaskState.COMPLETED
            });

            await wait.forWebSocket();

            // Should remain in progress and raise error
            assertions.taskHasStatus(board.tasks, dependentTask.id, TaskState.IN_PROGRESS);
            assertions.errorBoundaryHasError(context.errorBoundary, ValidationError);
        });
    });

    describe('Task Blocking', () => {
        it('should handle blocked task relationships', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create blocking relationship
            const blockingTask = context.addTask();
            const blockedTask = context.addTask({
                blocked_by: [blockingTask.id]
            });

            await wait.forWebSocket();

            // Verify blocking relationship
            const task = assertions.taskExists(board.tasks, blockedTask.id);
            expect(task.blocked_by).toContain(blockingTask.id);
        });

        it('should automatically unblock task when blocker completes', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create blocking relationship
            const blockingTask = context.addTask({
                status: TaskState.IN_PROGRESS
            });
            const blockedTask = context.addTask({
                status: TaskState.BLOCKED,
                blocked_by: [blockingTask.id]
            });

            await wait.forWebSocket();

            // Complete blocking task
            context.updateTask(blockingTask.id, {
                status: TaskState.COMPLETED
            });

            await wait.forWebSocket();

            // Blocked task should be unblocked
            assertions.taskHasStatus(board.tasks, blockedTask.id, TaskState.PENDING);
        });
    });

    describe('Task Groups', () => {
        it('should handle task group creation', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create group task
            const groupTask = context.addTask({
                type: 'group',
                metadata: {
                    group_type: 'sprint',
                    group_name: 'Sprint 1'
                }
            });

            // Create tasks in group
            const task1 = context.addTask({
                metadata: { group_id: groupTask.id }
            });
            const task2 = context.addTask({
                metadata: { group_id: groupTask.id }
            });

            await wait.forWebSocket();

            // Verify group relationships
            const tasks = board.tasks;
            expect(tasks.filter(t => t.metadata?.group_id === groupTask.id)).toHaveLength(2);
            expect(tasks.find(t => t.id === task1.id)?.metadata?.group_id).toBe(groupTask.id);
            expect(tasks.find(t => t.id === task2.id)?.metadata?.group_id).toBe(groupTask.id);
        });

        it('should update group status based on member tasks', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { tasks: Task[] };

            // Create group with tasks
            const groupTask = context.addTask({
                type: 'group',
                status: TaskState.IN_PROGRESS
            });
            const task1 = context.addTask({
                metadata: { group_id: groupTask.id }
            });
            const task2 = context.addTask({
                metadata: { group_id: groupTask.id }
            });

            await wait.forWebSocket();

            // Complete all tasks in group
            context.updateTask(task1.id, { status: TaskState.COMPLETED });
            context.updateTask(task2.id, { status: TaskState.COMPLETED });

            await wait.forWebSocket();

            // Group should be completed
            assertions.taskHasStatus(board.tasks, groupTask.id, TaskState.COMPLETED);
        });
    });
});
