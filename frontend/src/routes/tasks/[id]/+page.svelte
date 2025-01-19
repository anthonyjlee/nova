<script lang="ts">
  import { page } from '$app/stores';
  import { taskStore } from '$lib/stores/task';
  import { appStore } from '$lib/stores/app';
  import ErrorDisplay from '$lib/components/ErrorDisplay.svelte';
  import type { TaskNode } from '$lib/schemas/task';
  import { onMount, onDestroy } from 'svelte';
  import type { WebSocketMessage, TaskUpdate } from '$lib/schemas/websocket';
  import { NovaChannel, TaskUpdateSchema } from '$lib/schemas/websocket';
  import { goto } from '$app/navigation';

  // Get task ID from URL params
  $: taskId = $page.params.id;

  // State
  let error: { type: 'validation' | 'connection'; message: string } | null = null;
  let loading = true;
  let prevTask: TaskNode | null = null;
  let nextTask: TaskNode | null = null;

  // Message handler
  const handleTaskUpdate = (message: WebSocketMessage) => {
    if (message.type === 'task_update') {
      // Validate task update data
      const result = TaskUpdateSchema.safeParse(message);
      if (result.success) {
        const taskUpdate = result.data as TaskUpdate;
        if (taskUpdate.data.task_id === taskId) {
          loadTask();
        }
      }
    }
  };

  // Subscribe to task updates from appStore
  $: if ($appStore.socket && $appStore.authenticated) {
    $appStore.socket.addMessageHandler('task_update', handleTaskUpdate);
  }

  // Load initial task and connect WebSocket
  onMount(async () => {
    try {
      await appStore.connect('task');
      await appStore.subscribeToChannel(NovaChannel.TEAM);
      await loadTask();
    } catch (error) {
      handleError('connection', error instanceof Error ? error.message : 'Connection failed');
    } finally {
      loading = false;
    }
  });

  // Cleanup on destroy
  onDestroy(() => {
    if ($appStore.socket) {
      $appStore.socket.removeMessageHandler('task_update', handleTaskUpdate);
      appStore.disconnect();
    }
  });

  // Data loading
  async function loadTask() {
    try {
      await taskStore.loadTask(taskId);
    } catch (error) {
      handleError('connection', 'Failed to load task');
    }
  }

  // Error handling
  function handleError(type: 'validation' | 'connection', message: string) {
    error = { type, message };
  }

  function dismissError() {
    error = null;
  }

  // Navigation
  function goBack() {
    goto('/tasks');
  }

  // Priority colors
  function getPriorityColor(priority: string | undefined): string {
    switch (priority) {
      case 'high':
        return 'bg-[#F23F43]';
      case 'medium':
        return 'bg-[#F0B232]';
      case 'low':
        return 'bg-[#23A559]';
      default:
        return 'bg-[#949BA4]';
    }
  }

  // Get task from store
  $: task = $taskStore.activeTask;

  // Get next/previous tasks
  $: {
    const tasks = $taskStore.tasks;
    const currentIndex = tasks.findIndex(t => t.id === taskId);
    prevTask = currentIndex > 0 ? tasks[currentIndex - 1] : null;
    nextTask = currentIndex < tasks.length - 1 ? tasks[currentIndex + 1] : null;
  }
</script>

<div class="h-full bg-[#1A1D21] text-[#DCDDDE]">
  {#if loading}
    <div class="absolute inset-0 flex items-center justify-center bg-[#1A1D21] bg-opacity-50">
      <div class="flex flex-col items-center space-y-4">
        <div class="w-12 h-12 border-4 border-[#5865F2] border-t-transparent rounded-full animate-spin"></div>
        <div class="text-lg">Loading task...</div>
      </div>
    </div>
  {/if}

  <!-- Error Display -->
  {#if error}
    <ErrorDisplay
      error={error}
      dismissable={true}
      retryable={error.type === 'connection'}
      on:dismiss={dismissError}
    />
  {/if}

  <!-- Navigation -->
  <div class="flex-none h-12 border-b border-[#2C2D31] flex items-center px-4">
    <div class="flex-1 flex items-center space-x-4">
      <button 
        class="px-4 py-2 bg-[#2B2D31] hover:bg-[#35373C] rounded-md flex items-center space-x-2 transition-colors"
        on:click={goBack}
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        <span>Back to Tasks</span>
      </button>

      <div class="flex items-center space-x-4">
        {#if prevTask}
          <a 
            href="/tasks/{prevTask.id}"
            class="px-4 py-2 bg-[#2B2D31] hover:bg-[#35373C] rounded-md transition-colors"
          >
            Previous Task
          </a>
        {/if}

        {#if nextTask}
          <a 
            href="/tasks/{nextTask.id}"
            class="px-4 py-2 bg-[#2B2D31] hover:bg-[#35373C] rounded-md transition-colors"
          >
            Next Task
          </a>
        {/if}
      </div>
    </div>
  </div>

  <!-- Task Details -->
  {#if task}
    <div class="p-6">
      <div class="bg-[#2B2D31] rounded-lg p-6">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold">{task.label}</h1>
          <div class="flex items-center space-x-4">
            <div class="w-3 h-3 rounded-full {getPriorityColor(task.priority)}"></div>
            <span class="text-sm text-[#949BA4] capitalize">{task.priority || 'No Priority'}</span>
          </div>
        </div>

        <!-- Title -->
        {#if task.title}
          <div class="mb-6">
            <h2 class="text-lg text-[#949BA4]">{task.title}</h2>
          </div>
        {/if}

        <!-- Status -->
        <div class="mb-6">
          <h3 class="text-sm text-[#949BA4] mb-2">Status</h3>
          <span class="px-3 py-1 rounded-full bg-[#35373C] text-sm capitalize">{task.status}</span>
        </div>

        <!-- Assignee -->
        {#if task.assignee}
          <div class="mb-6">
            <h3 class="text-sm text-[#949BA4] mb-2">Assignee</h3>
            <span class="text-[#DCDDDE]">{task.assignee}</span>
          </div>
        {/if}

        <!-- Blocked By -->
        {#if task.blocked_by?.length}
          <div class="mb-6">
            <h3 class="text-sm text-[#949BA4] mb-2">Blocked By</h3>
            <div class="space-y-2">
              {#each task.blocked_by as blocker}
                <div class="text-[#F23F43]">{blocker}</div>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Completion Date -->
        {#if task.metadata?.completed_at}
          <div class="mb-6">
            <h3 class="text-sm text-[#949BA4] mb-2">Completed</h3>
            <span class="text-[#DCDDDE]">
              {new Date(task.metadata.completed_at as string).toLocaleString()}
            </span>
          </div>
        {/if}

        <!-- Metadata -->
        {#if task.metadata && Object.keys(task.metadata).length > 0}
          <div>
            <h3 class="text-sm text-[#949BA4] mb-2">Additional Details</h3>
            <pre class="bg-[#1A1D21] p-4 rounded-lg overflow-x-auto text-[#DCDDDE]">
              {JSON.stringify(task.metadata, null, 2)}
            </pre>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>
