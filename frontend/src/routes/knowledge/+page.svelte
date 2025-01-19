<script lang="ts">
  import { onMount } from 'svelte';
  import { knowledgeStore } from '$lib/stores/knowledge';
  import { knowledgeService } from '$lib/services/knowledge';
  import type { KnowledgeNode, KnowledgeEdge, KnowledgeNodeType, KnowledgeEdgeType } from '$lib/schemas/knowledge';

  let selectedNode: KnowledgeNode | null = null;
  let selectedEdge: KnowledgeEdge | null = null;

  onMount(async () => {
    try {
      await knowledgeService.loadKnowledgeGraph();
    } catch (error) {
      console.error('Failed to load knowledge graph:', error);
    }
  });

  function getNodeColor(type: KnowledgeNodeType): string {
    switch (type) {
      case 'concept':
        return '#5865F2';
      case 'task':
        return '#23A559';
      case 'domain':
        return '#F0B232';
      case 'agent':
        return '#F23F43';
      case 'resource':
        return '#80848E';
      default:
        return '#949BA4';
    }
  }

  function getEdgeColor(type: KnowledgeEdgeType): string {
    switch (type) {
      case 'REFERENCES':
        return '#5865F2';
      case 'DEPENDS_ON':
        return '#F23F43';
      case 'RELATES_TO':
        return '#23A559';
      case 'PART_OF':
        return '#F0B232';
      case 'CROSS_DOMAIN_ACCESS':
        return '#80848E';
      default:
        return '#949BA4';
    }
  }

  function isKnowledgeNodeType(type: string): type is KnowledgeNodeType {
    return ['concept', 'task', 'domain', 'agent', 'resource'].includes(type);
  }
</script>

<div class="h-full bg-[#1A1D21] text-[#DCDDDE]">
  <!-- Header -->
  <div class="flex-none h-12 border-b border-[#2C2D31] flex items-center px-4">
    <h1 class="text-lg font-semibold">Knowledge Graph</h1>
  </div>

  <!-- Content -->
  <div class="flex-1 p-4">
    {#if $knowledgeStore.loading}
      <div class="flex items-center justify-center h-full">
        <div class="w-12 h-12 border-4 border-[#5865F2] border-t-transparent rounded-full animate-spin"></div>
      </div>
    {:else if $knowledgeStore.error}
      <div class="flex flex-col items-center justify-center h-full">
        <div class="text-[#F23F43] mb-4">{$knowledgeStore.error}</div>
        <button
          class="px-4 py-2 bg-[#5865F2] text-white rounded-md hover:bg-[#4752C4] transition-colors"
          on:click={() => knowledgeService.loadKnowledgeGraph()}
        >
          Retry
        </button>
      </div>
    {:else if $knowledgeStore.nodes.length === 0}
      <div class="flex flex-col items-center justify-center h-full">
        <div class="text-[#949BA4] mb-4">No knowledge graph data available</div>
        <div class="text-sm text-[#72767D]">
          Knowledge will be populated as you interact with tasks and agents
        </div>
      </div>
    {:else}
      <div class="grid grid-cols-3 gap-4 h-full">
        <!-- Graph View -->
        <div class="col-span-2 bg-[#2B2D31] rounded-lg p-4">
          <!-- Graph visualization would go here -->
          <div class="flex flex-wrap gap-2">
            {#each $knowledgeStore.nodes as node}
              {#if isKnowledgeNodeType(node.type)}
                <div
                  class="px-3 py-1.5 rounded-full text-sm font-medium cursor-pointer transition-colors"
                  style="background-color: {getNodeColor(node.type)}33; color: {getNodeColor(node.type)}"
                  on:click={() => selectedNode = node}
                >
                  {node.label}
                </div>
              {/if}
            {/each}
          </div>
        </div>

        <!-- Details Panel -->
        <div class="bg-[#2B2D31] rounded-lg p-4">
          {#if selectedNode && isKnowledgeNodeType(selectedNode.type)}
            <div class="space-y-4">
              <h2 class="text-lg font-semibold">{selectedNode.label}</h2>
              <div>
                <div class="text-sm text-[#949BA4]">Type</div>
                <div class="flex items-center mt-1">
                  <div
                    class="w-2 h-2 rounded-full mr-2"
                    style="background-color: {getNodeColor(selectedNode.type)}"
                  ></div>
                  <div class="capitalize">{selectedNode.type}</div>
                </div>
              </div>
              {#if selectedNode.category}
                <div>
                  <div class="text-sm text-[#949BA4]">Category</div>
                  <div class="mt-1 capitalize">{selectedNode.category}</div>
                </div>
              {/if}
              {#if selectedNode.domain}
                <div>
                  <div class="text-sm text-[#949BA4]">Domain</div>
                  <div class="mt-1">{selectedNode.domain}</div>
                </div>
              {/if}
              {#if selectedNode.metadata}
                <div>
                  <div class="text-sm text-[#949BA4]">Metadata</div>
                  <pre class="mt-1 text-xs bg-[#1A1D21] p-2 rounded overflow-auto">
                    {JSON.stringify(selectedNode.metadata, null, 2)}
                  </pre>
                </div>
              {/if}
            </div>
          {:else}
            <div class="text-center text-[#949BA4]">
              Select a node to view details
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>
