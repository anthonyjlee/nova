<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import { setupChatWebSocket, sendMessage, getThread, getThreadMessages, getThreadAgents } from '$lib/services/chat';
  import type { Message, Thread, ThreadParticipant } from '$lib/types/chat';

  const threadId = $page.params.id;
  let thread: Thread | null = null;
  let messages: Message[] = [];
  let agents: ThreadParticipant[] = [];
  let inputContent = '';
  let inputElement: HTMLDivElement;
  let wsInstance: WebSocket | null = null;
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    if (inputElement) {
      inputElement.addEventListener('input', () => {
        inputContent = inputElement.textContent || '';
      });
    }

    // Load thread data
    try {
      [thread, messages, agents] = await Promise.all([
        getThread(threadId),
        getThreadMessages(threadId),
        getThreadAgents(threadId)
      ]);
    } catch (err) {
      console.error('Failed to load thread:', err);
      error = err instanceof Error ? err.message : 'Failed to load thread';
    } finally {
      loading = false;
    }

    // Set up WebSocket
    try {
      wsInstance = await setupChatWebSocket(
        // New message handler
        (message) => {
          if (message.threadId === threadId) {
            messages = [...messages, message];
          }
        },
        // Thread update handler
        (updatedThread) => {
          if (updatedThread.id === threadId) {
            thread = updatedThread;
          }
        },
        // Agent status handler
        (status) => {
          if (status.threadId === threadId) {
            agents = agents.map(agent => 
              agent.id === status.agentId 
                ? { ...agent, status: status.status === 'idle' ? 'active' : 'inactive' }
                : agent
            );
          }
        }
      );
    } catch (error) {
      console.error('WebSocket setup failed:', error);
    }
  });

  onDestroy(() => {
    if (wsInstance) {
      wsInstance.close();
    }
  });

  async function handleSend() {
    if (!inputContent.trim()) return;

    try {
      const message = await sendMessage(threadId, inputContent.trim());
      messages = [...messages, message];
      
      // Clear input
      if (inputElement) {
        inputElement.textContent = '';
        inputContent = '';
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // TODO: Show error to user
    }
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  }
</script>

<div class="flex-1 flex flex-col overflow-hidden relative">
  {#if loading}
    <div class="absolute inset-0 flex items-center justify-center bg-opacity-50" style="background-color: var(--slack-bg-primary);">
      <span style="color: var(--slack-text-secondary)">Loading thread...</span>
    </div>
  {/if}

  {#if error}
    <div class="absolute inset-0 flex items-center justify-center bg-opacity-50" style="background-color: var(--slack-bg-primary);">
      <span style="color: var(--slack-text-error)">{error}</span>
    </div>
  {/if}
  <!-- Thread Header -->
  <div class="p-4 border-b" style="border-color: var(--slack-border-dim);">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-lg font-bold" style="color: var(--slack-text-primary)">
          {thread?.name || 'Thread'}
        </h1>
        {#if thread?.metadata?.domain}
          <span class="text-sm" style="color: var(--slack-text-secondary)">
            Domain: {thread.metadata.domain}
          </span>
        {/if}
      </div>
      
      <!-- Participants -->
      <div class="flex items-center space-x-2">
        {#each agents as agent}
          <div 
            class="w-8 h-8 rounded-full flex items-center justify-center"
            style="background-color: var(--slack-accent-primary);"
            title={`${agent.name} (${agent.status || 'unknown'})`}
          >
            <span class="text-white text-sm font-medium">
              {agent.name[0].toUpperCase()}
            </span>
          </div>
        {/each}
      </div>
    </div>
  </div>

  <!-- Messages Area -->
  <div class="flex-1 overflow-y-auto slack-scrollbar p-4">
    {#each messages as message (message.id)}
      <div class="slack-message group">
        <div class="flex items-start space-x-2">
          <!-- Agent/User Avatar -->
          <div 
            class="w-9 h-9 rounded flex items-center justify-center flex-shrink-0"
            style="background-color: {message.sender.type === 'agent' ? 'var(--slack-accent-primary)' : 'var(--slack-accent-secondary)'}"
          >
            <span class="text-white font-medium">
              {message.sender.name[0].toUpperCase()}
            </span>
          </div>

          <!-- Message Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-baseline">
              <span class="font-bold" style="color: var(--slack-text-primary)">
                {message.sender.name}
              </span>
              <span 
                class="ml-2 text-xs opacity-60"
                style="color: var(--slack-text-secondary)"
              >
                {new Date(message.timestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
              </span>
            </div>
            <div style="color: var(--slack-text-primary)">
              {message.content}
            </div>
          </div>
        </div>
      </div>
    {/each}
  </div>

  <!-- Input Area -->
  <div class="p-4 border-t" style="border-color: var(--slack-border-dim);">
    <div class="flex items-center space-x-2">
      <div class="flex-1 relative">
        <div 
          bind:this={inputElement}
          class="min-h-[44px] max-h-[140px] overflow-y-auto p-3 rounded focus:outline-none w-full"
          contenteditable="true"
          role="textbox"
          aria-label="Message input"
          on:keydown={handleKeyDown}
          style="
            background-color: var(--slack-bg-tertiary);
            border: 1px solid var(--slack-border-dim);
            color: var(--slack-text-primary);
          "
        ></div>
        {#if !inputContent}
          <div 
            class="absolute left-3 top-3 pointer-events-none"
            style="color: var(--slack-text-muted);"
          >
            Reply to thread...
          </div>
        {/if}
      </div>
      <button 
        class="px-4 py-2 rounded font-medium hover:opacity-90 transition-opacity"
        style="background-color: var(--slack-accent-primary); color: white;"
        on:click={handleSend}
      >
        Send
      </button>
    </div>
  </div>
</div>
