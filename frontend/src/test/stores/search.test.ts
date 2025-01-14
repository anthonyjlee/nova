import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { searchStore, searchText, searchFilter, searchSort, searchPagination } from '$lib/stores/search';
import { TaskState } from '$lib/types/task';
import type { TaskFilter, SearchQuery, SortConfig } from '$lib/types/search';

describe('Search Store', () => {
    beforeEach(() => {
        searchStore.reset();
        searchStore.clearCache();
    });

    describe('Initial State', () => {
        it('should have default values', () => {
            const state = get(searchStore);
            expect(state.text).toBe('');
            expect(state.filter).toEqual({
                status: [],
                priority: [],
                assignee: [],
                dateRange: undefined
            });
            expect(state.sort).toEqual({
                field: 'updated_at',
                direction: 'desc'
            });
            expect(state.pagination).toEqual({
                page: 1,
                pageSize: 20,
                totalItems: 0,
                totalPages: 0
            });
        });

        it('should have correct derived store values', () => {
            expect(get(searchText)).toBe('');
            expect(get(searchFilter)).toEqual({
                status: [],
                priority: [],
                assignee: [],
                dateRange: undefined
            });
            expect(get(searchSort)).toEqual({
                field: 'updated_at',
                direction: 'desc'
            });
            expect(get(searchPagination)).toEqual({
                page: 1,
                pageSize: 20,
                totalItems: 0,
                totalPages: 0
            });
        });
    });

    describe('Store Actions', () => {
        it('should update text', () => {
            searchStore.setText('test query');
            expect(get(searchText)).toBe('test query');
        });

        it('should update filter', () => {
            const filter: TaskFilter = {
                status: [TaskState.PENDING],
                priority: ['high'],
                assignee: [],
                dateRange: undefined
            };
            searchStore.setFilter(filter);
            expect(get(searchFilter)).toEqual(filter);
        });

        it('should update sort', () => {
            const sort: SortConfig = {
                field: 'created_at',
                direction: 'asc'
            };
            searchStore.setSort(sort);
            expect(get(searchSort)).toEqual(sort);
        });

        it('should update pagination', () => {
            const pagination = {
                page: 2,
                pageSize: 30,
                totalItems: 100,
                totalPages: 4
            };
            searchStore.setPagination(pagination);
            expect(get(searchPagination)).toEqual(pagination);
        });

        it('should reset to initial state', () => {
            searchStore.setText('test');
            searchStore.setFilter({
                status: [TaskState.PENDING],
                priority: [],
                assignee: [],
                dateRange: undefined
            });
            searchStore.reset();
            expect(get(searchStore)).toEqual({
                text: '',
                filter: {
                    status: [],
                    priority: [],
                    assignee: [],
                    dateRange: undefined
                },
                sort: {
                    field: 'updated_at',
                    direction: 'desc'
                },
                pagination: {
                    page: 1,
                    pageSize: 20,
                    totalItems: 0,
                    totalPages: 0
                }
            });
        });
    });

    describe('Cache Operations', () => {
        it('should cache and retrieve search results', () => {
            const query = get(searchStore);
            const response = {
                tasks: [
                    {
                        id: '1',
                        label: 'Test Task',
                        type: 'task',
                        status: TaskState.PENDING,
                        created_at: '2025-01-15T00:00:00Z',
                        updated_at: '2025-01-15T00:00:00Z',
                        metadata: {}
                    }
                ],
                totalItems: 1,
                totalPages: 1
            };

            searchStore.setInCache(query, response);
            const cached = searchStore.getFromCache(query);
            expect(cached).toEqual(response);
        });

        it('should generate consistent cache keys', () => {
            const query1: SearchQuery = {
                text: 'test',
                filter: {
                    status: [TaskState.PENDING],
                    priority: [],
                    assignee: [],
                    dateRange: undefined
                },
                sort: {
                    field: 'updated_at',
                    direction: 'desc'
                },
                pagination: {
                    page: 1,
                    pageSize: 20,
                    totalItems: 0,
                    totalPages: 0
                }
            };

            const query2 = { ...query1 };
            const key1 = searchStore.getCacheKey(query1);
            const key2 = searchStore.getCacheKey(query2);
            expect(key1).toBe(key2);
        });

        it('should clear cache', () => {
            const query = get(searchStore);
            const response = {
                tasks: [],
                totalItems: 0,
                totalPages: 0
            };

            searchStore.setInCache(query, response);
            searchStore.clearCache();
            expect(searchStore.getFromCache(query)).toBeUndefined();
        });
    });
});
