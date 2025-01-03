# NIA Implementation Appendix

This document serves as a technical reference with detailed implementation examples for the NIA system. It complements the main README by providing specific code patterns and examples.

## Table of Contents
1. [Memory System Implementation](#memory-system-implementation)
2. [Agent Implementation Examples](#agent-implementation-examples)
3. [Testing Framework Examples](#testing-framework-examples)
4. [Task Management Examples](#task-management-examples)
5. [Integration Examples](#integration-examples)

## Memory System Implementation

### Chunking System
```python
class ChunkingSystem:
    """Implements text chunking for episodic memory."""
    def __init__(self, chunk_size: int = 512):
        self.chunk_size = chunk_size
        
    def chunk_text(self, text: str) -> List[Dict]:
        """Split text into chunks with metadata."""
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunk = text[i:i + self.chunk_size]
            chunks.append({
                "content": chunk,
                "metadata": {
                    "start_idx": i,
                    "length": len(chunk),
                    "timestamp": datetime.now().isoformat()
                }
            })
        return chunks
```

### Two-Layer Memory System
```python
class TwoLayerMemorySystem:
    """Implements episodic and semantic memory layers."""
    def __init__(self, neo4j_store, vector_store):
        self.episodic = EpisodicLayer(vector_store)
        self.semantic = SemanticLayer(neo4j_store)
        self.consolidation_manager = ConsolidationManager(
            self.episodic,
            self.semantic
        )
        
    async def store_with_domain(self, content: str, domain: str):
        """Store content with domain labeling."""
        # Store in episodic memory first
        chunk_id = await self.episodic.store(content)
        
        # If content meets criteria, consolidate to semantic memory
        if self.should_consolidate(content):
            await self.semantic.store({
                "content": content,
                "domain": domain,
                "source_chunk": chunk_id
            })
            
    async def query_by_domain(self, query: str, domain: str):
        """Query memory within a specific domain."""
        semantic_results = await self.semantic.query(
            query, 
            filters={"domain": domain}
        )
        episodic_results = await self.episodic.query(query)
        
        return {
            "semantic": semantic_results,
            "episodic": episodic_results
        }
```

### Memory Consolidation
```python
class ConsolidationManager:
    """Manages memory consolidation process."""
    def __init__(self, episodic_layer, semantic_layer):
        self.episodic = episodic_layer
        self.semantic = semantic_layer
        self.patterns = self.load_consolidation_patterns()
        
    async def consolidate_chunks(self, chunks: List[Dict]):
        """Consolidate chunks into semantic memory."""
        for chunk in chunks:
            # Extract patterns
            patterns = self.extract_patterns(chunk["content"])
            
            # Create semantic nodes
            for pattern in patterns:
                await self.semantic.create_node(
                    label=pattern["type"],
                    properties={
                        "content": pattern["content"],
                        "source_chunk": chunk["id"],
                        "confidence": pattern["confidence"]
                    }
                )
```

## Agent Implementation Examples

### Coordination Agent
```python
class CoordinationAgent(TinyPerson):
    """Manages agent groups and task coordination."""
    def __init__(self):
        super().__init__("CoordinationAgent")
        self.task_groups = {}
        self.dialogue_history = []
        
    def create_group(self, group_name: str, task_description: str = None):
        """Create a new agent group."""
        self.task_groups[group_name] = {
            "agents": [],
            "task": task_description,
            "status": "active"
        }
        
    def add_agent_to_group(self, agent_name: str, group_name: str):
        """Add agent to specified group."""
        if group_name in self.task_groups:
            self.task_groups[group_name]["agents"].append(agent_name)
```

### Emergent Task Detection
```python
class EmergentTaskDetector:
    """Detects potential tasks from conversations."""
    def __init__(self):
        self.patterns = [
            r"(?i)need to (?P<task>.*)",
            r"(?i)should (?P<task>.*)",
            r"(?i)must (?P<task>.*)"
        ]
        self.pending_tasks = {}
        
    async def analyze_conversation(self, dialogue: str) -> Optional[Dict]:
        """Analyze dialogue for potential tasks."""
        for pattern in self.patterns:
            if match := re.search(pattern, dialogue):
                task_desc = match.group("task")
                return {
                    "type": "emergent",
                    "description": task_desc,
                    "source": dialogue,
                    "status": "pending_approval"
                }
        return None
```

## Testing Framework Examples

### Basic Workflow Tests
```python
class TestScenarios:
    async def test_basic_workflow(self):
        """Test basic agent workflow."""
        # Create test environment
        world = TinyWorld("TestEnvironment")
        nova = Nova(world)
        
        # Test task pause/resume
        await nova.start_task("create_hello_world")
        await nova.pause_tasks()
        
        # Verify conversation still works
        response = await nova.handle_conversation("Status update?")
        assert response is not None
        
        # Resume and verify task completion
        await nova.resume_tasks()
        task_result = await nova.get_task_result("create_hello_world")
        assert task_result["status"] == "completed"
```

### Integration Tests
```python
class IntegrationTests:
    async def test_full_workflow(self):
        """Test complete system workflow."""
        # Initialize system
        nova = Nova(TinyWorld("TestEnvironment"))
        logger = ConversationLogger()
        controller = SimulationController()
        
        # Start complex task
        task_id = await nova.start_task("build_web_app")
        
        # Verify agent spawning
        agents = nova.get_active_agents()
        assert len(agents) >= 3  # Minimum required agents
        
        # Test pause/resume
        await controller.pause_tasks()
        assert controller.state["tasks_paused"]
        assert controller.state["conversation_enabled"]
        
        # Test memory operations
        memory = await nova.memory_store.query_domain("web_app")
        assert len(memory) > 0
```

## Task Management Examples

### Task Approval System
```python
class TaskApprovalSystem:
    """Manages emergent task approval workflow."""
    def __init__(self, nova_instance):
        self.nova = nova_instance
        self.pending_tasks = {}
        self.approved_tasks = {}
        
    async def submit_task(self, task: Dict):
        """Submit task for approval."""
        task_id = str(uuid.uuid4())
        self.pending_tasks[task_id] = {
            **task,
            "submitted_at": datetime.now().isoformat()
        }
        return task_id
        
    async def approve_task(self, task_id: str, assigned_group: str = None):
        """Approve and assign task."""
        if task := self.pending_tasks.get(task_id):
            # Move to approved
            self.approved_tasks[task_id] = {
                **task,
                "approved_at": datetime.now().isoformat(),
                "assigned_group": assigned_group
            }
            
            # Create agents if needed
            if assigned_group:
                await self.nova.spawn_agents_for_task(
                    task["description"],
                    assigned_group
                )
            
            del self.pending_tasks[task_id]
            return True
        return False
```

## Integration Examples

### Example 1: Conversation Processing
```python
async def process_conversation():
    # Initialize system
    nova = Nova(TinyWorld("ConversationEnvironment"))
    memory = TwoLayerMemorySystem(neo4j_store, vector_store)
    
    # Process user input
    user_input = "We should create a documentation site"
    
    # Store in episodic memory
    chunk_id = await memory.episodic.store(user_input)
    
    # Check for emergent tasks
    detector = EmergentTaskDetector()
    if task := await detector.analyze_conversation(user_input):
        # Submit for approval
        approval_system = TaskApprovalSystem(nova)
        task_id = await approval_system.submit_task(task)
        
    # Generate response
    response = await nova.generate_response(user_input)
    
    return response
```

### Example 2: Memory Operations
```python
async def handle_pdf_ingestion(pdf_content: str):
    # Initialize memory system
    memory = TwoLayerMemorySystem(neo4j_store, vector_store)
    
    # Create chunking system
    chunker = ChunkingSystem(chunk_size=512)
    
    # Split PDF into chunks
    chunks = chunker.chunk_text(pdf_content)
    
    # Store chunks in episodic memory
    chunk_ids = []
    for chunk in chunks:
        chunk_id = await memory.episodic.store(chunk["content"])
        chunk_ids.append(chunk_id)
    
    # Consolidate important information
    consolidation = ConsolidationManager(
        memory.episodic,
        memory.semantic
    )
    await consolidation.consolidate_chunks(chunks)
    
    return chunk_ids
```

### Example 3: Agent Group Management
```python
async def manage_large_task():
    # Initialize Nova with TinyWorld
    nova = Nova(TinyWorld("TaskEnvironment"))
    
    # Create coordination agent
    coordinator = CoordinationAgent()
    
    # Create task groups
    coordinator.create_group(
        "frontend_team",
        "Implement user interface components"
    )
    coordinator.create_group(
        "backend_team",
        "Implement API endpoints"
    )
    
    # Spawn and assign agents
    frontend_agents = await nova.spawn_agents(5, "frontend")
    backend_agents = await nova.spawn_agents(5, "backend")
    
    for agent in frontend_agents:
        coordinator.add_agent_to_group(agent.name, "frontend_team")
    
    for agent in backend_agents:
        coordinator.add_agent_to_group(agent.name, "backend_team")
    
    return {
        "frontend_team": coordinator.get_group_agents("frontend_team"),
        "backend_team": coordinator.get_group_agents("backend_team")
    }
```

These examples serve as implementation references for the NIA system. For high-level architecture and system overview, refer to the main README.md file.
