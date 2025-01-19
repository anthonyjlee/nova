<script lang="ts">
  import Chat from '$lib/components/Chat.svelte';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { userStore } from '$lib/stores/user';

  let threadId: string;

  onMount(async () => {
    try {
      // Try to get thread ID from URL
      threadId = $page.url.searchParams.get('thread') || '';
      
      if (!threadId) {
        // Create a new thread
        const response = await fetch('/api/threads', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': $userStore.user?.apiKey || 'valid-api-key'
          },
          body: JSON.stringify({
            title: 'Nova Chat',
            workspace: 'personal',
            domain: 'personal',
            participants: [],
            metadata: {
              type: 'chat',
              system: false,
              pinned: false,
              description: 'Chat with Nova'
            }
          })
        });

        if (response.ok) {
          const thread = await response.json();
          threadId = thread.id;
          // Update URL with new thread ID
          goto(`/chat/nova?thread=${threadId}`, { replaceState: true });
        } else {
          console.error('Failed to create thread:', await response.text());
        }
      }
    } catch (error) {
      console.error('Error initializing chat:', error);
    }
  });
</script>

{#if threadId}
  <div class="h-full">
    <Chat {threadId} domain="personal" />
  </div>
{:else}
  <div class="flex items-center justify-center h-full bg-gray-900 text-white">
    <div class="flex flex-col items-center space-y-4">
      <div class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      <div class="text-lg">Loading chat...</div>
    </div>
  </div>
{/if}
