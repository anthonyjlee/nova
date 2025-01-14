"""FastAPI documentation."""

API_DESCRIPTION = """
Nova's analytics and orchestration API

## Task Management Endpoints (/api/tasks)

### Task Search & Filtering (/api/tasks)
- GET /search - Search tasks with filtering, sorting, and pagination
  - Query params:
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

### Task Board Operations (/api/tasks)
- GET /board - Get tasks organized by state for Kanban board view
- GET /{task_id}/details - Get detailed information about a task including dependencies, subtasks, and comments

### Task Graph Operations (/api/tasks/graph)
- GET / - Get the current task graph with nodes and edges
- POST /addNode - Add a new task node
  - Body: TaskNode object with task details
- POST /updateNode - Update a task node
  - Body: TaskUpdate object with fields to update
- POST /addDependency - Add a dependency between tasks
  - Body: TaskEdge object with source and target task IDs

### Task Management (/api/tasks)
- POST / - Create a new task
  - Body: TaskNode object with task details
  - Response: { "success": true, "taskId": string }
- GET /{task_id}/details - Get detailed information about a task
  - Response: TaskDetails object with task data, dependencies, subtasks, comments
- GET /{task_id}/history - Get task history (state changes, updates, comments, assignments)
  - Response: {
      "taskId": string,
      "stateHistory": Array<{from: TaskState, to: TaskState}>,
      "updateHistory": Array<{field: string, from: any, to: any}>,
      "comments": Array<Comment>,
      "assignmentHistory": Array<{from: string, to: string}>
    }
- POST /{task_id}/transition - Transition a task to a new state
  - Body: TaskState enum value (pending, in_progress, blocked, completed)
  - Validation:
    - PENDING -> IN_PROGRESS
    - IN_PROGRESS -> BLOCKED (requires dependencies) or COMPLETED
    - BLOCKED -> IN_PROGRESS
    - COMPLETED -> No transitions allowed
  - Response: { "success": true, "taskId": string, "newState": TaskState }

### Task Components (/api/tasks)
- POST /{task_id}/subtasks - Add a subtask to a task
  - Body: SubTask object with description and completion status
  - Response: { "success": true, "taskId": string, "subtaskId": string }
- PATCH /{task_id}/sub-tasks/{subtask_id} - Update a subtask's completion status
  - Path params: task_id (task ID), subtask_id (subtask ID)
  - Body: { "completed": boolean }
  - Response: { "success": true, "taskId": string, "subtaskId": string, "completed": boolean }
- POST /{task_id}/comments - Add a comment to a task
  - Body: Comment object with content and author
  - Response: { "success": true, "taskId": string, "commentId": string }

### Task Groups (/api/tasks/groups)
- POST / - Create a new task group
  - Body: TaskNode object with type="group" (required)
  - Validation: Ensures type is "group"
  - Response: { "success": true, "taskId": string }
- POST /{group_id}/tasks/{task_id} - Add a task to a group
  - Path params: group_id (group ID), task_id (task ID)
  - Validation: Verifies group exists and is type "group"
  - Response: { "success": true, "groupId": string, "taskId": string }
- GET /{group_id}/tasks - Get all tasks in a group
  - Path params: group_id (group ID)
  - Response: { "tasks": TaskNode[], "groupId": string }

### Task Dependencies (/api/tasks/graph)
- POST /addDependency - Add a dependency between tasks
  - Body: TaskEdge object with source and target task IDs
  - Validation: Verifies both tasks exist and validates domain access
  - Response: { "success": true, "edgeId": string }
- GET / - Get the current task graph with nodes and edges
  - Response: { "analytics": { "nodes": Node[], "edges": Edge[] }, "timestamp": string }
- POST /updateNode - Update a task node
  - Body: TaskUpdate object with fields to update
  - Validation: Validates state transitions and domain access
  - Response: { "success": true, "taskId": string }

### Task History (/api/tasks)
- GET /{task_id}/history - Get task history
  - Path params: task_id (task ID)
  - Response: {
      "taskId": string,
      "stateHistory": Array<{from: TaskState, to: TaskState}>,
      "updateHistory": Array<{field: string, from: any, to: any}>,
      "comments": Array<Comment>,
      "assignmentHistory": Array<{from: string, to: string}>
    }

### Task Views (/api/tasks)
- GET /search - Search tasks with filtering, sorting, and pagination
  - Query params: q, status, priority, assignee, dates, sort, order, page, size
- GET /board - Get tasks organized by state for Kanban board view

### Deprecated Endpoints
- POST /api/tasks/graph/addNode - Add a new task node (deprecated: use POST /api/tasks instead)

### Response Models
- TaskNode: Base task model with all task fields
- TaskDetails: Extended task details including relationships
- TaskUpdate: Model for updating task fields
- SubTask: Model for task subtasks
- Comment: Model for task comments
- TaskState: Enum for task states (pending, in_progress, blocked, completed)
- TaskPriority: Type for task priorities (high, medium, low)

### Authentication & Authorization
- All endpoints require a valid API key in the X-API-Key header
- Invalid or missing API keys return 401 Unauthorized
- Write operations require write permission
- Read operations require read permission
- Permission errors return 403 Forbidden

### Domain Access
All task endpoints validate domain access:
- Tasks can only be created/updated in domains the user has access to
- Domain access is validated when:
  - Creating a new task
  - Updating a task's domain
  - Adding dependencies between tasks
  - Transitioning task states
  - Adding tasks to groups
- Domain validation errors return 403 Forbidden with details

### Error Responses
- 400 Bad Request: Invalid input data or state transitions
- 401 Unauthorized: Missing or invalid API key
- 403 Forbidden: Insufficient permissions or domain access
- 404 Not Found: Resource not found
- 500 Internal Server Error: Unexpected server errors

## Nova Endpoints (/api/nova)

### Nova Chat
- POST /ask - Ask Nova a question
  - Body: { "content": string }
  - Response: {
      "threadId": string,
      "message": {
          "id": string,
          "content": string,
          "sender_type": "agent",
          "sender_id": "nova",
          "timestamp": string,
          "metadata": object
      }
    }
  - Creates Nova thread if it doesn't exist
  - Requires write permission
  - Stores conversation in episodic memory

## Graph Endpoints (/api/graph)

### Knowledge Graph Operations
- GET /data - Get current graph data
  - Response: {
      "nodes": Node[],
      "edges": Edge[],
      "timestamp": string
    }

## Knowledge Graph Endpoints (/api/kg)

### Domain Operations
- POST /crossDomain - Request cross-domain access
  - Body: {
      source_domain: string,
      target_domain: string,
      reason?: string
    }
  - Response: {
      success: boolean,
      requestId: string,
      status: "pending"
    }
- GET /domains - List available knowledge domains
  - Response: {
      domains: Array<{
          name: string,
          type: string,
          description: string
      }>,
      relationships: Array<{
          source: string,
          target: string,
          status: string
      }>,
      timestamp: string
    }

### Task Knowledge Integration
- POST /taskReference - Link task to concept
  - Body: {
      task_id: string,
      concept_id: string,
      metadata?: object
    }
  - Response: {
      success: boolean,
      taskId: string,
      conceptId: string
    }
- GET /data - Get knowledge graph data
  - Response: {
      nodes: Array<{
          id: string,
          label: string,
          type: string,
          category: string,
          domain: string,
          metadata: object
      }>,
      edges: Array<{
          id: string,
          source: string,
          target: string,
          type: string,
          label: string
      }>,
      timestamp: string
    }
- GET /taskConcepts/{task_id} - Get concepts related to a task
  - Path params: task_id (task ID)
  - Response: {
      taskId: string,
      concepts: Array<{
          id: string,
          name: string,
          type: string,
          metadata: object,
          timestamp: string
      }>,
      timestamp: string
    }

## Agent Management Endpoints (/api/agents)

### Agent Operations
- GET "" - List all available agents
  - Response: Array<{
      id: string,
      name: string,
      type: string,
      workspace: string,
      status: string,
      metadata: object
    }>
- GET /graph - Get agent DAG visualization
  - Response: {
      "nodes": Array<{
          id: string,
          label: string,
          type: string,
          status: string,
          domain: string,
          properties: object
      }>,
      "edges": Array<{
          source: string,
          target: string,
          type: string,
          label: string,
          properties: object
      }>,
      "timestamp": string
    }

## Chat & Thread Endpoints

### Thread Management (/api/chat/threads)
- POST /threads/create - Create new thread
  - Body: ThreadRequest with title, domain, metadata, workspace
  - Response: ThreadResponse
- GET /threads/{thread_id} - Get thread details
  - Response: ThreadResponse with messages and metadata
- POST /threads/{thread_id}/messages - Add message
  - Body: MessageRequest with content and sender info
  - Response: MessageResponse
- GET /threads - List all threads
  - Response: ThreadListResponse with array of threads

### Agent Integration (/api/chat)
- GET /agents - List available chat agents
  - Response: Array of agent details with capabilities
- GET /threads/{thread_id}/agents - Get agents in thread
  - Response: Array of agent details for thread
- POST /threads/{thread_id}/agents - Add agent to thread
  - Body: { agentType: string, workspace?: string, domain?: string }
  - Response: Agent details
- POST /threads/{thread_id}/agent-team - Create agent team
  - Body: { agents: Array<AgentSpec> }
  - Response: Array of created agents

## WebSocket Endpoints (/api/ws)

### Chat WebSocket (/api/ws/chat/{client_id})
Real-time chat updates including:
- New messages
- Thread updates
- Message reactions
- Typing indicators

### Tasks WebSocket (/api/ws/tasks/{client_id})
Real-time task board updates including:
- Task state changes
- Assignment updates
- Comment notifications
- Progress tracking

Real-time search updates:
- Text search results
- Status filter updates
- Date range filter updates
- Pagination updates
- Combined search criteria

Message Format:
```typescript
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

### Agents WebSocket (/api/ws/agents/{client_id})
Real-time agent status updates including:
- Agent state changes
- Team updates
- Performance metrics
- Capability changes

### Graph WebSocket (/api/ws/graph/{client_id})
Real-time knowledge graph updates including:
- Node updates
- Edge modifications
- Domain changes
- Relationship tracking

Example connection:
```javascript
// API key required for WebSocket connections
const ws = new WebSocket('ws://localhost:8000/api/ws/chat/client123', {
    headers: {
        'X-API-Key': 'your-api-key'
    }
});

// Handle connection errors
ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

// Handle messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// Handle disconnection
ws.onclose = (event) => {
    console.log('WebSocket closed:', event.code, event.reason);
};
```

WebSocket Authentication:
- WebSocket connections require the same API key as REST endpoints
- API key must be provided in connection headers
- Invalid API keys result in immediate connection closure
- Connections are automatically closed on API key expiration

Message Format:
```typescript
interface WebSocketMessage {
    type: string;          // Message type (e.g. 'message', 'status', 'update')
    data: any;            // Message payload
    timestamp: string;    // ISO timestamp
    metadata?: {          // Optional metadata
        source?: string;
        domain?: string;
        importance?: number;
    }
}
```
"""
