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

## User Initialization System

### Psychometric Questionnaire System
```python
class PsychometricQuestionnaire:
    """Manages user psychometric profiling."""
    def __init__(self):
        self.questions = {
            "big_five": self.load_big_five_questions(),
            "learning_style": self.load_learning_style_questions()
        }
        
    async def conduct_questionnaire(self) -> Dict:
        """Conduct full psychometric assessment."""
        results = {
            "personality": await self.assess_big_five(),
            "learning_style": await self.assess_learning_style(),
            "task_preferences": await self.assess_task_preferences()
        }
        return results

    async def store_profile(self, results: Dict):
        """Store profile in Neo4j."""
        query = """
        MERGE (p:UserProfile {user_id: $user_id})
        SET p.personality = $personality,
            p.learning_style = $learning_style,
            p.task_preferences = $task_preferences,
            p.updated_at = datetime()
        """
        await self.neo4j.execute(query, {
            "user_id": results["user_id"],
            "personality": results["personality"],
            "learning_style": results["learning_style"],
            "task_preferences": results["task_preferences"]
        })
```

### Profile-Based Task Adaptation
```python
class TaskAdaptationSystem:
    """Adapts task presentation based on user profile."""
    def __init__(self, profile: Dict):
        self.profile = profile
        
    def adapt_task_presentation(self, task: Dict) -> Dict:
        """Modify task based on user profile."""
        # Adjust detail level based on conscientiousness
        if self.profile["personality"]["conscientiousness"] > 0.7:
            task = self.add_detailed_steps(task)
            
        # Adapt to learning style
        if self.profile["learning_style"] == "visual":
            task = self.add_visual_elements(task)
            
        # Consider emotional aspects
        if self.profile["personality"]["neuroticism"] > 0.6:
            task = self.add_reassurance(task)
            
        return task
        
    def should_auto_approve(self, task: Dict) -> bool:
        """Determine if task should be auto-approved."""
        return (
            self.profile["task_preferences"]["auto_approve"] and
            task["complexity"] <= self.profile["task_preferences"]["max_auto_complexity"]
        )
```

### Profile Integration with Nova
```python
class ProfileAwareNova:
    """Nova implementation with profile awareness."""
    def __init__(self):
        self.questionnaire = PsychometricQuestionnaire()
        self.adaptation = None
        
    async def initialize_user(self):
        """Initialize new user with profiling."""
        # Conduct questionnaire
        profile = await self.questionnaire.conduct_questionnaire()
        
        # Store in Neo4j
        await self.questionnaire.store_profile(profile)
        
        # Initialize adaptation system
        self.adaptation = TaskAdaptationSystem(profile)
        
        # Configure agents based on profile
        await self.configure_agents_for_profile(profile)
        
    async def configure_agents_for_profile(self, profile: Dict):
        """Configure specialized agents based on profile."""
        # Adjust EmotionAgent sensitivity
        await self.emotion_agent.configure_sensitivity(
            profile["personality"]["neuroticism"]
        )
        
        # Set DesireAgent motivation tracking
        await self.desire_agent.set_motivation_preferences(
            profile["task_preferences"]
        )
        
        # Configure DialogueAgent style
        await self.dialogue_agent.set_communication_style(
            profile["personality"]
        )
```

## Template Storage Examples

### Template Management System
```python
class TemplateManager:
    """Manages local storage of agent and flow templates."""
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = template_dir
        self.agent_dir = f"{template_dir}/agents"
        self.flow_dir = f"{template_dir}/flows"
        self.registry_file = f"{template_dir}/agent_registry.yaml"
        self.init_file = f"{template_dir}/init_agents.yaml"
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create template directories if they don't exist."""
        os.makedirs(self.agent_dir, exist_ok=True)
        os.makedirs(self.flow_dir, exist_ok=True)
        
    def register_agent_template(self, agent_name: str, template_data: dict):
        """Store new agent template."""
        file_path = f"{self.agent_dir}/{agent_name.lower()}_agent.yaml"
        with open(file_path, "w") as f:
            yaml.dump(template_data, f)
            
        # Update registry
        self.update_registry(agent_name, file_path)
        
        # Trigger reload
        self.reload_templates()
        return file_path
        
    def register_flow(self, flow_name: str, flow_config: dict):
        """Store new flow template."""
        file_path = f"{self.flow_dir}/{flow_name.lower()}.yaml"
        with open(file_path, "w") as f:
            yaml.dump(flow_config, f)
            
        # Update init flows if auto-launch
        if flow_config.get("auto_launch"):
            self.update_init_flows(flow_name, file_path)
            
        # Trigger reload
        self.reload_templates()
        return file_path
        
    def update_registry(self, agent_name: str, file_path: str):
        """Update agent registry."""
        registry = {}
        if os.path.exists(self.registry_file):
            with open(self.registry_file) as f:
                registry = yaml.safe_load(f) or {}
                
        registry[agent_name] = {
            "path": file_path,
            "updated_at": datetime.now().isoformat()
        }
        
        with open(self.registry_file, "w") as f:
            yaml.dump(registry, f)
            
    def update_init_flows(self, flow_name: str, file_path: str):
        """Update init flows configuration."""
        init_config = {}
        if os.path.exists(self.init_file):
            with open(self.init_file) as f:
                init_config = yaml.safe_load(f) or {}
                
        init_flows = init_config.get("init_flows", [])
        init_flows.append({
            "name": flow_name,
            "file": file_path,
            "auto_launch": True
        })
        
        init_config["init_flows"] = init_flows
        with open(self.init_file, "w") as f:
            yaml.dump(init_config, f)
            
    def reload_templates(self):
        """Reload all templates into memory."""
        agents, flows = self.load_templates()
        # Notify system of template updates
        self.notify_template_update(agents, flows)
        
    def load_templates(self):
        """Load all templates at startup."""
        agents = {}
        flows = {}
        
        # Load agent templates
        for file in glob.glob(f"{self.agent_dir}/*.yaml"):
            with open(file) as f:
                name = os.path.basename(file).replace("_agent.yaml", "")
                agents[name] = yaml.safe_load(f)
                
        # Load flow templates
        for file in glob.glob(f"{self.flow_dir}/*.yaml"):
            with open(file) as f:
                name = os.path.basename(file).replace(".yaml", "")
                flows[name] = yaml.safe_load(f)
                
        return agents, flows
```

### Template Integration with TinyFactory
```python
class TinyFactory:
    """Enhanced factory with template persistence."""
    def __init__(self):
        self.template_manager = TemplateManager()
        self.agents, self.flows = self.template_manager.load_templates()
        self.registry = self.load_registry()
        
    def load_registry(self):
        """Load agent registry."""
        if os.path.exists(self.template_manager.registry_file):
            with open(self.template_manager.registry_file) as f:
                return yaml.safe_load(f) or {}
        return {}
        
    async def create_agent(self, agent_type: str, config: dict):
        """Create agent and persist template."""
        # Store template first
        template_path = self.template_manager.register_agent_template(
            agent_type,
            config
        )
        
        # Create agent instance
        agent = await self._spawn_agent(agent_type, config)
        
        # Update registry
        self.agents[agent_type] = config
        self.registry = self.load_registry()  # Reload registry
        
        return agent
        
    async def create_flow(self, flow_name: str, flow_config: dict):
        """Create flow and persist template."""
        # Store flow template
        template_path = self.template_manager.register_flow(
            flow_name,
            flow_config
        )
        
        # Create flow instance
        flow = await self._spawn_flow(flow_config)
        
        # Update registry
        self.flows[flow_name] = flow_config
        
        return flow
```

### Initialization System
```python
class SystemInitializer:
    """Handles system startup and template loading."""
    def __init__(self):
        self.template_manager = TemplateManager()
        self.factory = TinyFactory()
        
    async def initialize(self):
        """Initialize system with templates."""
        # Load init configuration
        with open("templates/init_agents.yaml") as f:
            init_config = yaml.safe_load(f)
            
        # Auto-launch configured flows
        for flow in init_config.get("init_flows", []):
            if flow.get("auto_launch"):
                await self.factory.create_flow(
                    flow["name"],
                    flow["config"]
                )
                
        # Initialize required agents
        for agent in init_config.get("init_agents", []):
            await self.factory.create_agent(
                agent["type"],
                agent["config"]
            )
```

### Admin Interface
```python
class TemplateAdmin:
    """Admin interface for template management."""
    def __init__(self, template_manager: TemplateManager):
        self.manager = template_manager
        
    async def handle_command(self, command: str, args: dict = None):
        """Handle admin commands."""
        if command == "/reload_configs":
            await self.reload_templates()
        elif command == "/list_templates":
            return await self.list_templates()
        elif command == "/edit_template":
            return await self.edit_template(args["name"], args["content"])
            
    async def reload_templates(self):
        """Reload all templates."""
        self.manager.reload_templates()
        return "Templates reloaded successfully"
        
    async def list_templates(self):
        """List all available templates."""
        agents, flows = self.manager.load_templates()
        return {
            "agents": list(agents.keys()),
            "flows": list(flows.keys())
        }
        
    async def edit_template(self, name: str, content: dict):
        """Edit existing template."""
        if name.endswith("_agent"):
            return await self.manager.register_agent_template(
                name.replace("_agent", ""),
                content
            )
        else:
            return await self.manager.register_flow(name, content)
```

### Example Template Files

1. Agent Template (templates/agents/math_proof_agent.yaml):
```yaml
agent_type: "MathProofAgent"
system_prompt: "You are a math proof-checker..."
capabilities:
  - "checkProof"
  - "explainErrors"
domain_constraints:
  - "professional"
version: "1.0.0"
created_at: "2025-01-06T12:00:00Z"
updated_at: "2025-01-06T12:00:00Z"
```

2. Flow Template (templates/flows/survey_flow.yaml):
```yaml
flow_name: "SurveyFlow"
description: "Multi-agent flow for survey processing"
agent_list:
  - "SurveyAggregatorAgent"
  - "StatAnalysisAgent"
pattern: "parallel"
domain: "professional"
auto_launch: true
version: "1.0.0"
```

3. Registry File (templates/agent_registry.yaml):
```yaml
MathProofAgent:
  path: "templates/agents/math_proof_agent.yaml"
  updated_at: "2025-01-06T12:00:00Z"
  version: "1.0.0"
  status: "active"

SurveyAggregatorAgent:
  path: "templates/agents/survey_aggregator_agent.yaml"
  updated_at: "2025-01-06T12:00:00Z"
  version: "1.0.0"
  status: "active"
```

4. Init Configuration (templates/init_agents.yaml):
```yaml
init_flows:
  - name: "DailyReflectionFlow"
    file: "templates/flows/daily_reflection.yaml"
    auto_launch: true
    
  - name: "PromptWizardFlow"
    file: "templates/flows/prompt_wizard.yaml"
    auto_launch: false

init_agents:
  - type: "CoreProcessingAgent"
    config:
      capabilities: ["parsing", "analysis"]
      auto_start: true
      
  - type: "MonitoringAgent"
    config:
      capabilities: ["metrics", "alerts"]
      auto_start: true
```

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

### Mock Implementations
```python
class MockMemorySystem:
    """Example of proper async mock implementation."""
    class AsyncIterator:
        def __init__(self, memory_system):
            self.memory_system = memory_system
            self.done = False

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.done:
                raise StopAsyncIteration
            self.done = True
            return self.memory_system

    class MockStore:
        def __init__(self):
            self.store = self
            self.collection = "test_collection"
            
        async def connect(self):
            return self
            
        async def close(self):
            return None
            
        async def ensure_collection(self):
            return self.collection
            
        async def store(self, *args, **kwargs):
            return {"id": "test-id"}
            
        async def search(self, *args, **kwargs):
            return []
            
        async def __aenter__(self):
            await self.connect()
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            await self.close()

    def __init__(self):
        self.semantic = self.MockStore()
        self.episodic = self.MockStore()
        self.vector_store = self.MockStore()

    @classmethod
    def create_mock(cls):
        """Create properly wrapped mock system."""
        return cls.AsyncIterator(cls())
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

class WebSocketTests:
    """Test WebSocket functionality."""
    async def test_websocket_analytics(self, mock_memory, mock_analytics_agent):
        """Test WebSocket analytics processing."""
        # Override dependencies
        app.dependency_overrides[get_memory_system] = lambda: mock_memory
        app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
        
        try:
            # Create test client
            client = TestClient(app)
            
            # Connect to WebSocket endpoint
            async with client.websocket_connect(
                "/api/analytics/ws",
                headers={"X-API-Key": TEST_API_KEY}
            ) as websocket:
                # Send analytics request
                await websocket.send_json({
                    "type": "analytics_request",
                    "content": "Test content",
                    "domain": "test"
                })
                
                # Verify response
                response = await websocket.receive_json()
                assert response["type"] == "analytics_update"
                assert "analytics" in response
                assert "insights" in response
                assert "confidence" in response
                
                # Test error handling
                await websocket.send_json({"invalid": "request"})
                error_response = await websocket.receive_json()
                assert error_response["type"] == "error"
                assert "error" in error_response
        finally:
            # Clean up dependencies
            app.dependency_overrides.clear()
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

## Agent Identity Examples

### Agent Identity Management
```python
class AgentIdentityManager:
    """Manages agent identity and lifecycle."""
    def __init__(self, neo4j_store):
        self.store = neo4j_store
        
    async def get_agent_details(self, agent_id: str) -> Dict:
        """Get detailed agent information."""
        query = """
        MATCH (a:Agent {id: $agent_id})
        RETURN a {
            .id,
            .type,
            .capabilities,
            .status,
            .created_at,
            .updated_at
        }
        """
        result = await self.store.execute(query, {"agent_id": agent_id})
        return result[0] if result else None
        
    async def get_agent_status(self, agent_id: str) -> str:
        """Get current agent status."""
        query = """
        MATCH (a:Agent {id: $agent_id})
        RETURN a.status
        """
        result = await self.store.execute(query, {"agent_id": agent_id})
        return result[0] if result else None
        
    async def update_agent_status(self, agent_id: str, status: str):
        """Update agent status."""
        query = """
        MATCH (a:Agent {id: $agent_id})
        SET a.status = $status,
            a.updated_at = datetime()
        """
        await self.store.execute(query, {
            "agent_id": agent_id,
            "status": status
        })
        
    async def get_agent_history(self, agent_id: str) -> List[Dict]:
        """Get agent interaction history."""
        query = """
        MATCH (a:Agent {id: $agent_id})-[r:PARTICIPATED_IN]->(i:Interaction)
        RETURN i {
            .id,
            .type,
            .timestamp,
            .outcome
        }
        ORDER BY i.timestamp DESC
        """
        return await self.store.execute(query, {"agent_id": agent_id})
```

### Agent Identity API Routes
```python
@router.get("/agents")
async def list_agents():
    """List all agents with IDs."""
    return await identity_manager.get_all_agents()

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details."""
    return await identity_manager.get_agent_details(agent_id)

@router.get("/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get agent status."""
    return await identity_manager.get_agent_status(agent_id)

@router.post("/agents/{agent_id}/activate")
async def activate_agent(agent_id: str):
    """Activate agent."""
    await identity_manager.update_agent_status(agent_id, "active")
    return {"status": "activated"}

@router.get("/agents/search")
async def search_agents(
    capability: Optional[str] = None,
    agent_type: Optional[str] = None
):
    """Search agents by capability/type."""
    return await identity_manager.search_agents(capability, agent_type)

@router.get("/agents/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str):
    """Get agent performance metrics."""
    return await identity_manager.get_agent_metrics(agent_id)
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
