<script lang="ts">
  import Chat from '$lib/components/Chat.svelte';
  import { page } from '$app/stores';

  // Get thread ID from URL or create new one
  const threadId = $page.url.searchParams.get('thread') || crypto.randomUUID();
</script>

<div class="h-full">
  <Chat {threadId} domain="nova" />
</div>
