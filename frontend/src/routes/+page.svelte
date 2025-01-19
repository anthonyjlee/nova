<script lang="ts">
  import Chat from '$lib/components/Chat.svelte';
  import { page } from '$app/stores';

  // Get params from URL
  $: threadId = $page.params.thread || 'nova-hq';
  $: domain = $page.params.domain || 'general';
  $: workspace = $page.params.workspace || 'personal';

  // Loading state
  let loading = true;

  // Handle route changes
  $: {
    if ($page.params) {
      loading = false;
    }
  }
</script>

{#if loading}
  <div class="flex items-center justify-center h-full bg-gray-900 text-white">
    <div class="flex flex-col items-center space-y-4">
      <div class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      <div class="text-lg">Loading chat...</div>
    </div>
  </div>
{:else}
  <Chat {threadId} {domain} {workspace} />
{/if}
