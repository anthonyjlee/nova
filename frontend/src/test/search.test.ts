import { describe, it, expect } from 'vitest';
import { TaskState } from '$lib/types/task';
import {
    isDateRange,
    isTaskFilter,
    isSortConfig,
    isPaginationConfig,
    isSearchQuery,
    createDefaultPagination,
    createDefaultSort,
    createEmptyFilter,
    createSearchQuery,
    calculateTotalPages,
    validatePageNumber,
    calculateOffset,
    applyDateFilter,
    createDateRange,
    type DateRange,
    type TaskFilter,
    type SortConfig,
    type PaginationConfig,
    type SearchQuery
} from '$lib/types/search';

describe('Search Types', () => {
    describe('Type Guards', () => {
        it('should validate date range', () => {
            const validRange: DateRange = {
                from: '2025-01-01',
                to: '2025-12-31'
            };
            const invalidRange = {
                from: 123,
                to: new Date()
            };

            expect(isDateRange(validRange)).toBe(true);
            expect(isDateRange(invalidRange)).toBe(false);
            expect(isDateRange(null)).toBe(false);
            expect(isDateRange(undefined)).toBe(false);
        });

        it('should validate task filter', () => {
            const validFilter: TaskFilter = {
                status: [TaskState.PENDING, TaskState.IN_PROGRESS],
                assignee: ['user1', 'user2'],
                dateRange: { from: '2025-01-01' }
            };
            const invalidFilter = {
                status: 'pending',
                assignee: 'user1'
            };

            expect(isTaskFilter(validFilter)).toBe(true);
            expect(isTaskFilter(invalidFilter)).toBe(false);
            expect(isTaskFilter(null)).toBe(false);
            expect(isTaskFilter(undefined)).toBe(false);
        });

        it('should validate sort config', () => {
            const validSort: SortConfig = {
                field: 'created_at',
                direction: 'asc'
            };
            const invalidSort = {
                field: 'created_at',
                direction: 'invalid'
            };

            expect(isSortConfig(validSort)).toBe(true);
            expect(isSortConfig(invalidSort)).toBe(false);
            expect(isSortConfig(null)).toBe(false);
            expect(isSortConfig(undefined)).toBe(false);
        });

        it('should validate pagination config', () => {
            const validPagination: PaginationConfig = {
                page: 1,
                pageSize: 20,
                totalItems: 100
            };
            const invalidPagination = {
                page: 0,
                pageSize: -1
            };

            expect(isPaginationConfig(validPagination)).toBe(true);
            expect(isPaginationConfig(invalidPagination)).toBe(false);
            expect(isPaginationConfig(null)).toBe(false);
            expect(isPaginationConfig(undefined)).toBe(false);
        });

        it('should validate search query', () => {
            const validQuery: SearchQuery = {
                text: 'search term',
                filter: { status: [TaskState.PENDING] },
                sort: { field: 'created_at', direction: 'desc' },
                pagination: { page: 1, pageSize: 20 }
            };
            const invalidQuery = {
                text: 123,
                pagination: { page: 0 }
            };

            expect(isSearchQuery(validQuery)).toBe(true);
            expect(isSearchQuery(invalidQuery)).toBe(false);
            expect(isSearchQuery(null)).toBe(false);
            expect(isSearchQuery(undefined)).toBe(false);
        });
    });

    describe('Helper Functions', () => {
        it('should create default pagination', () => {
            const pagination = createDefaultPagination();
            expect(pagination.page).toBe(1);
            expect(pagination.pageSize).toBe(20);

            const customPagination = createDefaultPagination(50);
            expect(customPagination.pageSize).toBe(50);
        });

        it('should create default sort', () => {
            const sort = createDefaultSort();
            expect(sort.field).toBe('updated_at');
            expect(sort.direction).toBe('desc');
        });

        it('should create empty filter', () => {
            const filter = createEmptyFilter();
            expect(Object.keys(filter)).toHaveLength(0);
        });

        it('should create search query', () => {
            const query = createSearchQuery('search term');
            expect(query.text).toBe('search term');
            expect(query.pagination.page).toBe(1);
            expect(query.sort?.direction).toBe('desc');

            const customQuery = createSearchQuery(
                'custom',
                { status: [TaskState.PENDING] },
                { field: 'created_at', direction: 'asc' },
                { page: 2, pageSize: 30 }
            );
            expect(customQuery.filter?.status).toContain(TaskState.PENDING);
            expect(customQuery.sort?.direction).toBe('asc');
            expect(customQuery.pagination.pageSize).toBe(30);
        });
    });

    describe('Pagination Functions', () => {
        it('should calculate total pages', () => {
            expect(calculateTotalPages(100, 20)).toBe(5);
            expect(calculateTotalPages(101, 20)).toBe(6);
            expect(calculateTotalPages(0, 20)).toBe(0);
        });

        it('should validate page number', () => {
            expect(validatePageNumber(0, 5)).toBe(1);
            expect(validatePageNumber(6, 5)).toBe(5);
            expect(validatePageNumber(3, 5)).toBe(3);
        });

        it('should calculate offset', () => {
            expect(calculateOffset(1, 20)).toBe(0);
            expect(calculateOffset(2, 20)).toBe(20);
            expect(calculateOffset(3, 15)).toBe(30);
        });
    });

    describe('Filter Functions', () => {
        it('should apply date filter', () => {
            const date = '2025-01-15T12:00:00Z';
            const range: DateRange = {
                from: '2025-01-01T00:00:00Z',
                to: '2025-12-31T23:59:59Z'
            };

            expect(applyDateFilter(date, range)).toBe(true);
            expect(applyDateFilter(date, { ...range, to: '2025-01-01T00:00:00Z' })).toBe(false);
            expect(applyDateFilter(date, undefined)).toBe(true);
        });

        it('should create date range', () => {
            const range = createDateRange('2025-01-01', '2025-12-31');
            expect(range.from).toBe('2025-01-01');
            expect(range.to).toBe('2025-12-31');

            const partialRange = createDateRange(undefined, '2025-12-31');
            expect(partialRange.from).toBeUndefined();
            expect(partialRange.to).toBe('2025-12-31');
        });
    });

    describe('Edge Cases', () => {
        it('should handle empty search query', () => {
            const query = createSearchQuery();
            expect(query.text).toBeUndefined();
            expect(query.filter).toEqual({});
            expect(isSearchQuery(query)).toBe(true);
        });

        it('should handle invalid date ranges', () => {
            const invalidDate = '2025-13-45'; // Invalid date
            const range: DateRange = {
                from: '2025-01-01',
                to: invalidDate
            };

            expect(isDateRange(range)).toBe(true); // Type guard only checks types
            expect(() => applyDateFilter('2025-01-15', range)).toThrow();
        });

        it('should handle boundary pagination values', () => {
            expect(calculateTotalPages(0, 20)).toBe(0);
            expect(calculateTotalPages(1, 20)).toBe(1);
            expect(validatePageNumber(-1, 5)).toBe(1);
            expect(validatePageNumber(1000, 5)).toBe(5);
        });
    });
});
