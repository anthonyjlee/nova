<script lang="ts">
  import { page } from '$app/stores';
  import { appStore } from '$lib/stores/app';
  import { userStore } from '$lib/stores/user';
  import { NovaChannel } from '$lib/schemas/websocket';
  import TaskBoard from '$lib/components/TaskBoard.svelte';
  import { onMount, onDestroy } from 'svelte';

  // Get workspace and domain from URL params
  $: workspace = $page.params.workspace || 'personal';
  $: domain = $page.params.domain || 'general';

  onMount(async () => {
    try {
      // Get API key from user store
      const apiKey = $userStore.user?.apiKey || 'default-test-key';
      
      // Connect with task connection type
      await appStore.connect('task', apiKey);
      await appStore.joinChannel('NovaTeam');
    } catch (error) {
      console.error('Failed to connect:', error);
    }
  });

  onDestroy(() => {
    appStore.disconnect();
  });
</script>

<div class="flex flex-col h-screen bg-[#1A1D21] text-[#DCDDDE]">
  <!-- Header -->
  <div class="flex-none h-12 border-b border-[#2C2D31] flex items-center px-4">
    <h1 class="text-lg font-semibold">Tasks</h1>
  </div>

  <!-- Content -->
  <div class="flex-1 overflow-hidden">
    <TaskBoard {workspace} {domain} />
  </div>
</div>
