<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';

  onMount(() => {
    // Redirect to nova chat with a new thread
    goto('/chat/nova');
  });
</script>

<div class="flex items-center justify-center h-full bg-gray-900 text-white">
  <div class="flex flex-col items-center space-y-4">
    <div class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    <div class="text-lg">Loading chat...</div>
  </div>
</div>
