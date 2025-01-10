<script lang="ts">
  import '../app.css';
  import '../lib/styles/theme.css';
  import GraphPanel from '$lib/components/GraphPanel.svelte';
  import { WORKSPACE_DOMAINS } from '$lib/types/chat';
  import { currentWorkspace, currentDomain } from '$lib/stores/workspace';
  import { activeDomainFilter, type DomainFilter } from '$lib/stores/filters';
  import type { WorkspaceType, DomainType } from '$lib/types/chat';

  let showWorkspaceMenu = false;
  let showDomainMenu = false;
  let workspaceValue: WorkspaceType;
  let domainValue: DomainType;
  let currentFilter: DomainFilter;

  // Subscribe to stores
  currentWorkspace.subscribe(value => workspaceValue = value);
  currentDomain.subscribe(value => domainValue = value);
  activeDomainFilter.subscribe(value => currentFilter = value);

  function handleWorkspaceChange(workspace: WorkspaceType) {
    currentWorkspace.set(workspace);
    currentDomain.set(WORKSPACE_DOMAINS[workspace][0]);
    showWorkspaceMenu = false;
  }

  function handleDomainChange(domain: DomainType) {
    currentDomain.set(domain);
    showDomainMenu = false;
  }
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
    <!-- Main Chat Area -->
    <main class="flex-1 flex flex-col overflow-hidden" style="background-color: var(--slack-bg-secondary);">
      <slot />
    </main>

    <!-- Right Panel - Graph Visualization -->
    <aside class="w-96 flex-shrink-0 slack-panel slack-scrollbar overflow-y-auto">
      <GraphPanel />
    </aside>
  </div>
</div>
