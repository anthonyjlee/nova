import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import SortControls from '$lib/components/search/SortControls.svelte';
import type { SortConfig } from '$lib/types/search';

describe('SortControls', () => {
    it('should render with default sort config', () => {
        const { getByTestId } = render(SortControls);
        
        const sortField = getByTestId('sort-field') as HTMLSelectElement;
        const sortDesc = getByTestId('sort-desc') as HTMLInputElement;
        
        expect(sortField.value).toBe('updated_at');
        expect(sortDesc.checked).toBe(true);
    });

    it('should render with provided sort config', () => {
        const sort: SortConfig = {
            field: 'created_at',
            direction: 'asc'
        };

        const { getByTestId } = render(SortControls, { props: { sort } });
        
        const sortField = getByTestId('sort-field') as HTMLSelectElement;
        const sortAsc = getByTestId('sort-asc') as HTMLInputElement;
        
        expect(sortField.value).toBe('created_at');
        expect(sortAsc.checked).toBe(true);
    });

    it('should emit sort event when field changes', async () => {
        const { getByTestId, component } = render(SortControls);
        const mockSort = vi.fn();
        component.$on('sort', mockSort);

        const sortField = getByTestId('sort-field');
        await fireEvent.change(sortField, { target: { value: 'label' } });

        expect(mockSort).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: {
                    field: 'label',
                    direction: 'desc'
                }
            })
        );
    });

    it('should emit sort event when direction changes', async () => {
        const { getByTestId, component } = render(SortControls);
        const mockSort = vi.fn();
        component.$on('sort', mockSort);

        const sortAsc = getByTestId('sort-asc');
        await fireEvent.click(sortAsc);

        expect(mockSort).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: {
                    field: 'updated_at',
                    direction: 'asc'
                }
            })
        );
    });

    it('should render all sort field options', () => {
        const { getByText } = render(SortControls);
        
        expect(getByText('Created Date')).toBeTruthy();
        expect(getByText('Updated Date')).toBeTruthy();
        expect(getByText('Name')).toBeTruthy();
        expect(getByText('Status')).toBeTruthy();
        expect(getByText('Priority')).toBeTruthy();
    });

    it('should maintain sort direction when changing field', async () => {
        const { getByTestId, component } = render(SortControls);
        const mockSort = vi.fn();
        component.$on('sort', mockSort);

        // Change to ascending
        const sortAsc = getByTestId('sort-asc');
        await fireEvent.click(sortAsc);

        // Change field
        const sortField = getByTestId('sort-field');
        await fireEvent.change(sortField, { target: { value: 'label' } });

        // Should maintain ascending direction
        expect(mockSort).toHaveBeenLastCalledWith(
            expect.objectContaining({
                detail: {
                    field: 'label',
                    direction: 'asc'
                }
            })
        );
    });

    it('should maintain field when changing direction', async () => {
        const sort: SortConfig = {
            field: 'label',
            direction: 'desc'
        };

        const { getByTestId, component } = render(SortControls, { props: { sort } });
        const mockSort = vi.fn();
        component.$on('sort', mockSort);

        // Change direction
        const sortAsc = getByTestId('sort-asc');
        await fireEvent.click(sortAsc);

        // Should maintain label field
        expect(mockSort).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: {
                    field: 'label',
                    direction: 'asc'
                }
            })
        );
    });

    it('should handle multiple direction changes', async () => {
        const { getByTestId, component } = render(SortControls);
        const mockSort = vi.fn();
        component.$on('sort', mockSort);

        const sortAsc = getByTestId('sort-asc');
        const sortDesc = getByTestId('sort-desc');

        // Change to ascending
        await fireEvent.click(sortAsc);
        expect(mockSort).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: {
                    field: 'updated_at',
                    direction: 'asc'
                }
            })
        );

        // Change back to descending
        await fireEvent.click(sortDesc);
        expect(mockSort).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: {
                    field: 'updated_at',
                    direction: 'desc'
                }
            })
        );
    });

    it('should handle multiple field changes', async () => {
        const { getByTestId, component } = render(SortControls);
        const mockSort = vi.fn();
        component.$on('sort', mockSort);

        const sortField = getByTestId('sort-field');

        // Change to label
        await fireEvent.change(sortField, { target: { value: 'label' } });
        expect(mockSort).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: {
                    field: 'label',
                    direction: 'desc'
                }
            })
        );

        // Change to status
        await fireEvent.change(sortField, { target: { value: 'status' } });
        expect(mockSort).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: {
                    field: 'status',
                    direction: 'desc'
                }
            })
        );
    });
});
