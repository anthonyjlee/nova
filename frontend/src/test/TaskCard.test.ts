import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/svelte';
import TaskCard from '$lib/components/TaskCard.svelte';
import { TaskState } from '$lib/types/task';
import type { Task } from '$lib/types/task';
import { ValidationError } from '$lib/utils/validation';

describe('TaskCard', () => {
    const mockTask: Task = {
        id: '123',
        label: 'Test Task',
        type: 'task',
        status: TaskState.PENDING,
        description: 'Test description',
        team_id: 'team1',
        domain: 'test-domain',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {}
    };

    const defaultProps = {
        task: mockTask,
        isCompleted: false,
        systemState: 'initialized' as const
    };

    describe('Rendering', () => {
        it('should render task label', () => {
            const { getByText } = render(TaskCard, defaultProps);
            expect(getByText('Test Task')).toBeTruthy();
        });

        it('should render task ID', () => {
            const { getByText } = render(TaskCard, defaultProps);
            expect(getByText('#123')).toBeTruthy();
        });

        it('should render task description when present', () => {
            const { getByText } = render(TaskCard, defaultProps);
            expect(getByText('Test description')).toBeTruthy();
        });

        it('should render team ID when present', () => {
            const { getByText } = render(TaskCard, defaultProps);
            expect(getByText('Team: team1')).toBeTruthy();
        });

        it('should render domain badge when present', () => {
            const { getByText } = render(TaskCard, defaultProps);
            expect(getByText('test-domain')).toBeTruthy();
        });

        it('should apply completed styles when task is completed', () => {
            const { container } = render(TaskCard, {
                ...defaultProps,
                isCompleted: true
            });
            expect(container.firstChild).toHaveClass('opacity-75');
        });
    });

    describe('System State Handling', () => {
        it('should disable drag when system is not initialized', () => {
            const { container } = render(TaskCard, {
                ...defaultProps,
                systemState: 'initializing'
            });
            expect(container.firstChild).toHaveClass('cursor-not-allowed');
            expect(container.firstChild).toHaveClass('opacity-50');
        });

        it('should show initializing state', () => {
            const { getByText } = render(TaskCard, {
                ...defaultProps,
                systemState: 'initializing'
            });
            expect(getByText('Initializing...')).toBeTruthy();
        });

        it('should show error state', () => {
            const { getByText } = render(TaskCard, {
                ...defaultProps,
                systemState: 'error'
            });
            expect(getByText('System Error')).toBeTruthy();
        });
    });

    describe('Drag and Drop', () => {
        it('should handle dragstart event', () => {
            const { container } = render(TaskCard, defaultProps);
            const card = container.firstChild as HTMLElement;
            const mockDataTransfer = {
                setData: vi.fn(),
                effectAllowed: null
            };

            const dragEvent = new Event('dragstart') as DragEvent;
            Object.defineProperty(dragEvent, 'dataTransfer', {
                value: mockDataTransfer
            });

            card.dispatchEvent(dragEvent);
            expect(mockDataTransfer.setData).toHaveBeenCalledWith('text/plain', '123');
            expect(mockDataTransfer.effectAllowed).toBe('move');
        });

        it('should prevent drag when system is not initialized', () => {
            const { container } = render(TaskCard, {
                ...defaultProps,
                systemState: 'initializing'
            });
            const card = container.firstChild as HTMLElement;
            const mockDataTransfer = {
                setData: vi.fn(),
                effectAllowed: null
            };

            const dragEvent = new Event('dragstart') as DragEvent;
            Object.defineProperty(dragEvent, 'dataTransfer', {
                value: mockDataTransfer
            });

            card.dispatchEvent(dragEvent);
            expect(mockDataTransfer.setData).not.toHaveBeenCalled();
        });

        it('should handle dragend event', () => {
            const { container } = render(TaskCard, defaultProps);
            const card = container.firstChild as HTMLElement;

            // Start drag
            const dragStartEvent = new Event('dragstart') as DragEvent;
            Object.defineProperty(dragStartEvent, 'dataTransfer', {
                value: {
                    setData: vi.fn(),
                    effectAllowed: null
                }
            });
            card.dispatchEvent(dragStartEvent);

            // End drag
            const dragEndEvent = new Event('dragend');
            card.dispatchEvent(dragEndEvent);

            expect(card.classList.contains('border-2')).toBe(false);
        });
    });

    describe('Error Handling', () => {
        it('should handle validation errors', () => {
            const mockError = vi.fn();
            const invalidTask = { ...mockTask, id: '' };
            const { component } = render(TaskCard, {
                ...defaultProps,
                task: invalidTask as Task
            });

            const instance = component as unknown as { handleError: (error: Error | ValidationError) => void };
            instance.handleError = mockError;

            expect(mockError).toHaveBeenCalledWith(expect.any(ValidationError));
        });

        it('should handle drag operation errors', () => {
            const mockDispatch = vi.fn();
            const { container } = render(TaskCard, defaultProps);
            const card = container.firstChild as HTMLElement;

            Object.defineProperty(card, 'dispatchEvent', {
                value: mockDispatch,
                configurable: true
            });

            const dragEvent = new Event('dragstart') as DragEvent;
            Object.defineProperty(dragEvent, 'dataTransfer', {
                value: null
            });

            card.dispatchEvent(dragEvent);
            expect(mockDispatch).toHaveBeenCalledWith(expect.objectContaining({
                detail: expect.objectContaining({
                    message: expect.any(String),
                    retryable: true
                })
            }));
        });
    });

    describe('Date Formatting', () => {
        it('should format created_at date', () => {
            const date = new Date('2025-01-15T12:00:00Z');
            const { getByText } = render(TaskCard, {
                ...defaultProps,
                task: {
                    ...mockTask,
                    created_at: date.toISOString()
                }
            });

            // Note: Exact format will depend on locale, just check for presence
            expect(getByText(/Created:/)).toBeTruthy();
        });

        it('should format updated_at date', () => {
            const date = new Date('2025-01-15T12:00:00Z');
            const { getByText } = render(TaskCard, {
                ...defaultProps,
                task: {
                    ...mockTask,
                    updated_at: date.toISOString()
                }
            });

            // Note: Exact format will depend on locale, just check for presence
            expect(getByText(/Updated:/)).toBeTruthy();
        });
    });
});
