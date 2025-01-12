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

<div class="flex h-full">
    <!-- Main Content -->
    <div class="flex-1 overflow-hidden">
        <div class="h-full">
            <GraphPanel />
        </div>
    </div>
</div>

<style>
    /* Ensure full height layout */
    :global(body) {
        height: 100vh;
        overflow: hidden;
    }
</style>
