# API Schema Documentation

## Memory System (/api/memory)

### Endpoints

#### Store Memory
```http
POST /store
```

Store content in the memory system. This endpoint implements our two-layer memory architecture:

Frontend:
- Called by Chat.svelte when storing messages
- Called by TaskBoard.svelte when updating tasks
- Called by GraphPanel.svelte when updating relationships

Storage Flow:
1. Qdrant (Episodic Layer):
   - Stores raw content with embeddings
   - Handles short-term memory cleanup
   - Manages retention periods
   - Prevents recursion via direct storage pattern

2. Neo4j (Semantic Layer):
   - Stores consolidated knowledge
   - Manages domain boundaries
   - Handles relationship persistence
   - Tracks version history

3. DAG:
   - Manages memory dependencies
   - Prevents circular references
   - Handles consolidation triggers
   - Tracks operation order

**Request Body:**
```typescript
{
    content: any;           // Required: Content to store
    type: string;          // Required: Memory type
    importance?: number;    // Optional: Memory importance (default: 0.5)
    context?: {            // Optional: Additional context
        domain?: string;   // Optional: Memory domain
        [key: string]: any;
    };
}
```

**Query Parameters:**
- `domain` (optional): Override domain

**Response:**
```typescript
{
    memory_id: string;     // Generated memory UUID
    status: "stored";      // Operation status
    type: string;          // Memory type
    timestamp: string;     // ISO timestamp
}
```

#### Search Memory
```http
GET /search
```

Search memory with domain filtering. This endpoint integrates our semantic search capabilities:

Frontend:
- Used by Chat.svelte for message history search
- Used by TaskBoard.svelte for task context search
- Used by GraphPanel.svelte for relationship search

Storage Flow:
1. Qdrant:
   - Performs semantic similarity search
   - Filters by domain embeddings
   - Returns ranked results
   - Handles memory type filtering

2. Neo4j:
   - Validates domain access
   - Enriches results with relationships
   - Applies domain boundary rules
   - Tracks search patterns

3. Memory System:
   - Handles result consolidation
   - Manages access validation
   - Tracks search history
   - Updates relevance scores

**Query Parameters:**
- `query` (required): Search query string
- `domain` (optional): Filter by domain
- `memory_type` (optional): Filter by memory type
- `limit` (optional): Maximum results to return (default: 10)

**Response:**
```typescript
{
    query: string;         // Original search query
    matches: Array<{       // Search results
        content: any;      // Memory content
        type: string;      // Memory type
        metadata: {        // Memory metadata
            [key: string]: any;
        };
    }>;
    total: number;         // Total matches found
    timestamp: string;     // ISO timestamp
}
```

#### Cross-Domain Operation
```http
POST /cross-domain
```

Request cross-domain memory operation. This endpoint implements our domain boundary system:

Frontend:
- Called by Chat.svelte when messages cross domains
- Called by TaskBoard.svelte for cross-domain task updates
- Called by GraphPanel.svelte for relationship validation

Storage Flow:
1. Neo4j:
   - Validates domain boundaries
   - Tracks access patterns
   - Manages relationship permissions
   - Records transfer history

2. Qdrant:
   - Stores cross-domain request context
   - Tracks request patterns
   - Maintains access history
   - Updates embeddings for both domains

3. DAG:
   - Validates operation dependencies
   - Prevents circular access patterns
   - Manages approval workflows
   - Tracks operation sequences

**Request Body:**
```typescript
{
    from_domain: string;   // Required: Source domain
    to_domain: string;     // Required: Target domain
    operation: string;     // Required: Operation to perform
}
```

**Response:**
```typescript
{
    operation_id: string;  // Generated operation UUID
    status: "pending_approval";
    from_domain: string;   // Source domain
    to_domain: string;     // Target domain
    operation: string;     // Operation type
    timestamp: string;     // ISO timestamp
}
```

#### Consolidate Memory
```http
GET /consolidate
```

Trigger memory consolidation. This endpoint implements our memory consolidation system:

Frontend:
- Called periodically by background task in Chat.svelte
- Called after batch operations in TaskBoard.svelte
- Called during graph updates in GraphPanel.svelte

Storage Flow:
1. Qdrant:
   - Identifies patterns in episodic memory
   - Groups similar experiences
   - Calculates importance scores
   - Prepares for semantic extraction

2. Neo4j:
   - Creates consolidated knowledge nodes
   - Updates semantic relationships
   - Maintains domain hierarchies
   - Records consolidation history

3. DAG:
   - Manages consolidation order
   - Tracks dependencies between memories
   - Prevents consolidation cycles
   - Validates semantic consistency

**Query Parameters:**
- `domain` (optional): Filter consolidation by domain

**Response:**
```typescript
{
    consolidated_count: number;  // Number of memories consolidated
    pruned_count: number;       // Number of memories pruned
    timestamp: string;          // ISO timestamp
}
```

#### Prune Memory
```http
DELETE /prune
```

Prune knowledge graph. This endpoint implements our memory cleanup system:

Frontend:
- Called by background task in Chat.svelte after consolidation
- Called by TaskBoard.svelte during state transitions
- Called by GraphPanel.svelte during graph cleanup

Storage Flow:
1. Qdrant:
   - Removes outdated embeddings
   - Cleans up unused vectors
   - Archives important memories
   - Updates importance scores

2. Neo4j:
   - Removes redundant nodes
   - Cleans up stale relationships
   - Preserves critical paths
   - Updates domain hierarchies

3. DAG:
   - Validates deletion safety
   - Preserves required dependencies
   - Updates operation history
   - Maintains consistency

**Query Parameters:**
- `domain` (optional): Filter pruning by domain

**Response:**
```typescript
{
    pruned_nodes: number;       // Number of nodes pruned
    pruned_relationships: number; // Number of relationships pruned
    timestamp: string;          // ISO timestamp
}
```

### Core Types

#### Memory Types
```typescript
enum MemoryType {
  TASK_CREATE = "task_create",
  TASK_UPDATE = "task_update",
  AGENT_INTERACTION = "agent_interaction",
  CROSS_DOMAIN_REQUEST = "cross_domain_request",
  THREAD_MESSAGE = "thread_message",
  CONSOLIDATION_EVENT = "consolidation_event"
}
```

### Memory Models
```typescript
interface Memory {
  id?: string;
  content: string | Record<string, any>;
  type: MemoryType;
  importance: number;  // 0-1
  timestamp: string;   // ISO date
  context: Record<string, any>;
  consolidated: boolean;
  domain_context?: DomainContext;
  sync_state: {
    vector_stored: boolean;
    neo4j_stored: boolean;
    last_sync: string | null;
  };
}

interface DomainContext {
  primary_domain: string;
  knowledge_vertical?: string;
  cross_domain?: DomainTransfer;
  confidence: number;  // 0-1
  validation: ValidationSchema;
  access_control: {
    read: string[];
    write: string[];
    execute: string[];
  };
}

interface DomainTransfer {
  requested: boolean;
  approved: boolean;
  justification: string;
  source_domain?: string;
  target_domain?: string;
  source_vertical?: string;
  target_vertical?: string;
  approval_timestamp?: string;  // ISO date
  approval_source?: string;
}

interface ValidationSchema {
  domain: string;
  access_domain: string;
  confidence: number;  // 0-1
  source: string;
  timestamp: string;  // ISO date
  supported_by: string[];
  contradicted_by: string[];
  needs_verification: string[];
  cross_domain: CrossDomainSchema;
}

interface CrossDomainSchema {
  approved: boolean;
  requested: boolean;
  source_domain: string;
  target_domain: string;
  justification: string;
  approval_timestamp: string;  // ISO date
  approval_source: string;
}
```

## Task System

### Task Models
```typescript
interface TaskNode {
  id: string;
  label: string;
  type?: string;              // default: "task"
  status?: TaskState;         // default: "pending"
  description?: string;
  team_id?: string;
  domain?: string;
  created_at?: string;        // ISO date
  updated_at?: string;        // ISO date
  metadata?: Record<string, any>;
  title?: string;
  priority?: TaskPriority;
  assignee?: string;
  dueDate?: string;          // ISO date
  tags?: string[];
  time_active?: number;
  dependencies?: string[];
  blocked_by?: string[];
  sub_tasks?: SubTask[];
  completed?: boolean;
}

enum TaskState {
  PENDING = "pending",
  IN_PROGRESS = "in_progress",
  BLOCKED = "blocked",
  COMPLETED = "completed"
}

enum TaskPriority {
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low"
}

interface SubTask {
  id: string;
  description: string;
  completed?: boolean;    // default: false
  created_at?: string;    // ISO date
}

interface TaskEdge {
  source: string;         // Source task ID
  target: string;        // Target task ID
  type: "blocks" | "depends_on" | "related_to";
  metadata?: Record<string, any>;
}

interface TaskUpdate {
  taskId: string;
  status?: TaskState;
  priority?: TaskPriority;
  assignees?: string[];
  metadata?: Record<string, any>;
}
```

## Chat System

### Thread Models
```typescript
interface Thread {
  id: string;
  title: string;
  domain: string;         // default: "general"
  status: string;         // default: "active"
  created_at: string;     // ISO date
  updated_at: string;     // ISO date
  workspace: string;      // default: "personal"
  participants: ThreadParticipant[];
  metadata: Record<string, any>;
  validation: ThreadValidation;
}

interface ThreadParticipant {
  id: string;
  name: string;
  type: "user" | "agent";
  agentType?: string;
  role?: string;
  status?: string;
  workspace: string;      // default: "personal"
  domain?: string;
  threadId?: string;
  metadata?: {
    capabilities?: string[];
    confidence?: number;
    specialization?: string;
  };
}

interface ThreadValidation {
  domain: string;
  access_domain: string;
  confidence: number;     // 0-1
  source: string;
  timestamp: string;      // ISO date
  supported_by: string[];
  contradicted_by: string[];
  needs_verification: string[];
  cross_domain: Record<string, any>;
}
```

### Message Models
```typescript
interface Message {
  id: string;
  content: string;
  thread_id: string;
  sender_type: string;    // "user" | "agent"
  sender_id: string;
  timestamp: string;      // ISO date
  metadata?: Record<string, any>;
}

interface MessageRequest {
  content: string;
  thread_id: string;
  sender_type?: string;   // default: "user"
  sender_id?: string;
  metadata?: Record<string, any>;
}

interface MessageResponse {
  id: string;
  content: string;
  timestamp: string;      // ISO date
}
```

## WebSocket System

### Base Message
```typescript
interface WebSocketMessageBase {
  type: WebSocketEventType;
  timestamp: string;      // ISO date
  metadata?: {
    source?: string;
    domain?: string;
    importance?: number;  // 0-1
  };
}
```

### Chat Messages
```typescript
interface ThreadUpdateMessage extends WebSocketMessageBase {
  type: "thread_update";
  thread_id: string;
  changes: {
    title?: string;
    status?: "active" | "archived" | "deleted";
    metadata?: Record<string, any>;
    participants?: Array<{
      id: string;
      type: "user" | "agent";
      action: "add" | "remove";
    }>;
  };
}

interface ChatMessage extends WebSocketMessageBase {
  type: "message";
  content: string;
  thread_id: string;
  sender_type: string;
  sender_id: string;
}

interface TypingIndicator extends WebSocketMessageBase {
  type: "typing";
  user_id: string;
  thread_id: string;
  is_typing: boolean;
}
```

### Task Messages
```typescript
interface TaskUpdateMessage extends WebSocketMessageBase {
  type: "task_update";
  task_id: string;
  changes: Record<string, any>;
}

interface TaskProgressMessage extends WebSocketMessageBase {
  type: "task_progress";
  task_id: string;
  progress: number;      // 0-1
  status: string;
  message?: string;
}

interface TaskAssignmentMessage extends WebSocketMessageBase {
  type: "task_assignment";
  task_id: string;
  assignee: string;
  previous_assignee?: string;
}
```

### Agent Messages
```typescript
interface AgentStatusMessage extends WebSocketMessageBase {
  type: "agent_status";
  agent_id: string;
  status: string;
  metrics?: {
    response_time?: number;
    tasks_completed?: number;
    success_rate?: number;  // 0-1
    uptime?: number;
  };
}

interface AgentCapabilityMessage extends WebSocketMessageBase {
  type: "agent_capability";
  agent_id: string;
  capabilities: Array<{
    name: string;
    confidence: number;  // 0-1
  }>;
}

interface AgentTeamCreatedMessage extends WebSocketMessageBase {
  type: "agent_team_created";
  data: Array<{
    id: string;
    name: string;
    type: "user" | "agent";
    agentType?: string;
    role?: string;
    workspace: "personal" | "professional";
    domain?: string;
    metadata?: {
      capabilities?: string[];
      confidence?: number;
      specialization?: string;
    };
  }>;
}
```

### Graph Messages
```typescript
interface GraphUpdateMessage extends WebSocketMessageBase {
  type: "graph_update";
  nodes: Array<{
    id: string;
    type: string;
    changes: Record<string, any>;
  }>;
  edges: Array<{
    id: string;
    type: string;
    changes: Record<string, any>;
  }>;
}
```

### Memory Messages
```typescript
interface MemoryUpdateMessage extends WebSocketMessageBase {
  type: "memory_update";
  memory_id: string;
  sync_state: {
    vector_stored: boolean;
    neo4j_stored: boolean;
    last_sync: string | null;  // ISO date
  };
}

interface MemoryConsolidationMessage extends WebSocketMessageBase {
  type: "memory_consolidation";
  memory_id: string;
  consolidated: boolean;
  cleanup_performed: boolean;
  timestamp: string;  // ISO date
}
```

## User Profile System

### Profile Models
```typescript
interface UserProfile {
  id: string;
  psychometrics?: PsychometricQuestionnaire;
  auto_approval?: AutoApprovalSettings;
  created_at: string;     // ISO date
  updated_at: string;     // ISO date
  metadata: Record<string, any>;
}

interface PsychometricQuestionnaire {
  big_five: {
    openness: number;         // 0-1
    conscientiousness: number; // 0-1
    extraversion: number;     // 0-1
    agreeableness: number;    // 0-1
    neuroticism: number;      // 0-1
  };
  learning_style: {
    visual: number;          // 0-1
    auditory: number;        // 0-1
    kinesthetic: number;     // 0-1
  };
  communication: {
    direct: number;          // 0-1
    detailed: number;        // 0-1
    formal: number;          // 0-1
  };
}

interface AutoApprovalSettings {
  auto_approve_domains: string[];
  approval_thresholds: {
    task_creation: number;    // 0-1
    resource_access: number;  // 0-1
    domain_crossing: number;  // 0-1
  };
  restricted_operations: string[];
}
```

## Error Handling

### Error Response
```typescript
interface ErrorResponse {
  detail: Array<{
    loc: (string | number)[];
    msg: string;
    type: string;
  }>;
}
```

## Source Files

- Task Endpoints: src/nia/nova/endpoints/tasks_endpoints.py
- Chat/Thread Endpoints: src/nia/nova/endpoints/thread_endpoints.py
- Agent Endpoints: src/nia/nova/endpoints/agent_endpoints.py
- Nova Endpoints: src/nia/nova/endpoints/nova_endpoints.py
- Graph Endpoints: src/nia/nova/endpoints/graph_endpoints.py
- Knowledge Graph Endpoints: src/nia/nova/endpoints/knowledge_endpoints.py
- Channel Endpoints: src/nia/nova/endpoints/channel_endpoints.py
- User Endpoints: src/nia/nova/endpoints/user_endpoints.py
- WebSocket Endpoints: src/nia/nova/endpoints/websocket_endpoints.py
- Memory Endpoints: src/nia/nova/endpoints/memory_endpoints.py

Additional Implementation Files:
- Base Models: src/nia/nova/core/models.py
- Authentication: src/nia/nova/core/auth.py
- Error Handling: src/nia/nova/core/error_handlers.py
- WebSocket Server: src/nia/nova/core/websocket_server.py
- FastAPI App: src/nia/nova/core/app.py

## Task Graph Operations
Implementation: src/nia/nova/endpoints/tasks_endpoints.py

State Validation Rules (from implementation):
```python
VALID_TRANSITIONS = {
    TaskState.PENDING: [TaskState.IN_PROGRESS],  # Can only start from pending
    TaskState.IN_PROGRESS: [TaskState.BLOCKED, TaskState.COMPLETED],  # Can block or complete from in progress
    TaskState.BLOCKED: [TaskState.IN_PROGRESS],  # Can only resume to in progress from blocked
    TaskState.COMPLETED: []  # No transitions from completed
}
```

Additional Validation:
- Tasks can only be blocked if they have dependencies (checked in validate_state_transition)
- Domain access is validated for all operations (validate_domain_access)
- State transitions are strictly enforced

### GET /api/tasks/graph
Returns the current task graph with nodes and edges.

Storage:
- Neo4j: Used for graph structure and relationships via semantic layer
- Memory: Stores task states and validation context

Response Schema:
```typescript
{
  analytics: {
    nodes: Array<{
      id: string;
      type: 'task';
      label: string;
      status: TaskState;
      metadata: {
        domain: string;
        timestamp: string;
        importance: number;
      }
    }>;
    edges: Array<{
      source: string;
      target: string;
      type: string;
      label: string;
    }>;
  };
  timestamp: string;
}
```

### POST /api/tasks/graph/addNode
Adds a new task node to the graph.

Storage:
- Neo4j: Creates task node and relationships
- Memory: Stores task context and validation state

Request Schema:
```typescript
interface TaskNode {
  id: string;
  label: string;
  type: 'task';
  status?: TaskState;
  description?: string;
  team_id?: string;
  domain?: string;
  metadata?: Record<string, unknown>;
  title?: string;
  priority?: TaskPriority;
  assignee?: string;
  dueDate?: string;
  tags?: string[];
  time_active?: number;
  dependencies?: string[];
  blocked_by?: string[];
  sub_tasks?: SubTask[];
  completed?: boolean;
}
```

Response Schema:
```typescript
{
  success: boolean;
  taskId: string;
}
```

### POST /api/tasks/graph/addDependency
Creates a dependency relationship between tasks.

Storage:
- Neo4j: Creates relationship with validation
- Memory: Stores dependency context

Request Schema:
```typescript
interface TaskEdge {
  source: string;  // Source task ID
  target: string;  // Target task ID
  type: 'blocks' | 'depends_on' | 'related_to';
  metadata?: Record<string, unknown>;
}
```

Response Schema:
```typescript
{
  success: boolean;
  edgeId: string;  // Format: "{source}-{target}"
}
```

Validation:
- Verifies both tasks exist
- Checks domain access permissions
- Prevents circular dependencies
- Validates state transitions for blocking relationships

### POST /api/tasks/graph/updateNode
Updates a task node's metadata and state.

Storage:
- Neo4j: Updates task metadata and relationships
- Memory: Stores update history and validation state

Request Schema:
```typescript
interface TaskUpdate {
  label?: string;
  status?: TaskState;
  description?: string;
  team_id?: string;
  domain?: string;
  metadata?: Record<string, unknown>;
  title?: string;
  priority?: TaskPriority;
  assignee?: string;
  dueDate?: string;
  tags?: string[];
  completed?: boolean;
}
```

Response Schema:
```typescript
{
  success: boolean;
  taskId: string;
}
```

Validation:
- Validates state transitions based on VALID_TRANSITIONS map
- Checks domain access permissions
- Verifies task exists
- Additional validation for BLOCKED state requires dependencies

## Common Types

### TaskState
```typescript
enum TaskState {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  BLOCKED = 'blocked',
  COMPLETED = 'completed'
}
```

### TaskPriority
```typescript
enum TaskPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent'
}
```

### SubTask
```typescript
interface SubTask {
  id: string;
  description: string;
  completed?: boolean;
  created_at?: string;
}
```

## State Transitions

Valid state transitions are enforced by the backend:

```typescript
const VALID_TRANSITIONS = {
  [TaskState.PENDING]: [TaskState.IN_PROGRESS],
  [TaskState.IN_PROGRESS]: [TaskState.BLOCKED, TaskState.COMPLETED],
  [TaskState.BLOCKED]: [TaskState.IN_PROGRESS],
  [TaskState.COMPLETED]: []  // No transitions from completed
};
```

Additional validation rules:
- Tasks can only be blocked if they have dependencies
- State transitions require domain access permission
- Completed tasks cannot transition to any other state

## Storage Patterns

### Neo4j (Semantic Layer)
- Stores task nodes with all metadata
- Manages relationships between tasks
- Handles domain boundaries and access control
- Tracks state transitions and history

Example query for task creation:
```cypher
CREATE (t:Concept {
  name: $id,
  type: 'task',
  description: $label,
  status: $status,
  domain: $domain,
  created_at: datetime(),
  updated_at: datetime(),
  metadata: $metadata
})
```

### Memory System
- Stores task context and validation state
- Tracks domain access patterns
- Manages consolidation of task updates

Example memory storage:
```typescript
Memory {
  content: TaskNode;
  type: MemoryType.TASK_UPDATE;
  metadata: {
    task_id: string;
    type: 'task_update';
    timestamp: string;
  }
}
```

## Error Handling

All endpoints follow consistent error patterns:

### 400 Bad Request
- Invalid state transitions
- Missing required fields
- Schema validation failures

### 403 Forbidden
- Domain access denied
- Invalid state transition attempts
- Insufficient permissions

### 404 Not Found
- Task not found
- Source/target task not found for dependencies

### 500 Internal Server Error
- Storage layer failures
- Validation system errors
- Unexpected errors

Error responses include:
```typescript
{
  detail: string;
  type: string;
  path: string;
}
```

## Chat Operations
Implementation: src/nia/nova/endpoints/thread_endpoints.py

Key Components:
- OrchestrationAgent: Handles task creation and management
- CoordinationAgent: Manages threads and messages
- TwoLayerMemorySystem: Provides semantic and episodic memory storage

Error Handling:
- Retries operations up to 3 times (retry_on_error decorator)
- Validates request formats and required fields
- Domain access validation
- Rate limiting on all endpoints

Storage:
- Semantic Layer (Neo4j): Stores thread relationships and metadata
- Episodic Memory: Stores message content and history
- Memory System: Handles cross-domain validation and access control

### Thread Management

#### POST /api/tasks/propose
Propose a new task for approval.

Request Schema:
```typescript
{
  type: string;
  content: string;
  domain?: string;
}
```

Response Schema:
```typescript
{
  task_id: string;
  status: "pending_approval";
  type: string;
  content: string;
  timestamp: string;
}
```

#### POST /api/tasks/{task_id}/approve
Approve a pending task and trigger execution.

Response Schema:
```typescript
{
  task_id: string;
  thread_id: string;
  status: "approved";
  timestamp: string;
}
```

#### GET /api/threads/graph/projects/{project_id}
Get graph visualization data for a project.

Response Schema:
```typescript
{
  project_id: string;
  nodes: Array<Record<string, unknown>>;
  relationships: Array<{
    type: string;
    source: string;
    target: string;
  }>;
  timestamp: string;
}
```

#### GET /api/threads
Lists all chat threads.

Response Schema:
```typescript
interface ThreadListResponse {
  threads: Array<{
    id: string;
    name: string;
    domain: string;
    messages: Message[];
    createdAt: string;
    updatedAt: string;
    workspace: 'personal' | 'professional';
    participants: ThreadParticipant[];
    metadata: Record<string, unknown>;
  }>;
  total: number;
  timestamp: string;
}
```

#### POST /api/threads/create
Creates a new chat thread.

Request Schema:
```typescript
interface ThreadRequest {
  title: string;
  workspace: 'personal' | 'professional';
  domain?: string;
  participants?: string[];
  metadata?: Record<string, unknown>;
}
```

Response Schema:
```typescript
interface ThreadResponse {
  id: string;
  title: string;
  domain: string;
  status: string;
  created_at: string;
  updated_at: string;
  workspace: string;
  participants: ThreadParticipant[];
  metadata: Record<string, unknown>;
  validation: ThreadValidation;
}
```

### Message Operations

#### GET /api/threads/{thread_id}
Gets thread details and messages with pagination.

Query Parameters:
- start: Starting index for pagination (default: 0)
- limit: Maximum number of messages to return (default: 100)
- domain: Optional domain filter

Response Schema:
```typescript
{
  thread_id: string;
  task_id: string;
  messages: Message[];
  sub_threads: Array<Record<string, unknown>>;
  summary: Record<string, unknown>;
  total_messages: number;
  timestamp: string;
}
```

#### GET /api/threads/{thread_id}/messages
Gets messages from a thread.

Response Schema:
```typescript
Array<{
  id: string;
  content: string;
  thread_id: string;
  sender_type: string;
  sender_id: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}>
```

#### POST /api/threads/{thread_id}/message
Adds a message to a thread.

Request Schema:
```typescript
interface MessageRequest {
  content: string;
  thread_id: string;
  sender_type?: string;
  sender_id?: string;
  metadata?: Record<string, unknown>;
}
```

Response Schema:
```typescript
interface MessageResponse {
  id: string;
  content: string;
  timestamp: string;
}
```

### Agent Integration

#### GET /api/threads/{thread_id}/agents
Gets agents in a thread.

Response Schema:
```typescript
Array<{
  id: string;
  name: string;
  type: string;
  status: string;
  metadata: {
    capabilities: string[];
    confidence: number;
    specialization: string;
  };
}>
```

#### POST /api/threads/{thread_id}/agents
Adds an agent to a thread.

Request Schema:
```typescript
{
  agentType: string;
  workspace?: string;
  domain?: string;
}
```

Response Schema:
```typescript
{
  id: string;
  name: string;
  type: string;
  status: string;
  metadata: Record<string, unknown>;
}
```

## Common Types

### ThreadParticipant
```typescript
interface ThreadParticipant {
  id: string;
  name: string;
  type: 'user' | 'agent';
  agentType?: string;
  role?: string;
  status?: string;
  workspace: 'personal' | 'professional';
  domain?: string;
  threadId?: string;
  metadata?: {
    capabilities?: string[];
    confidence?: number;
    specialization?: string;
  };
}
```

## User Profile Operations

### POST /api/users/questionnaire
Submit psychometric questionnaire.

Request Schema:
```typescript
interface PsychometricQuestionnaire {
  big_five: {
    openness: number;        // 0-1
    conscientiousness: number; // 0-1
    extraversion: number;    // 0-1
    agreeableness: number;   // 0-1
    neuroticism: number;     // 0-1
  };
  learning_style: {
    visual: number;         // 0-1
    auditory: number;       // 0-1
    kinesthetic: number;    // 0-1
  };
  communication: {
    direct: number;         // 0-1
    detailed: number;       // 0-1
    formal: number;         // 0-1
  };
}
```

Response Schema:
```typescript
{
  success: boolean;
  profile_id: string;
  insights: {
    personality: Record<string, unknown>;
    learning: Record<string, unknown>;
    communication: Record<string, unknown>;
  };
}
```

### GET /api/users/profile/{profile_id}
Get user profile.

Response Schema:
```typescript
interface UserProfile {
  id: string;
  psychometrics?: PsychometricQuestionnaire;
  auto_approval?: AutoApprovalSettings;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
}
```

### POST /api/users/profile/{profile_id}/auto-approval
Update auto-approval settings.

Request Schema:
```typescript
interface AutoApprovalSettings {
  auto_approve_domains: string[];
  approval_thresholds: {
    task_creation: number;     // 0-1
    resource_access: number;   // 0-1
    domain_crossing: number;   // 0-1
  };
  restricted_operations: string[];
}
```

### GET /api/users/profile/{profile_id}/adaptations
Get profile-based adaptations.

Response Schema:
```typescript
{
  adaptations: {
    granularity: string;
    communication_style: string;
    visualization_preference: string;
  };
  profile_applied: boolean;
}
```

## Knowledge Graph Operations
Implementation: src/nia/nova/endpoints/knowledge_endpoints.py

This module implements our knowledge graph system that manages domain boundaries and relationships:

Frontend Integration:
- Used by Chat.svelte for domain context
- Used by TaskBoard.svelte for task categorization
- Used by GraphPanel.svelte for visualization

Storage Patterns:
1. Neo4j (Semantic Layer):
   - Stores domain hierarchies
   - Manages concept relationships
   - Handles access control
   - Tracks domain boundaries

2. Qdrant (Episodic Layer):
   - Stores access patterns
   - Tracks request history
   - Maintains embeddings
   - Handles similarity matching

3. DAG:
   - Validates domain transitions
   - Manages operation order
   - Prevents circular dependencies
   - Ensures consistency

Neo4j Queries:
```cypher
// Domain Listing
MATCH (d:Domain)
RETURN d.name as name, d.type as type, d.description as description

// Cross-Domain Relationships
MATCH (d1:Domain)-[r:CROSS_DOMAIN_ACCESS]->(d2:Domain)
RETURN d1.name as source, d2.name as target, r.status as status

// Knowledge Graph Data
MATCH (n)
RETURN n.id as id, n.name as label, labels(n)[0] as type,
       n.category as category, n.domain as domain,
       n.metadata as metadata

// Task-Related Concepts
MATCH (t:Task {id: $task_id})-[r:REFERENCES]->(c:Concept)
RETURN c.id as id, c.name as name, c.type as type,
       r.metadata as metadata, r.timestamp as timestamp
```

### POST /api/kg/crossDomain
Request cross-domain access.

Request Schema:
```typescript
{
  source_domain: string;
  target_domain: string;
  reason?: string;
}
```

Response Schema:
```typescript
{
  success: boolean;
  requestId: string;
  status: 'pending';
}
```

### GET /api/kg/domains
List available knowledge domains.

Response Schema:
```typescript
{
  domains: Array<{
    name: string;
    type: string;
    description: string;
  }>;
  relationships: Array<{
    source: string;
    target: string;
    status: string;
  }>;
  timestamp: string;
}
```

### POST /api/kg/taskReference
Link task to concept.

Request Schema:
```typescript
{
  task_id: string;
  concept_id: string;
  metadata?: Record<string, unknown>;
}
```

Response Schema:
```typescript
{
  success: boolean;
  taskId: string;
  conceptId: string;
}
```

### GET /api/kg/data
Get knowledge graph data. This endpoint provides the semantic knowledge network:

Frontend:
- Used by GraphPanel.svelte for knowledge visualization
- Used by Chat.svelte for context awareness
- Used by TaskBoard.svelte for task categorization

Storage Flow:
1. Neo4j:
   - Retrieves domain hierarchies
   - Resolves concept relationships
   - Validates access permissions
   - Tracks access patterns

2. Qdrant:
   - Provides semantic embeddings
   - Enriches node context
   - Handles similarity matching
   - Updates relevance scores

3. DAG:
   - Validates graph consistency
   - Manages traversal order
   - Prevents circular references
   - Ensures data integrity

Response Schema:
```typescript
{
  nodes: Array<{
    id: string;
    label: string;
    type: string;
    category: string;
    domain: string;
    metadata: Record<string, unknown>;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    type: string;
    label: string;
  }>;
  timestamp: string;
}
```

### GET /api/kg/taskConcepts/{task_id}
Get concepts related to a task.

Response Schema:
```typescript
{
  taskId: string;
  concepts: Array<{
    id: string;
    name: string;
    type: string;
    metadata: Record<string, unknown>;
    timestamp: string;
  }>;
  timestamp: string;
}
```

## Graph Operations
Implementation: src/nia/nova/endpoints/graph_endpoints.py

This module implements our graph visualization and analysis system:

Frontend Integration:
- Used by GraphPanel.svelte for interactive visualization
- Used by TaskBoard.svelte for dependency visualization
- Used by Chat.svelte for relationship context

Storage Patterns:
1. Neo4j:
   - Stores graph structure
   - Manages node relationships
   - Handles graph traversal
   - Maintains graph history

2. Qdrant:
   - Stores node embeddings
   - Handles similarity search
   - Tracks access patterns
   - Manages node context

3. DAG:
   - Validates graph operations
   - Prevents cycles
   - Manages operation order
   - Ensures consistency

### GET /api/graph/agents
Get agent graph data. This endpoint provides the agent collaboration network:

Frontend:
- Used by GraphPanel.svelte for team visualization
- Used by Chat.svelte for agent selection
- Used by TaskBoard.svelte for assignment

Response Schema:
```typescript
{
  nodes: Array<{
    id: string;
    label: string;
    type: string;
    status: string;
    domain: string;
    properties: Record<string, unknown>;
  }>;
  edges: Array<{
    source: string;
    target: string;
    type: string;
    label: string;
    properties: Record<string, unknown>;
  }>;
  timestamp: string;
}
```

### GET /api/graph/knowledge
Get knowledge graph data.

Response Schema:
```typescript
{
  nodes: Array<{
    id: string;
    label: string;
    type: string;
    domain: string;
    properties: Record<string, unknown>;
  }>;
  edges: Array<{
    source: string;
    target: string;
    type: string;
    label: string;
    properties: Record<string, unknown>;
  }>;
  timestamp: string;
}
```

### GET /api/graph/tasks
Get task graph data. This endpoint provides the task dependency network:

Frontend:
- Used by GraphPanel.svelte for dependency visualization
- Used by TaskBoard.svelte for task relationships
- Used by Chat.svelte for task context

Storage Flow:
1. Neo4j:
   - Retrieves task nodes and relationships
   - Resolves dependency chains
   - Validates task access
   - Tracks task history

2. Qdrant:
   - Provides task embeddings
   - Enriches task context
   - Handles similarity matching
   - Updates relevance scores

3. DAG:
   - Validates dependency cycles
   - Manages traversal order
   - Ensures graph consistency
   - Tracks operation sequence

Response Schema:
```typescript
{
  nodes: Array<{
    id: string;
    label: string;
    type: string;
    status: string;
    domain: string;
    properties: Record<string, unknown>;
  }>;
  edges: Array<{
    source: string;
    target: string;
    type: string;
    label: string;
    properties: Record<string, unknown>;
  }>;
  timestamp: string;
}
```

### ThreadValidation
```typescript
interface ThreadValidation {
  domain: string;
  access_domain: string;
  confidence: number;
  source: string;
  timestamp: string;
  supported_by: string[];
  contradicted_by: string[];
  needs_verification: string[];
  cross_domain: Record<string, unknown>;
}
```

## WebSocket Events

### Chat Events
```typescript
interface ThreadUpdateMessage {
  type: 'thread_update';
  thread_id: string;
  changes: {
    title?: string;
    status?: 'active' | 'archived' | 'deleted';
    metadata?: Record<string, unknown>;
    participants?: Array<{
      id: string;
      type: 'user' | 'agent';
      action: 'add' | 'remove';
    }>;
  };
}

interface ChatMessage {
  type: 'message';
  content: string;
  thread_id: string;
  sender_type: string;
  sender_id: string;
}

interface TypingIndicator {
  type: 'typing';
  user_id: string;
  thread_id: string;
  is_typing: boolean;
}
```

### Task Events
```typescript
interface TaskUpdateMessage {
  type: 'task_update';
  task_id: string;
  changes: Record<string, unknown>;
}

interface TaskProgressMessage {
  type: 'task_progress';
  task_id: string;
  progress: number;
  status: string;
  message?: string;
}

interface TaskAssignmentMessage {
  type: 'task_assignment';
  task_id: string;
  assignee: string;
  previous_assignee?: string;
}
```

## Agent Operations
Implementation: src/nia/nova/endpoints/agent_endpoints.py

Storage Patterns:
- Semantic Layer (Neo4j): Stores agent nodes with metadata and relationships
- Episodic Memory: Stores agent metrics and interaction history

Default Values (from implementation):
- agent_id: Generated UUID if not provided
- name: "Unknown Agent" if not provided
- type: "agent" if not provided
- status: "active" if not provided
- capabilities: [] if not provided
- workspace: "personal" if not provided
- confidence: 0.8 if not provided
- specialization: defaults to agent type if not provided

Neo4j Query for Agent Retrieval:
```cypher
MATCH (a:Concept {type: 'agent'})
RETURN a {
    .id,
    .name,
    .type,
    .status,
    .capabilities,
    .workspace,
    .metadata,
    agent_id: coalesce(a.id, randomUUID()),
    name: coalesce(a.name, 'Unknown Agent'),
    type: coalesce(a.type, 'agent'),
    status: coalesce(a.status, 'active'),
    capabilities: coalesce(a.capabilities, []),
    workspace: case when a.workspace in ['personal', 'professional'] 
               then a.workspace else 'personal' end,
    metadata: {
        capabilities: coalesce(a.capabilities, []),
        confidence: coalesce(a.confidence, 0.8),
        specialization: coalesce(a.specialization, a.type)
    }
} as agent
```

### GET /api/nova/agents
Lists all available agents.

Response Schema:
```typescript
Array<{
  id: string;
  name: string;
  type: 'agent';
  agentType: string;
  status: 'active' | 'inactive' | 'error';
  capabilities: string[];
  workspace: 'personal' | 'professional' | 'system';
  metadata: {
    capabilities: string[];
    confidence: number;
    specialization: string;
  };
  timestamp: string;
}>
```

### GET /api/nova/agents/{agent_id}
Gets a specific agent by ID.

Response Schema:
```typescript
{
  id: string;
  name: string;
  type: 'agent';
  agentType: string;
  status: 'active' | 'inactive' | 'error';
  capabilities: string[];
  workspace: 'personal' | 'professional' | 'system';
  metadata: {
    capabilities: string[];
    confidence: number;
    specialization: string;
  };
  timestamp: string;
}
```

### POST /api/nova/agents
Creates a new agent.

Request Schema:
```typescript
interface AgentInfo {
  id: string;
  name: string;
  type: 'agent' | 'team' | 'system';
  workspace?: 'personal' | 'shared' | 'system';
  domain?: 'general' | 'tasks' | 'chat' | 'analysis';
  status?: 'active' | 'inactive' | 'error';
  metadata: {
    type: string;
    capabilities: string[];
    created_at?: string;
    thread_id?: string;
  };
}
```

Response Schema:
```typescript
{
  id: string;
  name: string;
  type: 'agent';
  agentType: string;
  status: string;
  capabilities: string[];
  metadata: Record<string, unknown>;
  timestamp: string;
}
```

### GET /api/nova/agents/{agent_id}/metrics
Gets performance metrics for an agent.

Response Schema:
```typescript
{
  response_time: number;
  tasks_completed: number;
  success_rate: number;
  uptime: number;
  last_active: string;
  metadata: Record<string, unknown>;
}
```

## Nova Operations

### POST /api/nova/ask
Ask Nova a question. This endpoint implements our core processing pipeline:

Processing Flow:
1. Input Pre-Processing:
   - Parsing Agent: First point of contact
     * Uses Outlines library for JSON structured parsing
     * Converts raw input into structured format
     * Validates input schema and structure
     * Handles pre-processing before cognitive processing
   - Schema Agent:
     * Validates parsed input against schemas
     * Ensures data consistency and format
     * Works with parsing agent for validation

2. Core Processing:
   - Meta Agent coordinates:
     * Context retrieval (context_agent)
     * Memory access (memory_agent)
     * Planning (planning_agent)
     * Cognitive processing (belief/desire/emotion agents)
     * Reflection (reflection_agent)
     * Learning (learning_agent)

3. Output Post-Processing:
   - Validation:
     * validation_agent validates response
     * schema_agent validates output format
     * alerting_agent handles any issues
   - Response Generation:
     * orchestration_agent structures response
     * dialogue_agent generates natural language
     * synthesis_agent creates final output
   - Memory Storage:
     * memory_agent stores interaction
     * learning_agent stores new knowledge
     * monitoring_agent tracks metrics

Request Schema:
```typescript
{
  content: string;
  workspace: 'personal' | 'professional';
  debug_flags?: {
    log_validation: boolean;
    log_websocket: boolean;
    log_storage: boolean;
    strict_mode: boolean;
  }
}
```

Response Schema:
```typescript
{
  threadId: string;
  message: {
    id: string;
    content: string;
    sender_type: 'agent';
    sender_id: 'nova';
    timestamp: string;
    metadata: {
      parsing: {
        structured_input: Record<string, unknown>;
        validation_result: Record<string, unknown>;
      };
      processing: {
        context: Record<string, unknown>;
        cognitive_state: {
          beliefs: unknown[];
          desires: unknown[];
          emotions: unknown[];
          reflections: unknown[];
        };
        learning: {
          new_concepts: unknown[];
          updated_concepts: unknown[];
        };
      };
      validation: {
        schema_valid: boolean;
        format_valid: boolean;
        issues: unknown[];
      };
      debug?: {
        parsing_time: number;
        processing_time: number;
        validation_time: number;
        total_time: number;
      };
    };
  };
}
```

Storage:
- Neo4j: 
  * Stores thread relationships and domain context
  * Manages concept relationships
  * Tracks validation patterns
- Memory: 
  * Stores conversation history
  * Manages validation state
  * Tracks processing patterns
- Qdrant: 
  * Stores message embeddings
  * Handles semantic search
  * Manages concept embeddings

## Agent Types

### AgentType
```typescript
type AgentType = 'agent' | 'team' | 'system';
```

### AgentWorkspace
```typescript
type AgentWorkspace = 'personal' | 'shared' | 'system';
```

### AgentDomain
```typescript
type AgentDomain = 'general' | 'tasks' | 'chat' | 'analysis';
```

### AgentStatus
```typescript
type AgentStatus = 'active' | 'inactive' | 'error';
```

### AgentRelationType
```typescript
type AgentRelationType = 
  | 'COORDINATES'
  | 'MANAGES'
  | 'ASSISTS'
  | 'COLLABORATES_WITH'
  | 'REPORTS_TO'
  | 'DELEGATES_TO'
  | 'DEPENDS_ON';
```

## Storage Patterns

### Agent Storage
Neo4j query for agent creation:
```cypher
CREATE (a:Concept {
  id: $id,
  name: $name,
  type: 'agent',
  status: $status,
  workspace: $workspace,
  domain: $domain,
  metadata: $metadata,
  created_at: datetime()
})
```

Memory storage for agent interactions:
```typescript
Memory {
  content: {
    type: 'agent_interaction';
    agent_id: string;
    action: string;
    result: unknown;
  };
  type: MemoryType.AGENT_UPDATE;
  metadata: {
    timestamp: string;
    domain: string;
  };
}
```

## Channel Operations

### GET /api/channels/{channel_id}/details
Get detailed information about a channel.

Response Schema:
```typescript
interface ChannelDetails {
  id: string;
  name: string;
  description?: string;
  created_at: string;  // ISO date
  updated_at: string;  // ISO date
  is_public: boolean;
  workspace: string;
  domain?: string;
  type: string;        // default: 'channel'
  metadata: Record<string, unknown>;
}
```

### GET /api/channels/{channel_id}/members
Get list of members in a channel.

Response Schema:
```typescript
interface ChannelMember {
  id: string;
  name: string;
  type: string;
  role: string;
  status: string;
  joined_at: string;  // ISO date
  metadata: Record<string, unknown>;
}
```

### GET /api/channels/{channel_id}/pinned
Get pinned items in a channel.

Response Schema:
```typescript
interface PinnedItem {
  id: string;
  type: string;
  content: Record<string, unknown>;
  pinned_by: string;
  pinned_at: string;  // ISO date
  metadata: Record<string, unknown>;
}
```

### POST /api/channels/{channel_id}/settings
Update channel settings.

Request/Response Schema:
```typescript
interface ChannelSettings {
  notifications: boolean;  // default: true
  privacy: string;        // default: 'public'
  retention_days?: number;
  metadata: Record<string, unknown>;
}
```

## Task Search & Board Operations

### GET /api/tasks/search
Search tasks with filtering, sorting, and pagination.

Query Parameters:
- q: Text search query
- status: Comma-separated task states (pending, in_progress, blocked, completed)
- priority: Comma-separated priorities (high, medium, low)
- assignee: Comma-separated assignees
- from_date: Start date for date range filter
- to_date: End date for date range filter
- sort: Field to sort by (default: updated_at)
- order: Sort direction (asc/desc)
- page: Page number (default: 1)
- size: Page size (default: 20, max: 100)

Response Schema:
```typescript
{
  tasks: TaskNode[];
  totalItems: number;
  totalPages: number;
}
```

Storage:
- Qdrant: Semantic search on task descriptions
- Neo4j: Task metadata and relationships
- Memory: Task update history and validation state

### GET /api/tasks/board
Get tasks organized by state for Kanban board view.

Response Schema:
```typescript
{
  board: {
    pending: TaskNode[];
    in_progress: TaskNode[];
    blocked: TaskNode[];
    completed: TaskNode[];
  };
  timestamp: string;
}
```

Storage:
- Neo4j: Task nodes with state and relationships
- Memory: Task state history and validation

## Task Management Operations

### GET /api/tasks/{task_id}/history
Get task history including state changes, updates, comments, and assignments.

Response Schema:
```typescript
{
  taskId: string;
  stateHistory: Array<{
    from: TaskState;
    to: TaskState;
  }>;
  updateHistory: Array<{
    field: string;
    from: any;
    to: any;
  }>;
  comments: Comment[];
  assignmentHistory: Array<{
    from: string;
    to: string;
  }>;
}
```

### POST /api/tasks/{task_id}/transition
Transition a task to a new state.

Query Parameters:
- new_state: TaskState (pending, in_progress, blocked, completed)

Validation:
- PENDING -> IN_PROGRESS
- IN_PROGRESS -> BLOCKED (requires dependencies) or COMPLETED
- BLOCKED -> IN_PROGRESS
- COMPLETED -> No transitions allowed

Response Schema:
```typescript
{
  success: boolean;
  taskId: string;
  newState: TaskState;
}
```

### Task Groups

#### POST /api/tasks/groups
Create a new task group.

Request Schema:
```typescript
// Uses TaskNode schema with type="group"
{
  ...TaskNode;
  type: 'group';
}
```

Response Schema:
```typescript
{
  success: boolean;
  taskId: string;
}
```

#### POST /api/tasks/groups/{group_id}/tasks/{task_id}
Add a task to a group.

Validation:
- Verifies group exists and is type "group"

Response Schema:
```typescript
{
  success: boolean;
  groupId: string;
  taskId: string;
}
```

#### GET /api/tasks/groups/{group_id}/tasks
Get all tasks in a group.

Response Schema:
```typescript
{
  tasks: TaskNode[];
  groupId: string;
}
```

### Task Components

#### POST /api/tasks/{task_id}/subtasks
Add a subtask to a task.

Request Schema:
```typescript
interface SubTask {
  id: string;
  description: string;
  completed?: boolean;
  created_at?: string;
}
```

Response Schema:
```typescript
{
  success: boolean;
  taskId: string;
  subtaskId: string;
}
```

#### PATCH /api/tasks/{task_id}/sub-tasks/{subtask_id}
Update a subtask's completion status.

Request Schema:
```typescript
{
  completed: boolean;
}
```

Response Schema:
```typescript
{
  success: boolean;
  taskId: string;
  subtaskId: string;
  completed: boolean;
}
```

#### POST /api/tasks/{task_id}/comments
Add a comment to a task.

Request Schema:
```typescript
interface Comment {
  id: string;
  content: string;
  author: string;
  timestamp: string;
  edited?: boolean;
}
```

Response Schema:
```typescript
{
  success: boolean;
  taskId: string;
  commentId: string;
}
```

## WebSocket Operations
Implementation: src/nia/nova/endpoints/websocket_endpoints.py

This module implements our real-time communication system:

Frontend Integration:
- Used by Chat.svelte for live messaging
- Used by TaskBoard.svelte for task updates
- Used by GraphPanel.svelte for graph changes

Storage Flow:
1. Neo4j:
   - Tracks connection states
   - Manages subscription patterns
   - Records message history
   - Handles access control

2. Qdrant:
   - Stores message embeddings
   - Tracks interaction patterns
   - Manages message context
   - Updates relevance scores

3. Memory System:
   - Handles message persistence
   - Manages state synchronization
   - Tracks connection history
   - Ensures message delivery

Connection Types:
```typescript
type ConnectionType = 'chat' | 'tasks' | 'agents' | 'graph';
```

Server Components:
- WebSocketServer: Manages connections and message broadcasting
- Memory System Integration: Broadcasts memory updates to connected clients
- Connection Handlers: Specialized handlers for each connection type
- State Management: Handles connection lifecycles and recovery

Error Handling:
- API key validation on connection
- Automatic disconnection on invalid API key (code 4000)
- Runtime error handling (code 1011)
- Connection type validation
- Graceful disconnect handling

Connection Flow:
1. Client connects with API key and connection type
2. Server validates API key
3. Connection accepted if valid
4. Type-specific handler takes over
5. Real-time updates begin flowing
6. Disconnection handled gracefully

Memory Update Broadcasting:
```python
async def start_memory_updates():
    """Start background task for broadcasting memory updates."""
    try:
        server = get_websocket_server()
        return await server.broadcast_memory_updates()
    except Exception as e:
        logger.error(f"Error starting memory updates: {str(e)}")
        raise
```

### Chat WebSocket (/api/ws/chat/{client_id})

This endpoint implements our real-time chat system:

Frontend Integration:
- Used by Chat.svelte for live messaging
- Used by ThreadList.svelte for thread updates
- Used by TypingIndicator.svelte for typing status

Storage Flow:
1. Neo4j:
   - Tracks chat participants
   - Manages thread states
   - Records message history
   - Handles access control

2. Qdrant:
   - Stores message embeddings
   - Tracks conversation context
   - Manages semantic search
   - Updates relevance scores

3. Memory System:
   - Handles message persistence
   - Manages thread synchronization
   - Tracks conversation history
   - Ensures message delivery

Message Types:
```typescript
// Thread Updates
interface ThreadUpdateMessage {
  type: 'thread_update';
  thread_id: string;
  changes: {
    title?: string;
    status?: 'active' | 'archived' | 'deleted';
    metadata?: Record<string, unknown>;
    participants?: Array<{
      id: string;
      type: 'user' | 'agent';
      action: 'add' | 'remove';
    }>;
  };
}

// New Messages
interface ChatMessage {
  type: 'message';
  content: string;
  thread_id: string;
  sender_type: string;
  sender_id: string;
}

// Typing Indicators
interface TypingIndicator {
  type: 'typing';
  user_id: string;
  thread_id: string;
  is_typing: boolean;
}
```

### Tasks WebSocket (/api/ws/tasks/{client_id})

This endpoint implements our real-time task management system:

Frontend Integration:
- Used by TaskBoard.svelte for live updates
- Used by TaskList.svelte for task filtering
- Used by TaskDetails.svelte for progress tracking

Storage Flow:
1. Neo4j:
   - Tracks task states
   - Manages dependencies
   - Records task history
   - Handles access control

2. Qdrant:
   - Stores task embeddings
   - Tracks task context
   - Manages search updates
   - Updates relevance scores

3. Memory System:
   - Handles task persistence
   - Manages state synchronization
   - Tracks operation history
   - Ensures update delivery

Message Types:
```typescript
// Task Updates
interface TaskUpdateMessage {
  type: 'task_update';
  task_id: string;
  changes: Record<string, unknown>;
}

// Progress Updates
interface TaskProgressMessage {
  type: 'task_progress';
  task_id: string;
  progress: number;
  status: string;
  message?: string;
}

// Search Updates
interface TaskSearchMessage {
  type: 'task_search';
  data: {
    query?: string;           // Text search
    filters?: {
      status?: TaskState[];
      assignee?: string[];
      dateRange?: {
        from?: string;    // ISO date
        to?: string;      // ISO date
      };
    };
    pagination?: {
      page: number;         // >= 1
      pageSize: number;     // 1-100
    };
  };
  timestamp: string;
}
```

### Graph WebSocket (/api/ws/graph/{client_id})

This endpoint implements our real-time graph visualization system:

Frontend Integration:
- Used by GraphPanel.svelte for live visualization
- Used by TaskBoard.svelte for dependency updates
- Used by Chat.svelte for context changes

Storage Flow:
1. Neo4j:
   - Tracks graph changes
   - Manages node states
   - Records edge updates
   - Handles access control
   - Validates node relationships
   - Maintains graph consistency
   - Tracks version history
   - Manages domain boundaries

2. Qdrant:
   - Stores node embeddings
   - Tracks graph context
   - Manages similarity updates
   - Updates relevance scores
   - Handles semantic search
   - Maintains vector indices
   - Tracks access patterns
   - Updates importance scores

3. Memory System:
   - Handles graph persistence
   - Manages state synchronization
   - Tracks layout history
   - Ensures update delivery
   - Validates graph operations
   - Prevents circular references
   - Manages consolidation
   - Tracks operation order

Update Types:
- Node Updates: Changes to node properties, states, or metadata
- Edge Updates: New connections, removed connections, or relationship changes
- Layout Updates: Changes to graph visualization layout
- Domain Updates: Changes to domain boundaries or access control
- Validation Updates: Changes to graph consistency state

Message Types:
```typescript
// Graph Updates
interface GraphUpdateMessage {
  type: 'graph_update';
  nodes: Array<{
    id: string;
    type: string;
    changes: Record<string, unknown>;
  }>;
  edges: Array<{
    id: string;
    type: string;
    changes: Record<string, unknown>;
  }>;
}
```

### WebSocket Authentication
- API key required in connection headers
- Invalid keys result in immediate connection closure
- Connections close on API key expiration

Example Connection:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/chat/client123', {
  headers: {
    'X-API-Key': 'your-api-key'
  }
});

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.onclose = (event) => {
  console.log('WebSocket closed:', event.code, event.reason);
};
```
