# System Architecture and Implementation Guide

## Core Architecture

The system integrates TinyTroupe's agent simulation with a domain-aware memory system:

1. **Agent Layer**
   - Specialized Agents:
     * DialogueAgent: Conversation management
     * EmotionAgent: Affective computing
     * BeliefAgent: Knowledge management
     * ResearchAgent: Information gathering
     * ReflectionAgent: Pattern recognition
     * DesireAgent: Goal tracking
     * TaskAgent: Execution management
   - Team Dynamics:
     * Hierarchical organization
     * Role-based coordination
     * Emotional awareness
     * Domain-specific teams

2. **Memory Layer**
   - Two-Layer Architecture:
     * Episodic (short-term):
       - Stores raw interactions and events
       - Automatic cleanup after consolidation
       - Configurable retention period
     * Semantic (long-term):
       - Stores consolidated knowledge
       - Maintains relationships and patterns
       - Permanent storage with versioning
   - Memory Types:
     ```python
     class MemoryType(str, Enum):
         TASK_CREATE = "task_create"
         TASK_UPDATE = "task_update"
         AGENT_INTERACTION = "agent_interaction"
         CROSS_DOMAIN_REQUEST = "cross_domain_request"
         THREAD_MESSAGE = "thread_message"
         CONSOLIDATION_EVENT = "consolidation_event"
     ```
   - Consolidation Rules:
     * Triggers:
       - Time-based (every 24 hours)
       - Volume-based (>1000 memories)
       - Importance-based (>0.8 score)
     * Process:
       ```python
       async def consolidate_memories():
           # 1. Get unconsolidated memories
           memories = await episodic.get_unconsolidated()
           
           # 2. Group by type and context
           grouped = group_by_context(memories)
           
           # 3. Extract patterns
           patterns = extract_patterns(grouped)
           
           # 4. Store in semantic layer
           await semantic.store_patterns(patterns)
           
           # 5. Mark as consolidated
           await episodic.mark_consolidated(memories)
       ```
     * Cleanup:
       - Remove consolidated memories after 7 days
       - Keep high importance (>0.8) for 30 days
       - Archive to cold storage if needed

3. **Domain Management**
   - Boundary System:
     * Domain Types:
       ```python
       class DomainType(str, Enum):
           PERSONAL = "personal"      # Personal workspace
           PROFESSIONAL = "professional"  # Work workspace
           SYSTEM = "system"         # Internal system domain
       ```
     * Access Control:
       ```python
       async def validate_domain_access(
           source_domain: str,
           target_domain: str,
           confidence_threshold: float = 0.8
       ) -> bool:
           # 1. Check direct access
           if await has_direct_access(source_domain, target_domain):
               return True
               
           # 2. Check cross-domain request
           request = await get_cross_domain_request(
               source_domain, target_domain
           )
           if request and request.status == "approved":
               return True
               
           # 3. Check confidence score
           score = await calculate_confidence_score(
               source_domain, target_domain
           )
           return score >= confidence_threshold
       ```
     * Cross-Domain Flow:
       1. Request submitted (PENDING)
       2. Automatic validation if confidence > 0.8
       3. Manual approval needed if 0.5 <= confidence <= 0.8
       4. Auto-reject if confidence < 0.5
       
   - Validation Rules:
     * Content Validation:
       - Schema validation against domain rules
       - Content classification check
       - Sensitive data detection
     * Access Patterns:
       ```python
       class AccessPattern:
           source_domain: str
           target_domain: str
           access_type: str  # read/write
           frequency: int    # access count
           success_rate: float  # 0-1
           last_access: datetime
       ```
     * Transfer Policies:
       - One-way transfers only
       - Rate limiting per domain pair
       - Audit logging required
       
   - Memory Integration:
     * Storage:
       - Domain boundaries in Neo4j
       - Access patterns in Memory
       - Transfer logs in Qdrant
     * Validation:
       - Cross-reference all storage layers
       - Check for inconsistencies
       - Maintain audit trail
     * Cleanup:
       - Archive old access patterns
       - Clean up expired requests
       - Update confidence scores

## Task Management Endpoints (/api/tasks)

### Task Search & Filtering (/api/tasks)
GET /search - Search tasks with filtering, sorting, and pagination
- Frontend: Used by TaskBoard.svelte for Kanban view filtering
- Storage:
  * Qdrant: 
    - Semantic search on task descriptions
    - Similarity matching for related tasks
    - Embedding-based filtering
  * Neo4j: 
    - Task metadata and relationships
    - Domain access validation
    - State transition history
  * Memory: 
    - Task update history
    - Cross-domain validations
    - Consolidation status

Query params:
- q: Text search query (Qdrant semantic search)
- status: Task states (Neo4j metadata filter)
- priority: Task priorities (Neo4j metadata filter)
- assignee: Task assignees (Neo4j relationship filter)
- from_date/to_date: Date range (Neo4j metadata filter)
- sort/order: Sorting options (Applied post-query)
- page/size: Pagination (Applied post-query)

### Task Board Operations (/api/tasks)
GET /board - Get tasks organized by state
- Frontend: Primary data source for TaskBoard.svelte
- Implementation (src/nia/nova/core/tasks_endpoints.py):
  * State Validation:
    ```python
    VALID_TRANSITIONS = {
        TaskState.PENDING: [TaskState.IN_PROGRESS],
        TaskState.IN_PROGRESS: [TaskState.BLOCKED, TaskState.COMPLETED],
        TaskState.BLOCKED: [TaskState.IN_PROGRESS],
        TaskState.COMPLETED: []  # No transitions from completed
    }
    ```
  * Blocking Rules:
    - Tasks can only be blocked if they have dependencies
    - Validated through Neo4j relationship check
    - Automatic state validation on dependency changes
  * Default Values:
    - status: PENDING if not provided
    - workspace: "personal" if not provided
    - capabilities: [] if not provided

- Storage Pattern:
  * Neo4j: 
    - Task nodes with state and relationships
    - Domain access validation
    - Team and agent relationships
    ```cypher
    MATCH (t:Concept)
    WHERE t.type = 'task'
    RETURN t.name as id, t.description as label, 
           t.status as status, t.domain as domain,
           t.metadata as metadata
    ```
  * Memory:
    - Task state history
    - Agent interactions
    - Cross-domain operations
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

### Task Graph Operations (/api/tasks/graph)
GET / - Get task graph
- Frontend: Used by GraphPanel.svelte
- Implementation:
  * Graph Traversal:
    ```python
    async def get_task_graph():
        # 1. Get root tasks (no parents)
        roots = await get_root_tasks()
        
        # 2. Build dependency tree
        graph = {
            "nodes": [],
            "edges": []
        }
        
        for root in roots:
            # Add node
            graph["nodes"].append(root)
            
            # Get children recursively
            children = await get_task_children(root.id)
            for child in children:
                graph["nodes"].append(child)
                graph["edges"].append({
                    "source": root.id,
                    "target": child.id,
                    "type": "depends_on"
                })
                
        return graph
    ```
  * Validation Rules:
    ```python
    async def validate_graph_update(update):
        # 1. Check for cycles
        if has_cycles(update.edges):
            raise ValidationError("Cycles detected")
            
        # 2. Validate domain boundaries
        domains = get_unique_domains(update.nodes)
        for d1, d2 in itertools.combinations(domains, 2):
            if not await validate_domain_access(d1, d2):
                raise ValidationError(
                    f"Invalid cross-domain access: {d1} -> {d2}"
                )
                
        # 3. Check state consistency
        for edge in update.edges:
            source = get_node(edge.source)
            target = get_node(edge.target)
            if not is_valid_dependency(source, target):
                raise ValidationError(
                    f"Invalid dependency: {source.id} -> {target.id}"
                )
    ```
  * Update Flow:
    1. Validate graph update
    2. Begin transaction
    3. Apply node changes
    4. Update relationships
    5. Validate final state
    6. Commit or rollback
- Response: 
  ```typescript
  {
    "analytics": {
      "nodes": Node[],  // Task nodes with metadata
      "edges": Edge[]   // Dependencies and relationships
    },
    "timestamp": string
  }
  ```

POST /addNode - Add task node
- Frontend: Called from TaskBoard.svelte
- Storage:
  * Neo4j:
    - Create task node
    - Set domain relationships
    - Establish team connections
  * Qdrant:
    - Store task embeddings
    - Index for semantic search
    - Link related content
  * Memory:
    - Store task creation event
    - Initialize validation state
    - Set domain context

POST /addDependency - Add task dependency
- Frontend: Used by TaskBoard.svelte for workflow management
- Storage:
  * Neo4j:
    - Create dependency relationship
    - Validate graph cycles
    - Track domain boundaries
  * Memory:
    - Store dependency context
    - Update task states
    - Track validation
- Body: 
  ```typescript
  interface TaskEdge {
    source: string;  // Source task ID
    target: string;  // Target task ID
    type: 'blocks' | 'depends_on' | 'related_to';
    metadata?: Record<string, unknown>;
  }
  ```
- Validation:
  * Verifies both tasks exist
  * Checks domain access
  * Prevents circular dependencies
- Response: 
  ```typescript
  {
    "success": true,
    "edgeId": string
  }
  ```

POST /updateNode - Update task node
- Frontend: Used by TaskBoard.svelte for state changes
- Storage:
  * Neo4j:
    - Update task metadata
    - Track state transitions
    - Maintain relationships
  * Memory:
    - Store update history
    - Validate transitions
    - Update context
- Body:
  ```typescript
  interface TaskUpdate {
    taskId: string;
    status?: TaskStatus;
    priority?: TaskPriority;
    assignees?: string[];
    metadata?: Record<string, unknown>;
  }
  ```
- Validation:
  * Validates state transitions
  * Checks domain access
  * Verifies assignee permissions
- Response:
  ```typescript
  {
    "success": true,
    "taskId": string
  }
  ```

### Task Management (/api/tasks)
POST / - Create task
- Frontend: Used by Chat.svelte and TaskBoard.svelte
- Implementation:
  * Default Values:
    ```python
    defaults = {
        "status": TaskState.PENDING,
        "workspace": "personal",
        "capabilities": [],
        "importance": 0.5,
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    }
    ```
  * Validation Rules:
    - Tasks can only be blocked if they have dependencies
    - Dependencies cannot form cycles
    - Domain access required for both source and target
  * Memory Types:
    ```python
    memory = Memory(
        content=task,
        type=MemoryType.TASK_CREATE,
        metadata={
            "task_id": task.id,
            "domain": task.domain,
            "importance": task.importance
        }
    )
    ```

- Storage Pattern:
  * Neo4j:
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
  * Qdrant:
    - Store task embeddings
    - Index for search
    - Store detailed content
  * Memory:
    - Create task memory
    - Set validation rules
    - Initialize domain context

GET /{task_id}/details - Get task details
- Frontend: Used by TaskDetailsPanel.svelte
- Storage:
  * Neo4j:
    - Task metadata
    - Relationships
    - Access rules
  * Qdrant:
    - Task content
    - Historical context
    - Related items
  * Memory:
    - Task history
    - Agent interactions
    - Validation state

### Task Components (/api/tasks)
POST /{task_id}/subtasks - Add subtask
- Frontend: Used by TaskDetailsPanel.svelte
- Storage:
  * Neo4j:
    - Create subtask relationship
    - Update task hierarchy
    - Maintain domain context
  * Memory:
    - Store subtask creation
    - Update task state
    - Validate domain access

PATCH /{task_id}/sub-tasks/{subtask_id} - Update subtask
- Frontend: Used by TaskDetailsPanel.svelte
- Storage:
  * Neo4j:
    - Update subtask state
    - Maintain relationships
    - Track changes
  * Memory:
    - Store state change
    - Update validation
    - Track agent actions

POST /{task_id}/comments - Add comment
- Frontend: Used by TaskDetailsPanel.svelte
- Storage:
  * Qdrant:
    - Store comment content
    - Create embeddings
    - Enable search
  * Neo4j:
    - Create comment relationship
    - Track authorship
    - Maintain context
  * Memory:
    - Store comment event
    - Update task context
    - Track interactions

## Chat Endpoints (/api/chat)

### Thread Operations
GET /threads - List all chat threads
- Frontend: Used by Chat.svelte
- Storage:
  * Neo4j: Thread relationships and metadata
  * Memory: Thread context and history
  * Qdrant: Message search and embeddings
- Layer Verification:
  * Check thread exists in Neo4j
  * Verify memory context
  * Validate Qdrant entries
- Validation:
  * Domain access checks
  * Thread visibility rules
  * API key validation
- Error Handling:
  * Layer mismatch recovery
  * Cleanup on failure
  * Retry with backoff

POST /threads/create - Create new thread
- Frontend: Used by Chat.svelte
- Storage Pattern:
  ```python
  # Direct storage pattern
  async def create_thread(thread: Thread):
    # 1. Layer verification
    await verify_layers_ready()
    
    # 2. Direct storage to avoid recursion
    await episodic.store_memory({
      content: thread,
      type: "thread",
      timestamp: utc_now()
    })
    
    # 3. Verify storage
    await verify_thread_stored(thread.id)
  ```
- Validation:
  * Schema validation
  * Domain access checks
  * Duplicate prevention
- Error Recovery:
  * Cleanup partial storage
  * Retry with backoff
  * Log verification failures

POST /threads/create - Create new thread
- Frontend: Used by Chat.svelte
- Storage:
  * Neo4j: Create thread relationships
  * Memory: Initialize thread context
  * Qdrant: Prepare for message embeddings
- Validation:
  * Title requirement
  * Metadata validation
  * Domain access checks

GET /threads/{thread_id} - Get thread details
- Frontend: Used by Chat.svelte
- Storage:
  * Neo4j: Thread relationships
  * Memory: Thread context
  * Qdrant: Message history
- Validation:
  * Thread existence
  * Access permissions
  * Domain boundaries

### Message Operations
GET /threads/{thread_id}/messages - Get thread messages
- Frontend: Used by Chat.svelte
- Implementation:
  * Message Consolidation:
    ```python
    async def consolidate_messages(thread_id: str):
        # 1. Get unconsolidated messages
        messages = await get_unconsolidated_messages(thread_id)
        
        # 2. Group by context and intent
        grouped = group_messages_by_context(messages)
        
        # 3. Extract key information
        for group in grouped:
            summary = await summarize_message_group(group)
            await store_summary(summary)
            
        # 4. Update thread state
        await update_thread_state(thread_id)
    ```
  * Thread Validation:
    ```python
    async def validate_thread_access(
        thread_id: str,
        user_id: str
    ) -> bool:
        # 1. Check direct access
        if await has_thread_access(user_id, thread_id):
            return True
            
        # 2. Check domain access
        thread = await get_thread(thread_id)
        user = await get_user(user_id)
        return await validate_domain_access(
            user.domain,
            thread.domain
        )
    ```
  * Storage Pattern:
    ```python
    # Store in Qdrant
    await qdrant.store_embeddings({
        "messages": messages,
        "thread_id": thread_id,
        "embeddings": embeddings
    })
    
    # Store in Neo4j
    await neo4j.execute_query("""
        MATCH (t:Thread {id: $thread_id})
        CREATE (m:Message {
            id: $message_id,
            content: $content,
            timestamp: datetime()
        })-[:IN_THREAD]->(t)
    """, {
        "thread_id": thread_id,
        "message_id": message.id,
        "content": message.content
    })
    
    # Store in Memory
    await memory.store({
        "type": "message",
        "content": message,
        "metadata": {
            "thread_id": thread_id,
            "importance": calculate_importance(message)
        }
    })
    ```

POST /threads/{thread_id}/messages - Add message
- Frontend: Used by Chat.svelte
- Storage:
  * Qdrant: Store message embeddings
  * Neo4j: Create message relationships
  * Memory: Store message context
- Validation:
  * Content requirement
  * Sender validation
  * Domain access

### Agent Integration
GET /threads/{thread_id}/agents - Get thread agents
- Frontend: Used by Chat.svelte
- Storage:
  * Neo4j: Agent relationships
  * Memory: Agent state
- Validation:
  * Thread access
  * Agent visibility

POST /threads/{thread_id}/agents - Add agent to thread
- Frontend: Used by Chat.svelte
- Storage:
  * Neo4j: Create agent relationships
  * Memory: Initialize agent state
- Validation:
  * Agent type validation
  * Domain access
  * Team composition rules

POST /threads/{thread_id}/agent-team - Create agent team
- Frontend: Used by Chat.svelte
- Storage:
  * Neo4j: Team relationships
  * Memory: Team context
- Validation:
  * Team composition
  * Domain access
  * Role assignments

## Swarm Design Endpoints (/api/design)

### Design Session Management
POST /api/design/sessions - Create new design session
- Frontend: Used by Chat.svelte in NOVA HQ channel
- Storage:
  * Neo4j: Design session metadata
  * Memory: Research findings and iterations
- Phases:
  * Research & Understanding
  * Planning & Design
  * Confirmation
  * Execution

GET /api/design/sessions/{id} - Get design session
- Frontend: Used by Chat.svelte
- Storage:
  * Neo4j: Session relationships
  * Memory: Current state and history
- Validation:
  * Session existence
  * Access permissions
  * Phase validation

PATCH /api/design/sessions/{id} - Update design session
- Frontend: Used by Chat.svelte
- Storage:
  * Neo4j: Update session state
  * Memory: Store iteration history
- Validation:
  * Phase transitions
  * Blueprint validation
  * Access control

### Research Phase
POST /api/design/sessions/{id}/research - Add research finding
- Frontend: Used by Chat.svelte
- Storage:
  * Qdrant: Store research content
  * Neo4j: Research relationships
  * Memory: Research context
- Validation:
  * Phase validation
  * Content requirements
  * Domain access

### Planning Phase
POST /api/design/sessions/{id}/blueprint - Update solution blueprint
- Frontend: Used by Chat.svelte
- Storage:
  * Neo4j: Blueprint structure
  * Memory: Planning iterations
- Validation:
  * Agent counts
  * Skill requirements
  * Resource limits

### Spawn Phase
POST /api/design/sessions/{id}/spawn - Spawn agent solution
- Frontend: Used by Chat.svelte
- Storage:
  * Neo4j: Create agent team
  * Memory: Initialize team state
- Validation:
  * Resource availability
  * Domain access
  * Team composition

## Nova Endpoints (/api/nova)

### Nova Chat
POST /ask - Ask Nova a question
- Frontend: Used by Chat.svelte in NOVA HQ channel
- Storage:
  * Qdrant:
    - Store conversation history
    - Create message embeddings
    - Enable semantic search
  * Neo4j:
    - Track thread relationships
    - Maintain domain context
    - Store agent interactions
  * Memory:
    - Store conversation memory
    - Track agent responses
    - Handle validation

### Nova Specialized Agents
Implementation: src/nia/nova/core/agent_endpoints.py

## Memory System Implementation

### Architecture Overview

The memory system implements a two-layer architecture with specialized storage patterns:

1. Storage Layers:
- Episodic Layer (Qdrant):
  * Purpose: Short-term memory for raw interactions and events
  * Implementation: Vector embeddings with semantic search
  * Features:
    - Automatic cleanup after consolidation
    - Configurable retention periods
    - Metadata indexing for filtering
    - Connection pooling with timeouts
  * Key Patterns:
    - Direct storage to prevent recursion
    - Memory pools for caching
    - Batch operations for efficiency

- Semantic Layer (Neo4j):
  * Purpose: Long-term knowledge storage
  * Implementation: Graph database for relationships
  * Features:
    - Domain boundaries and access rules
    - Permanent storage with versioning
    - Relationship-based queries
  * Key Patterns:
    - Bidirectional relationships
    - Domain context validation
    - Cross-domain transfer tracking

2. Integration Strategy:
- Direct Storage Pattern:
  * Prevents recursion issues
  * Maintains data consistency
  * Enables parallel operations
- Memory Pools:
  * Caches frequently accessed data
  * Reduces database load
  * Improves response times
- Circuit Breaker:
  * Prevents cascading failures
  * Handles recursive operations
  * Implements exponential backoff

3. Consolidation Process:
- Triggers:
  * Time-based: Every 5 minutes
  * Volume-based: 10+ unconsolidated memories
  * Importance-based: >= 0.8 score
- Pattern Extraction:
  * Concepts with validation
  * Bidirectional relationships
  * Domain-aware knowledge
- Storage Integration:
  * Atomic operations
  * Transaction management
  * Rollback capabilities

4. Error Handling:
- Retry Pattern:
  * Maximum 3 retries
  * Exponential backoff
  * Error categorization
- Recovery Strategy:
  * Partial storage cleanup
  * State reconciliation
  * Audit logging
- Circuit Breaking:
  * Prevents cascading failures
  * Resource protection
  * Graceful degradation

5. Security Implementation:
- Authentication:
  * API key validation
  * Key rotation support
  * Expiration handling
- Authorization:
  * Permission-based access
  * Domain validation
  * Rate limiting
- Audit:
  * Operation logging
  * Access tracking
  * Violation monitoring

6. Performance Optimizations:
- Connection Management:
  * Connection pooling
  * Automatic cleanup
  * Load balancing
- Caching Strategy:
  * Memory pools
  * LRU caching
  * Cache invalidation
- Operation Batching:
  * Bulk operations
  * Transaction batching
  * Background processing

2. Memory Types:
```python
class MemoryType(str, Enum):
    """Type of memory."""
    EPISODIC = "episodic"     # Short-term memory
    SEMANTIC = "semantic"      # Long-term memory
    PROCEDURAL = "procedural" # Action/skill memory
```

3. Storage Patterns:

Direct Storage Pattern (prevents recursion):
```python
async def store_memory(memory: Memory) -> bool:
    """Store a memory directly in the vector store."""
    try:
        # Generate ID if not present
        memory_id = getattr(memory, "id", str(uuid.uuid4()))
        
        # Create minimal metadata
        metadata = {
            "id": memory_id,
            "type": memory.type.value,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store directly in vector store
        return await self.store.store_vector(
            content=memory.content,
            metadata=metadata,
            layer="episodic"
        )
    except Exception as e:
        logger.error(f"Failed to store memory: {str(e)}")
        return False
```

Memory Pools for Caching:
```python
# Initialize memory pools
self._memory_pools = {
    "episodic": {},  # Cache for episodic memories
    "semantic": {}   # Cache for semantic knowledge
}
```

4. Consolidation Process:

Triggers:
- Time-based: Every 5 minutes
- Volume-based: When 10+ unconsolidated memories exist
- Importance-based: When memories with importance >= 0.8 exist

Pattern Extraction:
```python
async def extract_knowledge(self, memories: List[Memory]) -> Dict:
    knowledge = {
        "concepts": [],        # Extracted concepts
        "relationships": [],   # Extracted relationships
        "beliefs": [],        # Extracted beliefs
        "domain_context": {}, # Domain validation
        "cross_domain_transfers": []
    }
    
    for memory in memories:
        # 1. Validate domain context
        if not memory.domain_context:
            memory.domain_context = create_domain_context()
            
        # 2. Extract concepts with validation
        for concept in memory.concepts:
            concept_with_validation = {
                "name": concept.name,
                "type": concept.type,
                "validation": create_validation(),
                "domain_context": memory.domain_context,
                "is_consolidation": True
            }
            knowledge["concepts"].append(concept_with_validation)
            
        # 3. Extract relationships with bidirectional support
        for rel in memory.relationships:
            relationship = {
                "source": rel.source,
                "target": rel.target,
                "type": rel.type,
                "validation": create_validation(),
                "domain_context": memory.domain_context,
                "is_consolidation": True
            }
            knowledge["relationships"].append(relationship)
            
            # Add reverse relationship if bidirectional
            if rel.bidirectional:
                reverse_rel = create_reverse_relationship(rel)
                knowledge["relationships"].append(reverse_rel)
    
    return knowledge
```

5. Error Handling:

Retry Pattern:
```python
@retry_on_error(max_retries=3)
async def store_memory(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        required_fields = ["content", "type"]
        for field in required_fields:
            if field not in request:
                raise ValidationError(f"Request must include '{field}' field")
                
        # Store memory...
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))
```

Circuit Breaker Pattern:
```python
# Maximum recursion depth for operations
MAX_DEPTH = 2

async def run_query(self, query: str, params: Dict, _depth: int = 0) -> List[Dict]:
    """Run query with circuit breaker."""
    if _depth > MAX_DEPTH:
        raise RuntimeError("Maximum recursion depth exceeded")
        
    try:
        return await self._execute_query(query, params)
    except Exception as e:
        if _depth < MAX_DEPTH:
            return await self.run_query(query, params, _depth + 1)
        raise
```

6. Security:

Authentication:
- API key required in X-API-Key header
- Keys validated on every request
- Automatic expiration handling

Authorization:
- Write permission for mutations
- Read permission for queries
- Domain access validation
- Rate limiting per client

7. Integration Points:

Frontend Integration:
```typescript
// WebSocket connection for real-time updates
const ws = new WebSocket('ws://localhost:8000/api/ws/memory/client123');

// Type-safe message handling
ws.onmessage = (event) => {
    const data = JSON.parse(event.data) as WebSocketMessage;
    switch(data.type) {
        case 'memory_update':
            handleMemoryUpdate(data as MemoryUpdateMessage);
            break;
        case 'consolidation':
            handleConsolidation(data as MemoryConsolidationMessage);
            break;
    }
};
```

Agent Integration:
```python
# Store agent interaction in memory
await memory_system.store({
    "type": "agent_interaction",
    "content": {
        "agent_id": agent.id,
        "action": action,
        "result": result
    },
    "metadata": {
        "timestamp": datetime.now().isoformat(),
        "domain": agent.domain
    }
})
```

8. Performance Optimizations:

- Connection pooling for both Qdrant and Neo4j
- Memory pools for caching frequently accessed data
- Batch operations for consolidation
- Automatic cleanup of old memories
- Index optimization for common queries
```python
# Direct storage pattern (prevents recursion)
async def store_memory(memory: Memory):
    # 1. Store in Qdrant for vector search
    await qdrant.store_embeddings({
        "content": memory.content,
        "metadata": memory.metadata
    })
    
    # 2. Store in Neo4j for relationships
    await neo4j.execute_query("""
        CREATE (m:Memory {
            id: $id,
            type: $type,
            timestamp: datetime()
        })
    """, {
        "id": memory.id,
        "type": memory.type
    })
    
    # 3. Store in Memory system for context
    await memory_system.episodic.store({
        "type": memory.type,
        "content": memory.content,
        "metadata": memory.metadata
    })
```

### Pattern Extraction
The system uses a pattern-based approach to extract knowledge during consolidation:

1. Consolidation Triggers:
- Time-based: Every 5 minutes
- Volume-based: When 10+ unconsolidated memories exist
- Importance-based: When memories with importance >= 0.8 exist

2. Pattern Types:
```python
class ConsolidationPattern:
    """Base class for memory consolidation patterns."""
    def __init__(self, name: str, threshold: float = 0.7):
        self.name = name
        self.threshold = threshold
        
    async def extract_knowledge(self, memories: List[Memory]) -> Dict:
        """Extract knowledge using this pattern."""
        # Pattern-specific implementation
```

3. TinyTroupe Pattern:
- Extracts domain-aware knowledge:
  * Concepts with validation
  * Relationships with bidirectional support
  * Cross-domain transfers
  * Beliefs and metadata

4. Knowledge Extraction Flow:
```python
async def extract_knowledge(self, memories: List[Memory]) -> Dict:
    knowledge = {
        "concepts": [],        # Extracted concepts
        "relationships": [],   # Extracted relationships
        "beliefs": [],        # Extracted beliefs
        "domain_context": {}, # Domain validation
        "cross_domain_transfers": []
    }
    
    for memory in memories:
        # 1. Validate domain context
        if not memory.domain_context:
            memory.domain_context = create_domain_context()
            
        # 2. Extract concepts
        for concept in memory.concepts:
            concept_with_validation = {
                "name": concept.name,
                "type": concept.type,
                "validation": create_validation(),
                "domain_context": memory.domain_context,
                "is_consolidation": True
            }
            knowledge["concepts"].append(concept_with_validation)
            
        # 3. Extract relationships
        for rel in memory.relationships:
            relationship = {
                "source": rel.source,
                "target": rel.target,
                "type": rel.type,
                "validation": create_validation(),
                "domain_context": memory.domain_context,
                "is_consolidation": True
            }
            knowledge["relationships"].append(relationship)
            
            # Add reverse relationship if bidirectional
            if rel.bidirectional:
                reverse_rel = create_reverse_relationship(rel)
                knowledge["relationships"].append(reverse_rel)
    
    return knowledge
```

5. Validation Rules:
- Domain validation for all extracted knowledge
- Cross-domain transfer validation
- Confidence scoring
- Access control validation

6. Storage Integration:
- Concepts stored in Neo4j with validation
- Relationships stored with bidirectional support
- Domain context maintained across storage layers
- Cross-domain transfers tracked and validated
async def store_memory(memory: Memory):
    # 1. Store in Qdrant for vector search
    await qdrant.store_embeddings({
        "content": memory.content,
        "metadata": memory.metadata
    })
    
    # 2. Store in Neo4j for relationships
    await neo4j.execute_query("""
        CREATE (m:Memory {
            id: $id,
            type: $type,
            timestamp: datetime()
        })
    """, {
        "id": memory.id,
        "type": memory.type
    })
    
    # 3. Store in Memory system for context
    await memory_system.episodic.store({
        "type": memory.type,
        "content": memory.content,
        "metadata": memory.metadata
    })
```

3. Frontend Integration:
```typescript
// WebSocket connection for real-time updates
const ws = new WebSocket('ws://localhost:8000/api/ws/chat/client123');

// Type-safe message handling
ws.onmessage = (event) => {
    const data = JSON.parse(event.data) as WebSocketMessage;
    switch(data.type) {
        case 'memory_update':
            handleMemoryUpdate(data as MemoryUpdateMessage);
            break;
        case 'consolidation':
            handleConsolidation(data as MemoryConsolidationMessage);
            break;
    }
};

// Centralized state management
const appStore = {
    workspace: writable(null),
    domain: writable(null),
    socket: createWebSocket(),
    handlers: {
        onMemoryUpdate,
        onConsolidation
    }
};
```

#### Agent Configuration System
Implementation: src/nia/config/agent_config.py

1. Skills Validation:
```python
# Pre-defined skills set
PREDEFINED_SKILLS = {
    "web_scraping",
    "literature_review",
    "data_analysis",
    "market_research",
    "report_generation",
    "sentiment_analysis",
    "code_execution",
    "database_querying",
    "api_interaction",
    "time_of_day_logic",
    "markdown_strategy"
}

# Skills validation in config
def validate_agent_config(config: Dict[str, Any]) -> bool:
    # Validate skills
    if "skills" in config:
        if not isinstance(config["skills"], list):
            raise ValueError("Skills must be a list.")
        for skill in config["skills"]:
            if skill not in PREDEFINED_SKILLS:
                print(f"Warning: Skill '{skill}' not in predefined skills")
    return True
```

2. Knowledge Vertical Validation:
```python
# Knowledge verticals enum
class KnowledgeVertical(str, Enum):
    RETAIL = "retail"
    BUSINESS = "business"
    PSYCHOLOGY = "psychology"
    TECHNOLOGY = "technology"
    BACKEND = "backend"
    DATABASE = "database"
    GENERAL = "general"

# Vertical validation in domain config
def validate_domain_config(config: Dict[str, Any]) -> bool:
    # Validate knowledge vertical if specified
    if ("knowledge_vertical" in config and 
        config["knowledge_vertical"] and 
        config["knowledge_vertical"] not in KNOWLEDGE_VERTICALS):
        raise ValueError(
            f"Invalid vertical: {config['knowledge_vertical']}. "
            f"Must be one of {KNOWLEDGE_VERTICALS}"
        )
    return True
```

3. Required Configuration Fields:
```python
REQUIRED_CONFIG_FIELDS = {
    "name",           # Agent identifier
    "agent_type",     # Type from AGENT_RESPONSIBILITIES
    "domain",         # Primary domain (personal/professional)
    "knowledge_vertical",  # Optional specialized domain
    "skills"          # List of agent capabilities
}
```

4. Domain Configuration:
```python
# Base domains required for all agents
BASE_DOMAINS = {
    "PERSONAL",
    "PROFESSIONAL"
}

# Knowledge verticals for specialized domains
KNOWLEDGE_VERTICALS = {
    "RETAIL",
    "BUSINESS", 
    "PSYCHOLOGY",
    "TECHNOLOGY",
    "BACKEND",
    "DATABASE",
    "GENERAL"
}
```

5. Skills and Capabilities:
```python
# Pre-defined skills
PREDEFINED_SKILLS = {
    "web_scraping",
    "literature_review",
    "data_analysis",
    "market_research",
    "report_generation",
    "sentiment_analysis",
    "code_execution",
    "database_querying",
    "api_interaction",
    "time_of_day_logic",
    "markdown_strategy"
}

# Sub-task types
SUB_TASK_TYPES = {
    "data_parsing",
    "data_analysis",
    "report_generation",
    "validation_task",
    "research_task"
}
```

4. Configuration Validation:
```python
def validate_agent_config(config: Dict[str, Any]) -> bool:
    # Check required fields
    missing_fields = REQUIRED_CONFIG_FIELDS - config.keys()
    if missing_fields:
        raise ValueError(f"Missing fields: {missing_fields}")
        
    # Validate agent type
    agent_type = config.get("agent_type")
    if agent_type not in AGENT_RESPONSIBILITIES:
        raise ValueError(f"Invalid type: {agent_type}")
        
    # Validate domain
    validate_domain_config(config)
    
    # Validate skills
    if "skills" in config:
        for skill in config["skills"]:
            if skill not in PREDEFINED_SKILLS:
                print(f"Warning: Skill '{skill}' not predefined")
                
    return True
```

5. Example Configuration:
```python
example_agent_config = {
    "name": "AdvancedDataAnalyst",
    "agent_type": "analytics",
    "domain": "professional",
    "knowledge_vertical": "BUSINESS",
    "skills": [
        "data_analysis",
        "report_generation",
        "visualization",
        "database_querying"
    ],
    "completion_criteria": "Final report generated",
    "potential_sub_tasks": [
        {
            "type": "data_parsing",
            "responsible_agent_types": ["parsing"]
        }
    ],
    "error_handling_config": {
        "max_retries": 3,
        "escalation_policy": "notify_orchestration_agent"
    },
    "preferred_swarm_architecture": "parallel"
}
```

# Configuration is merged in order:
# base_config <- type_config <- instance_config
async def get_agent_config(agent_id: str) -> Dict:
    # 1. Get base config
    config = base_config.copy()
    
    # 2. Apply type config
    agent = await get_agent(agent_id)
    if agent.type in type_configs:
        config.update(type_configs[agent.type])
        
    # 3. Apply instance config
    config.update(agent.config)
    
    return config
```

#### Agent Initialization Flow
```python
async def initialize_agent(agent_type: str, config: Dict):
    # 1. Create agent instance
    agent_id = str(uuid.uuid4())
    
    # 2. Load configurations
    base = await load_base_config()
    type_config = await load_type_config(agent_type)
    merged_config = {**base, **type_config, **config}
    
    # 3. Initialize storage
    await neo4j.execute_query("""
        CREATE (a:Agent {
            id: $id,
            type: $type,
            config: $config,
            created_at: datetime()
        })
    """, {
        "id": agent_id,
        "type": agent_type,
        "config": merged_config
    })
    
    # 4. Setup memory context
    await memory.store({
        "type": "agent_created",
        "agent_id": agent_id,
        "config": merged_config
    })
    
    # 5. Initialize capabilities
    for capability in merged_config.get("capabilities", []):
        await setup_capability(agent_id, capability)
        
    return agent_id
```

#### Agent Default Values
```python
# Default values from implementation
agent = {
    'agent_id': str(uuid.uuid4()),  # Generated if not provided
    'name': 'Unknown Agent',        # Default name
    'type': 'agent',               # Default type
    'status': 'active',            # Default status
    'capabilities': [],            # Empty capabilities list
    'workspace': 'personal',       # Default workspace
    'metadata': {
        'capabilities': [],
        'confidence': 0.8,         # Default confidence
        'specialization': agent['type']  # Defaults to agent type
    }
}
```

#### Agent Storage Pattern
Neo4j Query:
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

#### Agent Metrics
- Stored in episodic memory
- Tracked metrics:
  * response_time: Average response time
  * tasks_completed: Number of completed tasks
  * success_rate: Task success percentage
  * uptime: Agent uptime duration
  * last_active: Last activity timestamp

#### Agent Interactions
- Latest 100 interactions stored
- Sorted by timestamp descending
- Stored in episodic memory with:
  * type: "agent_interaction"
  * agent_id: Agent identifier
  * timestamp: Interaction time

GET /agents/specialized/{domain} - Get domain specialists
- Frontend: Used by AgentSelector.svelte
- Storage:
  * Neo4j:
    - Query specialized agents
    - Check domain access
    - Validate availability
  * Memory:
    - Load agent context
    - Check current tasks
    - Track performance

POST /agents/team/create - Create specialized team
- Frontend: Used by Chat.svelte for team creation
- Storage:
  * Neo4j:
    - Create team structure
    - Set domain boundaries
    - Track team composition
  * Memory:
    - Store team context
    - Initialize team state
    - Set validation rules

### Nova Domain Operations
POST /domain/validate - Validate domain access
- Frontend: Used by Chat.svelte and Navigation.svelte
- Storage:
  * Neo4j:
    - Check domain permissions
    - Track access history
    - Validate relationships
  * Memory:
    - Store validation state
    - Track access patterns
    - Monitor violations

POST /domain/crossover - Request domain crossover
- Frontend: Used by Chat.svelte for cross-domain operations
- Storage:
  * Neo4j:
    - Create cross-domain links
    - Track request history
    - Maintain boundaries
  * Memory:
    - Store request context
    - Track approval state
    - Monitor patterns

## Graph Endpoints (/api/graph)

### Knowledge Graph Operations
GET /data - Get graph data
- Frontend: Used by GraphPanel.svelte
- Storage:
  * Neo4j:
    - Graph structure
    - Domain relationships
    - Access rules
  * Memory:
    - Node metadata
    - Validation state
    - Domain context

## Knowledge Graph Endpoints (/api/kg)
Implementation: src/nia/nova/core/knowledge_endpoints.py

### Domain Operations
POST /crossDomain - Request cross-domain access
- Frontend: Used by Chat.svelte
- Implementation:
  ```python
  # Store cross-domain request in episodic memory
  memory = Memory(
      content={
          "source_domain": source_domain,
          "target_domain": target_domain,
          "reason": request.get("reason"),
          "status": "pending"
      },
      type=MemoryType.CROSS_DOMAIN_REQUEST,
      metadata={
          "timestamp": datetime.now().isoformat(),
          "importance": 0.8
      }
  )
  await memory_system.episodic.store(memory)
  
  # Create cross-domain relationship
  await memory_system.semantic.store_knowledge({
      "relationships": [{
          "from": f"domain:{source_domain}",
          "to": f"domain:{target_domain}",
          "type": "CROSS_DOMAIN_ACCESS",
          "status": "pending",
          "timestamp": datetime.now().isoformat()
      }]
  })
  ```
- Storage Pattern:
  * Neo4j:
    ```cypher
    MATCH (d:Domain)
    RETURN d.name as name, d.type as type, 
           d.description as description
    ```
  * Memory:
    - Cross-domain request history
    - Access validation state
    - Request metadata

GET /domains - List domains
- Frontend: Used by Navigation.svelte
- Storage:
  * Neo4j:
    - Domain nodes
    - Relationships
    - Access rules
  * Memory:
    - Domain metadata
    - Validation state
    - Usage patterns

### Task Knowledge Integration
POST /taskReference - Link task to concept
- Frontend: Used by TaskDetailsPanel.svelte
- Storage:
  * Neo4j:
    - Create relationships
    - Update domain context
    - Track connections
  * Memory:
    - Update task metadata
    - Validate domain access
    - Track changes

GET /data - Get knowledge graph
- Frontend: Used by GraphPanel.svelte
- Storage:
  * Neo4j:
    - Graph structure
    - Domain boundaries
    - Access rules
  * Memory:
    - Node metadata
    - Validation state
    - Context tracking

## WebSocket Integration (/api/ws)
Implementation: src/nia/nova/core/websocket_endpoints.py

### Connection Flow
1. Server Initialization:
```python
async def initialize_websocket_server():
    """Initialize the WebSocket server if not already initialized."""
    global _websocket_server
    async with _init_lock:
        if _websocket_server is None:
            _websocket_server = await WebSocketServer.create(get_memory_system)
```

2. Connection Types:
```typescript
type ConnectionType = 'chat' | 'tasks' | 'agents' | 'graph';
```

3. Connection Handling:
- API Key Validation:
  * Required in connection headers
  * Invalid keys result in code 4000 disconnect
  * Expiration triggers automatic disconnect
- Error Handling:
  * Runtime errors: code 1011
  * Connection type validation
  * Graceful disconnect handling
- Memory Integration:
  * Background memory updates
  * Broadcast to connected clients
  * Automatic reconnection

### Base Message Structure
```typescript
interface WebSocketMessageBase {
    type: WebSocketEventType;
    timestamp: string;
    metadata?: {
        source?: string;
        domain?: string;
        importance?: number;
    };
}
```

### Connection Handlers
```python
handlers = {
    "chat": server.handle_chat_connection,
    "tasks": server.handle_task_connection,
    "agents": server.handle_agent_connection,
    "graph": server.handle_graph_connection
}
```

### Chat WebSocket (/api/ws/chat/{client_id})
- Frontend: Used by Chat.svelte
- Message Types:
  * Thread Updates:
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
    ```
  * New Messages:
    ```typescript
    interface ChatMessage {
        type: 'message';
        content: string;
        thread_id: string;
        sender_type: string;
        sender_id: string;
    }
    ```
  * Typing Indicators:
    ```typescript
    interface TypingIndicator {
        type: 'typing';
        user_id: string;
        thread_id: string;
        is_typing: boolean;
    }
    ```

### Tasks WebSocket (/api/ws/tasks/{client_id})
- Frontend: Used by TaskBoard.svelte
- Message Types:
  * Task Updates:
    ```typescript
    interface TaskUpdateMessage {
        type: 'task_update';
        task_id: string;
        changes: Record<string, unknown>;
    }
    ```
  * Progress Updates:
    ```typescript
    interface TaskProgressMessage {
        type: 'task_progress';
        task_id: string;
        progress: number;
        status: string;
        message?: string;
    }
    ```
  * Assignment Changes:
    ```typescript
    interface TaskAssignmentMessage {
        type: 'task_assignment';
        task_id: string;
        assignee: string;
        previous_assignee?: string;
    }
    ```

### Agents WebSocket (/api/ws/agents/{client_id})
- Frontend: Used by AgentPanel.svelte
- Message Types:
  * Status Updates:
    ```typescript
    interface AgentStatusMessage {
        type: 'agent_status';
        agent_id: string;
        status: string;
        metrics?: {
            response_time?: number;
            tasks_completed?: number;
            success_rate?: number;
            uptime?: number;
        };
    }
    ```
  * Capability Updates:
    ```typescript
    interface AgentCapabilityMessage {
        type: 'agent_capability';
        agent_id: string;
        capabilities: Array<{
            name: string;
            confidence: number;
        }>;
    }
    ```
  * Team Updates:
    ```typescript
    interface AgentTeamCreatedMessage {
        type: 'agent_team_created';
        data: Array<{
            id: string;
            name: string;
            type: 'user' | 'agent';
            agentType?: string;
            role?: string;
            workspace: 'personal' | 'professional';
            domain?: string;
            metadata?: {
                capabilities?: string[];
                confidence?: number;
                specialization?: string;
            };
        }>;
    }
    ```

### Graph WebSocket (/api/ws/graph/{client_id})
- Frontend: Used by GraphPanel.svelte
- Message Types:
  * Graph Updates:
    ```typescript
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

### Memory WebSocket Updates
- Message Types:
  * Memory Updates:
    ```typescript
    interface MemoryUpdateMessage {
        type: 'memory_update';
        memory_id: string;
        sync_state: {
            vector_stored: boolean;
            neo4j_stored: boolean;
            last_sync: string | null;
        };
    }
    ```
  * Consolidation Events:
    ```typescript
    interface MemoryConsolidationMessage {
        type: 'memory_consolidation';
        memory_id: string;
        consolidated: boolean;
        cleanup_performed: boolean;
        timestamp: string;
    }
    ```

## TinyTroupe Integration (/api/tinytroupe)

### Emotional State
GET /emotions/{agent_id} - Get agent emotional state
- Frontend: Used by Chat.svelte and AgentPanel.svelte
- Storage:
  * Memory: Emotional context and history
  * Neo4j: Agent relationships
  * Qdrant: Interaction patterns

POST /emotions/update - Update emotional state
- Frontend: Used by Chat.svelte
- Storage:
  * Memory: Store new emotional state
  * Neo4j: Update relationships
  * Qdrant: Update patterns

### Team Dynamics
GET /team/{team_id}/emotional-state - Get team emotional state
- Frontend: Used by TeamView.svelte
- Storage:
  * Memory: Team emotional context
  * Neo4j: Team relationships
  * Qdrant: Team patterns

## Memory Management (/api/memory)

### Consolidation
POST /consolidate - Trigger memory consolidation
- Frontend: Used by system tasks
- Storage:
  * Memory: Consolidation state
  * Qdrant: Update embeddings
  * Neo4j: Update relationships

GET /consolidation/status - Get consolidation status
- Frontend: Used by system monitoring
- Storage:
  * Memory: Track progress
  * Neo4j: Validation state

### Validation
POST /validate/schema - Validate schema
- Frontend: Used across components
- Storage:
  * Memory: Validation results
  * Neo4j: Schema state

POST /validate/domain - Validate domain access
- Frontend: Used for cross-domain operations
- Storage:
  * Memory: Access patterns
  * Neo4j: Domain boundaries

## Analytics (/api/analytics)

### System Metrics
GET /metrics/performance - Get system performance
- Frontend: Used by monitoring dashboard
- Storage:
  * Memory: Performance data
  * Neo4j: System state
  * Qdrant: Query patterns

GET /metrics/validation - Get validation metrics
- Frontend: Used by monitoring dashboard
- Storage:
  * Memory: Validation stats
  * Neo4j: Error patterns

### User Analytics
GET /analytics/user/{user_id} - Get user analytics
- Frontend: Used by user dashboard
- Storage:
  * Memory: User patterns
  * Neo4j: User relationships
  * Qdrant: User interactions

## Authentication & Authorization

All endpoints require:
- Valid API key in X-API-Key header
- Write permission for mutations
- Read permission for queries
- Domain access validation
- Rate limiting

Domain validation includes:
- Cross-domain access rules
- Validation confidence scores
