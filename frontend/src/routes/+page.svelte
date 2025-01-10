<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { 
    setupChatWebSocket, 
    sendMessage, 
    getThreadMessages,
    askNova,
    suggestAgents,
    spawnAgent,
    createAgentTeam,
    createThread,
    listThreads,
    getThread,
    getThreadAgents
  } from '$lib/services/chat';
  import type { Message, AgentType, ThreadParticipant, Thread } from '$lib/types/chat';
  import AgentTeamView from '$lib/components/AgentTeamView.svelte';
  import AgentDetailsPanel from '$lib/components/AgentDetailsPanel.svelte';
  
  let messages: Message[] = [];
  let threads: Thread[] = [];
  let agents: ThreadParticipant[] = [];
  let inputContent = '';
  let inputElement: HTMLDivElement;
  let wsInstance: WebSocket | null = null;
  let currentThreadId = '';
  let suggestedAgents: { type: AgentType; confidence: number }[] = [];
  let showAgentSuggestions = false;
  let currentDomain: string | null = null;
  let loading = false;
  let error: string | null = null;
  let selectedAgent: ThreadParticipant | null = null;
  let filteredAgentId: string | null = null;

  $: filteredMessages = filteredAgentId 
    ? messages.filter(m => m.sender.id === filteredAgentId)
    : messages;

  async function handleThreadSelect(threadId: string) {
    try {
      loading = true;
      const [thread, threadMessages, threadAgents] = await Promise.all([
        getThread(threadId),
        getThreadMessages(threadId),
        getThreadAgents(threadId)
      ]);
      agents = threadAgents;
      currentThreadId = threadId;
      messages = threadMessages;
      if (thread.metadata?.domain) {
        currentDomain = thread.metadata.domain;
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load thread';
    } finally {
      loading = false;
    }
  }

  async function handleNewThread() {
    try {
      loading = true;
      const thread = await createThread('New Chat');
      threads = [...threads, thread];
      await handleThreadSelect(thread.id);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to create thread';
    } finally {
      loading = false;
    }
  }

  async function loadThreads() {
    try {
      loading = true;
      threads = await listThreads();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load threads';
    } finally {
      loading = false;
    }
  }

  onMount(async () => {
    await loadThreads();
    if (inputElement) {
      inputElement.addEventListener('input', () => {
        inputContent = inputElement.textContent || '';
      });
    }

    // Create initial thread
    try {
      const thread = await createThread('Nova Chat');
      currentThreadId = thread.id;
      messages = [{
        id: 'welcome',
        threadId: currentThreadId || '',
        content: 'Hello! How can I help you today?',
        sender: {
          id: 'nova',
          name: 'Nova',
          type: 'agent'
        },
        timestamp: new Date().toISOString()
      }];
    } catch (error) {
      console.error('Failed to create thread:', error);
    }

    // Set up WebSocket
    try {
      wsInstance = await setupChatWebSocket(
        // New message handler
        (message) => {
          if (message.threadId === currentThreadId) {
            messages = [...messages, message];
          }
        },
        // Thread update handler
        (thread) => {
          if (thread.id === currentThreadId) {
            // Update thread info if needed
          }
        },
        // Agent status handler
        (status) => {
          if (status.threadId === currentThreadId) {
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
      // Ask Nova first
      const { threadId, message } = await askNova(inputContent.trim());
      
      // Update thread ID if Nova created a new one
      if (threadId !== currentThreadId) {
        currentThreadId = threadId;
        messages = []; // Clear messages for new thread
      }

      messages = [...messages, message];
      
      // Get agent suggestions
      const suggestions = await suggestAgents(currentThreadId, inputContent.trim());
      if (suggestions.recommended.length > 0) {
        suggestedAgents = suggestions.recommended.map(type => ({
          type,
          confidence: suggestions.confidence
        }));
        showAgentSuggestions = true;
      }
      
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

  async function handleSpawnAgent(agentType: AgentType) {
    try {
      const agent = await spawnAgent({
        threadId: currentThreadId,
        agentType,
        domain: currentDomain || undefined
      });
      
      agents = [...agents, agent];
      
      // Add system message about agent joining
      messages = [...messages, {
        id: `system-${Date.now()}`,
        threadId: currentThreadId,
        content: `${agent.name} has joined the conversation.`,
        sender: {
          id: 'system',
          name: 'System',
          type: 'agent'
        },
        timestamp: new Date().toISOString()
      }];
      
      showAgentSuggestions = false;
    } catch (error) {
      console.error('Failed to spawn agent:', error);
      // TODO: Show error to user
    }
  }

  async function handleCreateTeam() {
    try {
      const team = await createAgentTeam(
        currentThreadId,
        suggestedAgents.map(({ type }) => ({ type, domain: currentDomain || undefined }))
      );
      
      agents = [...agents, ...team];
      
      // Add system message about team creation
      messages = [...messages, {
        id: `system-${Date.now()}`,
        threadId: currentThreadId,
        content: `Created a team with agents: ${team.map(a => a.name).join(', ')}`,
        sender: {
          id: 'system',
          name: 'System',
          type: 'agent'
        },
        timestamp: new Date().toISOString()
      }];
      
      showAgentSuggestions = false;
    } catch (error) {
      console.error('Failed to create team:', error);
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

<div class="flex h-screen overflow-hidden" style="background-color: var(--slack-bg-secondary);">
  <!-- Left Sidebar -->
  <div class="w-64 flex flex-col border-r" style="border-color: var(--slack-border-dim);">
    <!-- Domain Selector -->
    <div class="p-4 border-b" style="border-color: var(--slack-border-dim);">
      <select
        class="w-full px-3 py-2 rounded text-sm appearance-none cursor-pointer"
        style="
          background-color: var(--slack-bg-tertiary);
          border: 1px solid var(--slack-border-dim);
          color: var(--slack-text-primary);
        "
        bind:value={currentDomain}
      >
        <option value="general">General</option>
        <option value="retail">Retail</option>
        <option value="bfsi">BFSI</option>
        <option value="personal">Personal</option>
      </select>
    </div>

    <!-- Workspaces -->
    <div class="flex-1 overflow-y-auto slack-scrollbar">
      <!-- Personal Workspace -->
      <div class="mb-4">
        <div class="px-4 py-2 font-medium" style="color: var(--slack-text-secondary)">
          Personal Workspace
        </div>
        {#each threads.filter(t => t.metadata?.domain === 'personal') as thread (thread.id)}
          <button
            class="w-full px-4 py-2 text-left hover:opacity-80 transition-opacity"
            class:active={thread.id === currentThreadId}
            style="
              color: var(--slack-text-primary);
              background-color: {thread.id === currentThreadId ? 'var(--slack-bg-tertiary)' : 'transparent'};
            "
            on:click={() => handleThreadSelect(thread.id)}
          >
            <div class="font-medium">{thread.name}</div>
          </button>
        {/each}
      </div>

      <!-- Professional Workspace -->
      <div>
        <div class="px-4 py-2 font-medium" style="color: var(--slack-text-secondary)">
          Professional Workspace
        </div>
        <!-- BFSI Domain -->
        {#if threads.some(t => t.metadata?.domain === 'bfsi')}
          <div class="mb-2">
            <div class="px-6 py-1 text-sm" style="color: var(--slack-text-muted)">
              BFSI
            </div>
            {#each threads.filter(t => t.metadata?.domain === 'bfsi') as thread (thread.id)}
              <button
                class="w-full px-4 py-2 text-left hover:opacity-80 transition-opacity"
                class:active={thread.id === currentThreadId}
                style="
                  color: var(--slack-text-primary);
                  background-color: {thread.id === currentThreadId ? 'var(--slack-bg-tertiary)' : 'transparent'};
                "
                on:click={() => handleThreadSelect(thread.id)}
              >
                <div class="font-medium">{thread.name}</div>
              </button>
            {/each}
          </div>
        {/if}

        <!-- Retail Domain -->
        {#if threads.some(t => t.metadata?.domain === 'retail')}
          <div class="mb-2">
            <div class="px-6 py-1 text-sm" style="color: var(--slack-text-muted)">
              Retail
            </div>
            {#each threads.filter(t => t.metadata?.domain === 'retail') as thread (thread.id)}
              <button
                class="w-full px-4 py-2 text-left hover:opacity-80 transition-opacity"
                class:active={thread.id === currentThreadId}
                style="
                  color: var(--slack-text-primary);
                  background-color: {thread.id === currentThreadId ? 'var(--slack-bg-tertiary)' : 'transparent'};
                "
                on:click={() => handleThreadSelect(thread.id)}
              >
                <div class="font-medium">{thread.name}</div>
              </button>
            {/each}
          </div>
        {/if}

        <!-- General Domain -->
        {#if threads.some(t => !t.metadata?.domain || t.metadata.domain === 'general')}
          <div class="mb-2">
            <div class="px-6 py-1 text-sm" style="color: var(--slack-text-muted)">
              General
            </div>
            {#each threads.filter(t => !t.metadata?.domain || t.metadata.domain === 'general') as thread (thread.id)}
              <button
                class="w-full px-4 py-2 text-left hover:opacity-80 transition-opacity"
                class:active={thread.id === currentThreadId}
                style="
                  color: var(--slack-text-primary);
                  background-color: {thread.id === currentThreadId ? 'var(--slack-bg-tertiary)' : 'transparent'};
                "
                on:click={() => handleThreadSelect(thread.id)}
              >
                <div class="font-medium">{thread.name}</div>
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- New Thread Button -->
    <button
      class="p-4 border-t hover:opacity-80 transition-opacity"
      style="
        border-color: var(--slack-border-dim);
        color: var(--slack-text-primary);
      "
      on:click={handleNewThread}
    >
      + New Thread
    </button>
  </div>

  <!-- Main Chat Area -->
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
        <span style="color: var(--slack-text-secondary)">Loading...</span>
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
            Nova Chat
          </h1>
          {#if currentDomain}
            <span class="text-sm" style="color: var(--slack-text-secondary)">
              Domain: {currentDomain}
            </span>
          {/if}
        </div>
        
        <!-- Agent Controls -->
        <div class="flex items-center space-x-4">
          <!-- Agent Team View -->
          <AgentTeamView 
            {agents}
            onAgentClick={(agent) => {
              selectedAgent = agent;
              filteredAgentId = agent.id;
            }}
          />
        </div>
      </div>
    </div>

    <!-- Agent Suggestions -->
    {#if showAgentSuggestions}
    <div class="p-4 border-b" style="border-color: var(--slack-border-dim); background-color: var(--slack-bg-tertiary);">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium" style="color: var(--slack-text-secondary)">
          Suggested Agents
        </span>
        <button 
          class="text-sm hover:underline"
          style="color: var(--slack-text-secondary);"
          on:click={() => showAgentSuggestions = false}
        >
          Dismiss
        </button>
      </div>
      
      <div class="flex flex-wrap gap-2">
        {#each suggestedAgents as { type, confidence }}
          <button
            class="px-3 py-1 rounded text-sm transition-colors duration-150"
            style="background-color: var(--slack-accent-primary); color: white;"
            on:click={() => handleSpawnAgent(type)}
          >
            {type}
            <span class="ml-1 opacity-75">({Math.round(confidence * 100)}%)</span>
          </button>
        {/each}
        
        {#if suggestedAgents.length > 1}
          <button
            class="px-3 py-1 rounded text-sm transition-colors duration-150"
            style="background-color: var(--slack-accent-secondary); color: white;"
            on:click={handleCreateTeam}
          >
            Create Team
          </button>
        {/if}
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

            <!-- Thread Indicator -->
            {#if message.metadata?.hasThread}
              <button 
                class="opacity-0 group-hover:opacity-100 px-2 py-1 rounded text-sm transition-opacity duration-200"
                style="color: var(--slack-text-secondary); background-color: var(--slack-bg-tertiary);"
                on:click={() => goto(`/threads/${message.metadata?.threadId}`)}
              >
                View Thread
              </button>
            {/if}
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
            tabindex="0"
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
              Message Nova...
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
