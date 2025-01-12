<script lang="ts">
  import '../app.css';
  import '../lib/styles/theme.css';
  import GraphPanel from '$lib/components/GraphPanel.svelte';
  import { WORKSPACE_DOMAINS } from '$lib/types/chat';
  import { currentWorkspace, currentDomain } from '$lib/stores/workspace';
  import { activeDomainFilter, type DomainFilter } from '$lib/stores/filters';
  import type { WorkspaceType, DomainType } from '$lib/types/chat';
  import { page } from '$app/stores';

  let showWorkspaceMenu = false;
  let showDomainMenu = false;
  let workspaceValue: WorkspaceType;
  let domainValue: DomainType;
  let currentFilter: DomainFilter;

  // Subscribe to stores
  currentWorkspace.subscribe(value => workspaceValue = value);
  currentDomain.subscribe(value => domainValue = value);
  activeDomainFilter.subscribe(value => currentFilter = value);

  // Navigation state
  const channels = [
    { id: 'nova-main', name: 'NOVA Main', type: 'main' },
    { id: 'agent-teams', name: 'Agent Teams', type: 'team' }
  ];

  const sections = [
    { id: 'chat', name: 'Chat', icon: '💬', path: '/' },
    { id: 'tasks', name: 'Tasks', icon: '📋', path: '/tasks' },
    { id: 'agents', name: 'Agents', icon: '🤖', path: '/agents' },
    { id: 'knowledge', name: 'Knowledge', icon: '🧠', path: '/knowledge' }
  ];

  function handleWorkspaceChange(workspace: WorkspaceType) {
    currentWorkspace.set(workspace);
    currentDomain.set(WORKSPACE_DOMAINS[workspace][0]);
    showWorkspaceMenu = false;
  }

  function handleDomainChange(domain: DomainType) {
    currentDomain.set(domain);
    showDomainMenu = false;
  }

  // Get current section from URL
  $: currentSection = sections.find(s => $page.url.pathname === s.path)?.id || 'chat';
</script>

<div class="h-screen flex flex-col" style="background-color: var(--slack-bg-primary);">
  <!-- Top Navigation Bar -->
  <header class="p-4 border-b flex items-center justify-between" style="border-color: var(--slack-border-dim);">
    <div class="flex items-center space-x-4">
      <!-- Logo -->
      <h1 class="text-lg font-semibold" style="color: var(--slack-text-primary)">NIA</h1>

      <!-- Access Level -->
      <div class="relative">
        <button
          class="px-3 py-1 rounded text-sm hover:opacity-80 transition-opacity flex items-center"
          style="background-color: var(--slack-bg-tertiary); color: var(--slack-text-primary);"
          on:click={() => showWorkspaceMenu = !showWorkspaceMenu}
        >
          {workspaceValue === 'personal' ? 'Personal' : 'Professional'}
          <span class="ml-2">▼</span>
        </button>
        {#if showWorkspaceMenu}
          <div 
            class="absolute top-full left-0 mt-1 w-48 rounded shadow-lg z-50"
            style="background-color: var(--slack-bg-primary); border: 1px solid var(--slack-border-dim);"
          >
            <button
              class="w-full px-4 py-2 text-left hover:opacity-80 transition-opacity"
              style="color: var(--slack-text-primary);"
              on:click={() => handleWorkspaceChange('personal')}
            >
              Personal
            </button>
            <button
              class="w-full px-4 py-2 text-left hover:opacity-80 transition-opacity"
              style="color: var(--slack-text-primary);"
              on:click={() => handleWorkspaceChange('professional')}
            >
              Professional
            </button>
          </div>
        {/if}
      </div>

      <!-- Domain Selector -->
      <div class="relative">
        <button
          class="px-3 py-1 rounded text-sm hover:opacity-80 transition-opacity flex items-center"
          style="background-color: var(--slack-bg-tertiary); color: var(--slack-text-primary);"
          on:click={() => showDomainMenu = !showDomainMenu}
        >
          {domainValue.charAt(0).toUpperCase() + domainValue.slice(1)}
          <span class="ml-2">▼</span>
        </button>
        {#if showDomainMenu}
          <div 
            class="absolute top-full left-0 mt-1 w-48 rounded shadow-lg z-50"
            style="background-color: var(--slack-bg-primary); border: 1px solid var(--slack-border-dim);"
          >
            {#each WORKSPACE_DOMAINS[workspaceValue] as domain}
              <button
                class="w-full px-4 py-2 text-left hover:opacity-80 transition-opacity"
                style="color: var(--slack-text-primary);"
                on:click={() => handleDomainChange(domain)}
              >
                {domain.charAt(0).toUpperCase() + domain.slice(1)}
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </header>

  <!-- Main Content Area -->
  <div class="flex-1 flex overflow-hidden">
    <!-- Left Navigation Panel -->
    <nav class="w-60 border-r border-slack-border-dim flex flex-col">
      <!-- Search -->
      <div class="p-3 border-b border-slack-border-dim">
        <input
          type="text"
          placeholder="Search..."
          class="w-full px-3 py-1.5 rounded text-sm"
          style="background-color: var(--slack-bg-tertiary); color: var(--slack-text-primary); border: 1px solid var(--slack-border-dim);"
        />
      </div>

      <!-- Channels -->
      <div class="p-3 border-b border-slack-border-dim">
        <h2 class="text-sm font-medium mb-2" style="color: var(--slack-text-primary)">Channels</h2>
        <div class="space-y-1">
          {#each channels as channel}
            <a
              href="/"
              class="block px-2 py-1 rounded text-sm hover:bg-slack-bg-hover transition-colors duration-100"
              class:bg-slack-bg-active={currentSection === 'chat'}
              style="color: var(--slack-text-primary);"
            >
              # {channel.name}
            </a>
          {/each}
        </div>
      </div>

      <!-- Sections -->
      <div class="p-3">
        <h2 class="text-sm font-medium mb-2" style="color: var(--slack-text-primary)">Sections</h2>
        <div class="space-y-1">
          {#each sections as section}
            <a
              href={section.path}
              class="flex items-center px-2 py-1 rounded text-sm hover:bg-slack-bg-hover transition-colors duration-100"
              class:bg-slack-bg-active={currentSection === section.id}
              style="color: var(--slack-text-primary);"
            >
              <span class="mr-2">{section.icon}</span>
              {section.name}
            </a>
          {/each}
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col overflow-hidden" style="background-color: var(--slack-bg-secondary);">
      <slot />
    </main>

    <!-- Right Panel - Context Aware -->
    <aside class="w-96 flex-shrink-0 slack-panel slack-scrollbar overflow-y-auto">
      {#if currentSection === 'knowledge'}
        <GraphPanel />
      {:else if currentSection === 'tasks'}
        <!-- Task Details -->
        <slot name="task-details" />
      {:else if currentSection === 'agents'}
        <!-- Agent Details -->
        <slot name="agent-details" />
      {:else}
        <!-- Chat Details -->
        <slot name="chat-details" />
      {/if}
    </aside>
  </div>
</div>

<style>
  :global(.slack-panel) {
    border-left: 1px solid var(--slack-border-dim);
    background-color: var(--slack-bg-secondary);
  }

  :global(.slack-scrollbar) {
    scrollbar-width: thin;
    scrollbar-color: var(--slack-border-bright) transparent;
  }

  :global(.slack-scrollbar::-webkit-scrollbar) {
    width: 8px;
  }

  :global(.slack-scrollbar::-webkit-scrollbar-track) {
    background: transparent;
  }

  :global(.slack-scrollbar::-webkit-scrollbar-thumb) {
    background-color: var(--slack-border-bright);
    border-radius: 4px;
  }
</style>
