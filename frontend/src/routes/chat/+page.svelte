<script lang="ts">
import Layout from '$lib/components/layout/Layout.svelte';
import Chat from '$lib/components/Chat.svelte';
import { appStore, selectedTask } from '$lib/stores/app';
import TaskDetailsPanel from '$lib/components/TaskDetails.svelte';
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
</script>

<Layout>
    <Chat apiKey="test-api-key" />
    
    <svelte:fragment slot="details">
        {#if task}
            <TaskDetailsPanel task={task} />
        {/if}
    </svelte:fragment>
</Layout>
