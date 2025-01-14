<script lang="ts">
import { onMount } from 'svelte';
import { useComponentLifecycle } from '$lib/utils/component-lifecycle';
import AgentTeamView from '$lib/components/AgentTeamView.svelte';
import AgentDetailsPanel from '$lib/components/AgentDetailsPanel.svelte';
import type { ThreadParticipant, WorkspaceType, DomainType } from '$lib/types/chat';
import type { Agent, AgentType, AgentWorkspace, AgentDomain, AgentStatus } from '$lib/types/agent';
import { listAgents } from '$lib/services/agents';
import { appStore, workspace, activeDomainFilter, filteredAgents } from '$lib/stores/app';

const lifecycle = useComponentLifecycle('AgentsPage');

let agents: ThreadParticipant[] = [];
let selectedAgent: ThreadParticipant | null = null;
let loading = true;
let error: string | null = null;

// Subscribe to stores
const workspaceStore = lifecycle.trackSubscription(workspace.subscribe, {
    operation: 'subscribeToWorkspace',
    name: 'workspace'
});

const domainStore = lifecycle.trackSubscription(activeDomainFilter.subscribe, {
    operation: 'subscribeToActiveDomainFilter',
    name: 'activeDomainFilter'
});

const agentsStore = lifecycle.trackSubscription(filteredAgents.subscribe, {
    operation: 'subscribeToAgents',
    name: 'agents'
});

$: currentWorkspace = $workspaceStore;
$: currentDomain = $domainStore;

// Map workspace types
function mapWorkspaceType(workspace: WorkspaceType): AgentWorkspace {
    switch (workspace) {
        case 'personal': return 'personal';
        case 'professional': return 'shared';
        default: return 'system';
    }
}

// Map domain types
function mapDomainType(domain: DomainType | undefined): AgentDomain {
    if (!domain) return 'general';
    switch (domain) {
        case 'general': return 'general';
        case 'tasks': return 'tasks';
        case 'chat': return 'chat';
        default: return 'general';
    }
}

// Convert Agent to ThreadParticipant
function convertAgentToParticipant(agent: Agent): ThreadParticipant {
    const { capabilities, type, thread_id, created_at, ...otherMetadata } = agent.metadata;
    return {
        id: agent.id,
        name: agent.name,
        type: 'agent',
        agentType: agent.type === 'team' ? 'nova' : agent.type,
        workspace: agent.workspace === 'shared' ? 'professional' : 'personal',
        domain: agent.domain as DomainType,
        status: agent.status,
        threadId: thread_id,
        metadata: {
            capabilities,
            specialization: type,
            ...otherMetadata
        }
    };
}

// Convert ThreadParticipant to Agent
function convertParticipantToAgent(participant: ThreadParticipant): Agent {
    const { capabilities, specialization, ...otherMetadata } = participant.metadata || {};
    return {
        id: participant.id,
        name: participant.name,
        type: participant.agentType as AgentType || 'agent',
        workspace: mapWorkspaceType(participant.workspace),
        domain: mapDomainType(participant.domain),
        status: (participant.status || 'active') as AgentStatus,
        metadata: {
            capabilities: capabilities || [],
            type: specialization || '',
            thread_id: participant.threadId || '',
            created_at: new Date().toISOString(),
            ...otherMetadata
        }
    };
}

// Update agents when store changes
$: agents = $agentsStore.map(convertAgentToParticipant);

async function fetchAgents() {
    const resource = lifecycle.trackResource('api', {
        operation: 'fetchAgents'
    });

    try {
        loading = true;
        error = null;
        const fetchedAgents = await listAgents();
        // Convert ThreadParticipant[] to Agent[] before updating store
        const convertedAgents = fetchedAgents.map(convertParticipantToAgent);
        appStore.updateAgents(convertedAgents);
    } catch (e) {
        error = e instanceof Error ? e.message : 'Failed to load agents';
    } finally {
        loading = false;
        resource.release();
    }
}

function handleAgentClick(agent: ThreadParticipant) {
    selectedAgent = agent;
    appStore.setRightPanelOpen(true);
}

function handleThreadOpen(threadId: string) {
    // Navigate to thread
    window.location.href = `/threads/${threadId}`;
}

function handleClose() {
    selectedAgent = null;
    appStore.setRightPanelOpen(false);
}

function handleFocusMessages() {
    if (selectedAgent?.threadId) {
        handleThreadOpen(selectedAgent.threadId);
    }
}

onMount(() => {
    fetchAgents();
});
</script>

<div class="border-b border-gray-700 p-4 bg-[#0D1117]">
        <div class="flex items-center justify-between">
            <div class="flex items-center">
                <h1 class="text-lg font-medium text-gray-200">Agents</h1>
            </div>
            <div class="flex items-center space-x-4">
                <button 
                    class="inline-flex items-center justify-center h-9 px-3 text-sm font-medium rounded bg-white text-[#1D1C1D] hover:bg-[#F8F8F8] disabled:opacity-75 disabled:hover:bg-white transition-colors"
                >
                    New Agent
                </button>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="p-6 overflow-auto">
        <div class="max-w-6xl mx-auto">
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
        <AgentDetailsPanel
            agent={selectedAgent}
            onClose={handleClose}
            onFocusMessages={handleFocusMessages}
        />
    {/if}
