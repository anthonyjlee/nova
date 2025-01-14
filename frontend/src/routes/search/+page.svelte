<script lang="ts">
import Layout from '$lib/components/layout/Layout.svelte';
import SearchPanel from '$lib/components/search/SearchPanel.svelte';
import SearchResults from '$lib/components/search/SearchResults.svelte';
import TaskDetailsPanel from '$lib/components/TaskDetails.svelte';
import { appStore, selectedTask } from '$lib/stores/app';
import type { Task, TaskDetails } from '$lib/types/task';

// Convert Task to TaskDetails
function convertToTaskDetails(task: Task | undefined): TaskDetails | null {
    if (!task) return null;
    return {
        task,
        dependencies: task.dependencies || [],
        blocked_by: task.blocked_by || [],
        sub_tasks: task.sub_tasks || [],
        comments: [],
        time_active: task.time_active?.toString(),
        domain_access: [task.domain || 'general']
    };
}

// Subscribe to selected task and handle null case
$: task = $selectedTask ? convertToTaskDetails($selectedTask) : null;

// Subscribe to filtered tasks
$: ({ tasks } = $appStore);
</script>

<Layout>
    <div class="flex flex-col h-full">
        <div class="p-4 border-b border-slack-border-dim">
            <SearchPanel />
        </div>
        <div class="flex-1 overflow-auto p-4">
            <SearchResults {tasks} />
        </div>
    </div>
    
    <svelte:fragment slot="details">
        {#if task}
            <TaskDetailsPanel task={task} />
        {/if}
    </svelte:fragment>
</Layout>
