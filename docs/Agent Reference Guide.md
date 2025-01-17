# Agent Reference Guide

## Agent Architecture Overview

The Nova agent system uses a three-layer prompt architecture:

### 1. Core Interface Layer (core/interfaces/prompts.py)
- Defines the basic JSON response structure all agents must follow:
```python
{
    "response": "Your main response text here",
    "concepts": [...],
    "key_points": [...],
    "implications": [...],
    "uncertainties": [...],
    "reasoning": [...]
}
```
- Provides simple agent type descriptions in AGENT_PROMPTS
- Ensures consistent response format across all agents

### 2. Configuration Layer (config/agent_config.py)
- Provides shared template and responsibilities:
  * BASE_AGENT_TEMPLATE: Core template defining:
    - Memory system integration
    - Domain management
    - Swarm collaboration
    - Response formats
    - Metacognition
  * AGENT_RESPONSIBILITIES: Specific responsibilities for each agent type
  * get_agent_prompt(): Function that combines:
    - BASE_AGENT_TEMPLATE
    - Agent-specific responsibilities
    - Domain and skills information

### 3. Individual Agent Layer (config/prompts/[agent]_agent.py)
- Most detailed level specific to each agent
- Full breakdown of responsibilities
- Detailed response formats
- Special instructions
- Integration guidelines
- Channel-specific handling

### How It Works Together
1. When an agent is created:
   - Gets base JSON format from prompts.py
   - Gets template and responsibilities from agent_config.py
   - Gets specific details from its prompt file

2. When processing input:
   - Uses base format to structure response
   - Follows template for overall behavior
   - Uses responsibilities for specific actions

3. Example Flow:
```python
# 1. Agent gets prompt from config
prompt = get_agent_prompt(
    agent_type="parsing",
    domain="professional",
    skills=["text_parsing"]
)

# 2. Agent sends to LLM
response = await llm.get_structured_completion(
    prompt=prompt,
    agent_type="parsing"
)

# 3. Response follows base format
assert "response" in response
assert "concepts" in response
assert "key_points" in response
```

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

### Core Cognitive Agents
1. meta_agent:
- High-level cognitive coordination
- Manages agent teams
- Handles task distribution

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
- Manages agent flow
- Handles resource allocation
- Coordinates processing

4. dialogue_agent:
- Generates responses
- Handles natural language
- Manages conversation flow

5. synthesis_agent:
- Creates final output
- Combines all inputs
- Handles coherence

## Memory System Integration

Agents interact with a dual memory system:

### 1. Vector Storage (Qdrant)
- Stores text embeddings for similarity search
- Used for finding relevant content
- Supports metadata filtering

### 2. Knowledge Graph (Neo4j)
- Stores concepts and relationships
- Node types:
  * Concept: Core knowledge units
  * Brand: Brand-related concepts
  * Policy: Policy definitions
  * Customer: Customer information
- Rich relationship types with properties
- Domain-aware with validation

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

## Processing Flow

The processing flow involves:

### 1. Initial Processing
```python
# Schema validation
schema_result = await schema_agent.validate_schema(content)

# Input parsing
parsed_input = await parsing_agent.parse_text(content)
```

### 2. Context & Memory
```python
# Get context
context = await context_agent.get_context(parsed_input)

# Get memories
memory_context = await memory_agent.retrieve_relevant_memories(parsed_input)
```

### 3. Cognitive Processing
```python
# Meta processing
meta_response = await meta_agent.process_interaction(content)

# Integration
integrated_response = await integration_agent.integrate(all_responses)
```

### 4. Response Generation
```python
# Validation
validated_response = await validation_agent.validate(integrated_response)

# Dialogue
dialogue_response = await dialogue_agent.generate_response(validated_response)
```

## LM Studio Integration

The LM Studio integration spans multiple files to handle the three-layer prompt architecture:

### 1. Core Interface Integration (src/nia/core/interfaces/prompts.py)
```python
# Base JSON format that LM Studio must follow
SYSTEM_PROMPT = """You are an AI assistant specialized in {agent_type} tasks.
Please provide responses in the following JSON format:
{
    "response": "Your main response text here",
    "concepts": [...],
    "key_points": [...],
    "implications": [...],
    "uncertainties": [...],
    "reasoning": [...]
}"""

# Simple agent type descriptions
AGENT_PROMPTS = {
    "parsing": "You are specialized in parsing and structuring information.",
    "meta": "You are specialized in meta-level analysis.",
    # ...
}
```

### 2. Configuration Integration (src/nia/config/agent_config.py)
```python
# Template that LM Studio uses for all agents
BASE_AGENT_TEMPLATE = """You are an AI agent specialized in {agent_type} operations.

Memory System Integration:
- Store episodic memories
- Create semantic memories
- Participate in consolidation
...

Domain Management:
- Primary domain: {domain}
- Respect domain boundaries
...
"""

# Agent-specific responsibilities
AGENT_RESPONSIBILITIES = {
    "parsing": """
        - Extract structured data
        - Identify components
        - Validate structure
        ...
    """,
    # ...
}

def get_agent_prompt(agent_type: str, domain: str, skills: List[str]) -> str:
    """Combines template + responsibilities for LM Studio."""
    return BASE_AGENT_TEMPLATE.format(...)
```

### 3. Individual Agent Integration (src/nia/config/prompts/[agent]_agent.py)
Example for parsing agent (src/nia/config/prompts/parsing_agent.py):
```python
PARSING_AGENT_PROMPT = """You are Nova's parsing system agent.

Core Responsibilities:
1. Input Processing
- Parse input content
- Extract key elements
...

Response Format:
{
    "parsing": {
        "result": {
            "content": "Parsed content",
            "quality": 0.0-1.0,
            ...
        },
        ...
    }
}
"""
```

### LM Studio Processing Flow (src/nia/memory/llm.py)
```python
class LMStudioLLM:
    async def get_structured_completion(
        self,
        prompt: str,
        agent_type: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Get completion from LM Studio with format validation."""
        # 1. Format prompt with agent type
        formatted_prompt = SYSTEM_PROMPT.format(
            agent_type=agent_type
        )
        
        # 2. Add agent responsibilities
        agent_prompt = get_agent_prompt(
            agent_type=agent_type,
            domain=metadata.get("domain", "professional"),
            skills=metadata.get("skills", [])
        )
        
        # 3. Send to LM Studio API
        response = await self._call_api(
            prompt=formatted_prompt + "\n" + agent_prompt,
            max_tokens=1000
        )
        
        # 4. Validate JSON format
        try:
            parsed = json.loads(response)
            if not all(k in parsed for k in ["response", "concepts", "key_points"]):
                raise ValueError("Missing required fields")
            return parsed
        except json.JSONDecodeError:
            # Handle invalid JSON format
            return self._create_error_response()
```

### Test Integration (tests/nova/test_lmstudio_integration.py)
```python
@pytest.mark.asyncio
async def test_lmstudio_prompt_layers():
    """Test LM Studio handles all three prompt layers."""
    # 1. Test base format
    response = await llm.get_structured_completion(
        prompt=SYSTEM_PROMPT.format(agent_type="parsing"),
        agent_type="parsing"
    )
    assert "response" in response
    assert "concepts" in response
    
    # 2. Test with agent config
    response = await llm.get_structured_completion(
        prompt=get_agent_prompt("parsing", "professional", ["text_parsing"]),
        agent_type="parsing"
    )
    assert response["concepts"]  # Should have concepts
    
    # 3. Test with agent-specific prompt
    response = await llm.get_structured_completion(
        prompt=PARSING_AGENT_PROMPT,
        agent_type="parsing"
    )
    assert "parsing" in response  # Should have parsing-specific format
```

## TinyWorld Agent Spawning

When an agent is spawned in TinyWorld, it goes through multiple layers of initialization:

### 1. TinyFactory Creation (src/nia/agents/tiny_factory.py)
```python
class TinyFactory:
    async def create_agent(
        self,
        agent_type: str,
        name: str,
        world: NIAWorld,
        memory_system: TwoLayerMemorySystem,
        domain: str = "professional"
    ) -> TinyTroupeAgent:
        """Create a new agent with proper initialization."""
        # 1. Get agent class
        agent_class = self._get_agent_class(agent_type)
        
        # 2. Get agent prompt
        prompt = get_agent_prompt(
            agent_type=agent_type,
            domain=domain,
            skills=self._get_default_skills(agent_type)
        )
        
        # 3. Create agent instance
        agent = agent_class(
            name=name,
            memory_system=memory_system,
            world=world,
            domain=domain,
            prompt=prompt
        )
        
        # 4. Initialize in TinyWorld
        await world.add_agent(agent)
        
        return agent
```

### 2. TinyWorld Integration (src/nia/world/environment.py)
```python
class NIAWorld(TinyWorld):
    async def add_agent(self, agent: TinyTroupeAgent):
        """Add agent to world with prompt initialization."""
        # 1. Register in world
        self.agents[agent.name] = agent
        
        # 2. Set up agent's world view
        agent_view = {
            "domain": agent.domain,
            "world_state": self.get_state(),
            "active_agents": list(self.agents.keys())
        }
        await agent.initialize_world_view(agent_view)
        
        # 3. Initialize agent's LLM with prompts
        if agent.memory_system and agent.memory_system.llm:
            # Set base prompt
            await agent.memory_system.llm.initialize_prompt(
                SYSTEM_PROMPT.format(agent_type=agent.agent_type)
            )
            
            # Add agent config prompt
            await agent.memory_system.llm.add_prompt(agent.prompt)
            
            # Add agent-specific prompt if exists
            if hasattr(agent, 'agent_prompt'):
                await agent.memory_system.llm.add_prompt(agent.agent_prompt)
```

### 3. TinyTroupeAgent Integration (src/nia/agents/tinytroupe_agent.py)
```python
class TinyTroupeAgent:
    async def initialize_world_view(self, view: Dict[str, Any]):
        """Initialize agent's view of the world."""
        self.world_view = view
        
        # Update prompt with world context
        if self.memory_system and self.memory_system.llm:
            world_context = f"""
            World State:
            - Domain: {view['domain']}
            - Active Agents: {', '.join(view['active_agents'])}
            """
            await self.memory_system.llm.add_context(world_context)
```

This shows how:
1. TinyFactory creates agents with proper prompts
2. NIAWorld integrates them with all prompt layers
3. TinyTroupeAgent adds world context to prompts

### 4. TinyPerson Integration (src/nia/agents/tiny_person.py)
```python
class TinyPerson:
    """Base person with emotions, goals, and memories."""
    def __init__(
        self,
        name: str,
        attributes: Optional[Dict] = None
    ):
        self.name = name
        self._configuration = {
            "current_emotions": attributes.get("emotions", {}),
            "current_goals": attributes.get("desires", []),
            "capabilities": attributes.get("capabilities", []),
            "occupation": attributes.get("occupation", "AI Assistant")
        }
        
    @property
    def emotions(self) -> Dict[str, str]:
        """Get current emotional state."""
        return self._configuration.get("current_emotions", {})
        
    @property
    def desires(self) -> List[str]:
        """Get current goals/desires."""
        return self._configuration.get("current_goals", [])
        
    def update_state(self, updates: Dict[str, Any]):
        """Update person's state."""
        if "emotions" in updates:
            self._configuration["current_emotions"].update(updates["emotions"])
        if "goals" in updates:
            self._configuration["current_goals"].extend(updates["goals"])

class TinyTroupeAgent(TinyPerson, NovaAgent):
    """Combines TinyPerson with NovaAgent capabilities."""
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None,
        prompt: Optional[str] = None
    ):
        # Initialize TinyPerson first
        TinyPerson.__init__(self, name, attributes)
        
        # Then initialize NovaAgent with prompts
        NovaAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            agent_type=attributes.get("type", "unknown")
        )
        
        # Store prompt for LLM
        self.prompt = prompt
        
        # Add emotional context to prompt
        if self.prompt and self.emotions:
            emotional_context = f"""
            Emotional State:
            {json.dumps(self.emotions, indent=2)}
            
            Goals/Desires:
            {json.dumps(self.desires, indent=2)}
            """
            self.prompt += "\n" + emotional_context
```

This shows how:
1. TinyPerson provides the base personality:
   - Emotions
   - Goals/Desires
   - Capabilities
   - State management

2. TinyTroupeAgent combines:
   - TinyPerson's personality
   - NovaAgent's LLM capabilities
   - Prompt system integration

3. The prompt system includes:
   - Base JSON format (prompts.py)
   - Agent template (agent_config.py)
   - Agent-specific prompt
   - Emotional context from TinyPerson
   - World context from TinyWorld

This creates agents that have both:
- Personality (emotions, goals, capabilities)
- LLM capabilities with contextual prompts

## NIAWorld Environment

NIAWorld extends TinyWorld to provide a rich environment for agents to interact:

### 1. State Management (src/nia/world/environment.py)
```python
class NIAWorld(TinyWorld):
    """Nova's world environment with enhanced state management."""
    def __init__(self):
        self.agents = {}  # name -> agent
        self.state = {
            "domains": {},  # domain -> state
            "interactions": [],  # interaction history
            "resources": {},  # resource management
            "tasks": {}  # active tasks
        }
        self.memory_system = None
        
    async def update_agent_state(
        self,
        agent_name: str,
        updates: Dict[str, Any]
    ):
        """Update agent's state and notify others."""
        agent = self.agents[agent_name]
        
        # 1. Update agent's emotional state
        if "emotions" in updates:
            agent.update_state({"emotions": updates["emotions"]})
            # Notify other agents of emotional change
            await self._notify_agents(
                f"{agent_name} emotional state changed",
                exclude=[agent_name]
            )
        
        # 2. Update agent's goals
        if "goals" in updates:
            agent.update_state({"goals": updates["goals"]})
            # Update task assignments if needed
            await self._update_task_assignments(agent_name)
            
        # 3. Store state change in memory
        if self.memory_system:
            await self.memory_system.store_state_change({
                "agent": agent_name,
                "updates": updates,
                "timestamp": datetime.now().isoformat()
            })
```

### 2. Agent Interactions
```python
class NIAWorld(TinyWorld):
    async def handle_interaction(
        self,
        from_agent: str,
        to_agent: str,
        content: Dict[str, Any]
    ):
        """Handle agent-to-agent interaction."""
        # 1. Validate interaction
        if not self._can_interact(from_agent, to_agent):
            raise ValueError("Invalid interaction")
            
        # 2. Update emotional states
        await self._update_emotional_states(from_agent, to_agent, content)
        
        # 3. Process through receiving agent
        response = await self.agents[to_agent].process_interaction(
            content,
            metadata={
                "from_agent": from_agent,
                "emotional_context": self.agents[from_agent].emotions
            }
        )
        
        # 4. Store interaction in memory
        await self._store_interaction(from_agent, to_agent, content, response)
        
        return response
```

### 3. Domain Management
```python
class NIAWorld(TinyWorld):
    async def validate_domain_access(
        self,
        agent_name: str,
        target_domain: str
    ) -> bool:
        """Validate agent's access to domain."""
        agent = self.agents[agent_name]
        
        # 1. Check direct domain access
        if agent.domain == target_domain:
            return True
            
        # 2. Check cross-domain permissions
        if await self._has_cross_domain_permission(
            agent_name,
            target_domain
        ):
            return True
            
        # 3. Log access attempt
        await self._log_domain_access_attempt(
            agent_name,
            target_domain,
            success=False
        )
        
        return False
```

### 4. Task & Resource Management
```python
class NIAWorld(TinyWorld):
    async def assign_task(
        self,
        task: Dict[str, Any],
        agent_names: List[str]
    ):
        """Assign task to agents."""
        # 1. Validate task
        if not self._is_valid_task(task):
            raise ValueError("Invalid task")
            
        # 2. Check agent capabilities
        for agent_name in agent_names:
            if not self._has_required_capabilities(
                agent_name,
                task["required_capabilities"]
            ):
                raise ValueError(f"Agent {agent_name} missing capabilities")
                
        # 3. Create task assignment
        task_id = str(uuid.uuid4())
        self.state["tasks"][task_id] = {
            "task": task,
            "assigned_agents": agent_names,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        # 4. Update agent goals
        for agent_name in agent_names:
            await self.update_agent_state(
                agent_name,
                {
                    "goals": [f"Complete task {task_id}"],
                    "emotions": {
                        "task_focus": "high",
                        "collaboration_readiness": "active"
                    }
                }
            )
```

### 5. Emotional Influence System
```python
class NIAWorld(TinyWorld):
    async def _update_emotional_states(
        self,
        from_agent: str,
        to_agent: str,
        content: Dict[str, Any]
    ):
        """Update emotional states based on interaction."""
        # 1. Analyze emotional content
        emotional_impact = await self._analyze_emotional_impact(
            content,
            self.agents[from_agent].emotions,
            self.agents[to_agent].emotions
        )
        
        # 2. Update receiving agent's emotions
        await self.update_agent_state(
            to_agent,
            {"emotions": emotional_impact["receiver_emotions"]}
        )
        
        # 3. Update sending agent's emotions
        await self.update_agent_state(
            from_agent,
            {"emotions": emotional_impact["sender_emotions"]}
        )
        
        # 4. Update prompts with new emotional context
        await self._update_agent_prompts(
            [from_agent, to_agent],
            emotional_impact
        )
```

This shows how NIAWorld:
1. Manages agent states and updates
2. Handles agent-to-agent interactions
3. Controls domain access and validation
4. Manages tasks and resources
5. Implements an emotional influence system

The emotional system particularly influences prompts by:
1. Updating agent emotional states
2. Adding emotional context to prompts
3. Influencing agent interactions
4. Affecting task assignments
5. Guiding agent responses

For example, when an agent processes a request:
```python
# 1. Get emotional context
emotional_context = self.emotions

# 2. Add to prompt
prompt_with_emotions = f"""
{self.prompt}

Current Emotional State:
- Task Focus: {emotional_context.get('task_focus', 'neutral')}
- Collaboration: {emotional_context.get('collaboration_readiness', 'neutral')}
- Domain Alignment: {emotional_context.get('domain_confidence', 'neutral')}

Current Goals:
{json.dumps(self.desires, indent=2)}
"""

# 3. Get response with emotional influence
response = await self.llm.get_structured_completion(
    prompt=prompt_with_emotions,
    metadata={"emotional_context": emotional_context}
)
```

### 6. Memory System Integration
```python
class NIAWorld(TinyWorld):
    async def _store_interaction(
        self,
        from_agent: str,
        to_agent: str,
        content: Dict[str, Any],
        response: Dict[str, Any]
    ):
        """Store interaction in memory system."""
        # 1. Store in episodic memory (recent interactions)
        await self.memory_system.episodic.store_memory({
            "type": "interaction",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "content": content,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "emotional_context": {
                "sender": self.agents[from_agent].emotions,
                "receiver": self.agents[to_agent].emotions
            }
        })
        
        # 2. Extract concepts for semantic memory
        concepts = await self._extract_interaction_concepts(
            content, response
        )
        for concept in concepts:
            await self.memory_system.semantic.store_concept(
                name=concept["name"],
                type=concept["type"],
                description=concept["description"],
                metadata={
                    "interaction_id": str(uuid.uuid4()),
                    "agents": [from_agent, to_agent],
                    "emotional_context": concept.get("emotional_context")
                }
            )
            
        # 3. Update interaction patterns
        await self._update_interaction_patterns(
            from_agent, to_agent, content, response
        )

    async def _update_interaction_patterns(
        self,
        from_agent: str,
        to_agent: str,
        content: Dict[str, Any],
        response: Dict[str, Any]
    ):
        """Update and store interaction patterns."""
        # 1. Get recent interactions
        recent = await self.memory_system.episodic.get_recent_memories(
            filter_type="interaction",
            agents=[from_agent, to_agent],
            limit=10
        )
        
        # 2. Analyze patterns
        patterns = await self._analyze_interaction_patterns(recent)
        
        # 3. Store patterns in semantic memory
        for pattern in patterns:
            await self.memory_system.semantic.store_concept(
                name=f"interaction_pattern_{pattern['type']}",
                type="interaction_pattern",
                description=pattern["description"],
                metadata={
                    "agents": [from_agent, to_agent],
                    "frequency": pattern["frequency"],
                    "confidence": pattern["confidence"],
                    "examples": pattern["examples"]
                }
            )
            
        # 4. Update agent prompts with pattern context
        await self._update_agent_prompts_with_patterns(
            [from_agent, to_agent],
            patterns
        )

    async def _update_agent_prompts_with_patterns(
        self,
        agent_names: List[str],
        patterns: List[Dict[str, Any]]
    ):
        """Update agent prompts with interaction patterns."""
        pattern_context = "\n\nInteraction Patterns:\n"
        for pattern in patterns:
            pattern_context += f"""
- Type: {pattern['type']}
  Description: {pattern['description']}
  Frequency: {pattern['frequency']}
  Confidence: {pattern['confidence']}
"""
        
        for agent_name in agent_names:
            agent = self.agents[agent_name]
            if agent.memory_system and agent.memory_system.llm:
                await agent.memory_system.llm.add_context(pattern_context)

    async def get_agent_history(
        self,
        agent_name: str,
        history_type: str = "all"
    ) -> Dict[str, Any]:
        """Get agent's interaction history."""
        # 1. Get episodic memories
        episodic = await self.memory_system.episodic.get_agent_memories(
            agent_name,
            memory_type=history_type
        )
        
        # 2. Get semantic patterns
        patterns = await self.memory_system.semantic.get_agent_patterns(
            agent_name,
            pattern_type=history_type
        )
        
        # 3. Combine with emotional history
        emotional_history = await self._get_emotional_history(
            agent_name
        )
        
        return {
            "episodic_memories": episodic,
            "interaction_patterns": patterns,
            "emotional_history": emotional_history,
            "timestamp": datetime.now().isoformat()
        }
```

This shows how NIAWorld:
1. Stores interactions in both memory layers:
   - Episodic for recent interactions
   - Semantic for concepts and patterns

2. Maintains interaction patterns:
   - Analyzes recent interactions
   - Identifies recurring patterns
   - Updates semantic memory
   - Adjusts agent prompts

3. Tracks agent history:
   - Episodic memories
   - Semantic patterns
   - Emotional history

4. Uses memory for:
   - Improving agent interactions
   - Guiding emotional responses
   - Optimizing task assignments
   - Maintaining context

## Swarm Architecture

NIAWorld supports multiple swarm architectures for agent collaboration:

### 1. Swarm Types (src/nia/swarm/patterns.py)
```python
class SwarmType(Enum):
    HIERARCHICAL = "hierarchical"  # Tree structure with leader
    PARALLEL = "parallel"          # Independent concurrent execution
    SEQUENTIAL = "sequential"      # Chain of dependent tasks
    MESH = "mesh"                  # Dynamic peer-to-peer network

class SwarmPattern(Enum):
    MAJORITY_VOTING = "majority_voting"  # Consensus through voting
    ROUND_ROBIN = "round_robin"          # Take turns processing
    GRAPH_WORKFLOW = "graph_workflow"    # Follow task dependencies
    GROUP_CHAT = "group_chat"            # Multi-agent discussions
```

### 2. Swarm Creation (src/nia/swarm/factory.py)
```python
class SwarmFactory:
    async def create_swarm(
        self,
        swarm_type: SwarmType,
        pattern: SwarmPattern,
        agent_types: List[str],
        world: NIAWorld,
        task: Dict[str, Any]
    ) -> Swarm:
        """Create a new swarm with specified architecture."""
        # 1. Analyze task requirements
        requirements = await self._analyze_task_requirements(task)
        
        # 2. Select optimal team size
        team_size = self._determine_team_size(
            requirements["complexity"],
            requirements["parallelism"]
        )
        
        # 3. Create agents
        agents = []
        for agent_type in agent_types:
            agent = await world.tiny_factory.create_agent(
                agent_type=agent_type,
                name=f"{agent_type}_{uuid.uuid4()}",
                world=world,
                memory_system=world.memory_system,
                domain=task.get("domain", "professional")
            )
            agents.append(agent)
            
        # 4. Configure swarm architecture
        swarm = Swarm(
            agents=agents,
            swarm_type=swarm_type,
            pattern=pattern,
            task=task
        )
        
        # 5. Initialize collaboration patterns
        await self._initialize_collaboration(swarm)
        
        return swarm
```

### 3. Swarm Management (src/nia/swarm/swarm.py)
```python
class Swarm:
    async def process_task(self, task: Dict[str, Any]):
        """Process task through swarm."""
        if self.swarm_type == SwarmType.HIERARCHICAL:
            return await self._process_hierarchical(task)
        elif self.swarm_type == SwarmType.PARALLEL:
            return await self._process_parallel(task)
        elif self.swarm_type == SwarmType.SEQUENTIAL:
            return await self._process_sequential(task)
        else:  # MESH
            return await self._process_mesh(task)
            
    async def _process_hierarchical(self, task: Dict[str, Any]):
        """Process through hierarchical swarm."""
        # 1. Leader assigns subtasks
        leader = self.agents[0]
        subtasks = await leader.decompose_task(task)
        
        # 2. Workers process subtasks
        results = []
        for subtask, worker in zip(subtasks, self.agents[1:]):
            result = await worker.process(subtask)
            results.append(result)
            
        # 3. Leader combines results
        return await leader.combine_results(results)
```

### 4. Collaboration Patterns (src/nia/swarm/collaboration.py)
```python
class CollaborationManager:
    async def handle_collaboration(
        self,
        swarm: Swarm,
        pattern: SwarmPattern
    ):
        """Handle agent collaboration pattern."""
        if pattern == SwarmPattern.MAJORITY_VOTING:
            return await self._handle_voting(swarm)
        elif pattern == SwarmPattern.ROUND_ROBIN:
            return await self._handle_round_robin(swarm)
        elif pattern == SwarmPattern.GRAPH_WORKFLOW:
            return await self._handle_workflow(swarm)
        else:  # GROUP_CHAT
            return await self._handle_group_chat(swarm)
            
    async def _handle_voting(self, swarm: Swarm):
        """Handle majority voting pattern."""
        # 1. Each agent processes independently
        votes = []
        for agent in swarm.agents:
            result = await agent.process(swarm.task)
            votes.append(result)
            
        # 2. Count votes and find majority
        majority = self._find_majority(votes)
        
        # 3. Update agent prompts with voting result
        await self._update_prompts_with_vote(swarm, majority)
        
        return majority
```

### 5. Memory Integration (src/nia/swarm/memory.py)
```python
class SwarmMemory:
    async def update_prompts_with_history(
        self,
        swarm: Swarm
    ):
        """Update agent prompts with swarm history."""
        # 1. Get swarm history
        history = await self._get_swarm_history(swarm)
        
        # 2. Extract patterns
        patterns = await self._analyze_swarm_patterns(history)
        
        # 3. Update each agent's prompt
        for agent in swarm.agents:
            # Add swarm context
            swarm_context = f"""
            Swarm Architecture:
            - Type: {swarm.swarm_type}
            - Pattern: {swarm.pattern}
            - Role: {self._get_agent_role(agent, swarm)}
            
            Collaboration History:
            {self._format_patterns(patterns)}
            
            Team Members:
            {self._format_team_members(swarm.agents)}
            """
            
            # Add to agent's prompt
            if agent.memory_system and agent.memory_system.llm:
                await agent.memory_system.llm.add_context(swarm_context)
```

This shows how:
1. Different swarm types handle tasks:
   - Hierarchical: Leader assigns subtasks
   - Parallel: Independent processing
   - Sequential: Chain of dependencies
   - Mesh: Dynamic collaboration

2. Collaboration patterns determine interaction:
   - Majority Voting: Consensus through votes
   - Round Robin: Take turns processing
   - Graph Workflow: Follow dependencies
   - Group Chat: Multi-agent discussions

3. Memory system influences swarm behavior:
   - Stores swarm history
   - Identifies patterns
   - Updates agent prompts
   - Guides collaboration

For example, when processing a task:
```python
# 1. Meta agent analyzes task
task_analysis = await meta_agent.analyze_task(task)
swarm_requirements = {
    "complexity": task_analysis["complexity"],
    "parallelism": task_analysis["parallelism"],
    "dependencies": task_analysis["dependencies"],
    "domain": task_analysis["domain"]
}

# 2. Coordinator agent determines pattern
pattern = await coordinator_agent.determine_pattern(
    requirements=swarm_requirements,
    available_agents=world.get_available_agents(),
    current_workload=world.get_workload_stats()
)

# 3. Orchestrator agent creates swarm
swarm = await orchestrator_agent.create_swarm(
    pattern=pattern,
    requirements=swarm_requirements,
    world=world
)

# 4. Update prompts with swarm context
await swarm_memory.update_prompts_with_history(swarm)

# 5. Process through swarm
result = await swarm.process_task(task)
```

### Swarm Decision Making

The swarm architecture is determined through collaboration between three key agents:

### 1. Meta Agent's Role (src/nia/agents/specialized/meta_agent.py)
```python
class MetaAgent:
    """Analyzes tasks and determines high-level requirements."""
    
    async def analyze_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task to determine swarm requirements."""
        # 1. Analyze task complexity
        complexity = await self._analyze_complexity(task)
        
        # 2. Check parallelization potential
        parallelism = await self._check_parallelism(task)
        
        # 3. Identify dependencies
        dependencies = await self._identify_dependencies(task)
        
        # 4. Consider user preferences
        user_prefs = await self._get_user_preferences(task)
        
        return {
            "complexity": complexity,
            "parallelism": parallelism,
            "dependencies": dependencies,
            "user_preferences": user_prefs,
            "domain": task.get("domain", "professional")
        }
```

### 2. Coordinator Agent's Role (src/nia/agents/specialized/coordination_agent.py)
```python
class CoordinationAgent:
    """Determines optimal collaboration patterns."""
    
    async def determine_pattern(
        self,
        requirements: Dict[str, Any],
        available_agents: List[Dict[str, Any]],
        current_workload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine best swarm pattern based on requirements."""
        # 1. Select swarm type
        swarm_type = await self._select_swarm_type(
            complexity=requirements["complexity"],
            parallelism=requirements["parallelism"]
        )
        
        # 2. Choose collaboration pattern
        pattern = await self._choose_pattern(
            dependencies=requirements["dependencies"],
            available_agents=available_agents
        )
        
        # 3. Consider user preferences
        if requirements["user_preferences"].get("preferred_pattern"):
            pattern = self._adapt_to_preferences(
                pattern,
                requirements["user_preferences"]
            )
            
        # 4. Validate against current workload
        if not self._can_support_pattern(pattern, current_workload):
            pattern = await self._find_alternative_pattern(
                pattern,
                current_workload
            )
            
        return {
            "swarm_type": swarm_type,
            "pattern": pattern,
            "team_size": self._calculate_team_size(
                requirements["complexity"]
            )
        }
```

### 3. Orchestrator Agent's Role (src/nia/agents/specialized/orchestration_agent.py)
```python
class OrchestrationAgent:
    """Creates and manages swarms based on patterns."""
    
    async def create_swarm(
        self,
        pattern: Dict[str, Any],
        requirements: Dict[str, Any],
        world: NIAWorld
    ) -> Swarm:
        """Create swarm with specified pattern."""
        # 1. Select agents based on pattern
        agents = await self._select_agents(
            pattern["team_size"],
            requirements["domain"]
        )
        
        # 2. Configure swarm
        swarm = Swarm(
            agents=agents,
            swarm_type=pattern["swarm_type"],
            pattern=pattern["pattern"]
        )
        
        # 3. Initialize collaboration
        await self._initialize_collaboration(swarm)
        
        # 4. Set up monitoring
        await self._setup_monitoring(swarm)
        
        # 5. Create UI channel
        channel_id = await self._create_swarm_channel(swarm)
        
        return swarm
```

### UI Integration

The swarm system integrates with the UI through:

1. Task Creation:
```typescript
// User creates task through UI
interface TaskCreation {
    title: string;
    description: string;
    domain: string;
    preferences?: {
        preferred_pattern?: string;
        team_size?: number;
        priority?: string;
    }
}
```

2. Swarm Monitoring:
```typescript
// UI receives swarm updates
interface SwarmUpdate {
    swarm_id: string;
    status: 'forming' | 'active' | 'completed';
    agents: Array<{
        id: string;
        role: string;
        status: string;
    }>;
    progress: {
        completed: number;
        total: number;
        current_phase: string;
    }
}
```

3. Channel Management:
```typescript
// Each swarm gets a UI channel
interface SwarmChannel {
    id: string;
    swarm_id: string;
    name: string;
    agents: string[];
    messages: Array<{
        sender: string;
        content: string;
        timestamp: string;
    }>;
}
```

This shows how:
1. Meta agent analyzes tasks and requirements
2. Coordinator agent determines optimal patterns
3. Orchestrator agent creates and manages swarms
4. UI provides visibility and control

### Memory-Driven Swarm Patterns

The memory system influences swarm decisions through learned patterns:

### 1. Pattern Learning (src/nia/memory/pattern_learning.py)
```python
class SwarmPatternLearning:
    """Learns effective swarm patterns from history."""
    
    async def analyze_successful_patterns(
        self,
        task_type: str,
        domain: str
    ) -> Dict[str, Any]:
        """Analyze patterns that worked well for similar tasks."""
        # 1. Get relevant history
        history = await self.memory_system.semantic.query(
            f"""
            MATCH (t:Task)-[:USED_PATTERN]->(p:SwarmPattern)
            WHERE t.type = $task_type
            AND t.domain = $domain
            AND t.success = true
            RETURN p, count(*) as frequency
            ORDER BY frequency DESC
            """,
            {"task_type": task_type, "domain": domain}
        )
        
        # 2. Extract pattern statistics
        pattern_stats = {}
        for pattern in history:
            pattern_stats[pattern["type"]] = {
                "frequency": pattern["frequency"],
                "avg_completion_time": pattern["avg_time"],
                "success_rate": pattern["success_rate"],
                "team_sizes": pattern["team_sizes"]
            }
            
        # 3. Analyze effectiveness
        effectiveness = await self._analyze_pattern_effectiveness(
            pattern_stats
        )
        
        return {
            "pattern_stats": pattern_stats,
            "effectiveness": effectiveness,
            "recommendations": self._generate_recommendations(
                pattern_stats,
                effectiveness
            )
        }
```

### 2. Interaction History Analysis (src/nia/memory/interaction_analysis.py)
```python
class SwarmInteractionAnalysis:
    """Analyzes agent interaction patterns in swarms."""
    
    async def analyze_team_dynamics(
        self,
        agent_types: List[str]
    ) -> Dict[str, Any]:
        """Analyze how agent types work together."""
        # 1. Get interaction history
        history = await self.memory_system.episodic.get_interactions(
            agent_types=agent_types,
            limit=100
        )
        
        # 2. Analyze collaboration patterns
        collaboration = await self._analyze_collaboration(history)
        
        # 3. Identify synergies and conflicts
        dynamics = await self._analyze_team_dynamics(
            history,
            collaboration
        )
        
        return {
            "collaboration_patterns": collaboration,
            "team_dynamics": dynamics,
            "recommendations": self._generate_team_recommendations(
                dynamics
            )
        }
```

### 3. Pattern Integration (src/nia/swarm/pattern_integration.py)
```python
class SwarmPatternIntegration:
    """Integrates learned patterns into swarm decisions."""
    
    async def enhance_swarm_decision(
        self,
        task: Dict[str, Any],
        initial_pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance pattern with learned insights."""
        # 1. Get learned patterns
        learned_patterns = await self.pattern_learning.analyze_successful_patterns(
            task["type"],
            task["domain"]
        )
        
        # 2. Analyze team dynamics
        dynamics = await self.interaction_analysis.analyze_team_dynamics(
            initial_pattern["agent_types"]
        )
        
        # 3. Adjust pattern based on learning
        adjustments = self._calculate_adjustments(
            initial_pattern,
            learned_patterns,
            dynamics
        )
        
        # 4. Update swarm configuration
        enhanced_pattern = self._apply_adjustments(
            initial_pattern,
            adjustments
        )
        
        return enhanced_pattern
```

### 4. Memory-Enhanced Coordinator (src/nia/agents/specialized/coordination_agent.py)
```python
class CoordinationAgent:
    async def determine_pattern(
        self,
        requirements: Dict[str, Any],
        available_agents: List[Dict[str, Any]],
        current_workload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine best swarm pattern with memory enhancement."""
        # 1. Get initial pattern
        initial_pattern = await self._select_initial_pattern(
            requirements,
            available_agents
        )
        
        # 2. Enhance with learned patterns
        enhanced_pattern = await self.pattern_integration.enhance_swarm_decision(
            requirements["task"],
            initial_pattern
        )
        
        # 3. Validate against workload
        if not self._can_support_pattern(enhanced_pattern, current_workload):
            enhanced_pattern = await self._find_alternative_pattern(
                enhanced_pattern,
                current_workload
            )
        
        # 4. Update memory with decision
        await self._store_pattern_decision(
            requirements["task"],
            enhanced_pattern,
            {
                "initial_pattern": initial_pattern,
                "learned_adjustments": enhanced_pattern["adjustments"],
                "workload_impact": enhanced_pattern["workload_impact"]
            }
        )
        
        return enhanced_pattern
```

This shows how:
1. Pattern Learning:
   - Analyzes successful patterns
   - Tracks pattern statistics
   - Generates recommendations

2. Interaction Analysis:
   - Studies team dynamics
   - Identifies synergies
   - Recommends combinations

3. Pattern Integration:
   - Enhances decisions
   - Adjusts configurations
   - Updates memory

4. Memory Enhancement:
   - Improves pattern selection
   - Validates against workload
   - Tracks decisions

For example, when creating a swarm:
```python
# 1. Get initial pattern
pattern = await coordinator_agent.determine_pattern(
    requirements=task_requirements,
    available_agents=world.get_available_agents(),
    current_workload=world.get_workload_stats()
)

# 2. Enhance with memory
enhanced_pattern = await pattern_integration.enhance_swarm_decision(
    task=task,
    initial_pattern=pattern
)

# 3. Create swarm with enhanced pattern
swarm = await orchestrator_agent.create_swarm(
    pattern=enhanced_pattern,
    requirements=task_requirements,
    world=world
)

# 4. Update memory with results
await swarm_memory.store_swarm_results(
    swarm_id=swarm.id,
    pattern=enhanced_pattern,
    results=await swarm.process_task(task)
)

### Memory-Driven Emotional States

The memory system influences agent emotions and goals through learned patterns:

### 1. Emotional Pattern Learning (src/nia/memory/emotional_learning.py)
```python
class EmotionalPatternLearning:
    """Learns emotional patterns from swarm interactions."""
    
    async def analyze_emotional_patterns(
        self,
        swarm_type: str,
        agent_types: List[str]
    ) -> Dict[str, Any]:
        """Analyze emotional patterns in successful swarms."""
        # 1. Get emotional history
        history = await self.memory_system.semantic.query(
            f"""
            MATCH (s:Swarm)-[:HAD_EMOTION]->(e:EmotionalState)
            WHERE s.type = $swarm_type
            AND s.success = true
            RETURN e, count(*) as frequency
            ORDER BY frequency DESC
            """,
            {"swarm_type": swarm_type}
        )
        
        # 2. Extract emotional patterns
        emotional_patterns = {}
        for state in history:
            emotional_patterns[state["type"]] = {
                "frequency": state["frequency"],
                "avg_intensity": state["avg_intensity"],
                "success_correlation": state["success_correlation"],
                "team_performance": state["team_performance"]
            }
            
        # 3. Analyze effectiveness
        effectiveness = await self._analyze_emotional_effectiveness(
            emotional_patterns
        )
        
        return {
            "emotional_patterns": emotional_patterns,
            "effectiveness": effectiveness,
            "recommendations": self._generate_emotional_recommendations(
                emotional_patterns,
                effectiveness
            )
        }
```

### 2. Goal Adaptation (src/nia/memory/goal_adaptation.py)
```python
class GoalPatternLearning:
    """Adapts agent goals based on swarm patterns."""
    
    async def adapt_agent_goals(
        self,
        agent: TinyTroupeAgent,
        swarm: Swarm,
        emotional_patterns: Dict[str, Any]
    ):
        """Adapt agent goals based on learned patterns."""
        # 1. Get goal history
        history = await self.memory_system.episodic.get_agent_memories(
            agent.name,
            memory_type="goals",
            limit=50
        )
        
        # 2. Analyze goal effectiveness
        effectiveness = await self._analyze_goal_effectiveness(
            history,
            emotional_patterns
        )
        
        # 3. Generate adapted goals
        adapted_goals = self._adapt_goals(
            agent.desires,
            effectiveness,
            swarm.pattern
        )
        
        # 4. Update agent goals with emotional context
        await agent.update_state({
            "goals": adapted_goals,
            "emotions": {
                "goal_alignment": effectiveness["alignment"],
                "motivation": effectiveness["motivation"],
                "team_synergy": effectiveness["synergy"]
            }
        })
```

### 3. Emotional Integration (src/nia/swarm/emotional_integration.py)
```python
class SwarmEmotionalIntegration:
    """Integrates emotional patterns into swarm behavior."""
    
    async def enhance_swarm_emotions(
        self,
        swarm: Swarm,
        emotional_patterns: Dict[str, Any]
    ):
        """Enhance swarm with emotional patterns."""
        # 1. Get team emotional state
        team_state = await self._get_team_emotional_state(swarm)
        
        # 2. Analyze emotional coherence
        coherence = await self._analyze_emotional_coherence(
            team_state,
            emotional_patterns
        )
        
        # 3. Generate emotional adjustments
        adjustments = self._calculate_emotional_adjustments(
            team_state,
            coherence,
            emotional_patterns
        )
        
        # 4. Update agent emotions
        for agent in swarm.agents:
            agent_adjustment = adjustments.get(agent.name, {})
            await agent.update_state({
                "emotions": {
                    "team_alignment": agent_adjustment.get("alignment", 0.5),
                    "role_satisfaction": agent_adjustment.get("satisfaction", 0.5),
                    "collaboration_readiness": agent_adjustment.get("readiness", 0.5)
                }
            })
            
            # Update agent prompt with emotional context
            emotional_context = f"""
            Team Emotional State:
            - Alignment: {team_state['alignment']}
            - Coherence: {coherence['score']}
            - Role: {agent_adjustment['role']}
            
            Emotional Patterns:
            {self._format_emotional_patterns(emotional_patterns)}
            """
            await agent.memory_system.llm.add_context(emotional_context)
```

### 4. Memory-Enhanced Emotional States (src/nia/agents/specialized/emotion_agent.py)
```python
class EmotionAgent:
    async def update_swarm_emotions(
        self,
        swarm: Swarm,
        task_state: Dict[str, Any]
    ):
        """Update swarm emotional states with memory enhancement."""
        # 1. Learn emotional patterns
        patterns = await self.emotional_learning.analyze_emotional_patterns(
            swarm.swarm_type,
            [agent.agent_type for agent in swarm.agents]
        )
        
        # 2. Adapt agent goals
        for agent in swarm.agents:
            await self.goal_learning.adapt_agent_goals(
                agent,
                swarm,
                patterns
            )
            
        # 3. Integrate emotional patterns
        await self.emotional_integration.enhance_swarm_emotions(
            swarm,
            patterns
        )
        
        # 4. Update memory with emotional state
        await self._store_emotional_state(
            swarm.id,
            {
                "patterns": patterns,
                "team_state": await self._get_team_state(swarm),
                "task_state": task_state
            }
        )
```

This shows how:
1. Emotional Pattern Learning:
   - Analyzes successful emotional states
   - Tracks emotional patterns
   - Generates recommendations

2. Goal Adaptation:
   - Analyzes goal effectiveness
   - Adapts goals based on patterns
   - Updates emotional context

3. Emotional Integration:
   - Enhances team emotions
   - Maintains emotional coherence
   - Updates agent prompts

4. Memory Enhancement:
   - Improves emotional states
   - Adapts agent goals
   - Tracks emotional history

For example, when managing a swarm:
```python
# 1. Get emotional patterns
patterns = await emotion_agent.emotional_learning.analyze_emotional_patterns(
    swarm_type=swarm.swarm_type,
    agent_types=[agent.agent_type for agent in swarm.agents]
)

# 2. Adapt agent goals
for agent in swarm.agents:
    await emotion_agent.goal_learning.adapt_agent_goals(
        agent=agent,
        swarm=swarm,
        emotional_patterns=patterns
    )

# 3. Enhance swarm emotions
await emotion_agent.emotional_integration.enhance_swarm_emotions(
    swarm=swarm,
    emotional_patterns=patterns
)

# 4. Update task processing with emotional context
result = await swarm.process_task(
    task,
    emotional_context={
        "patterns": patterns,
        "team_state": await emotion_agent._get_team_state(swarm)
    }
)
```

### LLM Emotional Integration

The memory system's emotional patterns influence LLM responses through the prompt system:

### 1. Emotional Prompt Enhancement (src/nia/memory/prompt_enhancement.py)
```python
class EmotionalPromptEnhancement:
    """Enhances LLM prompts with emotional patterns."""
    
    async def enhance_prompt(
        self,
        base_prompt: str,
        agent: TinyTroupeAgent,
        emotional_patterns: Dict[str, Any]
    ) -> str:
        """Enhance prompt with emotional context."""
        # 1. Get agent's emotional history
        history = await self.memory_system.get_agent_history(
            agent.name,
            history_type="emotional"
        )
        
        # 2. Analyze emotional trends
        trends = await self._analyze_emotional_trends(
            history,
            emotional_patterns
        )
        
        # 3. Generate emotional guidance
        guidance = self._generate_emotional_guidance(
            trends,
            emotional_patterns
        )
        
        # 4. Format emotional context
        emotional_context = f"""
        Emotional Response Guidance:
        {guidance}
        
        Historical Emotional Patterns:
        {self._format_emotional_trends(trends)}
        
        Current Emotional State:
        {json.dumps(agent.emotions, indent=2)}
        
        Target Emotional Alignment:
        {self._format_target_emotions(emotional_patterns)}
        """
        
        return f"{base_prompt}\n\n{emotional_context}"
```

### 2. Response Modulation (src/nia/llm/emotional_modulation.py)
```python
class EmotionalResponseModulation:
    """Modulates LLM responses based on emotional patterns."""
    
    async def modulate_completion(
        self,
        llm: LMStudioLLM,
        prompt: str,
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get emotionally-modulated completion."""
        # 1. Add emotional weighting
        weighted_prompt = await self._add_emotional_weights(
            prompt,
            emotional_context
        )
        
        # 2. Generate response with emotional guidance
        response = await llm.get_structured_completion(
            prompt=weighted_prompt,
            metadata={
                "emotional_context": emotional_context,
                "response_guidance": {
                    "tone": emotional_context["target_tone"],
                    "empathy": emotional_context["target_empathy"],
                    "formality": emotional_context["target_formality"]
                }
            }
        )
        
        # 3. Validate emotional alignment
        alignment = await self._check_emotional_alignment(
            response,
            emotional_context
        )
        
        # 4. Adjust if needed
        if alignment["score"] < 0.8:  # Threshold for acceptable alignment
            response = await self._adjust_emotional_alignment(
                response,
                alignment,
                emotional_context
            )
            
        return response
```

### 3. Pattern-Based Templates (src/nia/llm/emotional_templates.py)
```python
class EmotionalPromptTemplates:
    """Manages emotional prompt templates."""
    
    async def get_template(
        self,
        emotional_pattern: str,
        context: Dict[str, Any]
    ) -> str:
        """Get appropriate emotional template."""
        # 1. Get template options
        templates = await self.memory_system.semantic.query(
            f"""
            MATCH (t:Template)-[:USED_IN]->(p:EmotionalPattern)
            WHERE p.type = $pattern_type
            AND t.success_rate > 0.8
            RETURN t ORDER BY t.success_rate DESC
            """,
            {"pattern_type": emotional_pattern}
        )
        
        # 2. Select best template
        template = await self._select_template(
            templates,
            context
        )
        
        # 3. Customize template
        customized = await self._customize_template(
            template,
            context
        )
        
        return customized
```

### 4. Memory-Enhanced LLM (src/nia/llm/memory_enhanced_llm.py)
```python
class MemoryEnhancedLLM:
    """LLM with memory-based emotional enhancement."""
    
    async def get_emotional_completion(
        self,
        prompt: str,
        agent: TinyTroupeAgent,
        task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get completion with emotional enhancement."""
        # 1. Get emotional patterns
        patterns = await self.emotional_learning.analyze_emotional_patterns(
            task_context["type"],
            [agent.agent_type]
        )
        
        # 2. Enhance prompt
        enhanced_prompt = await self.prompt_enhancement.enhance_prompt(
            prompt,
            agent,
            patterns
        )
        
        # 3. Get emotional template
        template = await self.emotional_templates.get_template(
            patterns["dominant_pattern"],
            task_context
        )
        
        # 4. Generate modulated response
        response = await self.emotional_modulation.modulate_completion(
            self.llm,
            f"{enhanced_prompt}\n\n{template}",
            {
                "patterns": patterns,
                "agent_state": agent.emotions,
                "task_context": task_context
            }
        )
        
        # 5. Update memory with response
        await self._store_emotional_response(
            agent.name,
            response,
            patterns
        )
        
        return response
```

This shows how:
1. Prompt Enhancement:
   - Analyzes emotional trends
   - Generates guidance
   - Formats context

2. Response Modulation:
   - Adds emotional weights
   - Validates alignment
   - Adjusts responses

3. Pattern Templates:
   - Selects templates
   - Customizes for context
   - Tracks success rates

4. Memory Enhancement:
   - Enhances prompts
   - Modulates responses
   - Updates memory

For example, when getting an LLM response:
```python
# 1. Initialize memory-enhanced LLM
llm = MemoryEnhancedLLM(
    base_llm=LMStudioLLM(),
    memory_system=memory_system,
    emotional_learning=emotional_learning
)

# 2. Get emotional completion
response = await llm.get_emotional_completion(
    prompt=base_prompt,
    agent=agent,
    task_context={
        "type": "collaborative_task",
        "domain": "professional",
        "emotional_requirements": {
            "empathy": "high",
            "formality": "medium",
            "tone": "supportive"
        }
    }
)

# 3. Validate and store response
alignment = await llm.emotional_modulation.check_emotional_alignment(
    response,
    emotional_context
)

if alignment["score"] >= 0.8:
    await llm._store_emotional_response(
        agent.name,
        response,
        emotional_patterns
    )
```
```

## Next Steps

1. Implement Defined Patterns:
- Add hierarchical processing support
- Enable parallel agent execution
- Implement mesh communication

2. Enhance Coordination:
- Add dynamic team formation
- Implement resource optimization
- Add adaptive task routing

3. Improve Monitoring:
- Add detailed agent metrics
- Implement pattern analysis
- Add performance tracking
