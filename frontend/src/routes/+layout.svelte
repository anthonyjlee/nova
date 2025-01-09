<script lang="ts">
  import '../app.css';
  import '../lib/styles/theme.css';
  import Sidebar from '$lib/components/Sidebar.svelte';
  import GraphPanel from '$lib/components/GraphPanel.svelte';
</script>

<div class="h-screen flex flex-col" style="background-color: var(--slack-bg-primary);">
  <!-- Top Navigation Bar -->
  <header class="slack-header">
    <div class="flex-1 flex items-center">
      <h1 class="text-lg font-semibold" style="color: var(--slack-text-primary)">NIA</h1>
    </div>
  </header>

  <!-- Main Content Area -->
  <div class="flex-1 flex overflow-hidden">
    <!-- Left Sidebar - Channels/Threads -->
    <nav class="w-64 flex-shrink-0 slack-panel slack-scrollbar overflow-y-auto">
      <Sidebar />
    </nav>

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
