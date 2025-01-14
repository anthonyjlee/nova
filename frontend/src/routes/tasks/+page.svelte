<script lang="ts">
import TaskBoard from '$lib/components/TaskBoard.svelte';
import TaskDetailsPanel from '$lib/components/TaskDetails.svelte';
import TaskModal from '$lib/components/TaskModal.svelte';
import { appStore } from '$lib/stores/app';
import { convertToTaskDetails } from '$lib/utils/task';
import { addTask } from '$lib/services/tasks';

let isModalOpen = false;

// Subscribe to selected task
$: selectedTask = $appStore.selectedTaskId ? 
    convertToTaskDetails($appStore.tasks.find(t => t.id === $appStore.selectedTaskId)) : null;

async function handleTaskSubmit(event: CustomEvent<any>) {
    try {
        const taskData = event.detail;
        const newTask = await addTask({
            label: taskData.label,
            type: 'task',
            status: 'pending',
            description: taskData.description,
            domain: taskData.domain,
            team_id: taskData.team_id,
            metadata: {
                priority: taskData.priority,
                assignee: taskData.assignee,
                dueDate: taskData.dueDate,
                tags: taskData.tags
            }
        });
        
        // Update store with new task
        const tasks = [...$appStore.tasks, newTask];
        appStore.updateTasks(tasks);
    } catch (error) {
        console.error('Failed to create task:', error);
    }
}

function handleKeydown(event: KeyboardEvent) {
    if ((event.metaKey || event.ctrlKey) && event.key === 'n') {
        event.preventDefault();
        isModalOpen = true;
    }
}
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="h-full flex flex-col">
    <!-- Header -->
    <div class="flex-shrink-0 border-b border-[#424242] p-3 sm:p-4 bg-[#1A1D21]">
        <div class="flex items-center justify-between">
            <div class="flex items-center">
                <h1 class="text-base sm:text-lg font-medium text-[#D1D5DB]">Tasks</h1>
            </div>
            <div class="flex items-center gap-2 sm:gap-4">
                <button 
                    class="inline-flex items-center justify-center h-8 sm:h-9 px-3 text-sm font-medium rounded bg-[#007A5A] text-white hover:bg-[#148567] disabled:opacity-75 disabled:hover:bg-[#007A5A] transition-colors focus:outline-none focus:ring-2 focus:ring-[#1264A3]"
                    on:click={() => isModalOpen = true}
                >
                    <span class="hidden sm:inline">New Task</span>
                    <span class="sm:hidden">+</span>
                    <span class="hidden sm:inline ml-1 text-xs opacity-75">(⌘N)</span>
                </button>
            </div>
        </div>
    </div>

    <!-- Task Board -->
    <div class="flex-1 min-h-0 overflow-hidden">
        <TaskBoard />
    </div>
</div>

<!-- Task Details Panel -->
{#if selectedTask}
    <TaskDetailsPanel task={selectedTask} />
{/if}

<!-- New Task Modal -->
<TaskModal 
    bind:isOpen={isModalOpen}
    on:submit={handleTaskSubmit}
/>
