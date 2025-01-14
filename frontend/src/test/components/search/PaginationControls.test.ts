import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import PaginationControls from '$lib/components/search/PaginationControls.svelte';
import type { PaginationConfig } from '$lib/types/search';

describe('PaginationControls', () => {
    it('should render with default pagination config', () => {
        const { getByTestId, getByText } = render(PaginationControls);
        
        expect(getByTestId('page-1')).toBeTruthy();
        expect(getByTestId('page-size')).toBeTruthy();
        expect(getByText('Items per page:')).toBeTruthy();
    });

    it('should render with provided pagination config', () => {
        const pagination: PaginationConfig = {
            page: 2,
            pageSize: 50,
            totalItems: 100,
            totalPages: 2
        };

        const { getByTestId } = render(PaginationControls, { props: { pagination } });
        
        const pageSize = getByTestId('page-size') as HTMLSelectElement;
        expect(pageSize.value).toBe('50');
        expect(getByTestId('page-2')).toHaveClass('active');
    });

    it('should emit paginate event when page changes', async () => {
        const pagination: PaginationConfig = {
            page: 1,
            pageSize: 20,
            totalItems: 100,
            totalPages: 5
        };

        const { getByTestId, component } = render(PaginationControls, {
            props: { pagination }
        });
        const mockPaginate = vi.fn();
        component.$on('paginate', mockPaginate);

        await fireEvent.click(getByTestId('page-2'));

        expect(mockPaginate).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: {
                    page: 2,
                    pageSize: 20,
                    totalItems: 100,
                    totalPages: 5
                }
            })
        );
    });

    it('should emit paginate event when page size changes', async () => {
        const pagination: PaginationConfig = {
            page: 2,
            pageSize: 20,
            totalItems: 100,
            totalPages: 5
        };

        const { getByTestId, component } = render(PaginationControls, {
            props: { pagination }
        });
        const mockPaginate = vi.fn();
        component.$on('paginate', mockPaginate);

        const pageSize = getByTestId('page-size');
        await fireEvent.change(pageSize, { target: { value: '50' } });

        expect(mockPaginate).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: {
                    page: 1, // Should reset to first page
                    pageSize: 50,
                    totalItems: 100,
                    totalPages: 2 // New total pages based on page size
                }
            })
        );
    });

    it('should handle next/previous navigation', async () => {
        const pagination: PaginationConfig = {
            page: 2,
            pageSize: 20,
            totalItems: 100,
            totalPages: 5
        };

        const { getByTestId, component } = render(PaginationControls, {
            props: { pagination }
        });
        const mockPaginate = vi.fn();
        component.$on('paginate', mockPaginate);

        // Test next page
        await fireEvent.click(getByTestId('next-page'));
        expect(mockPaginate).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({ page: 3 })
            })
        );

        // Test previous page
        await fireEvent.click(getByTestId('prev-page'));
        expect(mockPaginate).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({ page: 2 })
            })
        );
    });

    it('should disable navigation buttons at boundaries', () => {
        const pagination: PaginationConfig = {
            page: 1,
            pageSize: 20,
            totalItems: 20,
            totalPages: 1
        };

        const { getByTestId } = render(PaginationControls, {
            props: { pagination }
        });

        expect(getByTestId('prev-page')).toBeDisabled();
        expect(getByTestId('next-page')).toBeDisabled();
    });

    it('should show correct item range text', () => {
        const pagination: PaginationConfig = {
            page: 2,
            pageSize: 20,
            totalItems: 45,
            totalPages: 3
        };

        const { getByText } = render(PaginationControls, {
            props: { pagination }
        });

        expect(getByText('Showing 21 - 40 of 45 items')).toBeTruthy();
    });

    it('should handle last page item range text', () => {
        const pagination: PaginationConfig = {
            page: 3,
            pageSize: 20,
            totalItems: 45,
            totalPages: 3
        };

        const { getByText } = render(PaginationControls, {
            props: { pagination }
        });

        expect(getByText('Showing 41 - 45 of 45 items')).toBeTruthy();
    });

    it('should render ellipsis for many pages', () => {
        const pagination: PaginationConfig = {
            page: 5,
            pageSize: 10,
            totalItems: 100,
            totalPages: 10
        };

        const { getByText, getAllByText } = render(PaginationControls, {
            props: { pagination }
        });

        const ellipses = getAllByText('...');
        expect(ellipses).toHaveLength(2); // Should show ellipsis on both sides
        expect(getByText('1')).toBeTruthy(); // First page
        expect(getByText('10')).toBeTruthy(); // Last page
    });

    it('should handle custom page size options', () => {
        const customPageSizes = [5, 15, 25];
        const { getByTestId } = render(PaginationControls, {
            props: { pageSizeOptions: customPageSizes }
        });

        const pageSize = getByTestId('page-size') as HTMLSelectElement;
        const options = Array.from(pageSize.options).map(opt => Number(opt.value));
        expect(options).toEqual(customPageSizes);
    });

    it('should prevent navigation beyond bounds', async () => {
        const pagination: PaginationConfig = {
            page: 2,
            pageSize: 20,
            totalItems: 60,
            totalPages: 3
        };

        const { getByTestId, component } = render(PaginationControls, {
            props: { pagination }
        });
        const mockPaginate = vi.fn();
        component.$on('paginate', mockPaginate);

        // Try to go beyond last page
        for (let i = 0; i < 5; i++) {
            await fireEvent.click(getByTestId('next-page'));
        }

        // Should not go beyond page 3
        expect(mockPaginate).toHaveBeenLastCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({ page: 3 })
            })
        );

        // Try to go before first page
        for (let i = 0; i < 5; i++) {
            await fireEvent.click(getByTestId('prev-page'));
        }

        // Should not go before page 1
        expect(mockPaginate).toHaveBeenLastCalledWith(
            expect.objectContaining({
                detail: expect.objectContaining({ page: 1 })
            })
        );
    });
});
