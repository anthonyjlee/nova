<script lang="ts">
import { onMount } from 'svelte';
import { useComponentLifecycle } from '$lib/utils/component-lifecycle';
import GraphPanel from '$lib/components/GraphPanel.svelte';
import { currentWorkspace, currentDomain } from '$lib/stores/workspace';

const lifecycle = useComponentLifecycle('KnowledgePage');

// Track store subscriptions
const workspace = lifecycle.trackSubscription(currentWorkspace.subscribe, {
    operation: 'subscribeToWorkspace',
    name: 'workspace'
});
const domain = lifecycle.trackSubscription(currentDomain.subscribe, {
    operation: 'subscribeToDomain',
    name: 'domain'
});
</script>

<div class="border-b border-gray-700 p-4 bg-[#0D1117]">
    <div class="flex items-center justify-between">
        <div class="flex items-center">
            <h1 class="text-lg font-medium text-gray-200">Knowledge</h1>
        </div>
        <div class="flex items-center space-x-4">
            <button 
                class="inline-flex items-center justify-center h-9 px-3 text-sm font-medium rounded bg-white text-[#1D1C1D] hover:bg-[#F8F8F8] disabled:opacity-75 disabled:hover:bg-white transition-colors"
            >
                Add Document
            </button>
        </div>
    </div>
</div>

<div class="h-full">
    <GraphPanel />
</div>
