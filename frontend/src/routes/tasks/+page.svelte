<script lang="ts">
  import { page } from '$app/stores';
  import TaskBoard from '$lib/components/TaskBoard.svelte';

  // Get workspace and domain from URL params
  $: workspace = $page.params.workspace || 'personal';
  $: domain = $page.params.domain || 'general';
</script>

<div class="h-full bg-[#1A1D21] text-[#DCDDDE]">
  <!-- Header -->
  <div class="flex-none h-12 border-b border-[#2C2D31] flex items-center px-4">
    <h1 class="text-lg font-semibold">Tasks</h1>
  </div>

  <!-- Content -->
  <div class="flex-1">
    <TaskBoard {workspace} {domain} />
  </div>
</div>
