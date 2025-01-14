<script lang="ts">
import Chat from '$lib/components/Chat.svelte';
import { onMount } from 'svelte';
import { profileStore } from '$lib/stores/profile';

// Generate a unique client ID
const clientId = crypto.randomUUID() as `${string}-${string}-${string}-${string}-${string}`;

onMount(() => {
  // Initialize profile store with current user
  profileStore.loadProfile('current-user');
});
</script>

<div class="flex-1 flex flex-col h-full">
  <!-- Channel Header -->
  <header class="h-14 flex-shrink-0 flex items-center px-6 border-b border-[#424242] bg-[#1A1D21]">
    <div class="flex items-center gap-2">
      <span class="text-2xl text-[#9B9B9B]">#</span>
      <h1 class="text-lg font-bold text-[#D1D5DB]">main</h1>
    </div>
  </header>

  <!-- Chat Area -->
  <div class="flex-1 min-h-0">
    <Chat 
      apiKey="test-key"
      {clientId}
    />
  </div>
</div>
