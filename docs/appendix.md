# NIA Implementation Appendix

This document serves as a technical reference with detailed implementation examples for the NIA system. It complements the main README by providing specific code patterns and examples.

## Table of Contents
1. [User Initialization System](#user-initialization-system)
2. [Template Storage Examples](#template-storage-examples)
3. [Memory System Implementation](#memory-system-implementation)
4. [Agent Implementation Examples](#agent-implementation-examples)
5. [Testing Framework Examples](#testing-framework-examples)
6. [Task Management Examples](#task-management-examples)
7. [Integration Examples](#integration-examples)
8. [Core System Integration](#core-system-integration)

[Previous content remains unchanged...]

## Core System Integration

### Chat System & Memory Integration

The chat system endpoints integrate with our core memory systems in the following ways:

1. Qdrant (Vector Store) Integration:
   - Stores ephemeral chat messages and partial logs
   - Enables message search functionality via embeddings
   - Handles chain-of-thought logs from agents
   - Enables semantic search across threads
   ```python
class ChatMemorySystem:
    def __init__(self, vector_store, graph_store, coordination_agent):
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.coordination_agent = coordination_agent
        
    async def store_message(self, message: Dict):
        """Store chat message in vector store."""
        embedding = await self.get_embedding(message["content"])
        message_id = await self.vector_store.store(
            collection="chat_messages",
            vector=embedding,
            payload={
                "thread_id": message["thread_id"],
                "content": message["content"],
                "type": message["type"],
                "timestamp": message["timestamp"],
                "domain": message.get("domain"),
                "agent_thoughts": message.get("agent_thoughts", []),
                "chain_of_thought": message.get("chain_of_thought", [])
            }
        )
        
        # Store thread metadata in Neo4j if new thread
        if message.get("is_thread_start"):
            await self.graph_store.execute("""
            CREATE (t:Thread {
                id: $thread_id,
                type: $type,
                domain: $domain,
                created_at: datetime()
            })
            """, {
                "thread_id": message["thread_id"],
                "type": message.get("type", "main"),
                "domain": message.get("domain")
            })
            
        # Notify coordination agent
        await self.coordination_agent.handle_message(message)
        
        return message_id
           
       async def search_messages(self, query: str, thread_id: str):
           """Search messages in thread."""
           query_embedding = await self.get_embedding(query)
           return await self.store.search(
               collection="chat_messages",
               vector=query_embedding,
               filter={
                   "thread_id": thread_id
               }
           )
   ```

2. Neo4j (Graph Store) Integration:
   - Stores thread metadata and relationships
   - Maintains thread-to-node connections
   - Tracks domain references
   - Handles thread hierarchies (main/sub-threads)
   ```python
   class ThreadGraphSystem:
       def __init__(self, neo4j_store):
           self.store = neo4j_store
           
       async def create_thread(self, thread_data: Dict):
           """Create thread node with relationships."""
           query = """
           CREATE (t:Thread {
               id: $thread_id,
               type: $type,
               created_at: datetime(),
               domain: $domain
           })
           """
           if thread_data.get("parent_id"):
               query += """
               WITH t
               MATCH (p:Thread {id: $parent_id})
               CREATE (t)-[:SUB_THREAD_OF]->(p)
               """
           await self.store.execute(query, thread_data)
           
       async def link_thread_to_node(self, thread_id: str, node_id: str):
           """Create relationship between thread and graph node."""
           query = """
           MATCH (t:Thread {id: $thread_id})
           MATCH (n {id: $node_id})
           CREATE (t)-[:REFERENCES]->(n)
           """
           await self.store.execute(query, {
               "thread_id": thread_id,
               "node_id": node_id
           })
   ```

### Graph System & DAG Integration

The graph visualization endpoints integrate with our task execution system:

1. Neo4j (Graph Store) Integration:
   - Stores all node types (brand, policy, task)
   - Maintains node relationships and properties
   - Handles domain labeling
   - Tracks task dependencies
   ```python
class GraphVisualizationSystem:
    def __init__(self, neo4j_store, dag_manager):
        self.store = neo4j_store
        self.dag = dag_manager
        self.layout_algorithms = {
            "force": self.force_layout,
            "circular": self.circular_layout,
            "hierarchical": self.hierarchical_layout,
            "grid": self.grid_layout
        }
        
    async def get_node_details(self, node_id: str):
        """Get node details with type-specific information."""
        # Get node type first
        type_query = """
        MATCH (n {id: $node_id})
        RETURN labels(n)[0] as type
        """
        node_type = await self.store.execute(type_query, {"node_id": node_id})
        node_type = node_type[0]["type"] if node_type else None
        
        # Get type-specific details
        if node_type == "Brand":
            query = """
            MATCH (n:Brand {id: $node_id})
            RETURN n {
                .id,
                .name,
                .inventory_levels,
                .discount_rules,
                .last_updated,
                domain: 'professional'
            }
            """
        elif node_type == "Task":
            query = """
            MATCH (n:Task {id: $node_id})
            OPTIONAL MATCH (n)-[:HAS_THREAD]->(t:Thread)
            RETURN n {
                .id,
                .name,
                .status,
                .agent_logs,
                thread_id: t.id,
                domain: 'professional'
            }
            """
        elif node_type == "Policy":
            query = """
            MATCH (n:Policy {id: $node_id})
            RETURN n {
                .id,
                .name,
                .rules,
                .affected_brands,
                .last_updated,
                domain: 'professional'
            }
            """
        else:
            query = """
            MATCH (n {id: $node_id})
            RETURN n {.*}
            """
            
        result = await self.store.execute(query, {"node_id": node_id})
        return result[0] if result else None
        
    async def get_layout(self, algorithm: str, nodes: List[Dict]):
        """Get graph layout positions."""
        if algorithm not in self.layout_algorithms:
            raise ValueError(f"Unknown layout algorithm: {algorithm}")
            
        return await self.layout_algorithms[algorithm](nodes)
        
    async def get_performance_metrics(self, node_ids: List[str]):
        """Get performance metrics for visualization."""
        metrics = {
            "node_metrics": {},
            "edge_metrics": {},
            "system_metrics": {}
        }
        
        # Get node metrics
        for node_id in node_ids:
            node = await self.dag.get_task(node_id)
            if node:
                metrics["node_metrics"][node_id] = {
                    "execution_time": node.get_execution_time(),
                    "resource_usage": node.get_resource_usage(),
                    "error_rates": node.get_error_rates()
                }
                
        # Get system metrics
        metrics["system_metrics"] = {
            "total_nodes": await self.store.count_nodes(),
            "total_edges": await self.store.count_edges(),
            "memory_usage": await self.dag.get_memory_usage(),
            "cpu_usage": await self.dag.get_cpu_usage()
        }
        
        return metrics
           
       async def get_task_dependencies(self, task_id: str):
           """Get task dependencies for visualization."""
           query = """
           MATCH (t:Task {id: $task_id})
           MATCH (t)-[:DEPENDS_ON*]->(d)
           RETURN d
           """
           return await self.store.execute(query, {"task_id": task_id})
   ```

2. Task DAG Integration:
   - Visualized through execution flow endpoints
   - Shows real-time task execution state
   - Displays agent dependencies
   - Tracks task completion status
   ```python
   class TaskGraphSystem:
       def __init__(self, dag_manager):
           self.dag = dag_manager
           
       async def get_execution_flow(self, task_id: str):
           """Get task execution flow for visualization."""
           task = self.dag.get_task(task_id)
           return {
               "nodes": [
                   {
                       "id": t.id,
                       "type": "task",
                       "status": t.status,
                       "progress": t.progress
                   }
                   for t in task.get_all_subtasks()
               ],
               "edges": [
                   {
                       "from": e.source.id,
                       "to": e.target.id,
                       "type": e.type
                   }
                   for e in task.get_all_dependencies()
               ]
           }
           
       async def get_performance_metrics(self, task_id: str):
           """Get performance metrics for visualization."""
           task = self.dag.get_task(task_id)
           return {
               "execution_time": task.get_execution_time(),
               "resource_usage": task.get_resource_usage(),
               "error_rates": task.get_error_rates()
           }
   ```

### WebSocket Integration

The WebSocket system provides real-time updates with proper type safety and validation:

```typescript
// WebSocket message types with Zod validation
const TaskUpdateMessageSchema = z.object({
  type: z.literal('task_update'),
  taskId: z.string(),
  status: z.enum(['pending', 'running', 'completed', 'failed']),
  progress: z.number().optional(),
  error: z.string().optional()
});

// WebSocket client with type safety
class WebSocketClient {
  private socket: WebSocket;
  private messageHandlers: Map<string, (data: any) => void>;

  constructor(url: string) {
    this.socket = new WebSocket(url);
    this.messageHandlers = new Map();
    
    this.socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      const handler = this.messageHandlers.get(message.type);
      if (handler) {
        // Validate message before handling
        try {
          const validatedData = TaskUpdateMessageSchema.parse(message);
          handler(validatedData);
        } catch (error) {
          console.error('Invalid message format:', error);
        }
      }
    };
  }

  onTaskUpdate(handler: (data: z.infer<typeof TaskUpdateMessageSchema>) => void) {
    this.messageHandlers.set('task_update', handler);
  }

  // Proper cleanup
  disconnect() {
    this.socket.close();
    this.messageHandlers.clear();
  }
}
```

### Memory System Optimizations

Recent optimizations to improve performance and reliability:

```python
class OptimizedMemorySystem:
    def __init__(self):
        # Connection pooling
        self.vector_store = VectorStore(
            connection_pool_size=10,
            max_retries=3,
            timeout=30
        )
        
        # Memory pools for caching
        self.memory_pools = {
            'recent': deque(maxlen=100),
            'frequent': LRUCache(1000)
        }
        
        # Minimal serialization flags
        self.serialization_mode = 'minimal'
        
    async def store_memory(self, content: Dict):
        """Store with optimized serialization."""
        if self.serialization_mode == 'minimal':
            # Strip unnecessary fields
            content = {
                'id': content['id'],
                'type': content['type'],
                'core_data': content['core_data']
            }
            
        # Use connection pool
        async with self.vector_store.connection() as conn:
            await conn.store(content)
            
        # Update memory pools
        self.memory_pools['recent'].append(content['id'])
        self.memory_pools['frequent'].put(content['id'], time.time())
        
    async def cleanup(self):
        """Proper resource cleanup."""
        await self.vector_store.close_pools()
        self.memory_pools['recent'].clear()
        self.memory_pools['frequent'].clear()
```

### Data Flow Example

When a user creates a task in chat, the following data flow occurs:

```python
async def handle_task_creation(message: str, thread_id: str):
    # 1. Store message in Qdrant
    message_id = await chat_memory.store_message({
        "content": message,
        "thread_id": thread_id,
        "type": "user",
        "timestamp": datetime.now().isoformat()
    })
    
    # 2. Create task node in Neo4j
    task_id = await graph_store.create_task_node({
        "description": message,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    })
    
    # 3. Link thread to task in Neo4j
    await thread_graph.link_thread_to_node(thread_id, task_id)
    
    # 4. Add task to execution DAG
    task = await dag_manager.create_task(task_id)
    
    # 5. Send real-time updates via WebSocket
    await websocket.broadcast_update({
        "type": "task_created",
        "task_id": task_id,
        "thread_id": thread_id
    })
    
    return task_id
```

This integration ensures:
- Consistent domain boundaries through:
  * Channels handling structural aspects
  * Threads handling messaging
- Real-time visualization updates via WebSocket
- Efficient data access through:
  * Connection pooling
  * Memory pools
  * Minimal serialization
- Clear separation of concerns:
  * Qdrant: Message content and search
  * Neo4j: Relationships and metadata
  * DAG: Execution state and flow
- Type safety through:
  * Zod validation schemas
  * TypeScript interfaces
  * Runtime validation

[Previous content remains unchanged...]
