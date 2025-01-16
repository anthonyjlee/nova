# User Flow and System Integration

This document describes how users interact with the system, showing the endpoints and storage operations triggered at each step, with TinyTroupe integration.

## WebSocket Integration

### Connection Management
1. **Connection Setup**
   ```typescript
   // websocket/client.ts
   class WebSocketClient {
     private connections: Map<string, WebSocket>;
     private reconnectTimeouts: Map<string, number>;
     
     async connect(endpoint: string) {
       // Prevent duplicate connections
       if (this.connections.has(endpoint)) return;
       
       // Set connection timeout
       const ws = new WebSocket(endpoint);
       const timeout = setTimeout(() => {
         if (ws.readyState !== WebSocket.OPEN) {
           this.reconnect(endpoint);
         }
       }, 5000);
       
       this.connections.set(endpoint, ws);
       this.reconnectTimeouts.set(endpoint, timeout);
     }
     
     private reconnect(endpoint: string) {
       // Exponential backoff
       const attempts = (this.reconnectAttempts.get(endpoint) || 0) + 1;
       const delay = Math.min(1000 * Math.pow(2, attempts), 30000);
       
       setTimeout(() => this.connect(endpoint), delay);
       this.reconnectAttempts.set(endpoint, attempts);
     }
   }
   ```

2. **Message Validation**
   ```typescript
   // validation/websocket-schemas.ts
   const messageSchema = z.object({
     type: z.enum(['message', 'status', 'error']),
     timestamp: z.string().datetime(),
     payload: z.unknown(),
     metadata: z.object({
       domain: z.string().optional(),
       importance: z.number().optional()
     }).optional()
   });
   
   function validateMessage(data: unknown) {
     return messageSchema.parse(data);
   }
   ```

3. **Error Handling**
   ```typescript
   // websocket/error-handler.ts
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
     
     private handleValidationError(error: ValidationError) {
       // Log invalid message
       // Notify user if needed
       // Request message resend
     }
     
     private handleConnectionError(error: ConnectionError) {
       // Attempt reconnection
       // Update UI connection status
       // Queue messages for retry
     }
   }
   ```

### Real-time Updates

1. **Task Updates**
   ```typescript
   // stores/tasks.ts
   class TaskStore {
     private tasks: Map<string, Task>;
     
     handleUpdate(message: TaskUpdateMessage) {
       const task = this.tasks.get(message.task_id);
       if (!task) return;
       
       // Update task state
       Object.assign(task, message.changes);
       
       // Notify subscribers
       this.notify(task);
     }
   }
   ```

2. **Chat Messages**
   ```typescript
   // stores/chat.ts
   class ChatStore {
     private messages: Map<string, Message[]>;
     
     handleMessage(message: ChatMessage) {
       const thread = this.messages.get(message.thread_id);
       if (!thread) return;
       
       // Add message
       thread.push(message);
       
       // Update thread state
       this.updateThread(message.thread_id);
       
       // Notify subscribers
       this.notify(message.thread_id);
     }
   }
   ```

3. **Graph Updates**
   ```typescript
   // stores/graph.ts
   class GraphStore {
     private nodes: Map<string, Node>;
     private edges: Map<string, Edge>;
     
     handleUpdate(message: GraphUpdateMessage) {
       // Update nodes
       for (const node of message.nodes) {
         this.updateNode(node);
       }
       
       // Update edges
       for (const edge of message.edges) {
         this.updateEdge(edge);
       }
       
       // Notify visualization
       this.notifyGraphChange();
     }
   }
   ```

## Task & Agent System Flow

1. **Task Detection & Creation**
   - Component: Chat.svelte (NOVA HQ)
   - Implementation:
     * EmergentTaskDetector analyzes conversations
     * TaskApprovalSystem manages workflow
     * CoordinationAgent handles team creation
   - Endpoints:
     * POST /api/tasks - Create task
     * POST /api/tasks/graph/addNode - Add to graph
     * POST /api/tasks/groups - Create task group
   - Storage:
     * Neo4j: Task relationships
     * Memory: Task context
     * Validation: Domain boundaries

2. **Task Organization**
   - Component: TaskBoard.svelte
   - Implementation:
     * Tasks organized in groups
     * Subtasks for complex operations
     * History tracking
   - Endpoints:
     * POST /api/tasks/groups/{group_id}/tasks/{task_id} - Add to group
     * POST /api/tasks/{task_id}/subtasks - Add subtask
     * GET /api/tasks/{task_id}/history - Get history
   - Storage:
     * Neo4j: Task hierarchy
     * Memory: Task state
     * Validation: Task rules

3. **Agent Team Management**
   - Component: Chat.svelte
   - Implementation:
     * CoordinationAgent creates groups
     * Agents assigned to tasks
     * Performance monitoring
   - Endpoints:
     * POST /api/chat/threads/{thread_id}/agent-team - Create team
     * GET /api/agents/{agent_id}/details - Get details
     * GET /api/agents/{agent_id}/metrics - Get metrics
   - Storage:
     * Neo4j: Agent relationships
     * Memory: Team state
     * Validation: Team rules

4. **Knowledge Integration**
   - Component: GraphPanel.svelte
   - Implementation:
     * Tasks linked to concepts
     * Cross-domain operations
     * Knowledge boundaries
   - Endpoints:
     * POST /api/kg/taskReference - Link task to concept
     * GET /api/kg/taskConcepts/{task_id} - Get concepts
     * POST /api/kg/crossDomain - Handle cross-domain
   - Storage:
     * Neo4j: Knowledge graph
     * Memory: Domain context
     * Validation: Access rules

5. **Real-time Updates**
   - WebSocket: /api/ws/{connection_type}/{client_id}
   - Events:
     * task_update: Task state changes
     * agent_status: Agent state updates
     * graph_update: Knowledge graph changes

2. **Orchestration Layer**
   - Component: Chat.svelte
   - Core Responsibilities:
     * Manage workflows with domain awareness
     * Handle cross-domain dependencies
     * Configure communication patterns
     * Adjust resource allocation
   - Endpoints:
     * POST /api/chat/threads/{thread_id}/agent-team - Assign team
     * GET /api/agents/teams - Get structures
     * GET /api/agents/{agent_id}/metrics - Get metrics
   - Storage:
     * Neo4j: Workflow structure
     * Memory: Resource state
     * Validation: Operation constraints

3. **Task Management**
   - Component: TaskBoard.svelte
   - Core Responsibilities:
     * Execute domain-constrained tasks
     * Monitor progress and compliance
     * Handle errors gracefully
     * Manage resources
   - Endpoints:
     * GET /api/tasks/board - Get board
     * POST /api/tasks - Create task
     * PATCH /api/tasks/{id} - Update task
   - Storage:
     * Neo4j: Task relationships
     * Memory: Task state
     * Validation: Domain compliance

4. **Communication Layer**
   - Component: Chat.svelte
   - Core Responsibilities:
     * Manage domain-aware conversations
     * Handle domain transitions
     * Maintain context coherence
     * Track patterns
   - Endpoints:
     * GET /api/chat/threads/{id} - Load thread
     * POST /api/chat/threads/{id}/messages - Send message
     * GET /api/chat/threads/{id}/agents - Get agents
   - Storage:
     * Qdrant: Message content
     * Neo4j: Thread relationships
     * Memory: Conversation context

5. **Analysis Layer**
   - Component: GraphPanel.svelte
   - Core Responsibilities:
     * Analyze domain-aware data
     * Extract structured content
     * Generate insights
     * Validate formats
   - Endpoints:
     * GET /api/graph/data - Get graph
     * GET /api/kg/domains - Get mapping
     * GET /api/analytics/metrics/performance - Get metrics
   - Storage:
     * Neo4j: Analysis patterns
     * Memory: Insights
     * Validation: Data boundaries

Base Domains:
```typescript
const BASE_DOMAINS = {
  PERSONAL: "personal",
  PROFESSIONAL: "professional"
}

const KNOWLEDGE_VERTICALS = {
  RETAIL: "retail",
  BUSINESS: "business",
  PSYCHOLOGY: "psychology",
  TECHNOLOGY: "technology",
  BACKEND: "backend",
  DATABASE: "database",
  GENERAL: "general"
}
```

Domain Management:
- Each agent operates within defined domains
- Cross-domain operations require explicit validation
- Domain inheritance follows task hierarchy
- Vertical specialization based on knowledge areas

## User Interaction Flows

### Initial Load
1. **Application Launch**
   - User Action: Opens application in browser
   - Frontend: Layout.svelte mounts
   - Endpoints:
     * GET /api/status (Check system health)
     * GET /api/channels/ (Load channel list)
     * GET /api/domains (Load domain list)
   - WebSocket: Connects to all WS endpoints
   - Real-time: Receives initial state updates

### Task Management
1. **Creating a Task**
   - User Action: Clicks "New Task" or mentions task in chat
   - Frontend: TaskBoard.svelte or Chat.svelte
   - Endpoints:
     * POST /api/tasks (Create task)
     * POST /api/tasks/graph/addNode (Add to graph)
   - WebSocket: task_created event
   - Real-time: Task appears in board

2. **Moving Task Status**
   - User Action: Drags task card between columns
   - Frontend: TaskColumn.svelte handles drag
   - Endpoints:
     * POST /api/tasks/{id}/transition
     * POST /api/tasks/graph/updateNode
   - WebSocket: task_update event
   - Real-time: All users see task move

### Chat Operations
1. **Starting a Thread**
   - User Action: Clicks channel or DM
   - Frontend: Chat.svelte loads
   - Endpoints:
     * GET /api/chat/threads/{id}
     * GET /api/chat/threads/{id}/messages
   - WebSocket: Subscribes to thread updates
   - Real-time: Typing indicators, new messages

2. **Sending Message**
   - User Action: Types and sends message
   - Frontend: Chat.svelte input
   - Endpoints:
     * POST /api/chat/threads/{id}/messages
     * POST /api/chat/threads/{id}/validate
   - WebSocket: message event
   - Real-time: Message appears with status

### Nova Agent Interactions
1. **Specialized Agent Creation**
   - User Action: Creates domain specialist in NOVA HQ
   - Frontend: Chat.svelte
   - Endpoints:
     * POST /api/nova/agents/specialize
     * GET /api/nova/agents/specialized/{domain}
   - Storage:
     * Neo4j: Store specialization
     * Memory: Training history
   - Real-time: Agent initialization

2. **Team Assembly**
   - User Action: Creates specialized team
   - Frontend: Chat.svelte
   - Endpoints:
     * POST /api/nova/agents/team/create
     * GET /api/nova/agents/specialized/{domain}
   - Storage:
     * Neo4j: Team structure
     * Memory: Team context
   - Real-time: Team formation

3. **Domain Operations**
   - User Action: Cross-domain work
   - Frontend: Chat.svelte
   - Endpoints:
     * POST /api/nova/domain/validate
     * POST /api/nova/domain/crossover
   - Storage:
     * Neo4j: Domain boundaries
     * Memory: Access patterns
   - Real-time: Permission updates

### Knowledge Graph
1. **Viewing Graph**
   - User Action: Opens graph panel
   - Frontend: GraphPanel.svelte
   - Endpoints:
     * GET /api/graph/data
     * GET /api/kg/domain-boundaries
   - WebSocket: graph_update events
   - Real-time: Node/edge updates

2. **Adding Connections**
   - User Action: Links concepts/tasks
   - Frontend: GraphPanel.svelte
   - Endpoints:
     * POST /api/kg/taskReference
     * POST /api/kg/validate-link
   - WebSocket: graph_update event
   - Real-time: New edges appear

## Initial Load

1. **Application Launch**
   - Component: Layout.svelte
   - Endpoints:
     * GET /api/status - Check system health
     * GET /api/channels/ - Load available channels
     * GET /api/domains - Load domain list
     * GET /api/agents/teams - Load agent teams
   - Storage:
     * Neo4j: Load user's accessible domains and relationships
     * Memory: Load user preferences and validation rules
     * Qdrant: Prepare recent context embeddings
   - TinyTroupe Integration:
     * Initialize agent emotional states
     * Set up domain-specific teams
     * Prepare interaction patterns

2. **WebSocket Connection**
   - Component: websocket/client.ts
   - Endpoints:
     * WS /api/ws/chat/{client_id} - Real-time chat updates
     * WS /api/ws/tasks/{client_id} - Task updates
     * WS /api/ws/agents/{client_id} - Agent status and emotions
     * WS /api/ws/graph/{client_id} - Graph updates
   - Validation:
     * Domain access checks
     * Cross-domain request tracking
     * Real-time permission updates
     * Emotional state monitoring

## Main Interface

1. **Navigation Panel** (Left)
   - Component: Navigation.svelte
   - Primary Elements:
     * NOVA HQ Channel (highlighted)
       - Entry point for agent specialization
       - Team assembly interface
       - Domain expertise configuration
     * Channels List
       - Filtered by domain access
       - Shows active agent teams
       - Domain context indicators
     * Direct Messages
       - Agent-specific channels
       - Domain-aware routing
       - Emotional state indicators
     * Task Boards
       - Domain-specific views
       - Agent team assignments
       - Progress tracking
   - Interaction Patterns:
     * Click NOVA HQ: Opens agent specialization interface
     * Click Channel: Shows team composition and domain context
     * Click DM: Opens agent-specific communication
     * Click Task Board: Shows domain-filtered tasks
   - Endpoints:
     * GET /api/channels/ - Load channels
     * GET /api/tasks/board - Load task boards
     * GET /api/domains/access - Check permissions
     * GET /api/agents/teams - Load team structures
   - Storage:
     * Neo4j: Channel and task relationships
     * Memory: User preferences and context
     * Validation: Cross-domain access rules
     * TinyTroupe: Team emotional states

2. **Chat Interface** (Center)
   - Component: Chat.svelte
   - Primary Elements:
     * Message Thread
       - Domain context indicators
       - Agent response highlighting
       - Emotional state visualization
       - Memory context links
     * Input Area
       - Smart completion
       - Domain validation
       - Agent suggestions
       - Command palette
     * Thread Context
       - Active agents list
       - Team composition
       - Domain boundaries
       - Memory integration
     * Agent Response Panel
       - Emotional state display
       - Confidence indicators
       - Domain expertise badges
       - Action suggestions
   - Interaction Patterns:
     * Type @nova: Opens agent command palette
     * Click agent: Shows capabilities and state
     * Hover message: Shows context and relations
     * Drag content: Initiates knowledge sharing
   - Special Features:
     * NOVA HQ Mode
       - Agent specialization interface
       - Team assembly controls
       - Domain configuration
       - Performance metrics
     * Team Channel Mode
       - Task coordination
       - Knowledge sharing
       - Cross-domain operations
   - Endpoints:
     * GET /api/chat/threads/{thread_id} - Load thread
     * POST /api/chat/threads/{thread_id}/messages - Send message
     * GET /api/chat/threads/{thread_id}/agents - Get thread agents
     * POST /api/chat/threads/{thread_id}/validate - Validate message
     * GET /api/agents/emotions - Get emotional context
   - Storage:
     * Qdrant: Message content and semantic search
     * Neo4j: Thread relationships and domain links
     * Memory: Thread context and validation state
     * TinyTroupe: Emotional responses and team dynamics

3. **Context Panel** (Right)
   - Component: GraphPanel.svelte
   - Primary Elements:
     * Knowledge Graph View
       - Interactive domain visualization
       - Team relationship mapping
       - Task dependency chains
       - Memory connection display
     * Agent Status Panel
       - Team composition view
       - Specialization badges
       - Performance metrics
       - Emotional state indicators
     * Task Context View
       - Current objectives
       - Domain validations
       - Cross-domain links
       - Progress tracking
     * Memory Integration Panel
       - Context history
       - Pattern recognition
       - Knowledge extraction
       - Validation status
   - Interaction Patterns:
     * Click node: Shows detailed information
     * Drag connections: Creates relationships
     * Hover team: Shows capabilities
     * Filter view: Updates context
   - Special Features:
     * NOVA HQ Mode
       - Agent specialization graph
       - Team formation visualization
       - Domain expertise mapping
       - Performance analytics
     * Team Channel Mode
       - Task coordination view
       - Knowledge flow display
       - Cross-domain bridges
       - Memory consolidation
   - Endpoints:
     * GET /api/graph/data - Load graph
     * POST /api/nova/ask - Send to Nova
     * POST /api/chat/threads/create - New thread
     * GET /api/domains/validate - Check access
   - Storage:
     * Qdrant: Store embeddings
     * Neo4j: Create relationships
     * Memory: Store context
   - Validation:
     * Domain access checks
     * Content validation rules
     * Cross-domain handling
     * Team composition rules

2. **Task Creation**
   - User Action: Create task from chat or board
   - Components:
     * TaskBoard.svelte
     * TaskDetailsPanel.svelte
     * DomainValidation.svelte
   - Endpoints:
     * POST /api/tasks - Create task
     * POST /api/tasks/graph/addNode - Add to task graph
     * POST /api/domains/validate - Validate domain access
   - Storage:
     * Neo4j: Create task node and relationships
     * Qdrant: Store task content and embeddings
     * Memory: Initialize task state and validation
   - Validation:
     * Domain boundary checks
     * Task creation permissions
     * Cross-domain task rules

3. **Task Management**
   - User Action: Update task status
   - Components:
     * TaskColumn.svelte
     * TaskBoard.svelte
     * StateValidation.svelte
   - Endpoints:
     * POST /api/tasks/{task_id}/transition - Update state
     * POST /api/tasks/graph/updateNode - Update graph
     * GET /api/tasks/validate-transition - Check transition
   - Storage:
     * Neo4j: Update task state and relationships
     * Memory: Store state change and validation
     * WebSocket: Broadcast update with context
   - Validation:
     * State transition rules
     * Domain access checks
     * Dependency validation

4. **Knowledge Integration**
   - User Action: Link task to concept
   - Components:
     * TaskDetailsPanel.svelte
     * GraphPanel.svelte
     * DomainBoundary.svelte
   - Endpoints:
     * POST /api/kg/taskReference - Create link
     * GET /api/kg/taskConcepts/{task_id} - Get concepts
     * POST /api/kg/validate-link - Validate connection
   - Storage:
     * Neo4j: Create relationships with validation
     * Memory: Update context and rules
     * Qdrant: Update semantic connections

## Agent Team Dynamics

1. **Agent Team Creation**
   - User Action: Create agent team
   - Components:
     * AgentTeamView.svelte
     * TeamValidation.svelte
   - Endpoints:
     * POST /api/chat/threads/{thread_id}/agent-team - Create team
     * GET /api/agents/graph - Get agent relationships
     * POST /api/agents/validate-team - Validate team
   - Storage:
     * Neo4j: Create agent relationships
     * Memory: Store team context and rules
   - Team Roles:
     * Coordinator agent
     * Domain specialists
     * Task executors
     * Validation agents

2. **Agent Communication**
   - User Action: Interact with agents
   - Components:
     * Chat.svelte
     * AgentDetailsPanel.svelte
     * TeamContext.svelte
   - Endpoints:
     * POST /api/chat/threads/{thread_id}/messages - Send message
     * GET /api/agents/{agent_id}/metrics - Get metrics
     * GET /api/agents/team-context - Get team context
   - Storage:
     * Qdrant: Store interactions and patterns
     * Memory: Track agent state and team dynamics
     * Neo4j: Update team relationships
   - Team Coordination:
     * Role-based responses
     * Task delegation
     * Knowledge sharing
     * Cross-domain coordination

## Cross-Domain Operations

1. **Domain Switching**
   - User Action: Switch context
   - Components:
     * Navigation.svelte
     * ThreadValidation.svelte
     * DomainContext.svelte
   - Endpoints:
     * POST /api/kg/crossDomain - Request access
     * GET /api/kg/domains - List domains
     * GET /api/kg/validate-access - Check access
   - Storage:
     * Neo4j: Validate access and relationships
     * Memory: Store validation state
     * Qdrant: Update context embeddings
   - Validation Rules:
     * Access level checks
     * Content validation
     * History tracking
     * Team permissions

2. **Knowledge Transfer**
   - User Action: Share across domains
   - Components:
     * Chat.svelte
     * GraphPanel.svelte
     * ValidationPanel.svelte
   - Endpoints:
     * POST /api/kg/taskReference - Link concepts
     * GET /api/kg/data - Get knowledge
     * POST /api/kg/validate-transfer - Validate transfer
   - Storage:
     * Neo4j: Create cross-domain links
     * Memory: Validate transfer rules
     * Qdrant: Update semantic connections
   - Transfer Rules:
     * Content validation
     * Access control
     * History tracking
     * Pattern matching

## Memory System Integration

The memory system actively maintains context and validation throughout all operations:

1. **Episodic Memory**
   - User interactions with validation
   - Agent responses with context
   - Task updates with state tracking
   - Storage: Qdrant (short-term)
   - Validation:
     * Content rules
     * Access patterns
     * Domain boundaries

2. **Semantic Memory**
   - Knowledge extraction with validation
   - Pattern recognition with rules
   - Domain relationships with boundaries
   - Storage: Neo4j (long-term)
   - Integration:
     * Cross-domain links
     * Knowledge graphs
     * Concept relationships

3. **Validation System**
   - Domain boundaries with rules
   - Access control with history
   - Cross-domain rules with patterns
   - Storage: Both layers
   - Rules:
     * Content validation
     * Access patterns
     * Transfer policies

4. **Consolidation Process**
   - Pattern detection with validation
   - Knowledge extraction with rules
   - Cleanup with boundaries
   - Storage: System-wide
   - Integration:
     * Memory cleanup
     * Pattern matching
     * Rule updates
