import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, waitFor } from '@testing-library/svelte';
import SearchPage from '../../../routes/search/+page.svelte';
import { searchStore } from '$lib/stores/search';
import { TaskState } from '$lib/types/task';
import type { Task } from '$lib/types/task';

describe('Search Page', () => {
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

    // Mock window.location
    const originalLocation = window.location;
    const originalFetch = global.fetch;
    const originalAbortController = global.AbortController;

    beforeEach(() => {
        // Mock window.location
        // @ts-expect-error - Mocking window.location
        delete window.location;
        window.location = {
            ...originalLocation,
            search: '',
            href: 'http://localhost:3000/search',
        };
        window.history.replaceState = vi.fn();

        // Mock fetch
        global.fetch = vi.fn();

        // Reset store
        searchStore.reset();
    });

    afterEach(() => {
        window.location = originalLocation;
        global.fetch = originalFetch;
        global.AbortController = originalAbortController;
        vi.clearAllMocks();
    });

    it('should render search page with header', () => {
        const { getByText } = render(SearchPage);
        
        expect(getByText('Search Tasks')).toBeTruthy();
        expect(getByText('Search across all tasks using filters, sorting, and pagination.')).toBeTruthy();
    });

    it('should show loading state while fetching results', async () => {
        // Mock fetch to delay response
        vi.useFakeTimers();
        global.fetch = vi.fn().mockImplementation(() => new Promise(() => {}));

        const { getByText } = render(SearchPage);
        
        // Initial load
        expect(getByText('Loading tasks...')).toBeTruthy();

        vi.useRealTimers();
    });

    it('should handle successful API response', async () => {
        global.fetch = vi.fn().mockResolvedValueOnce({
            ok: true,
            json: () => Promise.resolve({
                tasks: mockTasks,
                totalItems: 2,
                totalPages: 1
            })
        } as Response);

        const { getByText } = render(SearchPage);

        await waitFor(() => {
            expect(getByText('Task 1')).toBeTruthy();
            expect(getByText('Task 2')).toBeTruthy();
        });
    });

    it('should handle API error', async () => {
        global.fetch = vi.fn().mockRejectedValueOnce(new Error('API Error'));

        const { getByText } = render(SearchPage);

        await waitFor(() => {
            expect(getByText('Failed to fetch search results')).toBeTruthy();
        });
    });

    it('should cancel previous request when new search is made', async () => {
        const abortSpy = vi.fn();
        const mockSignal = { aborted: false } as AbortSignal;
        const mockController = {
            signal: mockSignal,
            abort: abortSpy
        } as unknown as AbortController;

        global.AbortController = vi.fn().mockImplementation(() => mockController);
        global.fetch = vi.fn().mockImplementation(() => new Promise(() => {}));

        render(SearchPage);

        // Initial search
        searchStore.setText('first');
        await new Promise(resolve => setTimeout(resolve, 300)); // Wait for debounce

        // Second search before first completes
        searchStore.setText('second');
        await new Promise(resolve => setTimeout(resolve, 300)); // Wait for debounce

        expect(abortSpy).toHaveBeenCalledTimes(1);
    });

    it('should cleanup pending requests on unmount', async () => {
        const abortSpy = vi.fn();
        const mockSignal = { aborted: false } as AbortSignal;
        const mockController = {
            signal: mockSignal,
            abort: abortSpy
        } as unknown as AbortController;

        global.AbortController = vi.fn().mockImplementation(() => mockController);
        global.fetch = vi.fn().mockImplementation(() => new Promise(() => {}));

        const { unmount } = render(SearchPage);

        // Trigger a search
        searchStore.setText('test');
        await new Promise(resolve => setTimeout(resolve, 300)); // Wait for debounce

        unmount();

        expect(abortSpy).toHaveBeenCalledTimes(1);
    });

    it('should ignore AbortError when request is cancelled', async () => {
        const abortError = new Error('Aborted');
        abortError.name = 'AbortError';

        global.fetch = vi.fn()
            .mockRejectedValueOnce(abortError)
            .mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({
                    tasks: mockTasks,
                    totalItems: 2,
                    totalPages: 1
                })
            } as Response);

        const { queryByText, getByText } = render(SearchPage);

        // First search gets aborted
        searchStore.setText('first');
        await new Promise(resolve => setTimeout(resolve, 300)); // Wait for debounce

        // Should not show error for aborted request
        expect(queryByText('Failed to fetch search results')).toBeNull();

        // Second search succeeds
        searchStore.setText('second');
        await new Promise(resolve => setTimeout(resolve, 300)); // Wait for debounce

        await waitFor(() => {
            expect(getByText('Task 1')).toBeTruthy();
            expect(getByText('Task 2')).toBeTruthy();
        });
    });
});
