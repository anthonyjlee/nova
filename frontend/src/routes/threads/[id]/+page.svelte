<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import { setupChatWebSocket, sendMessage, getThread, getThreadMessages, getThreadAgents, spawnAgent as spawnAgentApi, switchDomain } from '$lib/services/chat';
  import type { Message, Thread, ThreadParticipant, AgentType, WorkspaceType, DomainType } from '$lib/types/chat';
  import { WORKSPACE_DOMAINS } from '$lib/types/chat';
  import AgentTeamView from '$lib/components/AgentTeamView.svelte';
  import AgentDetailsPanel from '$lib/components/AgentDetailsPanel.svelte';

  const threadId = $page.params.id;
  let thread: Thread | null = null;
  let messages: Message[] = [];
  let agents: ThreadParticipant[] = [];
  let inputContent = '';
  let inputElement: HTMLDivElement;
  let wsInstance: WebSocket | null = null;
  let loading = true;
  let error: string | null = null;
  let showAgentMenu = false;
  let selectedAgent: ThreadParticipant | null = null;
  let filteredAgentId: string | null = null;

  $: filteredMessages = filteredAgentId 
    ? messages.filter(m => m.sender.id === filteredAgentId)
    : messages;

  // Domain handling
  async function handleDomainChange(newDomain: DomainType) {
    try {
      await switchDomain(threadId, newDomain);
      if (thread) {
        thread = {
          ...thread,
          metadata: {
            ...thread.metadata,
            domain: newDomain
          }
        };
      }
    } catch (error) {
      console.error('Failed to switch domain:', error);
      // TODO: Show error to user
    }
  }

  // Agent spawning
  async function handleSpawnAgent(agentType: AgentType) {
    try {
      if (!thread) return;

      const agent = await spawnAgentApi({
        threadId,
        agentType,
        workspace: thread.workspace,
        domain: thread.metadata?.domain,
        metadata: {
          capabilities: [],
          specialization: agentType
        }
      });

      agents = [...agents, agent];
      showAgentMenu = false;

      // Add system message about agent joining
      messages = [...messages, {
        id: `system-${Date.now()}`,
        threadId,
        content: `${agent.name} has joined the conversation.`,
        sender: {
          id: 'system',
          name: 'System',
          type: 'agent'
        },
        workspace: thread.workspace,
        timestamp: new Date().toISOString()
      }];
    } catch (error) {
      console.error('Failed to spawn agent:', error);
      // TODO: Show error to user
    }
  }

  function setShowAgentMenu(show: boolean) {
    showAgentMenu = show;
  }

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
    if (!inputContent.trim() || !thread) return;

    try {
      const message = await sendMessage(threadId, inputContent.trim(), thread.workspace);
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
  <!-- Loading Overlay -->
  {#if loading}
    <div 
      class="absolute inset-0 flex items-center justify-center bg-opacity-50 z-50"
      style="background-color: var(--slack-bg-primary);"
    >
      <div class="flex flex-col items-center">
        <div class="w-8 h-8 border-4 border-t-4 rounded-full animate-spin mb-2"
          style="
            border-color: var(--slack-accent-primary);
            border-top-color: transparent;
          "
        ></div>
        <span style="color: var(--slack-text-secondary)">Loading thread...</span>
      </div>
    </div>
  {/if}

  <!-- Error Message -->
  {#if error}
    <div 
      class="absolute top-4 right-4 px-4 py-2 rounded shadow-lg z-50"
      style="
        background-color: var(--slack-text-error);
        color: white;
      "
    >
      {error}
      <button 
        class="ml-2 hover:opacity-80"
        on:click={() => error = null}
      >
        ✕
      </button>
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
      
      <!-- Domain & Participants -->
      <div class="flex items-center space-x-4">
        <!-- Domain Selector -->
        {#if thread}
          <div class="relative">
            <select
              class="px-3 py-1 rounded text-sm appearance-none cursor-pointer"
              style="
                background-color: var(--slack-bg-tertiary);
                border: 1px solid var(--slack-border-dim);
                color: var(--slack-text-primary);
              "
              value={thread.metadata?.domain}
              on:change={(e) => handleDomainChange(e.currentTarget.value as DomainType)}
            >
              {#if thread.workspace === 'personal'}
                {#each WORKSPACE_DOMAINS.personal as domain}
                  <option value={domain}>{domain.charAt(0).toUpperCase() + domain.slice(1)}</option>
                {/each}
              {:else}
                {#each WORKSPACE_DOMAINS.professional as domain}
                  <option value={domain}>{domain.toUpperCase()}</option>
                {/each}
              {/if}
            </select>
          </div>
        {/if}

        <!-- Agent Team View -->
        <AgentTeamView 
          {agents}
          onAgentClick={(agent) => {
            selectedAgent = agent;
            filteredAgentId = agent.id;
          }}
        />

        <!-- Add Agent Button -->
        <button
          class="w-8 h-8 rounded-full flex items-center justify-center hover:opacity-80 transition-opacity"
          style="background-color: var(--slack-bg-tertiary);"
          on:click={() => setShowAgentMenu(true)}
          title="Add Agent"
        >
          <span style="color: var(--slack-text-primary)">+</span>
        </button>
      </div>
    </div>
  </div>

  <!-- Agent Menu -->
  {#if showAgentMenu}
    <div 
      class="absolute right-4 top-16 p-4 rounded shadow-lg z-10"
      style="background-color: var(--slack-bg-primary); border: 1px solid var(--slack-border-dim);"
    >
      <div class="flex items-center justify-between mb-4">
        <span class="font-medium" style="color: var(--slack-text-primary)">Add Agent</span>
        <button 
          class="text-sm hover:opacity-80"
          style="color: var(--slack-text-secondary);"
          on:click={() => setShowAgentMenu(false)}
        >
          ✕
        </button>
      </div>

      <div class="space-y-2">
        {#each ['belief', 'desire', 'emotion', 'reflection', 'research', 'context'] as agentType}
          <button
            class="w-full px-3 py-2 rounded text-left hover:opacity-90 transition-opacity"
            style="background-color: var(--slack-accent-primary); color: white;"
            on:click={() => handleSpawnAgent(agentType)}
          >
            {agentType.charAt(0).toUpperCase() + agentType.slice(1)} Agent
          </button>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Messages Area -->
  <div class="flex-1 overflow-y-auto slack-scrollbar p-4">
    <!-- Filter Indicator -->
    {#if filteredAgentId}
      <div class="mb-4 px-4 py-2 rounded" style="background-color: var(--slack-bg-tertiary);">
        <div class="flex items-center justify-between">
          <span class="text-sm" style="color: var(--slack-text-secondary)">
            Showing messages from {agents.find(a => a.id === filteredAgentId)?.name}
          </span>
          <button
            class="text-sm hover:underline"
            style="color: var(--slack-text-secondary);"
            on:click={() => {
              selectedAgent = null;
              filteredAgentId = null;
            }}
          >
            Show All Messages
          </button>
        </div>
      </div>
    {/if}

    {#each filteredMessages as message (message.id)}
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

<!-- Agent Details Panel -->
{#if selectedAgent}
  <AgentDetailsPanel 
    agent={selectedAgent}
    onClose={() => {
      selectedAgent = null;
      filteredAgentId = null;
    }}
  />
{/if}
