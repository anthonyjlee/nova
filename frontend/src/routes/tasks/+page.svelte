<script lang="ts">
import { onMount } from 'svelte';
import { addMetric } from '$lib/utils/performance';
import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
import ErrorBoundary from '$lib/components/ErrorBoundary.svelte';
import type { PerformanceMetric } from '$lib/types/performance';

let TaskBoard: typeof import('$lib/components/TaskBoard.svelte').default;
let loading = true;
let error: string | null = null;

async function loadTaskBoard() {
    const startTime = performance.now();
    loading = true;
    error = null;

    try {
        const module = await import('$lib/components/TaskBoard.svelte');
        TaskBoard = module.default;

        const metric: PerformanceMetric = {
            component: 'TaskBoardRoute',
            operation: 'import',
            timestamp: performance.now(),
            totalTime: performance.now() - startTime
        };
        addMetric(metric);
    } catch (e) {
        error = e instanceof Error ? e.message : 'Failed to load task board';
        const metric: PerformanceMetric = {
            component: 'TaskBoardRoute',
            operation: 'import_error',
            timestamp: performance.now(),
            errorMessage: error
        };
        addMetric(metric);
    } finally {
        loading = false;
    }
}

onMount(loadTaskBoard);
</script>

<div class="h-full">
    {#if loading}
        <div class="flex items-center justify-center h-full">
            <LoadingSpinner 
                size={8} 
                label="Loading task board"
            />
        </div>
    {:else if error}
        <ErrorBoundary
            {error}
            retry={loadTaskBoard}
            title="Failed to Load Task Board"
            retryText="Try Again"
        />
    {:else if TaskBoard}
        <svelte:component this={TaskBoard} />
    {/if}
</div>
