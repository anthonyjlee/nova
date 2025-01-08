# NIA (Nova Intelligence Architecture)

> **Project Status (2025-01-08)**: Core components complete, improved code organization (Docker services and test structure). Preparing for frontend development.


NIA is a sophisticated multi-agent system built on TinyTroupe that combines metacognition (Nova) with domain-specific tasks. The system features:

- **Real-Time Communication**: FastAPI backend with WebSocket support for live updates and thread management
- **Two-Layer Memory**: Vector storage for ephemeral data (chat history, thread states) and Neo4j for semantic data (knowledge graph, task relations)
- **Dynamic Agent Creation**: TinyFactory for spawning and configuring agents based on task requirements
- **Flexible Swarm Patterns**: Support for hierarchical, parallel, sequential, and mesh agent collaboration
- **Domain-Aware Processing**: Strict separation between personal/professional data with cross-domain operation controls
- **Thread Management**: Main channel with sub-threads for specialized tasks, including aggregator summaries
- **Task Orchestration**: Structured workflow from proposal through approval to execution

## Why Now?

The emergence of NIA is driven by several critical factors:

### Research Foundations & Motivation
Building on Well-E's empirical success in health modeling, NIA addresses fundamental challenges in multi-agent systems (and in turn orchestration):

1. **Theoretical Framework**:
   * Information-theoretic bounds on agent communication (O(n²) complexity)
   * Formal verification of emergent collective behaviors
   * Convergence guarantees in distributed learning systems
   * Game-theoretic equilibria in heterogeneous agent networks

### Applications

1. **Market Research**:
   * Synthetic data generation with causal validation
   * Game-theoretic market equilibrium analysis
   * Multi-agent strategic interaction modeling
   * Bayesian consumer behavior simulation

2. **Healthcare Analytics**:
   * Evidence-based clinical decision support
   * Patient trajectory optimization
   * Treatment outcome prediction
   * Protocol efficacy validation

3. **Financial Systems**:
   * Stochastic risk modeling
   * Portfolio optimization under constraints
   * Market inefficiency detection
   * Behavioral economics validation

### Open Challenges
1. **Scalability**: Communication complexity and resource utilization in large-scale deployments
2. **Validation**: Standardized metrics for multi-agent system performance
3. **Reproducibility**: Experimental protocols for emergent behavior analysis
4. **Transfer Learning**: Cross-domain knowledge adaptation effectiveness
5. **Safety**: Formal verification of collective decision-making

## Why NIA?

NIA takes a fundamentally different approach to multi-agent orchestration compared to existing frameworks:

### Beyond Traditional Frameworks

- **TinyTroupe**: While NIA builds on TinyTroupe's foundation, it adds metacognitive capabilities through Nova, enabling agents to reflect on their own performance and adapt their strategies. Unlike basic TinyTroupe agents, NIA agents maintain a self-model in Neo4j and can evolve their capabilities through experience.

- **ChatDev**: ChatDev focuses on software development through predefined agent roles. NIA, in contrast, enables dynamic agent creation through TinyFactory based on emergent task requirements, allowing for more flexible and adaptable solutions across domains.

- **AutoGen/Ignite**: These frameworks provide agent templates and conversation patterns. NIA goes further by implementing domain-aware processing, strict personal/professional boundaries, and sophisticated memory consolidation that enables long-term learning.

- **LangChain/LangGraph**: These tools focus on chaining LLM operations. NIA implements a true multi-agent system with emergent task detection, swarm-based collaboration patterns, and sophisticated memory architecture that enables both ephemeral and semantic storage.

### Key Differentiators

1. **Co-Creation Focus**
   - Agents actively participate in solution design
   - Dynamic task decomposition and agent spawning
   - Collaborative refinement of approaches
   - Emergent strategy development

2. **Metacognitive Architecture**
   - Self-aware agents that reflect on performance
   - Dynamic capability evolution
   - Cross-domain learning and adaptation
   - Pattern-based strategy refinement

3. **Emergent Task Detection**
   - Proactive identification of opportunities
   - Context-aware task generation
   - Multi-agent consensus on task value
   - Domain-specific task validation

4. **Sophisticated Memory**
   - Two-layer architecture for different timescales
   - Knowledge consolidation across domains
   - Pattern-based learning and retrieval
   - Cross-domain relationship inference

5. **Domain Intelligence**
   - Strict personal/professional separation
   - Cross-domain operation controls
   - Context-aware processing
   - Domain-specific strategy adaptation

6. **Flexible Swarm Patterns**
   - Dynamic collaboration architectures
   - Task-specific swarm configuration
   - Resource-aware scaling
   - Pattern-based optimization

## System Overview

### Configuration System

The system uses a centralized configuration system for all agents:
- Unified prompt templates and responsibilities
- Domain-aware configuration validation
- Standardized agent initialization
- Centralized configuration management

Key components:
- `BASE_AGENT_TEMPLATE`: Core template all agents extend
- `AGENT_RESPONSIBILITIES`: Role-specific responsibilities
- Configuration validation with domain boundaries
- Standardized error handling

Example agent configuration:
```python
config = {
    "name": "validation_agent",
    "agent_type": "validation",
    "domain": "professional"
}
```

### Nova Orchestrator
The core orchestration system that combines metacognition with specialized agents to:
- Build and maintain a self-model in Neo4j for reflection and adaptation
- Understand user context through multi-modal intake and psychometric profiling
- Manage personal vs. professional domain boundaries
- Coordinate specialized agents for complex tasks
- Generate and manage emergent tasks through agent collaboration
- Create new agents dynamically via TinyFactory
- Provide skill access through SkillsAgent
- Adapt behavior based on user psychometric profile

#### Initialization Protocol
1. System Identity
   * Loads self-model and capabilities
   * Initializes specialized agents
   * Configures tool access and memory layers

2. User Context & Profiling
   * Conducts psychometric questionnaire (Big Five, learning style)
   * Stores profile in Neo4j (personality traits, preferences)
   * Analyzes work/personal domain boundaries
   * Establishes security and privacy settings
   * Configures task adaptation preferences

3. Memory Initialization
   * Verifies episodic (vector) and semantic (Neo4j) stores
   * Loads relevant conversation history
   * Prepares domain-specific knowledge partitions
   * Initializes user profile storage

4. Agent Reflection & Adaptation
   * ReflectionAgent analyzes user context and profile
   * BeliefAgent updates system beliefs
   * EmotionAgent calibrates based on user profile
   * DesireAgent aligns with user motivations
   * Specialized agents prepare profile-aware strategies

#### Self-Model & Metacognition
Nova maintains a self-model in Neo4j that:
- Tracks system beliefs and capabilities
- Records interaction patterns and user preferences
- Stores domain-specific knowledge and access rules
- Updates through agent reflections and observations
- Evolves based on task outcomes and user feedback

#### Long-Term Planning & Emergent Tasks
Nova orchestrates specialized agents to:
1. Pattern Recognition
   * ReflectionAgent identifies recurring themes
   * AnalysisAgent detects potential opportunities
   * ContextAgent provides environmental awareness

2. Task Generation
   * BeliefAgent validates against user preferences
   * DesireAgent prioritizes based on motivation
   * TaskAgent creates structured execution plans

3. Strategic Planning
   * MetaAgent synthesizes multi-domain strategies
   * OrchestrationAgent manages resource allocation
   * IntegrationAgent ensures cohesive execution

4. Continuous Improvement
   * EmotionAgent tracks user satisfaction
   * ValidationAgent ensures quality standards
   * MonitoringAgent optimizes performance

### Dynamic Agent Creation
Nova uses TinyFactory to:
- Design and spawn new agents based on task requirements
- Configure agent capabilities and domain access
- Manage agent lifecycle and resource allocation
- Scale agent populations as needed
- Optimize agent distribution for tasks
- Persist agent templates to local storage
- Version control agent definitions

Example agent creation flow:
1. Nova receives complex task
2. Task analyzed for required capabilities
3. TinyFactory designs optimal agent configuration
4. New agent template stored in local YAML/JSON
5. Agent spawned with specific skills
6. Agent integrated into existing workflow
7. Performance monitored for optimization

#### Local Template Storage
The system maintains persistent storage of agent and flow templates:

1. Directory Structure:
   ```
   templates/
   ├── agents/           # Agent template definitions
   │   ├── critique_agent.yaml
   │   ├── synthesis_agent.yaml
   │   └── ...
   ├── flows/            # Multi-agent flow definitions
   │   ├── prompt_wizard.yaml
   │   ├── reflection_flow.yaml
   │   └── ...
   └── init_agents.yaml  # Startup configuration
   ```

2. Template Management:
   - All new agents/flows are stored as YAML/JSON files
   - Version controlled through Git
   - Human-readable and editable
   - Survives system restarts
   - Supports manual and programmatic updates

3. Initialization Process:
   - System reads all templates at startup
   - Auto-launches configured flows
   - Maintains registry of available templates
   - Supports runtime updates and reloading

### Skills Management
The SkillsAgent provides:
- Access to OpenAI API endpoints for all agents
- Skill discovery and registration
- Capability matching for tasks
- Cross-agent skill sharing
- Dynamic skill loading

Available OpenAI endpoints:
- GPT-4 for complex reasoning
- GPT-3.5-turbo for rapid responses
- DALL-E for image generation
- Whisper for speech processing
- Embeddings for vector operations

Skill sharing example:
1. Agent requires new capability
2. SkillsAgent checks skill registry
3. Matching skill found in existing agent
4. Skill shared and configured
5. New capability ready for use

### Memory Architecture

#### Episodic Layer (Vector Store)
- **Chunking System**:
  * Configurable chunk size (512-1000 tokens)
  * Sliding window or paragraph-based chunking
  * Chunk metadata tracking
  * Ephemeral storage with rotation
  * Quick approximate lookups

- **Vector Operations**:
  * Embedding generation (OpenAI/Hugging Face)
  * Top-k nearest chunk retrieval
  * Cluster and adjacency expansions
  * Metadata-based filtering

#### Semantic Layer (Neo4j)
- **Graph Structure**:
  * Entity nodes with properties
  * Domain-labeled relationships
  * Numeric fact verification
  * Cross-domain knowledge management

- **Advanced Retrieval**:
  * Node embeddings for concept matching
  * Graph-based traversal and expansion
  * BFS for relationship exploration
  * Concept-level adjacency search

#### Memory Consolidation
- **Pattern Extraction**:
  * TinyTroupe integration for knowledge extraction
  * Domain-aware consolidation rules
  * Numeric fact validation
  * Relationship inference

- **Lifecycle Management**:
  * Ephemeral to semantic transition
  * Chunk rotation and cleanup
  * Knowledge verification
  * Domain boundary maintenance

### Agent Interaction Flow
1. User input received via WebSocket
2. Nova analyzes input using ParsingAgent
3. Relevant agents activated based on content
4. Parallel processing by specialized agents
5. Results consolidated by IntegrationAgent
6. Response generated by ResponseAgent
7. Memory updates by both storage layers

### Domain Management
- Strict separation between personal/professional data
- Cross-domain operations require explicit approval
- Domain inheritance for derived tasks
- Domain-aware validation at all levels

### Real-Time Processing
- WebSocket-based communication
- Live agent state updates
- Task monitoring and coordination
- Memory system synchronization

### Swarm Architecture
The system supports dynamic swarm architectures for agent collaboration through TinyFactory:

#### Swarm Patterns
Each pattern has its own validated configuration model:

- **Hierarchical**: Tree-structured command flow
  ```python
  hierarchical_config = {
      "name": "test_hierarchical",
      "description": "Test hierarchical swarm",
      "agents": ["agent1", "agent2", "agent3"],
      "supervisor_id": "agent1",
      "worker_ids": ["agent2", "agent3"]
  }
  ```

- **Parallel**: Independent concurrent processing
  ```python
  parallel_config = {
      "name": "test_parallel",
      "description": "Test parallel swarm",
      "agents": ["agent1", "agent2", "agent3"],
      "batch_size": 2,
      "load_balancing": True
  }
  ```

- **Sequential**: Ordered task processing chain
  ```python
  sequential_config = {
      "name": "test_sequential",
      "description": "Test sequential swarm",
      "agents": ["agent1", "agent2", "agent3"],
      "stages": [
          {"stage": "parse", "agent": "agent1"},
          {"stage": "analyze", "agent": "agent2"},
          {"stage": "validate", "agent": "agent3"}
      ],
      "progress_tracking": True
  }
  ```

- **Mesh**: Free-form agent communication
  ```python
  mesh_config = {
      "name": "test_mesh",
      "description": "Test mesh swarm",
      "agents": ["agent1", "agent2", "agent3"],
      "communication_patterns": ["broadcast", "direct", "group"]
  }
  ```

#### Advanced Swarm Types
Each type has specific configuration requirements:

- **MajorityVoting**: Consensus-based decisions
  ```python
  voting_config = {
      "name": "test_voting",
      "description": "Test voting swarm",
      "agents": ["agent1", "agent2", "agent3"],
      "threshold": 0.6,
      "voting_timeout": 30.0,
      "allow_revotes": False
  }
  ```

- **RoundRobin**: Cyclic task distribution
  ```python
  round_robin_config = {
      "name": "test_round_robin",
      "description": "Test round-robin swarm",
      "agents": ["agent1", "agent2", "agent3"],
      "rotation_interval": 1.0,
      "fair_scheduling": True
  }
  ```

#### Swarm Creation
Swarms are created through Nova's orchestration using TinyFactory:

```python
swarm_request = {
    "type": "swarm_creation",
    "domain": "test",
    "swarm_requirements": {
        "patterns": [
            "hierarchical",
            "parallel",
            "sequential",
            "mesh",
            "round_robin",
            "majority_voting"
        ],
        "capabilities": [
            "task_execution",
            "communication",
            "coordination"
        ]
    }
}

# Create swarms through Nova's orchestration
response = requests.post(
    "http://localhost:8000/api/orchestration/swarms",
    json=swarm_request
)
```

#### Resource Management
- Dynamic resource allocation through TinyFactory
- Pattern-specific configuration validation
- Automatic agent lifecycle management
- Performance monitoring and metrics
- Bottleneck detection and resolution
- Automatic scaling based on workload

## Core System Agents

### Factory & Skills
- **TinyFactory**:
  * Dynamic agent creation and configuration
  * Resource allocation for new agents
  * Agent template management
  * Lifecycle monitoring
  * Performance optimization

- **SkillsAgent**:
  * OpenAI API endpoint management
  * Skill registration and discovery
  * Capability matching
  * Cross-agent skill sharing
  * Dynamic skill loading

## Specialized Agents

### Core Processing Agents
- **ParsingAgent**: 
  * Domain-aware text parsing and concept extraction
  * Confidence-based reflection triggers
  * Enhanced schema validation
  * Key point extraction with domain boundaries
  * Integration with memory system
  * Swarm pattern recognition and validation
  * Multi-agent parsing coordination

- **AnalysisAgent**: 
  * Pattern detection with domain boundaries
  * Insight generation and validation
  * Real-time analysis state tracking
  * Analysis strategy system
  * Trend detector management
  * Swarm performance analysis
  * Collective insight generation

- **SynthesisAgent**: 
  * Theme identification across domains
  * Conclusion generation and validation
  * Pattern-based synthesis
  * Domain-aware content synthesis
  * Enhanced theme identification
  * Swarm consensus synthesis
  * Multi-agent knowledge integration

- **ValidationAgent**: 
  * Rule-based validation with domain context
  * Issue detection and reporting
  * Validation rules with domain boundaries
  * Enhanced error handling
  * Comprehensive validation coverage
  * Swarm validation protocols
  * Collective decision validation

- **SchemaAgent**: 
  * Schema validation with domain boundaries
  * Pydantic model generation
  * Schema evolution tracking
  * Enhanced model validation
  * Domain-aware schema analysis
  * Swarm schema coordination
  * Distributed schema management

### Cognitive Agents
- **BeliefAgent**: 
  * Evidence validation with domain boundaries
  * Belief system management
  * Confidence-based validation
  * Domain-specific belief tracking
  * Enhanced evidence validation
  * Swarm belief consensus
  * Collective belief refinement

- **DesireAgent**: 
  * Motivation tracking with domain boundaries
  * Priority management and validation
  * Domain-aware desire analysis
  * Enhanced motivation tracking
  * Priority validation system
  * Swarm goal alignment
  * Collective priority optimization

- **EmotionAgent**: 
  * Intensity tracking with domain context
  * Emotional state processing
  * Domain-aware emotion analysis
  * Enhanced intensity tracking
  * Emotional validation system
  * Swarm emotional awareness
  * Collective sentiment analysis

- **ReflectionAgent**: 
  * Pattern recognition with domain boundaries
  * Insight generation and validation
  * Domain-aware reflection analysis
  * Enhanced pattern recognition
  * Reflection recording system
  * Swarm reflection synthesis
  * Collective learning patterns

- **MetaAgent**: 
  * Meta-level orchestration and synthesis
  * Domain-aware agent coordination
  * Multi-domain agent orchestration
  * Enhanced response gathering
  * Domain-specific reflection recording
  * Swarm architecture management
  * Strategic swarm adaptation

### Task Management
- **TaskAgent**: 
  * Dependency tracking with domain boundaries
  * Task state management
  * Domain-aware task analysis
  * Enhanced dependency tracking
  * Task validation system
  * Swarm task distribution
  * Collective workload balancing

- **ExecutionAgent**: 
  * Sequence optimization with error recovery
  * Real-time sequence state tracking
  * Resource utilization monitoring
  * Priority queue management
  * Retry mechanism with limits
  * Swarm execution coordination
  * Distributed task execution

- **OrchestrationAgent**: 
  * Flow coordination with domain boundaries
  * Real-time flow state tracking
  * Resource utilization monitoring
  * Task dependency management
  * Automated issue detection
  * Swarm architecture orchestration
  * Dynamic swarm reconfiguration

- **CoordinationAgent**: 
  * Resource allocation with conflict detection
  * Group management and task dependencies
  * State tracking with emotional responses
  * Memory integration with reflections
  * Enhanced resource management
  * Swarm communication patterns
  * Multi-swarm coordination

### Communication
- **DialogueAgent**: 
  * Real-time conversation state tracking
  * Multi-agent conversation coordination
  * Flow control and intervention
  * Pattern recognition and recording
  * Enhanced memory integration
  * Swarm dialogue management
  * Collective conversation synthesis

- **ResponseAgent**: 
  * Component validation with domain boundaries
  * Response quality assessment
  * Domain-aware response analysis
  * Enhanced component validation
  * Quality validation system
  * Swarm response coordination
  * Collective response refinement

- **IntegrationAgent**: 
  * Relationship identification with domain boundaries
  * Connection generation and validation
  * Domain-aware content integration
  * Enhanced relationship handling
  * Integration evolution tracking
  * Swarm integration patterns
  * Multi-swarm knowledge fusion

### Research & Context
- **ResearchAgent**: 
  * Source validation with domain boundaries
  * Information gathering and verification
  * Domain-aware research analysis
  * Enhanced source validation
  * Finding validation system
  * Swarm research coordination
  * Collective knowledge discovery

- **ContextAgent**: 
  * Environment tracking with domain boundaries
  * Context-aware state management
  * Domain-aware context analysis
  * Enhanced environment tracking
  * Context validation system
  * Swarm context awareness
  * Multi-agent context synthesis

- **StructureAgent**: 
  * Pattern analysis with domain boundaries
  * Schema validation and evolution
  * Domain-aware structure analysis
  * Enhanced pattern detection
  * Structure validation system
  * Swarm structure coordination
  * Collective pattern recognition

### System Operations
- **MonitoringAgent**: 
  * Real-time metric state tracking
  * Health check automation
  * Alert generation and management
  * Incident lifecycle tracking
  * Trend analysis and aggregation
  * Swarm health monitoring
  * Multi-swarm performance tracking

- **AlertingAgent**: 
  * Real-time alert state tracking
  * Rule-based routing system
  * Delivery status monitoring
  * Retry mechanism with escalation
  * Filter-based noise reduction
  * Swarm alert coordination
  * Collective alert prioritization

- **LoggingAgent**: 
  * Real-time log state tracking
  * Format template system
  * Context enrichment rules
  * Storage policy management
  * Rotation policy handling
  * Swarm logging patterns
  * Distributed log aggregation

- **MetricsAgent**: 
  * Real-time metric state tracking
  * Collection strategy system
  * Aggregation rule management
  * Calculation template handling
  * Retention policy management
  * Swarm metrics collection
  * Multi-swarm performance metrics

- **AnalyticsAgent**: 
  * Real-time analysis state tracking
  * Analysis strategy system
  * Pattern template management
  * Insight model handling
  * Trend detector management
  * Swarm analytics coordination
  * Collective insight generation

- **VisualizationAgent**: 
  * Real-time visualization state tracking
  * Visualization strategy system
  * Layout template management
  * Chart template handling
  * Rendering engine management
  * Swarm visualization patterns
  * Multi-swarm state visualization

## Key Features

### Domain-Labeled Memory
- Strict separation between personal and professional data
- Cross-domain operations require explicit approval
- Domain inheritance for derived tasks

### Emergent Task Detection
1. Agents monitor conversations for potential tasks
2. Tasks are flagged with "pending_approval" status
3. User reviews and approves/rejects tasks
4. Approved tasks are assigned to appropriate agents

### Real-Time Processing
- WebSocket connections for live updates
- Task state monitoring
- Agent coordination messages
- Memory system updates

## Technical Stack

### Backend
- FastAPI for REST and WebSocket endpoints
- Pydantic for data validation
- Neo4j for semantic storage
- Vector store (FAISS/Qdrant) for ephemeral memory
- TinyTroupe for agent simulation

### Agent Identity Management
- **Agent Lifecycle Management**:
  * Unique agent identification
  * Status tracking and updates
  * Capability registration
  * Performance metrics
  * Interaction history

- **API Endpoints**:
  * GET /api/agents - List all agents
  * GET /api/agents/{agent_id} - Get agent details
  * GET /api/agents/{agent_id}/status - Get agent status
  * POST /api/agents/{agent_id}/activate - Activate agent
  * GET /api/agents/search - Search by capability/type
  * GET /api/agents/{agent_id}/metrics - Get performance metrics

- **Storage & Persistence**:
  * Neo4j for agent metadata
  * Status history tracking
  * Capability indexing
  * Performance metrics storage
  * Interaction logging

### Frontend Architecture
- SvelteKit for UI framework
- Cytoscape.js for graph visualization
- WebSocket for real-time updates
- Domain-aware UI components

### Main Interface
- **Slack-like Environment**:
  * Primary chat-style interface
  * Sub-thread spawning for tasks
  * Agent response logging
  * Real-time updates via WebSocket
  * Domain-labeled interactions

### Graph System
- **Dual Implementation**:
  * DAG (Runtime Execution):
    - Task execution flow tracking
    - Dynamic dependency management
    - Real-time state updates
    - Concurrent execution handling
    - Performance optimization
  * Neo4j (Pattern Storage):
    - Swarm pattern persistence
    - Configuration templates
    - Historical execution data
    - Pattern relationships
    - Optimization insights

- **Graph Visualization**:
  * Interactive Cytoscape.js display:
    - DAG view for active executions
    - Neo4j view for stored patterns
    - Combined view for debugging
  * Real-time updates and animations
  * Domain-labeled data visualization
  * Node and edge interactions
  * Performance metrics overlay

- **Graph Features**:
  * Click-to-expand node details
  * Search and filtering
  * Domain-based node coloring
  * Task dependency visualization
  * Thread linking capabilities
  * Pattern template management
  * Execution flow tracking
  * Performance analysis tools

### Channel Chaining
- **Team Connections**:
  * Link multiple channels for complex workflows
  * Cross-team task coordination
  * Resource sharing between teams
  * Domain boundary management
  * Access control and permissions

- **Chain Management**:
  * Visual chain builder interface
  * Drag-and-drop channel linking
  * Chain templates and presets
  * Validation and testing tools
  * Performance monitoring

- **Chain Features**:
  * Bidirectional data flow
  * Event propagation control
  * Error handling and recovery
  * Resource allocation
  * Load balancing
  * Monitoring and metrics

- **Chain UI**:
  * Chain visualization dashboard
  * Real-time status updates
  * Performance analytics
  * Debug and troubleshooting tools
  * Configuration management

### Thread Management UI
- **Main Channel Interface**:
  * Primary Nova interaction channel
  * Real-time message updates via WebSocket
  * Thread creation and management
  * Task proposal and approval workflow
  * Aggregator summaries with drill-down

- **Sub-Thread Management**:
  * Specialized task threads (100+ messages)
  * Direct agent-to-agent communication
  * Thread status indicators
  * Progress tracking visualization
  * Resource utilization monitoring

- **Thread Navigation**:
  * Thread list with status overview
  * Quick thread switching
  * Search and filtering capabilities
  * Thread archiving controls
  * Thread relationship visualization

- **Message Organization**:
  * Hierarchical message threading
  * Context-aware message grouping
  * Domain labeling and separation
  * Message type indicators
  * Interaction history tracking

#### Swarm Architecture UI
- **Swarm Visualization**:
  * Real-time swarm architecture visualization
  * Agent role and relationship display
  * Communication pattern visualization
  * Resource allocation monitoring
  * Performance metrics dashboard

- **Swarm Management**:
  * Architecture type selection (hierarchical/parallel/sequential/mesh)
  * Swarm type configuration (MajorityVoting/RoundRobin/GraphWorkflow)
  * Agent role assignment interface
  * Resource allocation controls
  * Communication pattern settings

- **Swarm Monitoring**:
  * Real-time swarm health metrics
  * Communication overhead tracking
  * Resource utilization graphs
  * Task completion rate charts
  * Performance bottleneck detection

- **Swarm Control**:
  * Architecture transition interface
  * Voting system management
  * Resource reallocation tools
  * Communication pattern switching
  * Emergency swarm reconfiguration

## Getting Started

### Prerequisites
- Python 3.9+
- Docker Desktop
- LMStudio (for LLM inference)

### Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/NIA.git
   cd NIA
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. Start all services:
   ```bash
   # Start all required services (Neo4j, Qdrant, FastAPI)
   python scripts/manage.py start

   # Check service status
   python scripts/manage.py status

   # Stop all services when done
   python scripts/manage.py stop
   ```

   Note: You'll need to manually:
   1. Launch LMStudio application
   2. Load your preferred model
   3. Start the local server (default: http://localhost:1234)

### Development Setup

1. Running Tests:
   ```bash
   # Run all tests
   pytest
   
   # Run specific test categories
   pytest tests/nova/test_websocket.py  # WebSocket tests
   pytest tests/nova/test_memory_api.py  # Memory API tests
   pytest tests/nova/test_agent_coordination.py  # Agent coordination tests
   ```

2. Development Tools:
   - LMStudio: Local LLM inference (http://localhost:1234)
   - Neo4j Browser: Graph database interface (http://localhost:7474)
   - Qdrant Dashboard: Vector store management (http://localhost:6333/dashboard)

### Service Dependencies

1. **Neo4j (Graph Database)**
   - Purpose: Semantic memory storage
   - Port: 7474 (HTTP), 7687 (Bolt)
   - Status Check: http://localhost:7474
   - Configuration: scripts/docker/neo4j/

2. **Qdrant (Vector Store)**
   - Purpose: Ephemeral memory & embeddings
   - Port: 6333
   - Status Check: http://localhost:6333/dashboard
   - Configuration: scripts/docker/qdrant/

3. **LMStudio (LLM Server)**
   - Purpose: Local LLM inference
   - Port: 1234
   - Status Check: http://localhost:1234/v1/models

4. **FastAPI Server**
   - Purpose: Main application server
   - Port: 8000
   - Status Check: http://localhost:8000/docs

### Common Issues & Solutions

1. **Neo4j Connection Issues**
   ```bash
   # Restart Neo4j container
   docker compose -f scripts/docker/compose/docker-compose.yml restart neo4j
   # Check logs
   docker compose -f scripts/docker/compose/docker-compose.yml logs neo4j
   ```

2. **Qdrant Connection Issues**
   ```bash
   # Restart Qdrant container
   docker compose -f scripts/docker/compose/docker-compose.yml restart qdrant
   # Check logs
   docker compose -f scripts/docker/compose/docker-compose.yml logs qdrant
   ```

3. **LMStudio Issues**
   - Ensure model is loaded
   - Check server is running at http://localhost:1234
   - Verify API key is set to "lm-studio"

4. **FastAPI Server Issues**
   - Check all services are running
   - Verify environment variables
   - Check logs for errors

## System Architecture

```
                                Nova Intelligence Architecture
                                ===========================

+------------------------+    WebSocket    +----------------------------------------+
|      Svelte UI         |<--------------->|              FastAPI Backend           |
|  +-----------------+   |     Events     |  +------------------+                  |
|  |  Thread View    |   |                |  |   API Endpoints  |                  |
|  |  - Main Channel |   |                |  |   - Analytics    |                  |
|  |  - Sub-threads  |   |                |  |   - Thread Mgmt  |                  |
|  |  - Task Status  |   |                |  |   - Memory Ops   |                  |
|  +-----------------+   |                |  +------------------+                  |
+------------------------+                |                                        |
                                        |  +----------------------------------+   |
                                        |  |        Nova Orchestrator         |   |
                                        |  |  +---------------------------+   |   |
                                        |  |  |       TinyFactory        |   |   |
                                        |  |  | - Dynamic Agent Creation  |   |   |
                                        |  |  | - Resource Management    |   |   |
                                        |  |  | - Swarm Configuration   |   |   |
                                        |  |  +---------------------------+   |   |
                                        |  |              |                  |   |
                                        |  |              v                  |   |
                                        |  |  +---------------------------+   |   |
                                        |  |  |     Agent Ecosystem      |   |   |
                                        |  |  | +-------------------+    |   |   |
                                        |  |  | |  Core Processing  |    |   |   |
                                        |  |  | | - ParsingAgent    |    |   |   |
                                        |  |  | | - AnalysisAgent   |    |   |   |
                                        |  |  | | - ValidationAgent |    |   |   |
                                        |  |  | +-------------------+    |   |   |
                                        |  |  |                         |   |   |
                                        |  |  | +-------------------+   |   |   |
                                        |  |  | |  Task Management  |   |   |   |
                                        |  |  | | - TaskAgent       |   |   |   |
                                        |  |  | | - ExecutionAgent  |   |   |   |
                                        |  |  | +-------------------+   |   |   |
                                        |  |  +---------------------------+   |   |
                                        |  +----------------------------------+   |
                                        |                 |                      |
                                        |                 v                      |
                                        |  +----------------------------------+   |
                                        |  |         Memory System           |   |
                                        |  | +-------------+ +------------+  |   |
                                        |  | |Vector Store | |   Neo4j    |  |   |
                                        |  | |(Ephemeral)  | |(Semantic)  |  |   |
                                        |  | |             | |            |  |   |
                                        |  | +-------------+ +------------+  |   |
                                        |  +----------------------------------+   |
                                        +----------------------------------------+

Swarm Patterns:
==============
Each pattern represents a dynamic agent collaboration strategy:

Hierarchical (H)    Parallel (P)      Sequential (S)     Mesh (M)
     [S]         [W1]--[W2]--[W3]    [1]->[2]->[3]    [A]<-->[B]
      |                   |                              ^      ^
   [W1]-[W2]          [Output]                          |      |
                                                       [C]<----+

S = Supervisor, W = Worker, Numbers = Stages, Letters = Peer Agents
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
### Common Issues & Solutions

1. **Neo4j Connection Issues**
   ```bash
   # Restart Neo4j container
   docker compose -f scripts/docker/docker-compose.yml restart neo4j
   # Check logs
   docker compose -f scripts/docker/docker-compose.yml logs neo4j
   ```

2. **Qdrant Connection Issues**
   ```bash
   # Restart Qdrant container
   docker compose -f scripts/docker/docker-compose.yml restart qdrant
   # Check logs
   docker compose -f scripts/docker/docker-compose.yml logs qdrant
   ```

