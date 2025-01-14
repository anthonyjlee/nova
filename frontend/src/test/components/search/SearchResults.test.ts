import { describe, it, expect } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import SearchResults from '$lib/components/search/SearchResults.svelte';
import { TaskState } from '$lib/types/task';
import type { Task } from '$lib/types/task';

describe('SearchResults', () => {
    const mockTasks: Task[] = [
        {
            id: '1',
            type: 'task',
            label: 'Task 1',
            description: 'Description 1',
            status: TaskState.PENDING,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            metadata: {}
        },
        {
            id: '2',
            type: 'task',
            label: 'Task 2',
            description: 'Description 2',
            status: TaskState.IN_PROGRESS,
            created_at: '2025-01-02T00:00:00Z',
            updated_at: '2025-01-02T00:00:00Z',
            metadata: {}
        }
    ];

    it('should render loading state', () => {
        const { getByText } = render(SearchResults, {
            props: { loading: true }
        });
        
        expect(getByText('Loading tasks...')).toBeTruthy();
    });

    it('should render error state', () => {
        const error = new Error('Test error');
        const { getByText } = render(SearchResults, {
            props: { error }
        });
        
        expect(getByText('Error loading tasks')).toBeTruthy();
        expect(getByText('Test error')).toBeTruthy();
    });

    it('should render empty state with default message', () => {
        const { getByText } = render(SearchResults);
        
        expect(getByText('No tasks found')).toBeTruthy();
    });

    it('should render empty state with custom message', () => {
        const { getByText } = render(SearchResults, {
            props: { emptyMessage: 'Custom empty message' }
        });
        
        expect(getByText('Custom empty message')).toBeTruthy();
    });

    it('should render task list', () => {
        const { getByText, getAllByTestId } = render(SearchResults, {
            props: { tasks: mockTasks }
        });
        
        expect(getByText('Task 1')).toBeTruthy();
        expect(getByText('Task 2')).toBeTruthy();
        expect(getAllByTestId('task-card')).toHaveLength(2);
    });

    it('should not show empty state when loading', () => {
        const { queryByText } = render(SearchResults, {
            props: { loading: true }
        });
        
        expect(queryByText('No tasks found')).toBeNull();
    });

    it('should not show empty state when error', () => {
        const { queryByText } = render(SearchResults, {
            props: { error: new Error('Test error') }
        });
        
        expect(queryByText('No tasks found')).toBeNull();
    });

    it('should not show loading state when has tasks', () => {
        const { queryByText } = render(SearchResults, {
            props: { tasks: mockTasks, loading: true }
        });
        
        expect(queryByText('Loading tasks...')).toBeNull();
    });

    it('should not show error state when loading', () => {
        const { queryByText } = render(SearchResults, {
            props: { 
                error: new Error('Test error'),
                loading: true
            }
        });
        
        expect(queryByText('Error loading tasks')).toBeNull();
    });

    it('should handle task card interactions', async () => {
        const { getAllByTestId } = render(SearchResults, {
            props: { tasks: mockTasks }
        });
        
        const cards = getAllByTestId('task-card');
        await fireEvent.click(cards[0]);
        
        // TaskCard component should handle the click event
        // We're just verifying the structure here
        expect(cards[0]).toHaveClass('task-card-wrapper');
    });

    it('should update when tasks change', async () => {
        const { component, getAllByTestId } = render(SearchResults, {
            props: { tasks: mockTasks }
        });
        
        expect(getAllByTestId('task-card')).toHaveLength(2);
        
        const newTasks = [...mockTasks, {
            id: '3',
            type: 'task',
            label: 'Task 3',
            description: 'Description 3',
            status: TaskState.COMPLETED,
            created_at: '2025-01-03T00:00:00Z',
            updated_at: '2025-01-03T00:00:00Z',
            metadata: {}
        }];
        
        await component.$set({ tasks: newTasks });
        expect(getAllByTestId('task-card')).toHaveLength(3);
    });

    it('should handle transitions between states', async () => {
        const { component, queryByText } = render(SearchResults);
        
        // Start with empty state
        expect(queryByText('No tasks found')).toBeTruthy();
        
        // Show loading
        await component.$set({ loading: true });
        expect(queryByText('Loading tasks...')).toBeTruthy();
        expect(queryByText('No tasks found')).toBeNull();
        
        // Show error
        await component.$set({ 
            loading: false,
            error: new Error('Test error')
        });
        expect(queryByText('Error loading tasks')).toBeTruthy();
        expect(queryByText('Loading tasks...')).toBeNull();
        
        // Show results
        await component.$set({
            error: null,
            tasks: mockTasks
        });
        expect(queryByText('Task 1')).toBeTruthy();
        expect(queryByText('Error loading tasks')).toBeNull();
    });
});
