# NIA Implementation Plan
# NIA Implementation Plan

## Overview

NIA is a sophisticated multi-agent system that combines metacognitive capabilities with domain task execution, built on the TinyTroupe framework. This implementation plan ensures a smooth transition to TinyTroupe while incorporating Nova's metacognitive approach, robust memory design, emergent tasks, conversation unaffected by pause, and the capacity to spawn or group large numbers of agents.

## Architecture and Goals

### 1. TinyTroupe as Agent Simulation Framework
- Use TinyTroupe's base classes for agent definitions (TinyPerson, TinyWorld, etc.)
- Retain Nova's overarching metacognition approach (meta-synthesis, emergent tasks, memory design)
- Harness TinyTroupe's environment and conversation mechanics, but expand them for advanced features

### 2. Nova as Meta-Orchestrator
- Nova remains the single orchestrator (or "director")
- Continues to spawn or manage specialized agents as TinyTroupe TinyPersons
- Coordinates tasks, memory, pausing/resuming, and conversation flows

### 3. Gradio and LangSmith Integration
- Expose controls (pause/resume tasks, agent grouping, emergent task approvals) in Gradio
- Integrate conversation logs and analytics with LangSmith

## Current Status (December 30, 2024)

### Current Structure
```
src/nia/
├── memory/
│   ├── types/          # New structure
│   │   ├── concept_utils/
│   │   └── json_utils/
│   ├── vector/
│   │   ├── embeddings.py
│   │   └── vector_store.py
│   ├── neo4j/
│   ├── consolidation.py
│   └── two_layer.py
└── ui/                  # To be reorganized
```

### Completed Components

1. Base Integration:
   - [x] TinyTroupeAgent base class combining:
     * Original BaseAgent memory capabilities
     * TinyTroupe simulation features
     * Emotion and desire tracking

2. Specialized Agents:
   - [x] DialogueAgent: Conversation flow and context tracking
   - [x] EmotionAgent: Affective analysis and emotional state
   - [x] BeliefAgent: Knowledge and belief management
   - [x] ResearchAgent: Information gathering and analysis
   - [x] ReflectionAgent: Pattern recognition and meta-learning
   - [x] DesireAgent: Goal and motivation tracking
   - [x] TaskAgent: Planning and execution management

3. Memory Architecture:
   - [x] Neo4j integration maintenance
   - [x] Vector store integration
   - [x] Memory consolidation enhancement
   - [x] Domain-specific memory handling
   - [x] Relationship creation and validation
   - [x] Memory type organization
   - [x] Utility code migration

4. World Environment:
   - [x] NIAWorld extending TinyWorld
   - [x] Resource management
   - [x] Domain handling
   - [x] Task coordination

5. Phase 1 Progress:
   - [x] Memory system reorganization
   - [x] Memory types and utilities migration
   - [x] Test coverage improvements
   - [x] Relationship handling fixes
   - [ ] Core agent migration (In Progress)
   - [ ] UI reorganization (Next Phase)

### Performance Optimizations
- Large agent group handling
- Enhanced memory operations
- Improved state management
- Batch processing for UI updates

### Communication Features
- Conversation preservation during task pauses
- Enhanced dialogue synthesis
- Emotional state tracking
- Goal alignment improvements

## Memory System Integration

### Existing Components

1. Two-Layer Memory:
```python
class TwoLayerMemorySystem:
    """Implements episodic and semantic memory layers."""
    
    def __init__(self, neo4j_store: Optional[Neo4jMemoryStore] = None, 
                 vector_store: Optional[VectorStore] = None):
        self.episodic = EpisodicLayer(vector_store)
        self.semantic = SemanticLayer(neo4j_store)
        self.consolidation_manager = None
        
    async def store_experience(self, experience: Memory):
        """Store new experience in episodic memory."""
        await self.episodic.store(experience)
        if self.consolidation_manager and await self.consolidation_manager.should_consolidate():
            await self.consolidate_memories()
```

2. LLM Interface:
```python
class EnhancedLLMInterface(LLMInterface):
    """Enhanced LLM interface with TinyTroupe integration."""
    
    def __init__(self, use_mock: bool = False):
        super().__init__(use_mock)
        self.world = None  # TinyWorld reference
        
    async def process_agent_response(self, response: str, agent_type: str):
        """Process response with agent-specific handling."""
        structured = await self.get_structured_completion(
            response, 
            agent_type,
            metadata={"world_state": self.world.get_state()}
        )
        
        if hasattr(structured, "tasks"):
            for task in structured.tasks:
                await self.world.create_task(task)
```
## Prompt System Integration

### Existing Prompts
```python
# From prompts.py
AGENT_PROMPTS = {
    "meta": """You are a meta-agent responsible for synthesizing responses from other agents.
Your role is to:
- Coordinate and integrate perspectives from all agents
- Identify common themes and patterns across agent responses
- Resolve any conflicts or contradictions between agents
- Generate a coherent final response that incorporates key insights""",

    "belief": """You are a belief agent responsible for validating knowledge and beliefs.
Your role is to:
- Analyze statements for factual accuracy
- Identify underlying assumptions and beliefs
- Evaluate the reliability of information
- Flag any misconceptions or uncertainties""",

    "emotion": """You are an emotion agent responsible for processing emotional context.
Your role is to:
- Detect emotional tone and sentiment
- Understand emotional triggers and responses
- Consider emotional impact and implications
- Ensure emotional awareness in responses""",

    "reflection": """You are a reflection agent responsible for analyzing patterns and insights.
Your role is to:
- Identify recurring patterns and themes
- Draw connections between different elements
- Extract meaningful insights and lessons
- Suggest areas for deeper exploration""",

    "research": """You are a research agent responsible for adding knowledge and facts.
Your role is to:
- Identify areas needing additional information
- Suggest relevant facts and context
- Connect to existing knowledge
- Highlight areas for further research""",

    "task_planner": """You are a task planning agent responsible for organizing and sequencing tasks.
Your role is to:
- Break down goals into concrete tasks
- Establish task dependencies and order
- Estimate time and resource requirements
- Create actionable task sequences"""
}

# TinyTroupe Integration
TINYTROUPE_PROMPTS = {
    "world": """You are operating in a TinyWorld environment.
Your responses should consider:
- Current world state
- Active agents and their states
- Available resources
- Task dependencies""",
    
    "agent": """You are a TinyPerson agent with specific capabilities.
Your responses should:
- Use self.define(...) for attributes
- Call self.act() for actions
- Maintain conversation during pauses
- Track emotional and desire states""",
    
    "coordinator": """You are a coordination agent managing TinyPerson agents.
Your responses should:
- Track agent groups and assignments
- Manage task dependencies
- Handle resource allocation
- Maintain agent relationships""",
    
    "emotion": """You are an emotion-aware TinyPerson agent.
Your responses should:
- Track emotional states
- Consider emotional impacts
- Manage emotional responses
- Maintain emotional balance""",
    
    "task": """You are a task-focused TinyPerson agent.
Your responses should:
- Break down objectives
- Track dependencies
- Estimate resources
- Monitor progress"""
}

# Update existing prompts with TinyTroupe capabilities
for agent_type, prompt in TINYTROUPE_PROMPTS.items():
    if agent_type in AGENT_PROMPTS:
        AGENT_PROMPTS[agent_type] = f"{AGENT_PROMPTS[agent_type]}\n\n{prompt}"
    else:
        AGENT_PROMPTS[agent_type] = prompt
```


### Directory Structure
```
src/nia/
├── nova/                 # Nova's core capabilities
│   ├── core/            # Core processing modules
│   │   ├── parsing.py   # From ParsingAgent
│   │   ├── meta.py      # From MetaAgent
│   │   ├── structure.py # From StructureAgent
│   │   ├── context.py   # From ContextAgent
│   │   └── processor.py # From ResponseProcessor
│   ├── tasks/           # Task management
│   │   ├── planner.py   # From TaskPlannerAgent
│   │   └── context.py   # From ContextBuilder
│   └── orchestrator.py  # Main Nova class
├── agents/              # Agent implementations
│   ├── specialized/     # TinyTroupe-integrated agents
│   │   ├── dialogue_agent.py
│   │   ├── emotion_agent.py
│   │   ├── belief_agent.py
│   │   ├── research_agent.py
│   │   ├── reflection_agent.py
│   │   ├── desire_agent.py
│   │   └── task_agent.py
│   ├── base.py         # Base agent implementation
│   ├── tinytroupe_agent.py
│   ├── skills_agent.py
│   ├── coordination_agent.py
│   └── factory.py
├── memory/             # Memory system
│   ├── neo4j/          # Neo4j integration
│   ├── vector/         # Vector store management
│   ├── types/          # Memory type definitions
│   ├── consolidation.py
│   ├── embeddings.py
│   └── two_layer.py
└── ui/                 # User interface
    ├── components/     # UI building blocks
    ├── handlers/       # Event handlers
    ├── visualization/  # Agent visualization
    └── state.py       # UI state management
```

## Implementation Phases

### Phase 1: Core Component Migration

1. File Movement:
```bash
# Create nova directory structure
mkdir -p src/nia/nova/{core,tasks}

# Move core agent functionality
mv src/nia/memory/agents/parsing_agent.py src/nia/nova/core/parsing.py
mv src/nia/memory/agents/meta_agent.py src/nia/nova/core/meta.py
mv src/nia/memory/agents/structure_agent.py src/nia/nova/core/structure.py
mv src/nia/memory/agents/context_agent.py src/nia/nova/core/context.py
mv src/nia/memory/agents/response_processor.py src/nia/nova/core/processor.py

# Move task management
mv src/nia/memory/agents/task_planner_agent.py src/nia/nova/tasks/planner.py
mv src/nia/memory/agents/context_builder.py src/nia/nova/tasks/context.py
```

2. Code Updates:
```python
# Old implementation
class ParsingAgent(BaseAgent):
    ...

# New implementation
class NovaParser:
    """Core parsing functionality from ParsingAgent."""
    def __init__(self):
        self.schema_validator = self.load_existing_schema_validator()
        self.orson_parser = self.initialize_orson_parser()
```

3. Nova Integration:
```python
class Nova:
    def __init__(self):
        # Initialize core components
        self.parser = NovaParser()
        self.synthesizer = NovaSynthesizer()
        self.structure_validator = NovaValidator()
        self.context_manager = NovaContext()
        self.response_processor = NovaProcessor()
        
        # Initialize task components
        self.task_planner = NovaTaskPlanner()
        self.context_builder = NovaContextBuilder()
        
        # Initialize TinyTroupe integration
        self.world = TinyWorld("NovaEnvironment")
        self.initialize_specialized_agents()
        
        # Initialize memory system
        self.memory = TwoLayerMemorySystem(
            neo4j_store=self.store,
            vector_store=self.vector_store
        )
        
        # Initialize LLM interface
        self.llm = EnhancedLLMInterface()
        self.llm.world = self.world
```

### Phase 2: UI Development

1. File Organization:
```bash
# Create UI directories
mkdir -p src/nia/ui/{components,handlers,visualization}

# Move UI components
mv src/nia/ui/base.py src/nia/ui/components/
mv src/nia/ui/chat.py src/nia/ui/components/
mv src/nia/ui/graph.py src/nia/ui/components/
mv src/nia/ui/handlers.py src/nia/ui/handlers/
mv src/nia/ui/message_handlers.py src/nia/ui/handlers/
```

2. Component Implementation:
```python
def create_ui_components(gr):
    with gr.Blocks() as demo:
        with gr.Row():
            with gr.Column():
                # Core Controls
                start_btn = gr.Button("Start Simulation")
                pause_btn = gr.Button("Pause Tasks")
                resume_btn = gr.Button("Resume Tasks")
                
            with gr.Column():
                # Status Display
                status = gr.JSON(label="System Status")
                metrics = gr.JSON(label="Performance Metrics")
```

3. Memory Visualization:
```python
def create_memory_interface(gr):
    with gr.Blocks() as demo:
        with gr.Row():
            with gr.Column():
                # Memory Controls
                query_input = gr.Textbox(label="Memory Query")
                search_btn = gr.Button("Search Memories")
                
            with gr.Column():
                # Memory Display
                with gr.Accordion("Episodic Memories"):
                    episodic_display = gr.JSON(label="Recent Experiences")
                    
                with gr.Accordion("Semantic Knowledge"):
                    semantic_display = gr.JSON(label="Consolidated Knowledge")
```

### Phase 3: Memory System Integration

1. Directory Organization:
```bash
# Create memory system directories
mkdir -p src/nia/memory/{neo4j,vector,types}

# Move memory components
mv src/nia/memory/memory_types.py src/nia/memory/types/
mv src/nia/memory/neo4j_store.py src/nia/memory/neo4j/
mv src/nia/memory/vector_store.py src/nia/memory/vector/
```

2. Memory System Implementation:
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
```

3. TinyTroupe Integration:
```python
class TinyTroupePattern(ConsolidationPattern):
    """Pattern for extracting TinyTroupe-specific knowledge."""
    def __init__(self):
        super().__init__("tinytroupe", threshold=0.7)
```

### Phase 4: Testing and LangSmith Integration

1. Testing Framework:
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
        
    async def test_emergent_tasks(self):
        """Test emergent task detection and handling."""
        nova = Nova(TinyWorld("TestEnvironment"))
        
        # Simulate conversation that should trigger emergent task
        conversation = "We should create a documentation site"
        response = await nova.handle_conversation(conversation)
        
        # Verify emergent task detection
        emergent_tasks = nova.get_emergent_tasks()
        assert len(emergent_tasks) > 0
        assert emergent_tasks[0]["type"] == "documentation"
        
    async def test_large_agent_groups(self):
        """Test handling of large agent groups."""
        nova = Nova(TinyWorld("TestEnvironment"))
        
        # Create multiple agent groups
        for i in range(5):
            await nova.create_agent_group(f"TestGroup_{i}")
            
        # Add agents to groups
        for i in range(50):
            agent = await nova.spawn_agent(f"TestAgent_{i}")
            group_id = i % 5  # Distribute across groups
            await nova.add_agent_to_group(agent, f"TestGroup_{group_id}")
            
        # Verify group management
        for i in range(5):
            group = await nova.get_agent_group(f"TestGroup_{i}")
            assert len(group.agents) == 10
```

2. LangSmith Integration:
```python
class ConversationLogger:
    def __init__(self):
        self.langsmith_client = LangSmith(
            api_key=os.getenv("LANGSMITH_API_KEY")
        )
        self.trace_configs = {
            "conversation": {
                "tags": ["dialogue", "agent_interaction"],
                "metadata": {"type": "agent_conversation"}
            },
            "task": {
                "tags": ["task_execution", "agent_action"],
                "metadata": {"type": "agent_task"}
            }
        }
        
    async def log_conversation(self, dialogue: Dict):
        """Log conversation with detailed tracing."""
        trace = await self.langsmith_client.create_trace(
            name="agent_dialogue",
            config=self.trace_configs["conversation"]
        )
        
        # Add conversation details
        await trace.add_event(
            type="dialogue",
            data=dialogue
        )
        
        return trace.id
        
    async def log_task_execution(self, task: Dict):
        """Log task execution details."""
        trace = await self.langsmith_client.create_trace(
            name="task_execution",
            config=self.trace_configs["task"]
        )
        
        # Add task execution details
        await trace.add_event(
            type="task",
            data=task
        )
        
        return trace.id
```

3. Integration Testing:
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
        
        # Test UI updates
        ui_state = nova.get_ui_state()
        assert ui_state["orchestration"]["agent_count"] > 0
```


### Phase 5: Agent Grouping and Management

1. Group Management Implementation:
```python
class CoordinationAgent(TinyPerson):
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
            
    def get_group_agents(self, group_name: str) -> List[str]:
        """Get all agents in a group."""
        return self.task_groups.get(group_name, {}).get("agents", [])
        
    def get_agent_group(self, agent_name: str) -> Optional[str]:
        """Find which group an agent belongs to."""
        for group_name, group in self.task_groups.items():
            if agent_name in group["agents"]:
                return group_name
        return None
```

2. UI Integration for Groups:
```python
def create_group_interface(gr):
    with gr.Blocks() as demo:
        with gr.Row():
            with gr.Column():
                # Group Management
                group_name = gr.Textbox(label="Group Name")
                task_desc = gr.Textbox(label="Task Description")
                create_btn = gr.Button("Create Group")
                
                # Agent Assignment
                agent_name = gr.Textbox(label="Agent Name")
                group_dropdown = gr.Dropdown(choices=[], label="Select Group")
                assign_btn = gr.Button("Assign Agent")
                
            with gr.Column():
                # Group Display
                with gr.Accordion("Active Groups"):
                    groups_display = gr.JSON(label="Groups")
                    
                # Search/Filter
                search_box = gr.Textbox(label="Search Agents")
                filtered_display = gr.JSON(label="Filtered Results")
```

### Phase 6: Emergent Task Management

1. Task Detection System:
```python
class EmergentTaskDetector:
    """Detects potential tasks from agent conversations."""
    
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

2. Task Approval Workflow:
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

3. UI Integration for Tasks:
```python
def create_task_interface(gr):
    with gr.Blocks() as demo:
        with gr.Row():
            with gr.Column():
                # Pending Tasks
                with gr.Accordion("Pending Tasks", open=True):
                    pending_list = gr.JSON(label="Requires Approval")
                    
                # Task Actions
                task_id = gr.Textbox(label="Task ID")
                group_assign = gr.Dropdown(label="Assign to Group")
                approve_btn = gr.Button("Approve & Assign")
                reject_btn = gr.Button("Reject")
                
            with gr.Column():
                # Active Tasks
                with gr.Accordion("Active Tasks"):
                    active_tasks = gr.JSON(label="In Progress")
                    
                # Task Progress
                with gr.Accordion("Task Progress"):
                    progress_display = gr.JSON(label="Status")
```

## Success Criteria

### Functionality
- All core processing capabilities preserved
- Memory integration maintained
- Conversation flows unaffected
- Task pause/resume working

### Performance
- Equal or better processing speed
- Maintained memory efficiency
- Smooth conversation handling
- Efficient large agent group handling

### Integration
- Clean interaction with specialized agents
- Proper TinyTroupe integration
- Maintained extensibility
- Smooth UI operation

### Memory Integration
- Successful episodic to semantic conversion
- Efficient memory consolidation
- Proper LLM response handling
- Accurate knowledge extraction

## Next Steps

### Core Agent Migration Checklist

1. Nova Core Setup:
   - [ ] Create nova directory structure
   - [ ] Set up core module initialization
   - [ ] Implement Nova orchestrator base

2. Agent Migration:
   - [ ] Move ParsingAgent to nova/core/parsing.py
   - [ ] Move MetaAgent to nova/core/meta.py
   - [ ] Move StructureAgent to nova/core/structure.py
   - [ ] Move ContextAgent to nova/core/context.py
   - [ ] Move ResponseProcessor to nova/core/processor.py
   - [ ] Update all import paths

3. Task Management Migration:
   - [ ] Move TaskPlannerAgent to nova/tasks/planner.py
   - [ ] Move ContextBuilder to nova/tasks/context.py
   - [ ] Implement task coordination logic
   - [ ] Update task-related imports

4. Integration Tasks:
   - [ ] Update agent initialization in Nova class
   - [ ] Implement TinyTroupe integration points
   - [ ] Set up agent communication channels
   - [ ] Add memory system hooks

5. Testing Requirements:
   - [ ] Create unit tests for Nova core
   - [ ] Add integration tests for agent communication
   - [ ] Test TinyTroupe compatibility
   - [ ] Verify memory system integration

### Additional Tasks

1. Implement UI improvements
2. Add monitoring tools
3. Enhance error handling
4. Complete comprehensive testing
5. Update documentation

## Notes

- Keep existing functionality while transitioning
- Ensure backward compatibility
- Maintain test coverage
- Document all changes
- Focus on performance optimization
- Preserve conversation during task pauses
- Implement efficient agent grouping for large-scale operations
- Maintain clear task approval workflow
- Consider future scaling with specialized UI frameworks

## Future Extensions

1. TinyTroupe Integration
   - Gains robust agent simulation fundamentals
   - Unifies advanced memory design, emergent tasks, and conversation-based reflection
   - Enables domain expansions under one consistent environment

2. Nova's Role
   - Orchestrates specialized agents
   - Spawns new domain helpers
   - Handles emergent tasks
   - Ensures memory updates

3. UI Capabilities
   - Pausing tasks without blocking conversation
   - Approving emergent tasks
   - Managing large agent groups
   - Well-designed Gradio layout

4. Scalability
   - New specialized domain agents
   - Expanded LangSmith usage
   - Advanced memory sharding for massive projects
   - Specialized UI frameworks as needed

5. Memory Enhancements
   - Advanced pattern recognition
   - Improved consolidation triggers
   - Enhanced knowledge extraction
   - Memory visualization tools
