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
    createThread
  } from '$lib/services/chat';
  import type { Message, AgentType, ThreadParticipant } from '$lib/types/chat';
  
  let messages: Message[] = [];
  let inputContent = '';
  let inputElement: HTMLDivElement;
  let wsInstance: WebSocket | null = null;
  let currentThreadId = '';
  let suggestedAgents: { type: AgentType; confidence: number }[] = [];
  let showAgentSuggestions = false;
  let currentDomain: string | null = null;

  onMount(async () => {
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
            // Update agent status if needed
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

<div class="flex-1 flex flex-col overflow-hidden relative" style="background-color: var(--slack-bg-secondary);">
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
