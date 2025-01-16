# Agent Reference Guide

## Agent Architecture Overview

The Nova agent system is built on two key components:

### 1. Agent Configuration (agent_config.py)
- Provides centralized agent configuration through:
  * BASE_AGENT_TEMPLATE: Core template for all agents defining:
    - Memory system integration
    - Domain management
    - Swarm collaboration
    - Response formats
    - Metacognition
  * AGENT_RESPONSIBILITIES: Specific responsibilities for each agent type
  * get_agent_prompt(): Function that generates agent prompts by combining:
    - BASE_AGENT_TEMPLATE
    - Agent-specific responsibilities
    - Domain and skills information

### 2. TinyTroupe Implementation
- Provides the base agent architecture through:
  * TinyWorld (tiny_world.py):
    - Base world with basic state management
    - Manages agents and resources
    - Handles basic state updates
  * TinyPerson (tiny_person.py):
    - Base person with emotions, goals, memories
    - Handles basic state management
    - Manages personal attributes
  * NIAWorld (environment.py):
    - Extends TinyWorld with NIA features
    - Adds memory system integration
    - Handles actions, resources, domains
  * TinyTroupeAgent (tinytroupe_agent.py):
    - Combines TinyPerson with BaseAgent
    - Provides full agent implementation
    - Handles memory and world interaction
  * TinyFactory:
    - Creates and manages TinyTroupe agents
    - Handles agent initialization
    - Manages agent relationships

### Agent Creation Flow
1. Agent configuration defined in agent_config.py
2. Agent prompt generated through get_agent_prompt()
3. TinyTroupeAgent created with configuration
4. Agent initialized in NIAWorld environment
5. Agent integrated with memory system

## Memory System Integration

Agents interact with a dual memory system:

### 1. Vector Storage (Qdrant)
- Stores text embeddings for similarity search
- Embeddings created through LM Studio API:
  ```python
  # Create embedding through API
  curl http://127.0.0.1:1234/v1/embeddings \
    -H "Content-Type: application/json" \
    -d '{
      "model": "text-embedding-nomic-embed-text-v1.5@q8_0",
      "input": "Text to embed"
    }'
  ```
- Used for finding relevant content
- Supports metadata filtering and scoring

### 2. Knowledge Graph (Neo4j)
- Stores concepts and relationships
- Node types:
  * Concept: Core knowledge units
  * Brand: Brand-related concepts
  * Policy: Policy definitions
  * Customer: Customer information
- Rich relationship types with properties
- Domain-aware with validation
- Example concept storage:
  ```cypher
  MERGE (c:Concept {name: $name})
  SET c.type = $type,
      c.description = $description,
      c.domain = $domain,
      c.created_at = datetime()
  ```

### Memory Flow
1. Input Processing:
   - Text is embedded via LM Studio API
   - Embeddings stored in Qdrant
   - LLM analyzes for concepts
   - Concepts stored in Neo4j

2. Retrieval:
   - Vector similarity search in Qdrant
   - Graph traversal in Neo4j
   - Results combined for context

3. Storage:
   - Episodic layer for recent memories
   - Semantic layer for consolidated knowledge
   - Cross-domain validation

## Core Agent Types

### Pre-Processing Agents
1. schema_agent:
- Validates input schemas
- Ensures data consistency
- Works with parsing_agent

2. parsing_agent:
- First point of contact for input
- Converts raw input to structured format
- Handles pre-processing validation

3. structure_agent:
- Advanced structure analysis and validation
- Capabilities:
  * Structure analysis
  * Schema validation
  * Domain validation
  * Integrity checking
- Key Methods:
  ```python
  async def analyze_and_store(
      self,
      text: str,
      expected_schema: Optional[Dict] = None,
      target_domain: Optional[str] = None
  ):
      """Analyze structure and store results with domain awareness."""
      result = await self.analyze_structure(
          text,
          expected_schema,
          metadata={"domain": target_domain or self.domain}
      )
      
      # Store analysis result
      await self.store_memory(
          content={
              "type": "structure_analysis",
              "text": text,
              "expected_schema": expected_schema,
              "analysis": {
                  "response": result.response,
                  "concepts": result.concepts,
                  "key_points": result.key_points,
                  "confidence": result.confidence,
                  "validation": result.validation,
                  "timestamp": datetime.now().isoformat()
              }
          }
      )
  ```

### Core Cognitive Agents
1. meta_agent:
- High-level cognitive coordination and agent spawning
- Capabilities:
  * Spawns new agents through TinyFactory
  * Creates and manages agent teams
  * Detects and handles tasks in conversations
  * Manages task state transitions and groups
  * Coordinates cognitive processing with validation
  * Analyzes cognitive needs and complexity
  * Maintains active teams and tasks tracking
- Key Methods:
  ```python
  # Agent spawning
  async def spawn_agent(
      self,
      agent_type: str,
      domain: str,
      capabilities: List[str],
      supervisor_id: Optional[str] = None,
      attributes: Optional[Dict] = None
  ) -> str

  # Team creation
  async def create_team(
      self,
      team_type: str,
      domain: str,
      capabilities: List[str],
      team_size: int = 3
  ) -> Dict[str, str]

  # Task handling
  async def detect_and_handle_task(
      self,
      content: Dict[str, Any],
      thread_id: str
  ) -> Optional[str]

  # Cognitive processing
  async def process_interaction(
      self,
      content: Dict[str, Any],
      metadata: Optional[Dict] = None
  ) -> AgentResponse
  ```

2. belief_agent:
- Analyzes beliefs with evidence
- Processes supporting facts
- Handles belief confidence

3. desire_agent:
- Analyzes motivations
- Processes goal alignment
- Handles priority factors

4. emotion_agent:
- Analyzes emotional content
- Processes emotional state
- Handles emotional influence

5. reflection_agent:
- Analyzes reflections
- Processes meta-understanding
- Handles self-awareness

### Support Agents
1. context_agent:
- Retrieves relevant context
- Manages context awareness
- Handles domain context

2. memory_agent:
- Retrieves relevant memories
- Stores interactions
- Handles memory consolidation

3. planning_agent:
- Creates execution plans
- Manages task flow
- Handles dependencies

4. research_agent:
- Gathers information
- Processes research results
- Handles information retrieval

5. reasoning_agent:
- Analyzes logic
- Processes reasoning chains
- Handles logical validation

6. analysis_agent:
- Performs analysis
- Processes analytical results
- Handles insight generation

7. learning_agent:
- Learns from interactions
- Updates knowledge
- Handles pattern recognition

### Integration & Control Agents
1. integration_agent:
- Combines agent responses
- Manages integration flow
- Handles consistency

2. validation_agent:
- Validates responses
- Ensures data quality
- Handles validation rules

3. orchestration_agent:
- Advanced agent orchestration and flow management
- Capabilities:
  * Flow state tracking and validation
  * Analytics integration
  * Resource allocation
  * Swarm configuration validation
  * Pattern management
  * Execution monitoring
- Key Components:
  ```python
  # Flow state tracking
  active_flows = {}  # flow_id -> flow_state
  flow_patterns = {}  # pattern_id -> pattern_config
  execution_monitors = {}  # task_id -> monitor_state
  resource_allocations = {}  # resource_id -> allocation_state
  dependency_graph = {}  # task_id -> dependencies
  swarm_validations = {}  # swarm_id -> validation_state
  ```

- Flow State Management:
  ```python
  flow_state = {
      "status": "active",
      "start_time": timestamp,
      "steps_completed": 0,
      "current_phase": "initialization",
      "metrics": {},
      "needs_attention": False,
      "analytics": {
          "last_update": None,
          "performance": {},
          "predictions": {},
          "optimizations": []
      },
      "validation": {
          "last_check": None,
          "issues": [],
          "patterns": [],
          "status": "pending"
      }
  }
  ```

- Validation Integration:
  ```python
  # Swarm configuration validation
  validation_result = await self._validate_swarm_config(
      swarm_config,
      debug_flags
  )

  # Validation pattern tracking
  validation_patterns = {
      "type": issue.get("type"),
      "severity": issue.get("severity", "low"),
      "description": issue.get("description"),
      "frequency": count,
      "first_seen": timestamp,
      "last_seen": timestamp
  }
  ```

- Analytics Integration:
  ```python
  # Apply analytics insights
  flow_state["analytics"] = {
      "last_update": timestamp,
      "performance": analytics.analytics.get("analytics", {}),
      "predictions": {},
      "optimizations": []
  }

  # Handle insights
  for insight in analytics.insights:
      if insight.get("type") == "performance":
          # Update performance metrics
      elif insight.get("type") == "prediction":
          # Store predictions
      elif insight.get("type") == "optimization":
          # Add optimization suggestions
      elif insight.get("type") == "validation":
          # Track validation patterns
  ```

4. dialogue_agent:
- Generates responses
- Handles natural language
- Manages conversation flow

5. synthesis_agent:
- Creates final output
- Combines all inputs
- Handles coherence

6. execution_agent:
- Advanced action execution management
- Capabilities:
  * Executes and tracks action sequences
  * Manages resource usage
  * Handles error recovery
  * Controls retry strategies
  * Manages execution schedules
- Key Components:
  ```python
  # Execution tracking
  active_sequences = {}  # sequence_id -> sequence_state
  execution_patterns = {}  # pattern_id -> pattern_config
  resource_usage = {}  # resource_id -> usage_state
  error_recovery = {}  # error_id -> recovery_state
  retry_states = {}  # action_id -> retry_state
  schedule_queue = {}  # priority -> action_queue
  ```

7. task_agent:
- Advanced task analysis and management
- Capabilities:
  * Task analysis
  * Dependency tracking
  * Domain validation
  * Priority assessment
  * Task lifecycle management
  * Resource allocation
  * Agent assignment
- Key Methods:
  ```python
  # Task Analysis
  async def analyze_and_store(
      self,
      content: Dict[str, Any],
      target_domain: Optional[str] = None
  ):
      """Analyze tasks and store results with domain awareness."""
      result = await self.analyze_tasks(
          content,
          metadata={"domain": target_domain or self.domain}
      )
      
      # Store task analysis
      await self.store_memory(
          content={
              "type": "task_analysis",
              "content": content,
              "analysis": {
                  "tasks": result.tasks,
                  "confidence": result.confidence,
                  "dependencies": result.dependencies,
                  "timestamp": datetime.now().isoformat()
              }
          }
      )
  
  # Task Management
  async def create_task(
      self,
      task_id: str,
      task_data: Dict[str, Any],
      domain: Optional[str] = None,
      metadata: Optional[Dict] = None
  ):
      """Create a new task."""
      task = {
          "task_id": task_id,
          "status": task_data.get("status", "pending"),
          "type": task_data.get("type", "unknown"),
          "content": task_data.get("content", {}),
          "created_at": datetime.now().isoformat(),
          "domain": domain or self.domain,
          "metadata": metadata or {},
          "assigned_agents": task_data.get("assigned_agents", []),
          "dependencies": task_data.get("dependencies", []),
          "resources": task_data.get("resources", {})
      }
      
      await self.memory_system.episodic.store_memory(
          Memory(
              content=task,
              type="task",
              importance=0.8,
              context={
                  "domain": domain or self.domain,
                  "task_id": task_id,
                  "task_type": task["type"]
              }
          )
      )
  ```

8. response_agent:
- Advanced response analysis and validation
- Capabilities:
  * Component validation
  * Domain validation
  * Quality assessment
  * Response structure tracking
- Key Methods:
  ```python
  async def analyze_and_store(
      self,
      content: Dict[str, Any],
      target_domain: Optional[str] = None
  ):
      """Analyze response and store results with domain awareness."""
      result = await self.analyze_response(
          content,
          metadata={"domain": target_domain or self.domain}
      )
      
      # Store analysis results
      await self.store_memory(
          content={
              "type": "response_analysis",
              "content": content,
              "analysis": {
                  "components": result.components,
                  "confidence": result.confidence,
                  "structure": result.structure,
                  "timestamp": datetime.now().isoformat()
              }
          }
      )
  ```

### Analytics & Integration Agents
1. swarm_metrics_agent:
- Tracks swarm performance metrics
- Capabilities:
  * Collects performance data
  * Analyzes behavior patterns
  * Identifies optimization opportunities
  * Generates performance insights
- Key Components:
  ```python
  # Performance Analysis
  patterns = {
      "performance_trends": self._analyze_performance_trends(metrics_data),
      "resource_utilization": self._analyze_resource_utilization(metrics_data),
      "error_patterns": self._analyze_error_patterns(metrics_data),
      "optimization_opportunities": self._identify_optimization_opportunities(metrics_data)
  }

  # Metrics Storage
  await self.store.run_query("""
      MATCH (s:Swarm {id: $swarm_id})
      CREATE (m:SwarmMetrics {
          id: $id,
          metrics: $metrics,
          timestamp: $timestamp
      })
      CREATE (s)-[:HAS_METRICS]->(m)
      RETURN m
  """)
  ```

2. metrics_agent:
- Advanced metrics management
- Capabilities:
  * Metrics collection and tracking
  * Collection strategies
  * Aggregation rules
  * Calculation templates
  * Retention policies
- Key Components:
  ```python
  # Metrics tracking
  active_metrics = {}  # metric_id -> metric_state
  collection_strategies = {}  # strategy_id -> strategy_config
  aggregation_rules = {}  # rule_id -> rule_config
  calculation_templates = {}  # template_id -> template_config
  retention_policies = {}  # policy_id -> policy_config
  ```

3. analytics_agent:
- Analyzes system performance
- Tracks metrics and patterns
- Generates insights
- Provides optimization suggestions
- Integrates with validation

3. swarm_registry_agent:
- Advanced swarm pattern management
- Capabilities:
  * Pattern registration
  * Configuration validation
  * Lifecycle tracking
  * Pattern management
- Key Methods:
  ```python
  async def register_pattern(
      self,
      pattern_type: str,
      config: Dict[str, Any],
      metadata: Optional[Dict[str, Any]] = None
  ):
      """Register new swarm pattern."""
      pattern_data = {
          "id": str(uuid.uuid4()),
          "type": pattern_type,
          "config": config,
          "metadata": metadata or {},
          "created_at": datetime.now().isoformat(),
          "status": "active"
      }
      
      # Store in Neo4j
      await self.store.run_query("""
          CREATE (p:SwarmPattern {
              id: $id,
              type: $type,
              config: $config,
              metadata: $metadata,
              created_at: $created_at,
              status: $status
          })
          RETURN p
      """)
  ```

4. integration_agent:
- Core integration functionality
- Capabilities:
  * Content integration with domain awareness
  * Integration validation and confidence scoring
  * Insight extraction and validation
  * Issue tracking and severity assessment
  * Similar integration matching via vector store
- Key Components:
  ```python
  class IntegrationResult:
      def __init__(
          self,
          is_valid: bool,
          integration: Dict,
          insights: List[Dict],
          confidence: float,
          metadata: Optional[Dict] = None,
          issues: Optional[List[Dict]] = None
      )
  ```

### Visualization Agents
1. visualization_agent:
- Advanced visualization management
- Capabilities:
  * Visualization state tracking
  * Layout template management
  * Chart template handling
  * Rendering engine integration
  * Strategy optimization
- Key Components:
  ```python
  # State tracking
  active_visualizations = {}  # visualization_id -> state
  visualization_strategies = {}  # strategy_id -> config
  layout_templates = {}  # template_id -> config
  chart_templates = {}  # template_id -> config
  rendering_engines = {}  # engine_id -> config
  ```

### Infrastructure & Core Services

#### Language Model Integration (LMStudioLLM)
- Core LM Studio integration for agent capabilities
- Responsibilities:
  * Structured completions with response models
  * Content analysis with templates
  * Analytics processing
  * Error handling and validation
- Key Components:
  ```python
  class LMStudioLLM:
      def __init__(
          self,
          chat_model: str,
          embedding_model: str,
          api_base: str = "http://localhost:1234/v1"
      )
      
      async def get_structured_completion(
          self,
          prompt: str,
          response_model: Any,
          agent_type: Optional[str] = None,
          metadata: Optional[Dict] = None,
          max_tokens: int = 1000
      )
      
      async def analyze(
          self,
          content: Dict[str, Any],
          template: str = "parsing_analysis",
          max_tokens: int = 1000
      )
  ```

#### Knowledge Graph Components
1. concept_manager (ConceptManager):
- Core knowledge graph management
- Responsibilities:
  * Manages concept definitions in Neo4j
  * Handles concept relationships
  * Updates concept hierarchies
  * Validates concept integrity
  * Maintains semantic links
- Integration:
  * Works with graph_store for persistence
  * Coordinates with memory_agent
  * Supports knowledge validation
  * Manages concept lifecycle
- Domain Management:
  * Handles cross-domain access requests
  * Manages domain relationships
  * Validates domain access
  * Tracks domain-specific knowledge
  ```python
  # Cross-domain request example
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

2. graph_store (GraphStore):
- Neo4j database integration
- Responsibilities:
  * Handles Neo4j operations
  * Manages graph schema
  * Handles graph queries
  * Manages graph indices
  * Ensures data consistency
- Knowledge Operations:
  * Lists available domains
  * Manages domain relationships
  * Links tasks to concepts
  * Retrieves graph data
  * Handles task-concept references
- Integration:
  * Primary storage for concepts
  * Supports DAG operations
  * Manages relationships
  * Handles graph traversal
- Example Operations:
  ```python
  # List domains
  domains = await memory_system.semantic.run_query("""
      MATCH (d:Domain)
      RETURN d.name as name, d.type as type, 
             d.description as description
  """)

  # Link task to concept
  await memory_system.semantic.store_knowledge({
      "relationships": [{
          "from": f"task:{task_id}",
          "to": f"concept:{concept_id}",
          "type": "REFERENCES",
          "metadata": metadata,
          "timestamp": datetime.now().isoformat()
      }]
  })
  ```

3. agent_store (AgentStore):
- Agent state persistence
- Responsibilities:
  * Manages agent records
  * Tracks agent states
  * Handles agent relationships
  * Maintains agent history
  * Validates agent operations
  * Coordinates with memory_system
  * Supports agent recovery

4. profile_store (ProfileStore):
- User profile management
- Responsibilities:
  * Manages user profiles
  * Handles preferences
  * Maintains user history
  * Manages access control
  * Validates profile updates
  * Supports domain access
  * Handles cross-domain requests

### Self & Thread Management
1. self_model_agent:
- Maintains system self-model
- Updates system state
- Tracks capabilities
- Manages self-reflection
- Handles state transitions

2. thread_manager:
- Advanced thread management
- Capabilities:
  * Thread creation and verification
  * Message handling
  * Sub-thread management
  * Thread summarization
  * Layer synchronization
- Key Methods:
  ```python
  async def create_thread(
      self,
      thread_id: str,
      task_id: str,
      domain: Optional[str] = None,
      metadata: Optional[Dict] = None
  ):
      """Create a new thread."""
      thread_data = {
          "thread_id": thread_id,
          "task_id": task_id,
          "status": "active",
          "created_at": datetime.now().isoformat(),
          "message_count": 0,
          "domain": domain or self.domain
      }
      
      # Store in both semantic and episodic layers
      await self._store_thread(
          thread_data,
          domain=domain,
          metadata=metadata
      )
  
  async def post_message(
      self,
      thread_id: str,
      message_id: str,
      content: str,
      domain: Optional[str] = None,
      metadata: Optional[Dict] = None
  ):
      """Post a message to a thread."""
      message_data = {
          "message_id": message_id,
          "thread_id": thread_id,
          "content": content,
          "created_at": datetime.now().isoformat(),
          "domain": domain or self.domain,
          "metadata": metadata or {}
      }
      
      await self.memory_system.store_experience(
          Memory(
              id=message_id,
              content=message_data,
              type="message",
              importance=0.6,
              context={
                  "domain": domain or self.domain,
                  "thread_id": thread_id,
                  "message_id": message_id
              }
          )
      )
  ```

3. tiny_factory:
- Creates specialized agents
- Manages agent initialization
- Handles agent configuration
- Validates agent creation
- Maintains agent registry

### Monitoring Agents
1. monitoring_agent:
- Tracks processing
- Handles metrics
- Manages monitoring state
- Integrates with analytics
- Provides real-time insights

2. alerting_agent:
- Handles alerts
- Manages notifications
- Tracks issues
- Coordinates responses
- Prioritizes alerts

3. debugging_agent:
- Handles debug logging
- Manages debug state
- Tracks debug info
- Supports troubleshooting
- Integrates with monitoring

4. logging_agent:
- Advanced log management
- Capabilities:
  * Log state tracking
  * Format template management
  * Storage policy handling
  * Context rule processing
  * Enrichment rule application
  * Rotation policy management
- Key Components:
  ```python
  # Logging tracking
  active_logs = {}  # log_id -> log_state
  format_templates = {}  # template_id -> template_config
  storage_policies = {}  # policy_id -> policy_config
  context_rules = {}  # rule_id -> rule_config
  enrichment_rules = {}  # rule_id -> rule_config
  rotation_policies = {}  # policy_id -> policy_config
  ```

## Agent Initialization

Agents are initialized through dependencies.py:
```python
# Core cognitive agents
get_belief_agent()
get_desire_agent()
get_emotion_agent()
get_reflection_agent()
get_meta_agent()
get_self_model_agent()
get_analysis_agent()
get_research_agent()
get_integration_agent()
get_memory_agent()
get_planning_agent()
get_reasoning_agent()
get_learning_agent()

# Support agents
get_parsing_agent()
get_orchestration_agent()
get_dialogue_agent()
get_context_agent()
get_validation_agent()
get_synthesis_agent()
get_alerting_agent()
get_monitoring_agent()
get_debugging_agent()
get_schema_agent()
```

## Processing Flow

The processing flow involves two key components:

### 1. Meta Agent's Cognitive Architecture

The meta_agent coordinates the cognitive processing:

1. Task Detection & Analysis:
```python
# Analyze cognitive needs
cognitive_needs = await self._analyze_cognitive_needs(content, metadata)

# Spawn required agents/teams
for need in cognitive_needs:
    if need["type"] == "team":
        team = await self.create_team(
            team_type=need["team_type"],
            domain=need["domain"],
            capabilities=need["capabilities"]
        )
    elif need["type"] == "agent":
        agent = await self.spawn_agent(
            agent_type=need["agent_type"],
            domain=need["domain"],
            capabilities=need["capabilities"]
        )
```

2. Cognitive Processing:
```python
# Process through cognitive layers
processed = content
for agent_type, agent in agents.items():
    result = await agent.process(processed)
    processed = result.content

# Store and reflect
memory_id = await self.store_memory(
    content=str(processed),
    importance=0.8,
    context={"type": "cognitive_processing"}
)

# Update state and reflect
self.update_state({
    "emotions": {
        "cognitive_load": self._assess_complexity(processed),
        "processing_confidence": 0.8
    },
    "goals": ["Complete cognitive processing"]
})
await self.reflect()
```

### 2. Nova Endpoints Processing Flow

The actual processing flow in nova_endpoints.py's ask_nova endpoint:

1. Initial Processing:
```python
# Schema validation
schema_result = await schema_agent.validate_schema(
    content=content,
    schema_type="user_input",
    metadata={"debug_flags": debug_flags}
)

# Input parsing
parsed_input = await parsing_agent.parse_text(
    request.content,
    metadata={
        "debug_flags": debug_flags,
        "schema_result": schema_result.dict()
    }
)
```

2. Context & Memory:
```python
# Get context
context = await context_agent.get_context({
    "query": parsed_input.response,
    "workspace": request.workspace,
    "domain": "general",
    "debug_flags": debug_flags
})

# Get memories
memory_context = await memory_agent.retrieve_relevant_memories({
    "query": parsed_input.response,
    "context": context,
    "debug_flags": debug_flags
})
```

3. Planning & Research:
```python
# Create plan
plan = await planning_agent.create_plan({
    "query": parsed_input.response,
    "context": context,
    "debug_flags": debug_flags
})

# Gather information
research_response = await research_agent.gather_information(
    query=parsed_input.response,
    context=context,
    plan=plan,
    metadata={"debug_flags": debug_flags}
)
```

4. Cognitive Processing:
```python
# Meta processing
meta_response = await meta_agent.process_interaction(
    content=parsed_input.response,
    metadata={
        "type": "user_query",
        "workspace": request.workspace,
        "domain": "general",
        "context": context,
        "debug_flags": debug_flags,
        "agents": {
            "research": {
                "agent": research_agent,
                "validation_result": research_response.validation
            },
            "analysis": {
                "agent": analysis_agent,
                "validation_result": analysis_response.validation
            },
            "belief": {
                "agent": belief_agent
            },
            "desire": {
                "agent": desire_agent
            },
            "emotion": {
                "agent": emotion_agent
            },
            "reflection": {
                "agent": reflection_agent
            },
            "integration": {
                "agent": integration_agent
            }
        }
    }
)
```

5. Response Generation:
```python
# Integration
integrated_response = await integration_agent.integrate({
    "parsed_input": parsed_input,
    "research": research_response,
    "analysis": analysis_response,
    "beliefs": belief_response,
    "desires": desire_response,
    "emotions": emotion_response,
    "reflections": reflection_response,
    "context": context
})

# Validation
validated_response = await validation_agent.validate({
    "integrated_response": integrated_response,
    "context": context,
    "beliefs": belief_response
})

# Orchestration
orchestrated_response = await orchestration_agent.process_request({
    "validated_response": validated_response,
    "context": context
})

# Dialogue
dialogue_response = await dialogue_agent.generate_response({
    "orchestrated_response": orchestrated_response,
    "emotions": emotion_response,
    "context": context
})
```

6. Final Processing:
```python
# Synthesis
final_response = await synthesis_agent.synthesize({
    "parsed_input": parsed_input,
    "research": research_response,
    "analysis": analysis_response,
    "beliefs": belief_response,
    "desires": desire_response,
    "emotions": emotion_response,
    "reflections": reflection_response,
    "integrated": integrated_response,
    "validated": validated_response,
    "orchestrated": orchestrated_response,
    "dialogue": dialogue_response,
    "context": context,
    "reasoning": reasoning_context
})

# Learning
await learning_agent.learn_from_interaction({
    "query": parsed_input.response,
    "response": final_response,
    "context": context,
    "research": research_response,
    "analysis": analysis_response,
    "debug_flags": debug_flags
})

# Memory storage
await memory_agent.store_interaction_memory({
    "query": parsed_input.response,
    "response": final_response,
    "learned_knowledge": learning_agent.get_learned_knowledge(),
    "debug_flags": debug_flags
})
```

## Agent Interaction Patterns

The system supports multiple interaction patterns through different components:

### 1. Meta Agent Team Patterns
```python
# Team composition based on complexity
def _determine_team_composition(self, requirements):
    complexity = requirements["complexity"]
    if complexity > 0.8:
        team_size = 5  # Large team for complex tasks
    elif complexity > 0.5:
        team_size = 3  # Medium team for moderate tasks
    else:
        team_size = 2  # Small team for simple tasks
```

### 2. Task Management Patterns
```python
# Task states with validation rules
TASK_STATES = {
    "pending": {
        "transitions": ["in_progress", "blocked"],
        "validation": lambda task: True
    },
    "in_progress": {
        "transitions": ["completed", "blocked", "paused_for_human"],
        "validation": lambda task: task.get("assignee") is not None
    },
    "blocked": {
        "transitions": ["in_progress"],
        "validation": lambda task: len(task.get("blocked_by", [])) > 0
    },
    "completed": {
        "transitions": [],  # Terminal state
        "validation": lambda task: all(subtask.get("completed", False) 
                                    for subtask in task.get("sub_tasks", []))
    }
}
```

### 3. Coordination Patterns

While coordination_agent.py defines different architectures and patterns, the current implementation uses a primarily sequential flow:

### Defined Patterns (Not Fully Implemented)
```python
# Valid swarm architectures
VALID_ARCHITECTURES = ["hierarchical", "parallel", "sequential", "mesh"]
VALID_SWARM_TYPES = ["MajorityVoting", "RoundRobin", "GraphWorkflow"]
VALID_COMMUNICATION_PATTERNS = ["broadcast", "direct", "group"]
```

### Actual Implementation
The coordination functionality focuses on:
1. Processing coordination (process_coordination)
2. Managing groups and assignments (_extract_groups, _extract_assignments)
3. Handling resources (_extract_resources)
4. Tracking issues (_extract_issues)
5. Validating coordination (_determine_validity)

Core coordination code in coordination.py handles:
```python
class CoordinationResult:
    def __init__(
        self,
        is_valid: bool,
        groups: Dict[str, Dict],
        assignments: Dict[str, List[str]],
        resources: Dict[str, Any],
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    )
```

This manages:
- Group structure and status
- Agent assignments to groups
- Resource allocation
- Task dependencies
- Validation and issues

## Agent Tracking & Monitoring

Implementation Files:
- src/nia/agents/monitoring/agent_tracking.py - Core tracking implementation
- src/nia/agents/monitoring/models.py - Data models and schemas
- src/nia/agents/monitoring/storage.py - Storage integration
- src/nia/agents/monitoring/debug.py - Debug channel integration

### Core Models (src/nia/agents/monitoring/models.py)
```typescript
// Agent Action Record
interface AgentAction {
  agent_id: string;
  action_type: string;
  timestamp: string;
  details: Record<string, unknown>;
  result?: Record<string, unknown>;
}

// Enhanced Message Metadata
interface MessageMetadata {
  agent_actions: AgentAction[];
  cognitive_state?: Record<string, unknown>;
  task_context?: Record<string, unknown>;
  debug_info?: Record<string, unknown>;
}

// Enhanced Thread Model
interface Thread {
  id: string;
  title: string;
  domain: string;         // default: "general"
  status: string;         // default: "active"
  created_at: string;     // ISO date
  updated_at: string;     // ISO date
  workspace: string;      // default: "personal"
  participants: ThreadParticipant[];
  metadata: {
    agent_summary: {
      active_agents: string[];
      task_type: string;
      workspace: string;
    };
    agent_context: {
      task_detection?: Record<string, unknown>;
      plan?: Record<string, unknown>;
    };
  };
  validation: ThreadValidation;
}
```

### Agent Activity Tracking (src/nia/agents/monitoring/agent_tracking.py)
The system now tracks agent activities through:

1. Message Level:
- Each message includes agent actions
- Cognitive state is captured
- Task context is preserved

2. Thread Level:
- Agent summaries in thread metadata
- Active agents are tracked
- Task types and workspace context preserved

3. Memory System:
- Ephemeral storage for session context
- Permanent storage for learned knowledge
- Agent context in memory metadata

### Monitoring Integration (src/nia/agents/monitoring/monitoring_agent.py)
The monitoring_agent now provides:

1. Agent Performance:
```python
async def track_agent_performance(
    self,
    agent_id: str,
    action_type: str,
    result: Dict[str, Any]
):
    """Track agent performance metrics."""
    metrics = {
        "action_type": action_type,
        "timestamp": datetime.now().isoformat(),
        "success": result.get("success", True),
        "duration": result.get("duration"),
        "error": result.get("error")
    }
    
    await self.store_metrics(agent_id, metrics)
```

2. Debug Channel Integration:
```python
async def log_to_channel(
    self,
    channel: str,
    message: str,
    metadata: Optional[Dict] = None
):
    """Log to debug channels (#NovaTeam, #NovaSupport)."""
    await self.debugging_agent.log_to_channel(
        channel=channel,
        message=message,
        metadata=metadata
    )
```

3. Activity Tracking:
```python
async def track_activity(
    self,
    agent_id: str,
    activity: Dict[str, Any]
):
    """Track agent activities."""
    await self.memory_system.store_ephemeral({
        "type": "agent_activity",
        "content": {
            "agent_id": agent_id,
            "activity": activity,
            "timestamp": datetime.now().isoformat()
        }
    })
```

## Next Steps

1. Implement Defined Patterns:
- Add hierarchical processing support
- Enable parallel agent execution
- Implement mesh communication
- Add swarm type support

2. Enhance Coordination:
- Add dynamic team formation
- Implement resource optimization
- Add adaptive task routing
- Enhance validation patterns

3. Improve Monitoring:
- Add detailed agent metrics
- Implement pattern analysis
- Add performance tracking
- Enhance debug support
