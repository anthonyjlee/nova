import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import SearchPanel from '$lib/components/search/SearchPanel.svelte';
import { TaskState } from '$lib/types/task';
import type { TaskFilter, SortConfig, PaginationConfig } from '$lib/types/search';

describe('SearchPanel', () => {
    it('should render all search components', () => {
        const { getByTestId, getByText } = render(SearchPanel);
        
        // Search input
        expect(getByTestId('search-input')).toBeTruthy();
        
        // Filter controls
        expect(getByText('Status')).toBeTruthy();
        expect(getByText('Priority')).toBeTruthy();
        
        // Sort controls
        expect(getByText('Sort By')).toBeTruthy();
        expect(getByTestId('sort-field')).toBeTruthy();
        
        // Pagination controls
        expect(getByText('Items per page:')).toBeTruthy();
        expect(getByTestId('page-size')).toBeTruthy();
    });

    it('should initialize with provided values', () => {
        const initialQuery = 'test query';
        const filter: TaskFilter = {
            status: [TaskState.PENDING]
        };
        const sort: SortConfig = {
            field: 'created_at',
            direction: 'asc'
        };
        const pagination: PaginationConfig = {
            page: 2,
            pageSize: 50,
            totalItems: 100,
            totalPages: 2
        };

        const { getByTestId, getByDisplayValue } = render(SearchPanel, {
            props: { initialQuery, filter, sort, pagination }
        });

        // Check search input
        expect(getByDisplayValue(initialQuery)).toBeTruthy();

        // Check filter
        expect(getByTestId(`status-${TaskState.PENDING}`)).toBeChecked();

        // Check sort
        const sortField = getByTestId('sort-field') as HTMLSelectElement;
        expect(sortField.value).toBe('created_at');
        expect(getByTestId('sort-asc')).toBeChecked();

        // Check pagination
        const pageSize = getByTestId('page-size') as HTMLSelectElement;
        expect(pageSize.value).toBe('50');
    });

    it('should emit search event when search input changes', async () => {
        const { getByTestId, component } = render(SearchPanel);
        const mockSearch = vi.fn();
        component.$on('search', mockSearch);

        const input = getByTestId('search-input');
        await fireEvent.input(input, { target: { value: 'test' } });

        // Wait for debounce
        await new Promise(resolve => setTimeout(resolve, 300));

        expect(mockSearch).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    text: 'test'
                })
            })
        );
    });

    it('should emit search event when filter changes', async () => {
        const { getByTestId, component } = render(SearchPanel);
        const mockSearch = vi.fn();
        component.$on('search', mockSearch);

        const statusCheckbox = getByTestId(`status-${TaskState.PENDING}`);
        await fireEvent.click(statusCheckbox);

        expect(mockSearch).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    filter: expect.objectContaining({
                        status: [TaskState.PENDING]
                    })
                })
            })
        );
    });

    it('should emit search event when sort changes', async () => {
        const { getByTestId, component } = render(SearchPanel);
        const mockSearch = vi.fn();
        component.$on('search', mockSearch);

        const sortField = getByTestId('sort-field');
        await fireEvent.change(sortField, { target: { value: 'label' } });

        expect(mockSearch).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    sort: expect.objectContaining({
                        field: 'label'
                    })
                })
            })
        );
    });

    it('should emit search event when pagination changes', async () => {
        const { getByTestId, component } = render(SearchPanel);
        const mockSearch = vi.fn();
        component.$on('search', mockSearch);

        const pageSize = getByTestId('page-size');
        await fireEvent.change(pageSize, { target: { value: '50' } });

        expect(mockSearch).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    pagination: expect.objectContaining({
                        pageSize: 50,
                        page: 1 // Should reset to first page
                    })
                })
            })
        );
    });

    it('should reset search when clear is clicked', async () => {
        const initialQuery = 'test query';
        const { getByTestId, component } = render(SearchPanel, {
            props: { initialQuery }
        });
        const mockSearch = vi.fn();
        component.$on('search', mockSearch);

        const clearButton = getByTestId('clear-search');
        await fireEvent.click(clearButton);

        expect(mockSearch).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    text: ''
                })
            })
        );
    });

    it('should maintain filter when changing sort', async () => {
        const filter: TaskFilter = {
            status: [TaskState.PENDING]
        };

        const { getByTestId, component } = render(SearchPanel, {
            props: { filter }
        });
        const mockSearch = vi.fn();
        component.$on('search', mockSearch);

        const sortField = getByTestId('sort-field');
        await fireEvent.change(sortField, { target: { value: 'label' } });

        expect(mockSearch).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    filter: expect.objectContaining({
                        status: [TaskState.PENDING]
                    }),
                    sort: expect.objectContaining({
                        field: 'label'
                    })
                })
            })
        );
    });

    it('should maintain sort when changing filter', async () => {
        const sort: SortConfig = {
            field: 'label',
            direction: 'asc'
        };

        const { getByTestId, component } = render(SearchPanel, {
            props: { sort }
        });
        const mockSearch = vi.fn();
        component.$on('search', mockSearch);

        const statusCheckbox = getByTestId(`status-${TaskState.PENDING}`);
        await fireEvent.click(statusCheckbox);

        expect(mockSearch).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    filter: expect.objectContaining({
                        status: [TaskState.PENDING]
                    }),
                    sort: expect.objectContaining({
                        field: 'label',
                        direction: 'asc'
                    })
                })
            })
        );
    });
});
