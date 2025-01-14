import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/svelte';
import TaskBoard from '$lib/components/TaskBoard.svelte';
import type { Task } from '$lib/types/task';
import { TaskState } from '$lib/types/task';
import type { TaskUpdate, WebSocketMessage } from '$lib/types/websocket';
import { ValidationError } from '$lib/utils/validation';
import { tasksSocket } from '$lib/stores/websocket';

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

describe('TaskBoard', () => {
    const mockTask: Task = {
        id: '123',
        label: 'Test Task',
        type: 'task',
        status: TaskState.PENDING,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {}
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('WebSocket Integration', () => {
        it('should connect to WebSocket on mount', () => {
            render(TaskBoard);
            expect(tasksSocket.connect).toHaveBeenCalled();
        });

        it('should add task update listener on mount', () => {
            render(TaskBoard);
            expect(tasksSocket.addEventListener).toHaveBeenCalledWith(
                'task_update',
                expect.any(Function)
            );
        });

        it('should remove task update listener on destroy', () => {
            const { component } = render(TaskBoard);
            component.$destroy();
            expect(tasksSocket.removeEventListener).toHaveBeenCalledWith(
                'task_update',
                expect.any(Function)
            );
        });

        it('should handle valid task updates', () => {
            const { component } = render(TaskBoard);
            const instance = component as unknown as { handleTaskUpdate: (event: WebSocketMessage) => void };

            const taskUpdate: TaskUpdate = {
                type: 'task_update',
                data: mockTask,
                timestamp: new Date().toISOString()
            };

            instance.handleTaskUpdate(taskUpdate);
            // Task should be added to the board
            const board = component as unknown as { tasks: Task[] };
            expect(board.tasks).toContainEqual(mockTask);
        });

        it('should handle invalid task updates', () => {
            const { component } = render(TaskBoard);
            const instance = component as unknown as { 
                handleTaskUpdate: (event: WebSocketMessage) => void;
                handleError: (error: Error | ValidationError) => void;
            };

            const mockError = vi.fn();
            instance.handleError = mockError;

            const invalidTask = { ...mockTask, id: '' };
            const taskUpdate: TaskUpdate = {
                type: 'task_update',
                data: invalidTask as Task,
                timestamp: new Date().toISOString()
            };

            instance.handleTaskUpdate(taskUpdate);
            expect(mockError).toHaveBeenCalledWith(expect.any(ValidationError));
        });
    });

    describe('Task Filtering', () => {
        it('should filter tasks by status', () => {
            const tasks = [
                { ...mockTask, status: TaskState.PENDING },
                { ...mockTask, id: '456', status: TaskState.IN_PROGRESS },
                { ...mockTask, id: '789', status: TaskState.COMPLETED }
            ];

            const { component } = render(TaskBoard);
            const board = component as unknown as { 
                tasks: Task[];
                filterTasks: (status: TaskState) => Task[];
            };
            board.tasks = tasks;

            const pendingTasks = board.filterTasks(TaskState.PENDING);
            expect(pendingTasks).toHaveLength(1);
            expect(pendingTasks[0].id).toBe('123');

            const inProgressTasks = board.filterTasks(TaskState.IN_PROGRESS);
            expect(inProgressTasks).toHaveLength(1);
            expect(inProgressTasks[0].id).toBe('456');

            const completedTasks = board.filterTasks(TaskState.COMPLETED);
            expect(completedTasks).toHaveLength(1);
            expect(completedTasks[0].id).toBe('789');
        });
    });

    describe('Task Updates', () => {
        it('should update task status on drop', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { 
                tasks: Task[];
                handleDrop: (event: DragEvent) => Promise<void>;
            };
            board.tasks = [mockTask];

            const dropEvent = new Event('drop') as DragEvent;
            Object.defineProperty(dropEvent, 'dataTransfer', {
                value: {
                    getData: () => '123'
                }
            });

            await board.handleDrop(dropEvent);
            expect(tasksSocket.send).toHaveBeenCalledWith(expect.objectContaining({
                type: 'task_update'
            }));
        });

        it('should validate task before update', async () => {
            const { component } = render(TaskBoard);
            const board = component as unknown as { 
                tasks: Task[];
                handleDrop: (event: DragEvent) => Promise<void>;
                handleError: (error: Error | ValidationError) => void;
            };
            const mockError = vi.fn();
            board.handleError = mockError;

            const invalidTask = { ...mockTask, id: '' };
            board.tasks = [invalidTask as Task];

            const dropEvent = new Event('drop') as DragEvent;
            Object.defineProperty(dropEvent, 'dataTransfer', {
                value: {
                    getData: () => ''
                }
            });

            await board.handleDrop(dropEvent);
            expect(mockError).toHaveBeenCalledWith(expect.any(ValidationError));
        });
    });

    describe('Error Handling', () => {
        it('should handle WebSocket connection errors', () => {
            const mockError = vi.fn();
            const { component } = render(TaskBoard);
            const board = component as unknown as { handleError: (error: Error) => void };
            board.handleError = mockError;

            tasksSocket.connect = vi.fn().mockImplementation(() => {
                throw new Error('Connection failed');
            });

            render(TaskBoard);
            expect(mockError).toHaveBeenCalledWith(expect.any(Error));
        });

        it('should handle task validation errors', () => {
            const mockError = vi.fn();
            const { component } = render(TaskBoard);
            const board = component as unknown as { 
                tasks: Task[];
                handleError: (error: Error | ValidationError) => void;
            };
            board.handleError = mockError;

            const invalidTask = { ...mockTask, id: '' };
            board.tasks = [invalidTask as Task];

            expect(mockError).toHaveBeenCalledWith(expect.any(ValidationError));
        });
    });
});
