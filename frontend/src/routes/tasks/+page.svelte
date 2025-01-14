<script lang="ts">
import Layout from '$lib/components/layout/Layout.svelte';
import TaskBoard from '$lib/components/TaskBoard.svelte';
import TaskDetailsPanel from '$lib/components/TaskDetails.svelte';
import { appStore } from '$lib/stores/app';
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

// Subscribe to selected task
$: selectedTask = $appStore.selectedTaskId ? 
    convertToTaskDetails($appStore.tasks.find(t => t.id === $appStore.selectedTaskId)) : null;
</script>

<Layout>
    <TaskBoard />
    
    <svelte:fragment slot="details">
        {#if selectedTask}
            <TaskDetailsPanel task={selectedTask} />
        {/if}
    </svelte:fragment>
</Layout>
