<script lang="ts">
  import Chat from '$lib/components/Chat.svelte';

  // In a real app, this would be loaded from environment variables or user session
  const API_KEY = 'test-api-key';
</script>

<div class="container mx-auto h-screen p-4">
  <div class="max-w-2xl mx-auto h-full bg-white rounded-lg shadow-lg overflow-hidden">
    <Chat apiKey={API_KEY} />
  </div>
</div>

<style>
  :global(html, body) {
    height: 100%;
    background-color: #f3f4f6;
  }
</style>
