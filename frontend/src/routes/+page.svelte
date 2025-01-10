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
    getThreadAgents,
    getAvailableAgents,
    toggleThreadPin,
    updateThreadMetadata,
    checkServerStatus
  } from '$lib/services/chat';
  import type { 
    Message, 
    AgentType, 
    ThreadParticipant, 
    Thread,
    WorkspaceType,
    DomainType,
    WorkspaceConfig
  } from '$lib/types/chat';
  import { WORKSPACE_DOMAINS } from '$lib/types/chat';
  import { currentWorkspace, currentDomain } from '$lib/stores/workspace';
  import AgentTeamView from '$lib/components/AgentTeamView.svelte';
  import AgentDetailsPanel from '$lib/components/AgentDetailsPanel.svelte';
  
  let messages: Message[] = [];
  let threads: Thread[] = [];

  let novaThread: Thread | null = null;
  let novaTeamThread: Thread | null = null;

  let specializedAgents: ThreadParticipant[] = [];

  let agents: ThreadParticipant[] = [];
  let inputContent = '';
  let inputElement: HTMLDivElement;
  let wsInstance: WebSocket | null = null;
  let currentThreadId = 'nova-team';
  let suggestedAgents: { type: AgentType; confidence: number }[] = [];
  let showAgentSuggestions = false;
  let loading = false;
  let error: string | null = null;
  let selectedAgent: ThreadParticipant | null = null;
  let filteredAgentId: string | null = null;
  let workspaceConfig: WorkspaceConfig | null = null;
  let workspaceValue: WorkspaceType;
  let domainValue: DomainType;
  let serverStatus: { status: string; version: string } | null = null;

  // Subscribe to stores
  currentWorkspace.subscribe(value => workspaceValue = value);
  currentDomain.subscribe(value => domainValue = value);

  $: filteredMessages = filteredAgentId 
    ? messages.filter(m => m.sender.id === filteredAgentId)
    : messages;

  async function handleThreadSelect(threadId: string) {
    try {
      loading = true;
      
      // If selecting NovaTeam, use the thread from server
      if (threadId === 'nova-team' && novaTeamThread) {
        const [threadMessages, threadAgents] = await Promise.all([
          getThreadMessages(threadId),
          getThreadAgents(threadId)
        ]);
        
        agents = threadAgents;
        currentThreadId = threadId;
        messages = threadMessages;
        currentWorkspace.set(novaTeamThread.workspace);
        if (novaTeamThread.metadata?.domain) {
          currentDomain.set(novaTeamThread.metadata.domain);
        }
      } else if (threadId === 'nova-team') {
        // NovaTeam thread not found
        error = 'NovaTeam thread not found';
        return;
      } else {
        // Otherwise fetch from server
        const [thread, threadMessages, threadAgents] = await Promise.all([
          getThread(threadId),
          getThreadMessages(threadId),
          getThreadAgents(threadId)
        ]);
        agents = threadAgents;
        currentThreadId = threadId;
        messages = threadMessages;
        currentWorkspace.set(thread.workspace);
        if (thread.metadata?.domain) {
          currentDomain.set(thread.metadata.domain);
        }
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load thread';
    } finally {
      loading = false;
    }
  }

  async function handleNewThread(type: 'channel' | 'project') {
    try {
      loading = true;
      const thread = await createThread('New Chat', {
        workspace: workspaceValue,
        domain: domainValue,
        metadata: {
          type,
          status: 'active'
        }
      });
      threads = [...threads, thread];
      await handleThreadSelect(thread.id);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to create thread';
    } finally {
      loading = false;
    }
  }

  import { activeDomainFilter, type DomainFilter } from '$lib/stores/filters';
  let currentFilter: DomainFilter;
  activeDomainFilter.subscribe(value => currentFilter = value);

  // Computed lists
  $: channelThreads = (() => {
    const allThreads = novaTeamThread ? [novaTeamThread, ...threads] : threads;
    return Array.isArray(allThreads) 
      ? allThreads.filter(t => 
          t.metadata?.type === 'channel' || t.metadata?.type === 'agent-team'
        )
        .sort((a, b) => {
          // Sort pinned threads first
          if (a.metadata?.pinned && !b.metadata?.pinned) return -1;
          if (!a.metadata?.pinned && b.metadata?.pinned) return 1;
          // Then sort by name
          return a.name.localeCompare(b.name);
        })
      : [];
  })();
  $: projectThreads = Array.isArray(threads) 
    ? threads.filter(t => 
        t.metadata?.type === 'project'
      ) 
    : [];
  $: directMessageAgents = Array.isArray(agents) 
    ? agents.filter(a => a.type === 'agent') 
    : [];

  async function loadThreads() {
    try {
      loading = true;
      
      // Load all threads
      const userThreads = await listThreads();
      
      // Find or create Nova and NovaTeam threads
      novaThread = userThreads.find(t => t.id === 'nova') || null;
      novaTeamThread = userThreads.find(t => t.id === 'nova-team') || null;

      if (!novaThread) {
        novaThread = await createThread('NOVA', {
          workspace: 'personal',
          metadata: {
            type: 'direct-message',
            status: 'active',
            system: true
          }
        });
        userThreads.push(novaThread);
      }

      if (!novaTeamThread) {
        novaTeamThread = await createThread('NovaTeam', {
          workspace: 'personal',
          metadata: {
            type: 'agent-team',
            status: 'active',
            system: true,
            pinned: true,
            description: 'This is where NOVA and core agents like BeliefAgent, DesireAgent, and IntentionAgent collaborate.'
          }
        });
        
        // Create core team
        await createAgentTeam(
          novaTeamThread.id,
          [
            { type: 'nova', workspace: 'personal' },
            { type: 'belief', workspace: 'personal' },
            { type: 'desire', workspace: 'personal' },
            { type: 'intention', workspace: 'personal' }
          ]
        );
        
        userThreads.push(novaTeamThread);
      }
      
      // Filter out Nova and NovaTeam from regular threads
      threads = userThreads.filter(t => t.id !== 'nova' && t.id !== 'nova-team');
      
      // Select NovaTeam by default if no thread is selected
      if (!currentThreadId) {
        await handleThreadSelect('nova-team');
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load threads';
    } finally {
      loading = false;
    }
  }

  onMount(async () => {
    try {
      // Check server status
      try {
        serverStatus = await checkServerStatus();
      } catch (err) {
        console.error('Failed to check server status:', err);
        error = 'Server is not responding';
        return;
      }

      // Load available agents
      try {
        specializedAgents = await getAvailableAgents();
      } catch (err) {
        console.error('Failed to load available agents:', err);
        // Keep empty list if API fails
      }

      await loadThreads();
      if (inputElement) {
        inputElement.addEventListener('input', () => {
          inputContent = inputElement.textContent || '';
        });
      }

      // Initialize NovaTeam thread
      await handleThreadSelect('nova-team');
    } catch (err) {
      console.error('Failed to initialize:', err);
      error = err instanceof Error ? err.message : 'Failed to initialize';
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
        workspace: workspaceValue,
        domain: domainValue
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
        workspace: workspaceValue,
        timestamp: new Date().toISOString()
      }];
      
      showAgentSuggestions = false;
    } catch (error) {
      console.error('Failed to spawn agent:', error);
      // TODO: Show error to user
    }
  }

  async function togglePin(thread: Thread) {
    // Don't allow unpinning NovaTeam
    if (thread.id === 'nova-team') return;
    
    try {
      const result = await toggleThreadPin(thread.id);
      
      // Update thread in list
      threads = threads.map(t => 
        t.id === thread.id 
          ? { 
              ...t, 
              metadata: { 
                ...t.metadata, 
                pinned: result.pinned 
              } 
            }
          : t
      );
    } catch (error) {
      console.error('Failed to toggle pin:', error);
    }
  }

  async function handleCreateTeam() {
    try {
      // Create a new team thread
      const teamName = `NovaTeam-${Date.now()}`;
      const teamThread = await createThread(teamName, {
        workspace: workspaceValue,
        domain: domainValue,
        metadata: {
          type: 'agent-team',
          status: 'active'
        }
      });

      // Create the team in the new thread
      const team = await createAgentTeam(
        teamThread.id,
        suggestedAgents.map(({ type }) => ({ 
          type, 
          workspace: workspaceValue,
          domain: domainValue
        }))
      );
      
      // Update threads list
      threads = [...threads, teamThread];
      
      // Switch to the new team thread
      await handleThreadSelect(teamThread.id);
      
      showAgentSuggestions = false;
    } catch (error) {
      console.error('Failed to create team:', error);
      // TODO: Show error to user
    }
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleSend();
    }
  }
</script>

<div class="flex h-screen overflow-hidden" style="background-color: var(--slack-bg-secondary);">
  <!-- Left Sidebar -->
  <div class="w-64 flex flex-col border-r overflow-hidden" style="border-color: var(--slack-border-dim);">

    <!-- Channel List -->
    <div class="flex-1 overflow-y-auto slack-scrollbar p-4 pb-16">

      <!-- Channels -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-sm font-medium" style="color: var(--slack-text-secondary)">
            Channels
          </h2>
          <button
            class="w-5 h-5 rounded flex items-center justify-center hover:opacity-80 transition-opacity"
            style="background-color: var(--slack-bg-tertiary);"
            on:click={() => handleNewThread('channel')}
            title="New Channel"
          >
            <span style="color: var(--slack-text-primary)">+</span>
          </button>
        </div>
        {#each channelThreads as thread}
          <button
            class="w-full px-2 py-1 rounded text-left hover:opacity-80 transition-opacity flex items-center group"
            class:active={currentThreadId === thread.id}
            style="
              background-color: {currentThreadId === thread.id ? 'var(--slack-bg-tertiary)' : 'transparent'};
              color: var(--slack-text-primary);
            "
            on:click={() => handleThreadSelect(thread.id)}
          >
            <span class="mr-2">#</span>
            {thread.name}
            <div class="ml-auto flex items-center space-x-2">
              {#if thread.metadata?.type === 'agent-team' && !thread.metadata?.system}
                <button
                  class="opacity-0 group-hover:opacity-100 text-xs px-2 py-0.5 rounded hover:opacity-80 transition-opacity"
                  style="
                    background-color: var(--slack-bg-tertiary);
                    color: var(--slack-text-muted);
                    border: 1px solid var(--slack-border-dim);
                  "
                  on:click|stopPropagation={() => togglePin(thread)}
                >
                  {thread.metadata?.pinned ? 'Unpin' : 'Pin'}
                </button>
              {/if}
              {#if thread.metadata?.unread}
                <span class="w-2 h-2 rounded-full" style="background-color: var(--slack-accent-primary);"></span>
              {/if}
            </div>
          </button>
        {/each}
      </div>

      <!-- Projects -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-sm font-medium" style="color: var(--slack-text-secondary)">
            Projects
          </h2>
          <button
            class="w-5 h-5 rounded flex items-center justify-center hover:opacity-80 transition-opacity"
            style="background-color: var(--slack-bg-tertiary);"
            on:click={() => handleNewThread('project')}
            title="New Project"
          >
            <span style="color: var(--slack-text-primary)">+</span>
          </button>
        </div>
        {#each projectThreads as thread}
          <button
            class="w-full px-2 py-1 rounded text-left hover:opacity-80 transition-opacity flex items-center"
            class:active={currentThreadId === thread.id}
            style="
              background-color: {currentThreadId === thread.id ? 'var(--slack-bg-tertiary)' : 'transparent'};
              color: var(--slack-text-primary);
            "
            on:click={() => handleThreadSelect(thread.id)}
          >
            <span class="mr-2">📂</span>
            {thread.name}
            {#if thread.metadata?.unread}
              <span class="ml-auto w-2 h-2 rounded-full" style="background-color: var(--slack-accent-primary);"></span>
            {/if}
          </button>
        {/each}
      </div>

      <!-- Direct Messages -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-sm font-medium" style="color: var(--slack-text-secondary)">
            Direct Messages
          </h2>
          <button
            class="text-xs hover:underline"
            style="color: var(--slack-text-muted);"
            on:click={() => {/* TODO: Toggle agent list */}}
          >
            {agents.length > 10 ? 'Show more...' : ''}
          </button>
        </div>
        <!-- NOVA (Always First) -->
        <button
          class="w-full px-2 py-1 rounded text-left hover:opacity-80 transition-opacity flex items-center mb-2"
          class:active={currentThreadId === 'nova'}
          style="
            background-color: {currentThreadId === 'nova' ? 'var(--slack-bg-tertiary)' : 'transparent'};
            color: var(--slack-text-primary);
          "
          on:click={() => handleThreadSelect('nova')}
        >
          <div class="w-5 h-5 rounded-full flex items-center justify-center mr-2" style="background-color: var(--slack-accent-primary);">
            <span class="text-white text-xs font-medium">N</span>
          </div>
          <span>NOVA</span>
          <span 
            class="ml-2 w-2 h-2 rounded-full"
            style="background-color: var(--slack-presence-active)"
          ></span>
        </button>
        {#each specializedAgents as agent}
          <button
            class="w-full px-2 py-1 rounded text-left hover:opacity-80 transition-opacity flex items-center"
            style="color: var(--slack-text-primary);"
            on:click={async () => {
              try {
                // Create a DM thread if it doesn't exist
                const thread = await createThread(`DM with ${agent.name}`, {
                  workspace: workspaceValue,
                  metadata: {
                    type: 'direct-message',
                    status: 'active',
                    participants: [agent]
                  }
                });
                
                // Add agent to thread
                await spawnAgent({
                  threadId: thread.id,
                  agentType: agent.agentType || 'unknown',
                  workspace: workspaceValue
                });
                
                // Switch to the thread
                await handleThreadSelect(thread.id);
              } catch (error) {
                console.error('Failed to open DM:', error);
              }
            }}
          >
            <div class="w-5 h-5 rounded-full flex items-center justify-center mr-2" style="background-color: var(--slack-accent-secondary);">
              <span class="text-white text-xs font-medium">{agent.name[0]}</span>
            </div>
            <span>{agent.name}</span>
            <span 
              class="ml-2 w-2 h-2 rounded-full"
              style="background-color: {agent.status === 'active' ? 'var(--slack-presence-active)' : 'var(--slack-text-muted)'}"
            ></span>
          </button>
        {/each}
      </div>
    </div>

    <!-- User Settings (Fixed at Bottom) -->
    <div class="absolute bottom-0 left-0 right-0 p-4 border-t" style="border-color: var(--slack-border-dim); background-color: var(--slack-bg-primary);">
      <button
        class="w-full px-3 py-2 rounded text-sm text-left hover:opacity-80 transition-opacity flex flex-col"
        style="color: var(--slack-text-primary);"
      >
        <div class="flex items-center">
          <div 
            class="w-6 h-6 rounded-full flex items-center justify-center mr-2"
            style="background-color: var(--slack-accent-secondary);"
          >
            <span class="text-white text-xs font-medium">U</span>
          </div>
          <span>User Settings</span>
        </div>
        {#if serverStatus}
          <div class="mt-1 text-xs flex items-center" style="color: var(--slack-text-muted);">
            <span 
              class="w-2 h-2 rounded-full mr-1"
              style="background-color: {serverStatus.status === 'running' ? 'var(--slack-presence-active)' : 'var(--slack-text-error)'}"
            ></span>
            Server {serverStatus.status} (v{serverStatus.version})
          </div>
        {/if}
      </button>
    </div>
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
      <!-- Thread Title & Participants -->
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <h1 class="text-lg font-bold mr-4" style="color: var(--slack-text-primary)">
            {(() => {
              if (currentThreadId === 'nova' && novaThread) {
                return novaThread.name;
              } else if (currentThreadId === 'nova-team' && novaTeamThread) {
                return novaTeamThread.name;
              } else {
                return threads.find(t => t.id === currentThreadId)?.name || '';
              }
            })()}
          </h1>
          {#if (currentThreadId === 'nova-team' && novaTeamThread?.metadata?.type === 'agent-team') || threads.find(t => t.id === currentThreadId)?.metadata?.type === 'agent-team'}
            <div class="flex items-center space-x-1">
              {#each agents as agent}
                <button 
                  class="w-6 h-6 rounded-full flex items-center justify-center -ml-1 first:ml-0 border-2 hover:opacity-80 transition-opacity"
                  style="
                    background-color: var(--slack-accent-secondary);
                    border-color: var(--slack-bg-primary);
                  "
                  on:click={() => {
                    selectedAgent = agent;
                    filteredAgentId = agent.id;
                  }}
                >
                  <span class="text-white text-xs font-medium">{agent.name[0]}</span>
                </button>
              {/each}
            </div>
          {/if}
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
              Message NOVA...
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
