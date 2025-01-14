import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import TaskColumn from '$lib/components/TaskColumn.svelte';
import type { Task } from '$lib/types/task';
import { TaskState } from '$lib/types/task';
import { ValidationError } from '$lib/utils/validation';

describe('TaskColumn', () => {
    const mockTask: Task = {
        id: '123',
        label: 'Test Task',
        type: 'task',
        status: TaskState.PENDING,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {}
    };

    const defaultProps = {
        title: 'Test Column',
        tasks: [mockTask],
        state: TaskState.PENDING,
        systemState: 'initialized' as const,
        isCompleted: false,
        isDragging: false,
        draggedTask: null
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('Rendering', () => {
        it('should render column title', () => {
            const { getByText } = render(TaskColumn, defaultProps);
            expect(getByText('Test Column')).toBeTruthy();
        });

        it('should render task count', () => {
            const { getByText } = render(TaskColumn, defaultProps);
            expect(getByText('(1)')).toBeTruthy();
        });

        it('should render tasks', () => {
            const { getByText } = render(TaskColumn, defaultProps);
            expect(getByText('Test Task')).toBeTruthy();
        });
    });

    describe('State Transitions', () => {
        const validTransitions: Record<TaskState, TaskState[]> = {
            [TaskState.PENDING]: [TaskState.IN_PROGRESS, TaskState.BLOCKED],
            [TaskState.IN_PROGRESS]: [TaskState.BLOCKED, TaskState.COMPLETED, TaskState.PENDING],
            [TaskState.BLOCKED]: [TaskState.PENDING, TaskState.IN_PROGRESS],
            [TaskState.COMPLETED]: [TaskState.IN_PROGRESS]
        };

        Object.entries(validTransitions).forEach(([fromState, toStates]) => {
            describe(`From ${fromState}`, () => {
                toStates.forEach(toState => {
                    it(`should allow transition to ${toState}`, () => {
                        const { container } = render(TaskColumn, {
                            ...defaultProps,
                            state: toState,
                            draggedTask: { ...mockTask, status: fromState as TaskState }
                        });

                        const column = container.querySelector('[data-column]');
                        expect(column?.classList.contains('can-drop')).toBe(true);
                    });
                });

                // Test invalid transitions
                const allStates: TaskState[] = [
                    TaskState.PENDING,
                    TaskState.IN_PROGRESS,
                    TaskState.BLOCKED,
                    TaskState.COMPLETED
                ];
                allStates
                    .filter(state => !toStates.includes(state) && state !== fromState)
                    .forEach(invalidState => {
                        it(`should not allow transition to ${invalidState}`, () => {
                            const { container } = render(TaskColumn, {
                                ...defaultProps,
                                state: invalidState,
                                draggedTask: { ...mockTask, status: fromState as TaskState }
                            });

                            const column = container.querySelector('[data-column]');
                            expect(column?.classList.contains('can-drop')).toBe(false);
                        });
                    });
            });
        });
    });

    describe('Drag and Drop', () => {
        it('should handle dragover event', async () => {
            const { container } = render(TaskColumn, {
                ...defaultProps,
                isDragging: true,
                draggedTask: { ...mockTask, status: TaskState.PENDING }
            });

            const column = container.querySelector('[data-column]');
            await fireEvent.dragOver(column as HTMLElement);

            // Column should show it can accept the drop
            expect(column?.classList.contains('can-drop')).toBe(true);
        });

        it('should prevent invalid state transitions on dragover', async () => {
            const { container } = render(TaskColumn, {
                ...defaultProps,
                state: TaskState.COMPLETED,
                isDragging: true,
                draggedTask: { ...mockTask, status: TaskState.BLOCKED }
            });

            const column = container.querySelector('[data-column]');
            await fireEvent.dragOver(column as HTMLElement);

            // Column should not show it can accept the drop
            expect(column?.classList.contains('can-drop')).toBe(false);
        });

        it('should handle drop event', async () => {
            const mockDispatch = vi.fn();
            const { container } = render(TaskColumn, {
                ...defaultProps,
                isDragging: true,
                draggedTask: { ...mockTask, status: TaskState.PENDING }
            });

            const element = container.querySelector('[data-column]') as HTMLElement;
            element.dispatchEvent = mockDispatch;

            const column = container.querySelector('[data-column]');
            await fireEvent.drop(column as HTMLElement);

            expect(mockDispatch).toHaveBeenCalled();
        });

        it('should validate task before drop', async () => {
            const invalidTask = { ...mockTask, id: '' } as Task;
            const { container } = render(TaskColumn, {
                ...defaultProps,
                isDragging: true,
                draggedTask: invalidTask
            });

            const column = container.querySelector('[data-column]');
            await fireEvent.drop(column as HTMLElement);

            // Should not allow drop of invalid task
            expect(column?.classList.contains('can-drop')).toBe(false);
        });
    });

    describe('Error Handling', () => {
        it('should handle validation errors', () => {
            const mockError = vi.fn();
            const { component } = render(TaskColumn, {
                ...defaultProps,
                tasks: [{ ...mockTask, id: '' } as Task]
            });

            const instance = component as unknown as { handleError: (e: Error | ValidationError) => void };
            instance.handleError = mockError;

            expect(mockError).toHaveBeenCalledWith(expect.any(ValidationError));
        });

        it('should handle system state errors', async () => {
            const { container } = render(TaskColumn, {
                ...defaultProps,
                systemState: 'error'
            });

            const column = container.querySelector('[data-column]');
            expect(column?.classList.contains('cursor-not-allowed')).toBe(true);
        });
    });
});
