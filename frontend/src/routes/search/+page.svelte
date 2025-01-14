<script lang="ts">
import { onMount } from 'svelte';
import SearchPanel from '$lib/components/search/SearchPanel.svelte';
import type { Task } from '$lib/types/task';
import { searchStore } from '$lib/stores/search';
import type { SearchQuery } from '$lib/types/search';
import { debounce } from '$lib/utils/debounce';

let tasks: Task[] = [];
let loading = false;
let error: Error | null = null;
let currentController: AbortController | null = null;

// Create debounced fetch function
const debouncedFetch = debounce(fetchResults, 300);

// Subscribe to search store changes and fetch results
$: {
    const query = $searchStore;
    debouncedFetch(query).catch((e) => {
        // Ignore AbortError since it's expected when cancelling requests
        if (e.name !== 'AbortError') {
            error = e instanceof Error ? e : new Error('Failed to fetch search results');
        }
    });
}

async function fetchResults(query: SearchQuery): Promise<void> {
    // Cancel previous request if exists
    if (currentController) {
        currentController.abort();
    }

    // Create new abort controller
    currentController = new AbortController();

    try {
        loading = true;
        error = null;

        const params = new URLSearchParams();
        if (query.text) params.set('q', query.text);
        if (query.filter?.status?.length) params.set('status', query.filter.status.join(','));
        if (query.filter?.priority?.length) params.set('priority', query.filter.priority.join(','));
        if (query.filter?.assignee?.length) params.set('assignee', query.filter.assignee.join(','));
        if (query.filter?.dateRange?.from) params.set('from', query.filter.dateRange.from);
        if (query.filter?.dateRange?.to) params.set('to', query.filter.dateRange.to);
        if (query.sort?.field) params.set('sort', query.sort.field);
        if (query.sort?.direction) params.set('order', query.sort.direction);
        if (query.pagination?.page) params.set('page', query.pagination.page.toString());
        if (query.pagination?.pageSize) params.set('size', query.pagination.pageSize.toString());

        const response = await fetch(`/api/tasks/search?${params.toString()}`, {
            signal: currentController.signal
        });

        if (!response.ok) {
            throw new Error('Failed to fetch search results');
        }

        const data = await response.json();
        tasks = data.tasks;

        // Update pagination with total counts from response
        searchStore.setPagination({
            ...query.pagination,
            totalItems: data.totalItems,
            totalPages: data.totalPages
        });
    } finally {
        if (currentController?.signal.aborted) {
            // Don't update loading state if request was aborted
            return;
        }
        loading = false;
        currentController = null;
    }
}

// Initialize search from URL params on mount
onMount(() => {
    searchStore.init();
    return () => {
        // Cleanup: abort any pending request when component unmounts
        if (currentController) {
            currentController.abort();
        }
    };
});
</script>

<div class="search-page">
    <header class="search-header">
        <h1 class="search-title">Search Tasks</h1>
        <p class="search-description">
            Search across all tasks using filters, sorting, and pagination.
        </p>
    </header>

    <main class="search-content">
        <SearchPanel
            {tasks}
            {loading}
            {error}
        />
    </main>
</div>

<style lang="postcss">
.search-page {
    @apply min-h-screen bg-gray-50 dark:bg-gray-900;
    @apply p-6;
}

.search-header {
    @apply mb-8;
}

.search-title {
    @apply text-3xl font-bold text-gray-900 dark:text-white;
    @apply mb-2;
}

.search-description {
    @apply text-lg text-gray-600 dark:text-gray-400;
}

.search-content {
    @apply max-w-[1600px] mx-auto;
}
</style>
