<script lang="ts">
import SearchPanel from '$lib/components/search/SearchPanel.svelte';
import SearchResults from '$lib/components/search/SearchResults.svelte';
import TaskDetailsPanel from '$lib/components/TaskDetails.svelte';
import { appStore, selectedTask } from '$lib/stores/app';
import { convertToTaskDetails } from '$lib/utils/task';

// Subscribe to selected task and handle null case
$: task = $selectedTask ? convertToTaskDetails($selectedTask) : null;

// Subscribe to filtered tasks
$: ({ tasks } = $appStore);
</script>

<div class="border-b border-gray-700 p-4 bg-[#0D1117]">
        <div class="flex items-center justify-between">
            <div class="flex items-center">
                <h1 class="text-lg font-medium text-gray-200">Search</h1>
            </div>
            <div class="flex items-center space-x-4">
                <button 
                    class="inline-flex items-center justify-center h-9 px-3 text-sm font-medium rounded bg-white text-[#1D1C1D] hover:bg-[#F8F8F8] disabled:opacity-75 disabled:hover:bg-white transition-colors"
                >
                    Save Search
                </button>
            </div>
        </div>
    </div>

    <div class="h-full flex flex-col">
        <div class="p-4 border-b border-gray-800">
            <SearchPanel />
        </div>
        <div class="flex-1 overflow-auto p-4">
            <SearchResults {tasks} />
        </div>
    </div>
    
{#if task}
    <TaskDetailsPanel task={task} />
{/if}
