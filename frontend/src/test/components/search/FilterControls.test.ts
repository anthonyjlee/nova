import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import FilterControls from '$lib/components/search/FilterControls.svelte';
import { TaskState } from '$lib/types/task';
import type { TaskFilter } from '$lib/types/search';

describe('FilterControls', () => {
    it('should render all filter sections by default', () => {
        const { getByText, getByTestId } = render(FilterControls);
        
        expect(getByText('Status')).toBeTruthy();
        expect(getByText('Priority')).toBeTruthy();
        expect(getByText('Assignee')).toBeTruthy();
        expect(getByText('Date Range')).toBeTruthy();
        expect(getByTestId('reset-filters')).toBeTruthy();
    });

    it('should hide sections based on props', () => {
        const { queryByText } = render(FilterControls, {
            props: {
                showStatusFilter: false,
                showPriorityFilter: false,
                showDateFilter: false,
                showAssigneeFilter: false
            }
        });
        
        expect(queryByText('Status')).toBeNull();
        expect(queryByText('Priority')).toBeNull();
        expect(queryByText('Assignee')).toBeNull();
        expect(queryByText('Date Range')).toBeNull();
    });

    it('should initialize with provided filter values', () => {
        const initialFilter: TaskFilter = {
            status: [TaskState.PENDING],
            priority: ['high'],
            assignee: ['user1'],
            dateRange: {
                from: '2025-01-01',
                to: '2025-01-31'
            }
        };

        const { getByTestId } = render(FilterControls, {
            props: { filter: initialFilter }
        });

        expect(getByTestId(`status-${TaskState.PENDING}`)).toBeChecked();
        expect(getByTestId('priority-high')).toBeChecked();
        expect(getByTestId('date-from')).toHaveValue('2025-01-01');
        expect(getByTestId('date-to')).toHaveValue('2025-01-31');
    });

    it('should emit filter event when status changes', async () => {
        const { getByTestId, component } = render(FilterControls);
        const mockFilter = vi.fn();
        component.$on('filter', mockFilter);

        const checkbox = getByTestId(`status-${TaskState.PENDING}`);
        await fireEvent.click(checkbox);

        expect(mockFilter).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    status: [TaskState.PENDING]
                })
            })
        );
    });

    it('should emit filter event when priority changes', async () => {
        const { getByTestId, component } = render(FilterControls);
        const mockFilter = vi.fn();
        component.$on('filter', mockFilter);

        const checkbox = getByTestId('priority-high');
        await fireEvent.click(checkbox);

        expect(mockFilter).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    priority: ['high']
                })
            })
        );
    });

    it('should emit filter event when date range changes', async () => {
        const { getByTestId, component } = render(FilterControls);
        const mockFilter = vi.fn();
        component.$on('filter', mockFilter);

        const dateFrom = getByTestId('date-from');
        await fireEvent.input(dateFrom, { target: { value: '2025-01-01' } });

        expect(mockFilter).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    dateRange: expect.objectContaining({
                        from: '2025-01-01'
                    })
                })
            })
        );
    });

    it('should reset all filters when reset button is clicked', async () => {
        const initialFilter: TaskFilter = {
            status: [TaskState.PENDING],
            priority: ['high'],
            assignee: ['user1'],
            dateRange: {
                from: '2025-01-01',
                to: '2025-01-31'
            }
        };

        const { getByTestId, component } = render(FilterControls, {
            props: { filter: initialFilter }
        });

        const mockReset = vi.fn();
        const mockFilter = vi.fn();
        component.$on('reset', mockReset);
        component.$on('filter', mockFilter);

        const resetButton = getByTestId('reset-filters');
        await fireEvent.click(resetButton);

        expect(mockReset).toHaveBeenCalled();
        expect(mockFilter).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    status: undefined,
                    priority: undefined,
                    assignee: undefined,
                    dateRange: undefined
                })
            })
        );

        // Verify inputs are reset
        expect(getByTestId(`status-${TaskState.PENDING}`)).not.toBeChecked();
        expect(getByTestId('priority-high')).not.toBeChecked();
        expect(getByTestId('date-from')).toHaveValue('');
        expect(getByTestId('date-to')).toHaveValue('');
    });

    it('should handle multiple status selections', async () => {
        const { getByTestId, component } = render(FilterControls);
        const mockFilter = vi.fn();
        component.$on('filter', mockFilter);

        await fireEvent.click(getByTestId(`status-${TaskState.PENDING}`));
        await fireEvent.click(getByTestId(`status-${TaskState.IN_PROGRESS}`));

        expect(mockFilter).toHaveBeenLastCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    status: [TaskState.PENDING, TaskState.IN_PROGRESS]
                })
            })
        );
    });

    it('should handle multiple priority selections', async () => {
        const { getByTestId, component } = render(FilterControls);
        const mockFilter = vi.fn();
        component.$on('filter', mockFilter);

        await fireEvent.click(getByTestId('priority-high'));
        await fireEvent.click(getByTestId('priority-medium'));

        expect(mockFilter).toHaveBeenLastCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    priority: ['high', 'medium']
                })
            })
        );
    });

    it('should handle assignee selection', async () => {
        const { getByTestId, component } = render(FilterControls);
        const mockFilter = vi.fn();
        component.$on('filter', mockFilter);

        const select = getByTestId('assignee-select') as HTMLSelectElement;
        select.options[0].selected = true;
        await fireEvent.change(select);

        expect(mockFilter).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({
                    assignee: ['user1']
                })
            })
        );
    });
});
