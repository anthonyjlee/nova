<script lang="ts">
  import { onMount } from 'svelte';
  
  // Mock data for initial development
  const messages = [
    {
      id: 1,
      agent: 'Nova',
      content: 'Hello! How can I help you today?',
      timestamp: new Date().toISOString(),
      hasThread: false
    }
  ];

  let inputContent = '';
  let inputElement: HTMLDivElement;

  onMount(() => {
    if (inputElement) {
      inputElement.addEventListener('input', () => {
        inputContent = inputElement.textContent || '';
      });
    }
  });
</script>

<div class="flex-1 flex flex-col overflow-hidden">
  <!-- Messages Area -->
  <div class="flex-1 overflow-y-auto slack-scrollbar p-4">
    {#each messages as message (message.id)}
      <div class="slack-message group">
        <div class="flex items-start space-x-2">
          <!-- Agent Avatar -->
          <div 
            class="w-9 h-9 rounded flex items-center justify-center flex-shrink-0"
            style="background-color: var(--slack-accent-primary);"
          >
            <span class="text-white font-medium">
              {message.agent[0].toUpperCase()}
            </span>
          </div>

          <!-- Message Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-baseline">
              <span class="font-bold" style="color: var(--slack-text-primary)">
                {message.agent}
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
          {#if message.hasThread}
            <button 
              class="opacity-0 group-hover:opacity-100 px-2 py-1 rounded text-sm transition-opacity duration-200"
              style="color: var(--slack-text-secondary); background-color: var(--slack-bg-tertiary);"
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
          aria-label="Message input"
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
      >
        Send
      </button>
    </div>
  </div>
</div>
