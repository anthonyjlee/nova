<script lang="ts">
import { onMount } from 'svelte';
import { useComponentLifecycle } from '$lib/utils/component-lifecycle';
import AgentTeamView from '$lib/components/AgentTeamView.svelte';
import AgentDetailsPanel from '$lib/components/AgentDetailsPanel.svelte';
import type { ThreadParticipant } from '$lib/types/chat';
import { currentWorkspace, currentDomain } from '$lib/stores/workspace';

const lifecycle = useComponentLifecycle('AgentsPage');

let agents: ThreadParticipant[] = [];
let selectedAgent: ThreadParticipant | null = null;
let loading = true;
let error: string | null = null;

// Track store subscriptions
const workspace = lifecycle.trackSubscription(currentWorkspace.subscribe, {
    operation: 'subscribeToWorkspace',
    name: 'workspace'
});
const domain = lifecycle.trackSubscription(currentDomain.subscribe, {
    operation: 'subscribeToDomain',
    name: 'domain'
});

async function fetchAgents() {
    const resource = lifecycle.trackResource('api', {
        operation: 'fetchAgents'
    });

    try {
        loading = true;
        error = null;
        const response = await fetch('/api/agents');
        if (!response.ok) throw new Error('Failed to fetch agents');
        
        agents = await response.json();
    } catch (e) {
        error = e instanceof Error ? e.message : 'Failed to load agents';
    } finally {
        loading = false;
        resource.release();
    }
}

function handleAgentClick(agent: ThreadParticipant) {
    selectedAgent = agent;
}

function handleThreadOpen(threadId: string) {
    // Navigate to thread
    window.location.href = `/threads/${threadId}`;
}

function handleClose() {
    selectedAgent = null;
}

function handleFocusMessages() {
    if (selectedAgent?.threadId) {
        handleThreadOpen(selectedAgent.threadId);
    }
}

onMount(() => {
    fetchAgents();
    
    // Set up WebSocket for real-time updates
    const ws = lifecycle.trackResource('websocket', {
        operation: 'connectWebSocket',
        name: 'agentUpdates'
    });
    
    const socket = new WebSocket('ws://localhost:3000/api/ws/agents');
    
    socket.onmessage = (event) => {
        const update = JSON.parse(event.data);
        agents = lifecycle.trackCompute(() => {
            return agents.map(agent => 
                agent.id === update.agentId 
                    ? { ...agent, ...update }
                    : agent
            );
        }, {
            operation: 'updateAgent',
            agentId: update.agentId
        });
    };
    
    return () => {
        socket.close();
        ws.release();
    };
});
</script>

<div class="flex h-full">
    <!-- Main Content -->
    <div class="flex-1 p-6 overflow-auto">
        <div class="max-w-6xl mx-auto">
            <!-- Header -->
            <div class="mb-6">
                <h1 class="text-2xl font-semibold text-slack-text-primary">Agents</h1>
                <p class="text-slack-text-muted mt-1">
                    View and manage all agents and teams
                </p>
            </div>

            {#if error}
                <div class="bg-red-500 bg-opacity-10 text-red-500 p-4 rounded mb-6">
                    {error}
                    <button
                        class="underline ml-2"
                        on:click={fetchAgents}
                    >
                        Retry
                    </button>
                </div>
            {/if}

            {#if loading}
                <div class="flex items-center justify-center h-32">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-slack-text-primary"></div>
                </div>
            {:else}
                <AgentTeamView
                    {agents}
                    showAll={true}
                    onAgentClick={handleAgentClick}
                    onThreadOpen={handleThreadOpen}
                />
            {/if}
        </div>
    </div>

    <!-- Details Panel -->
    {#if selectedAgent}
        <div class="w-96 border-l border-slack-border-dim">
            <AgentDetailsPanel
                agent={selectedAgent}
                onClose={handleClose}
                onFocusMessages={handleFocusMessages}
            />
        </div>
    {/if}
</div>

<style>
    /* Ensure full height layout */
    :global(body) {
        height: 100vh;
        overflow: hidden;
    }
</style>
