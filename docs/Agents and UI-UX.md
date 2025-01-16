# Agents and UI/UX Integration

This document explains how Nova's agent system integrates with the UI/UX, focusing on a simple yet powerful interface that enables sophisticated agent behaviors while maintaining a clean user experience.

## Core UI Structure

Implementation Files:
- frontend/src/lib/components/Layout.svelte - Main layout structure
- frontend/src/lib/components/Navigation.svelte - Navigation panel
- frontend/src/lib/components/Chat.svelte - Chat interface
- frontend/src/lib/components/TaskBoard.svelte - Task management
- frontend/src/lib/components/GraphPanel.svelte - Graph visualization

### 1. Access Levels (frontend/src/lib/types/workspace.ts)
```typescript
// Two main workspaces
type Workspace = 'professional' | 'personal';

// Domain context in header
interface DomainContext {
    workspace: Workspace;
    domain: string;  // Current conversation/task domain
}
```

### 2. Main Interface (frontend/src/lib/components/Layout.svelte)
```typescript
// Left Panel
- Ask Nova (Primary interaction point)
- Channels:
  * #NovaTeam (Debug: Core specialized agents)
  * #NovaSupport (Debug: Supporting agents)
  * Spawned agent team channels

// Knowledge Tab
- DAG View: Task dependencies and chains
- Agents View: Spawned agent overview
- Knowledge View: Nova's learnings

// Tasks Tab
- Kanban board with state transitions
- Support for human-in-loop pausing
- Focus on autonomous progression
```

## Agent Integration

Implementation Files:
- src/nia/nova/core/nova_endpoints.py - Core Nova API endpoints
- src/nia/nova/core/dependencies.py - Agent dependencies
- src/nia/nova/orchestrator.py - Agent orchestration
- src/nia/agents/specialized/coordination_agent.py - Agent coordination

### 1. Nova Interaction (src/nia/nova/core/nova_endpoints.py)
```typescript
// Ask Nova endpoint
POST /api/nova/ask
{
    content: string;           // User's message
    workspace: Workspace;      // Current workspace
    domain?: string;          // Optional domain context
}

// Nova processes through:
1. Task Detection & Analysis
2. Agent Team Assembly
3. Knowledge Integration
4. Response Generation
```

### 2. Agent Teams (src/nia/agents/specialized/team_agent.py)

Agents in the system are divided into three categories:

1. Core Agents (#NovaTeam):
- Permanent specialized agents
- Handle core cognitive functions
- Always available in the system

2. Supporting Agents (#NovaSupport):
- Permanent utility agents
- Handle system operations
- Always available in the system

3. Spawned Agents:
- Ephemeral task-specific agents
- Created dynamically as needed
- Exist only for duration of task
- UI for management not yet developed

```typescript
// Team spawning based on task needs (src/nia/agents/models/team.py)
interface AgentTeam {
    id: string;
    task_id: string;
    agents: Array<{
        id: string;
        role: string;
        skills: string[];
        type: 'core' | 'support' | 'spawned';
    }>;
    channel_id: string;  // For team communication
}

// Direct agent messaging (src/nia/agents/models/message.py)
interface AgentMessage {
    agent_id: string;
    content: string;
    context: {
        task_id?: string;
        thread_id: string;
    };
}

// Note: UI for managing spawned agents (configuration,
// monitoring, etc.) is still under development
```

### 3. Task Management (src/nia/agents/specialized/task_agent.py)

Tasks can be created in two ways:

1. Conversational Creation:
- Tasks emerge naturally through conversation with Nova
- Nova identifies task opportunities through discussion
- Natural brainstorming to clarify scope
- More flexible and context-aware approach

2. Manual Creation (UI under development):
- Tasks can be manually created in the task tab
- UI for specifying dependencies, blockages, and agent assignments not yet implemented
- Required parameters from API spec:
  ```typescript
  // src/nia/agents/models/task.py
  interface TaskNode {
      id: string;
      label: string;
      type: string;
      status: TaskState;
      description?: string;
      team_id?: string;
      domain?: string;
      priority?: 'high' | 'medium' | 'low';
      assignee?: string;
      dependencies?: string[];
      blocked_by?: string[];
      metadata: Record<string, any>;
  }
  ```

```typescript
// Task States (src/nia/agents/models/task_states.py)
type TaskState = 
    | 'pending'       // Initial state after detection
    | 'in_progress'   // Active work
    | 'blocked'       // Waiting on dependencies
    | 'completed';    // Task finished

// Task Creation Flow
1. Conversational Detection:
   - User discusses potential work with Nova
   - Nova identifies task opportunities
   - Natural brainstorming to clarify scope

2. Team Assembly:
   - Nova analyzes task requirements
   - Spawns specialized agents as needed
   - Creates team channel for collaboration

3. Task Management (POST /api/tasks):
   ```typescript
   // src/nia/agents/models/task.py
   interface TaskNode {
       id: string;
       label: string;
       type: string;
       status: TaskState;
       description?: string;
       team_id?: string;
       domain?: string;
       priority?: 'high' | 'medium' | 'low';
       assignee?: string;
       dependencies?: string[];
       blocked_by?: string[];
       metadata: Record<string, any>;
   }
   ```

4. Task Updates (POST /api/tasks/{task_id}/transition):
   - State transitions with validation
   - Dependency management
   - Progress tracking
   - Human intervention when needed
```

### 4. Knowledge System (src/nia/memory/knowledge_system.py)
```typescript
// Two-layer storage
interface KnowledgeSystem {
    ephemeral: {
        // Session-based storage
        conversations: Map<string, any>;
        task_context: Map<string, any>;
        agent_state: Map<string, any>;
    };
    permanent: {
        // Long-term storage
        taxonomies: Map<string, any>;
        ontologies: Map<string, any>;
        learned_skills: Map<string, any>;
        failure_patterns: Map<string, any>;
    };
}
```

## System Integration

### 1. FastAPI Integration (src/nia/nova/core/nova_endpoints.py)

The agents integrate with FastAPI through endpoints in nova_endpoints.py:

```python
@nova_router.post("/ask", response_model=NovaResponse)
async def ask_nova(
    request: NovaRequest,
    memory_system: Any = Depends(get_memory_system),
    # Core cognitive agents
    belief_agent: Any = Depends(get_belief_agent),
    desire_agent: Any = Depends(get_desire_agent),
    emotion_agent: Any = Depends(get_emotion_agent),
    # ... other agents
):
    """Ask Nova a question through its complete cognitive architecture."""
    try:
        # 1. Initial Processing
        schema_result = await schema_agent.validate_schema(...)
        parsed_input = await parsing_agent.parse_text(...)
        
        # 2. Context & Memory
        context = await context_agent.get_context(...)
        memory_context = await memory_agent.retrieve_relevant_memories(...)
        
        # 3. Core Cognitive Processing
        belief_response = await belief_agent.analyze_beliefs(...)
        desire_response = await desire_agent.analyze_desires(...)
        emotion_response = await emotion_agent.analyze_emotion(...)
        
        # 4. Integration & Response
        integrated_response = await integration_agent.integrate(...)
        final_response = await synthesis_agent.synthesize(...)
        
        return NovaResponse(
            threadId="nova",
            message=message.dict()
        )
    except Exception as e:
        raise ServiceError(str(e))
```

### 2. Redis Integration (src/nia/core/redis_client.py)

Redis is used for:

1. WebSocket Pub/Sub:
```python
# Redis pub/sub for real-time updates
redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB
)

async def publish_update(channel: str, message: dict):
    """Publish update to Redis channel."""
    await redis_client.publish(
        channel,
        json.dumps(message)
    )
```

2. Caching:
```python
# Cache agent responses
@cache(ttl=300)  # 5 minute cache
async def get_agent_response(
    agent_id: str,
    query: str
) -> Dict:
    return await agent_store.get_response(
        agent_id,
        query
    )
```

3. Task Queue with Celery:
```python
# Background tasks via Celery
celery_app = Celery(
    'nova',
    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0'
)

@celery_app.task
def consolidate_memories():
    """Background task to consolidate memories."""
    memory_system.consolidate()
```

### 3. WebSocket Integration (frontend/src/lib/websocket/client.ts)

Real-time updates are handled through WebSocket connections:

1. Connection Types:
```typescript
// websocket/client.ts
class WebSocketClient {
    private connections: Map<string, WebSocket>;
    
    async connect(endpoint: string) {
        const ws = new WebSocket(endpoint);
        this.connections.set(endpoint, ws);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch(data.type) {
                case 'agent_status':
                    this.handleAgentStatus(data);
                    break;
                case 'task_update':
                    this.handleTaskUpdate(data);
                    break;
                case 'message':
                    this.handleMessage(data);
                    break;
            }
        };
    }
}
```

2. Message Types:
```typescript
interface WebSocketMessage {
    type: 'agent_status' | 'task_update' | 'message';
    timestamp: string;
    payload: unknown;
    metadata?: {
        domain?: string;
        importance?: number;
    };
}
```

### 4. Pydantic Models (src/nia/nova/models.py)

Data validation using Pydantic models:

```python
class NovaRequest(BaseModel):
    """Request model for Nova's ask endpoint."""
    content: str
    workspace: str = Field(
        default="personal",
        pattern="^(personal|professional)$"
    )
    debug_flags: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Debug flags for validation"
    )

class NovaResponse(BaseModel):
    """Response model for Nova's ask endpoint."""
    threadId: str
    message: Dict[str, Any]

class Message(BaseModel):
    """Chat message model."""
    id: str
    content: str
    sender_type: str
    sender_id: str
    timestamp: str
    metadata: Optional[Dict[str, Any]]
```

### 5. Zod Schema (frontend/src/lib/validation/schemas.ts)

Frontend validation using Zod:

```typescript
// validation/websocket-schemas.ts
const messageSchema = z.object({
    type: z.enum(['message', 'status', 'error']),
    timestamp: z.string().datetime(),
    payload: z.unknown(),
    metadata: z.object({
        domain: z.string().optional(),
        importance: z.number().optional(),
        agent_actions: z.array(agentActionSchema).optional(),
        cognitive_state: z.record(z.unknown()).optional(),
        task_context: z.record(z.unknown()).optional(),
        debug_info: z.record(z.unknown()).optional()
    }).optional()
});

// validation/agent-schemas.ts
const agentActionSchema = z.object({
    agent_id: z.string(),
    action_type: z.string(),
    timestamp: z.string().datetime(),
    details: z.record(z.unknown()),
    result: z.record(z.unknown()).optional()
});

const threadSchema = z.object({
    id: z.string(),
    title: z.string(),
    domain: z.string().default('general'),
    status: z.string().default('active'),
    created_at: z.string().datetime(),
    updated_at: z.string().datetime(),
    workspace: z.string().default('personal'),
    participants: z.array(threadParticipantSchema),
    metadata: z.object({
        agent_summary: z.object({
            active_agents: z.array(z.string()),
            task_type: z.string(),
            workspace: z.string()
        }),
        agent_context: z.object({
            task_detection: z.record(z.unknown()).optional(),
            plan: z.record(z.unknown()).optional()
        })
    }),
    validation: threadValidationSchema
});

const threadParticipantSchema = z.object({
    id: z.string(),
    type: z.enum(['user', 'agent']),
    role: z.string(),
    joined_at: z.string().datetime(),
    metadata: z.record(z.unknown()).optional()
});

const threadValidationSchema = z.object({
    is_valid: z.boolean(),
    issues: z.array(z.object({
        type: z.string(),
        severity: z.enum(['low', 'medium', 'high']),
        message: z.string()
    })).optional()
});

// validation/form-schemas.ts
const taskSchema = z.object({
    title: z.string().min(1),
    description: z.string(),
    status: z.enum(['pending', 'in_progress', 'completed']),
    assignee: z.string().optional(),
    due_date: z.string().datetime().optional()
});

// validation/debug-schemas.ts
const agentMetricsSchema = z.object({
    actionCount: z.number(),
    successRate: z.number(),
    avgResponseTime: z.number(),
    errorRate: z.number().optional(),
    lastUpdate: z.string().datetime()
});

const agentActivitySchema = z.object({
    timestamp: z.string().datetime(),
    agent_id: z.string(),
    action_type: z.string(),
    result: z.object({
        success: z.boolean(),
        error: z.string().optional(),
        duration: z.number().optional()
    }).optional()
});

const debugMessageSchema = z.object({
    type: z.enum(['validation', 'websocket', 'storage', 'error']),
    timestamp: z.string().datetime(),
    data: z.record(z.unknown()),
    level: z.enum(['info', 'warn', 'error']).optional()
});

// validation/debug-schemas.ts
const validationErrorSchema = z.object({
    type: z.literal('validation_error'),
    field: z.string(),
    message: z.string(),
    value: z.unknown(),
    constraints: z.array(z.string()).optional()
});

const validationResultSchema = z.object({
    success: z.boolean(),
    errors: z.array(validationErrorSchema).optional(),
    warnings: z.array(validationErrorSchema).optional(),
    metadata: z.object({
        duration: z.number(),
        schema_version: z.string()
    }).optional()
});

const webSocketErrorSchema = z.object({
    type: z.literal('websocket_error'),
    code: z.number(),
    message: z.string(),
    timestamp: z.string().datetime(),
    reconnect_attempt: z.number().optional()
});

const debugStateSchema = z.object({
    flags: z.object({
        log_validation: z.boolean(),
        log_websocket: z.boolean(),
        log_storage: z.boolean(),
        strict_mode: z.boolean()
    }),
    active_subscriptions: z.array(z.string()),
    message_queue: z.array(z.unknown()),
    error_count: z.record(z.number())
});

const debugEventSchema = z.discriminatedUnion('type', [
    z.object({
        type: z.literal('validation'),
        result: validationResultSchema
    }),
    z.object({
        type: z.literal('websocket'),
        event: webSocketErrorSchema
    }),
    z.object({
        type: z.literal('storage'),
        operation: z.string(),
        duration: z.number(),
        success: z.boolean()
    }),
    z.object({
        type: z.literal('error'),
        error: z.unknown(),
        context: z.record(z.unknown())
    })
]);
```

## UI Components

### 1. Navigation (frontend/src/lib/components/Navigation.svelte)

```svelte
<script lang="ts">
    import { appStore } from '$lib/stores';
    import type { Channel, Agent } from '$lib/types';
    
    // WebSocket connection for real-time updates
    const ws = new WebSocket('ws://localhost:8000/api/ws/agents/client123');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'agent_status') {
            updateAgentStatus(data);
        }
    };
</script>

<nav>
    <!-- NOVA HQ Channel -->
    <div class="channel nova-hq">
        <span class="status {$appStore.novaStatus}"></span>
        NOVA HQ
    </div>
    
    <!-- Agent Channels -->
    {#each $appStore.agents as agent}
        <div class="channel agent">
            <span class="status {agent.status}"></span>
            {agent.name}
        </div>
    {/each}
</nav>
```

### 2. Chat Interface (frontend/src/lib/components/Chat.svelte)

```svelte
<script lang="ts">
    import { messageStore } from '$lib/stores';
    import type { Message, AgentAction } from '$lib/types';
    
    // WebSocket for real-time messages and agent actions
    const ws = new WebSocket('ws://localhost:8000/api/ws/chat/client123');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'message') {
            messageStore.addMessage(data.payload);
        } else if (data.type === 'agent_action') {
            messageStore.addAgentAction(data.payload);
        }
    };

    // Track agent activities in UI
    function renderAgentActions(actions: AgentAction[]) {
        return actions.map(action => ({
            id: action.agent_id,
            type: action.action_type,
            time: action.timestamp,
            details: action.details,
            result: action.result
        }));
    }
    
    // Send message to Nova
    async function sendMessage(content: string) {
        const response = await fetch('/api/nova/ask', {
            method: 'POST',
            body: JSON.stringify({
                content,
                workspace: 'personal'
            })
        });
        const data = await response.json();
        messageStore.addMessage(data.message);
    }
</script>

<div class="chat">
    <!-- Message Thread with Agent Actions -->
    {#each $messageStore.messages as message}
        <div class="message {message.sender_type}">
            <div class="content">{message.content}</div>
            
            <!-- Agent Activity Tracking -->
            {#if message.metadata?.agent_actions?.length}
                <div class="agent-actions">
                    <h4>Agent Activities:</h4>
                    {#each renderAgentActions(message.metadata.agent_actions) as action}
                        <div class="agent-action">
                            <span class="agent">{action.id}</span>
                            <span class="type">{action.type}</span>
                            <span class="time">{action.time}</span>
                            {#if action.result}
                                <div class="result">
                                    Result: {JSON.stringify(action.result)}
                                </div>
                            {/if}
                        </div>
                    {/each}
                </div>
            {/if}

            <!-- Cognitive State -->
            {#if message.metadata?.cognitive_state}
                <div class="cognitive-state">
                    <h4>Cognitive State:</h4>
                    <pre>{JSON.stringify(message.metadata.cognitive_state, null, 2)}</pre>
                </div>
            {/if}

            <!-- Task Context -->
            {#if message.metadata?.task_context}
                <div class="task-context">
                    <h4>Task Context:</h4>
                    <pre>{JSON.stringify(message.metadata.task_context, null, 2)}</pre>
                </div>
            {/if}
        </div>
    {/each}
    
    <!-- Input Area -->
    <div class="input-area">
        <input bind:value={messageText} />
        <button on:click={() => sendMessage(messageText)}>Send</button>
    </div>

    <!-- Debug Panel for Agent Activities -->
    {#if debugFlags.showAgentPanel}
        <div class="agent-debug-panel">
            <h3>Active Agents</h3>
            <div class="agent-list">
                {#each activeAgents as agent}
                    <div class="agent-item">
                        <span class="name">{agent.id}</span>
                        <span class="status {agent.status}"></span>
                        <div class="metrics">
                            <div>Actions: {agent.actionCount}</div>
                            <div>Success Rate: {agent.successRate}%</div>
                            <div>Response Time: {agent.avgResponseTime}ms</div>
                        </div>
                    </div>
                {/each}
            </div>

            <h3>Recent Activities</h3>
            <div class="activity-timeline">
                {#each recentActivities as activity}
                    <div class="activity-item">
                        <span class="time">{formatTime(activity.timestamp)}</span>
                        <span class="agent">{activity.agent_id}</span>
                        <span class="action">{activity.action_type}</span>
                        {#if activity.result?.success}
                            <span class="success">✓</span>
                        {:else if activity.result?.error}
                            <span class="error">✗</span>
                        {/if}
                    </div>
                {/each}
            </div>

            <h3>Performance Metrics</h3>
            <div class="metrics-panel">
                <div class="metric">
                    <label>Average Response Time</label>
                    <div class="value">{avgResponseTime}ms</div>
                </div>
                <div class="metric">
                    <label>Success Rate</label>
                    <div class="value">{successRate}%</div>
                </div>
                <div class="metric">
                    <label>Active Agents</label>
                    <div class="value">{activeAgentCount}</div>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .agent-debug-panel {
        position: fixed;
        right: 0;
        top: 0;
        width: 300px;
        height: 100vh;
        background: #1e1e1e;
        color: #fff;
        padding: 1rem;
        overflow-y: auto;
    }

    .agent-item {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        border-bottom: 1px solid #333;
    }

    .agent-item .status {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin: 0 0.5rem;
    }

    .status.active { background: #4caf50; }
    .status.busy { background: #ff9800; }
    .status.error { background: #f44336; }

    .activity-timeline {
        margin: 1rem 0;
    }

    .activity-item {
        display: flex;
        align-items: center;
        padding: 0.25rem;
        font-size: 0.9rem;
    }

    .activity-item .time {
        color: #888;
        margin-right: 0.5rem;
    }

    .activity-item .success { color: #4caf50; }
    .activity-item .error { color: #f44336; }

    .metrics-panel {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin-top: 1rem;
    }

    .metric {
        background: #333;
        padding: 0.5rem;
        border-radius: 4px;
    }

    .metric label {
        font-size: 0.8rem;
        color: #888;
    }

    .metric .value {
        font-size: 1.2rem;
        font-weight: bold;
    }
</style>
```

### 3. Task Management (frontend/src/lib/components/TaskBoard.svelte)

```svelte
<script lang="ts">
    import { taskStore } from '$lib/stores';
    import type { Task } from '$lib/types';
    
    // WebSocket for real-time task updates
    const ws = new WebSocket('ws://localhost:8000/api/ws/tasks/client123');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'task_update') {
            taskStore.updateTask(data.payload);
        }
    };
    
    // Task validation schema
    const taskSchema = z.object({
        title: z.string().min(1),
        status: z.enum(['pending', 'in_progress', 'completed'])
    });
</script>

<div class="board">
    <!-- Task Columns -->
    {#each ['pending', 'in_progress', 'completed'] as status}
        <div class="column">
            <h3>{status}</h3>
            {#each $taskStore.getTasks(status) as task}
                <div class="task">
                    <h4>{task.title}</h4>
                    <p>{task.description}</p>
                </div>
            {/each}
        </div>
    {/each}
</div>
```

### 4. Graph Visualization (frontend/src/lib/components/GraphPanel.svelte)

```svelte
<script lang="ts">
    import { graphStore } from '$lib/stores';
    import type { Node, Edge } from '$lib/types';
    
    // WebSocket for real-time graph updates
    const ws = new WebSocket('ws://localhost:8000/api/ws/graph/client123');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'graph_update') {
            graphStore.updateGraph(data.payload);
        }
    };
</script>

<div class="graph">
    <!-- Node Visualization -->
    {#each $graphStore.nodes as node}
        <div class="node {node.type}"
             style="left: {node.x}px; top: {node.y}px">
            {node.label}
        </div>
    {/each}
    
    <!-- Edge Visualization -->
    {#each $graphStore.edges as edge}
        <svg class="edge">
            <line x1={edge.source.x}
                  y1={edge.source.y}
                  x2={edge.target.x}
                  y2={edge.target.y} />
        </svg>
    {/each}
</div>
```

## State Management

### 1. Centralized Store (frontend/src/lib/stores/app.ts)
```typescript
// stores/app.ts - Single source of truth
export const appStore = {
    // Shared state
    workspace: writable(null),
    domain: writable(null),
    activeFilters: writable([]),
    
    // Single WebSocket connection
    socket: createWebSocket(),
    
    // Shared handlers
    handlers: {
        onTaskUpdate,
        onAgentUpdate,
        onThreadUpdate
    }
};

// Usage in components
<script>
    import { appStore } from '$lib/stores';
    $: ({ workspace, domain } = $appStore);
</script>
```

### 2. WebSocket Store (frontend/src/lib/stores/websocket.ts)
```typescript
// stores/websocket.ts
interface WebSocketState {
    // Service Status
    services: {
        redis: ServiceStatus;
        celery: ServiceStatus;
        neo4j: ServiceStatus;
        qdrant: ServiceStatus;
    };
    
    // Memory System
    memory: {
        consolidation_status: 'idle' | 'running';
        last_consolidation: string;
        pending_operations: number;
    };
    
    // Workspace
    workspace: {
        current: 'personal' | 'professional';
        domains: string[];
        thresholds: Record<string, number>;
    };
}

const wsStore = writable<WebSocketState>({
    services: {
        redis: { status: 'inactive' },
        celery: { status: 'inactive' },
        neo4j: { status: 'inactive' },
        qdrant: { status: 'inactive' }
    },
    memory: {
        consolidation_status: 'idle',
        last_consolidation: '',
        pending_operations: 0
    },
    workspace: {
        current: 'personal',
        domains: [],
        thresholds: {}
    }
});
```

## Error Handling

### 1. Frontend Validation (frontend/src/lib/validation/error-handler.ts)
```typescript
// validation/error-handler.ts
class WebSocketErrorHandler {
    handle(error: Error) {
        if (error instanceof ValidationError) {
            // Schema validation failed
            this.handleValidationError(error);
        } else if (error instanceof ConnectionError) {
            // Connection issues
            this.handleConnectionError(error);
        } else {
            // Unknown error
            this.logError(error);
        }
    }
}
```

### 2. Backend Validation (src/nia/core/error_handling.py)
```python
# error_handling.py
class ServiceError(Exception):
    """Base error for service operations."""
    pass

@nova_router.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )
```

## Debug Integration

### 1. Feature Flags (src/nia/core/feature_flags.py)
```python
# src/nia/core/feature_flags.py
class FeatureFlags:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "debug:"
        
    async def enable_debug(self, flag_name: str):
        """Enable debug flag."""
        key = f"{self.prefix}{flag_name}"
        await self.redis.set(key, "true")
        
    async def is_debug_enabled(self, flag_name: str) -> bool:
        """Check if debug flag is enabled."""
        key = f"{self.prefix}{flag_name}"
        return await self.redis.get(key) == b"true"

# Debug flags
DEBUG_FLAGS = {
    'log_validation': 'debug:log_validation',     # Log all validation attempts
    'log_websocket': 'debug:log_websocket',       # Log WebSocket messages
    'log_storage': 'debug:log_storage',           # Log storage operations
    'strict_mode': 'debug:strict_mode'            # Throw on any validation error
}
```

### 2. Debug UI Panel (frontend/src/lib/components/DebugPanel.svelte)
```svelte
<!-- frontend/src/lib/components/DebugPanel.svelte -->
<script lang="ts">
    import { debugFlags } from '../validation/debug';
    import { webSocket } from '../websocket/client';
    
    let messages: any[] = [];
    
    $: {
        if (debugFlags.logValidation) {
            // Subscribe to validation logs
            webSocket.on('validation', (data) => {
                messages = [...messages, {
                    type: 'validation',
                    ...data,
                    timestamp: new Date().toISOString()
                }];
            });
        }
        
        if (debugFlags.logWebSocket) {
            // Subscribe to WebSocket logs
            webSocket.on('websocket', (data) => {
                messages = [...messages, {
                    type: 'websocket',
                    ...data,
                    timestamp: new Date().toISOString()
                }];
            });
        }
    }
</script>

<div class="debug-panel">
    <div class="controls">
        <label>
            <input type="checkbox" bind:checked={debugFlags.logValidation}>
            Log Validation
        </label>
        <label>
            <input type="checkbox" bind:checked={debugFlags.logWebSocket}>
            Log WebSocket
        </label>
        <label>
            <input type="checkbox" bind:checked={debugFlags.strictMode}>
            Strict Mode
        </label>
    </div>
    
    <div class="logs">
        {#each messages as msg}
            <div class="log-entry">
                <span class="timestamp">{msg.timestamp}</span>
                <span class="type">{msg.type}</span>
                <pre class="data">{JSON.stringify(msg.data, null, 2)}</pre>
            </div>
        {/each}
    </div>
</div>
```

### 3. Enhanced WebSocket Debugging (frontend/src/lib/websocket/client.ts)
```typescript
// websocket/client.ts
export class WebSocketClient {
    constructor(private debugFlags = debugFlags) {
        this.ws = new WebSocket('ws://localhost:8000/ws');
        this.setupDebugHandlers();
    }
    
    private setupDebugHandlers() {
        // Handle debug messages
        this.ws.addEventListener('message', (event) => {
            if (this.debugFlags.logWebSocket) {
                console.log('WS Received:', event.data);
            }
            
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'debug_update') {
                    this.handleDebugUpdate(data);
                }
            } catch (error) {
                if (this.debugFlags.logWebSocket) {
                    console.error('WS Parse error:', error);
                }
            }
        });
    }
    
    async send(message: unknown) {
        if (this.debugFlags.logWebSocket) {
            console.log('WS Sending:', message);
        }
        
        try {
            const validated = validateMessage(message);
            if (!validated && this.debugFlags.strictMode) {
                throw new Error('Message validation failed');
            }
            
            await this.ws.send(JSON.stringify(validated));
            
        } catch (error) {
            if (this.debugFlags.logWebSocket) {
                console.error('WS Send error:', error);
            }
            throw error;
        }
    }
}
```

### 4. Enhanced Validation Debugging (frontend/src/lib/validation/messages.ts)
```typescript
// validation/messages.ts
export const validateMessage = (data: unknown) => {
    if (debugFlags.logValidation) {
        console.log('Validating message:', data);
    }
    
    try {
        const result = messageSchema.parse(data);
        
        if (debugFlags.logValidation) {
            console.log('Validation successful:', result);
        }
        
        return result;
    } catch (error) {
        if (debugFlags.logValidation) {
            console.error('Validation failed:', error);
        }
        
        if (debugFlags.strictMode) {
