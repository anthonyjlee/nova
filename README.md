# NIA (Nova Intelligence Architecture)

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

### Industry Evolution
- **Beyond Health & Wellness**: Lydia AI's expansion from healthcare into broader domains requires sophisticated orchestration capabilities that can handle diverse industry requirements and regulations
- **Vertical AI Challenges**: Complex industries like telecom and finance need specialized AI solutions that can:
  * Handle industry-specific compliance requirements
  * Process domain-specific data formats
  * Integrate with legacy systems
  * Manage complex workflows
  * Scale across enterprise operations

### Technical Advances
- **Multi-Modal Evolution**: Building on Well-E's success in multi-modal health modeling, NIA extends these capabilities to orchestrate:
  * Multiple specialized models
  * Cross-domain integrations
  * Industry-specific pipelines
  * Real-time data processing
  * Regulatory compliance checks

### Scale Requirements
- **Massive Agent Orchestration**: Unique ability to manage hundreds of specialized agents, necessary because:
  * Complex domains require multiple specialized agents working in parallel
  * Each agent focuses on a specific aspect of the problem
  * Large-scale systems need continuous monitoring at multiple points
  * Real-time processing requires distributed agent networks
  * Cross-domain operations need specialized agent teams

### Vertical AI Solutions
NIA enables specialized solutions requiring large-scale agent deployment:

1. **Telecom**:
   - Network optimization agents (50+ agents):
     * Each monitoring different network segments
     * Load balancing across regions
     * Protocol-specific optimization
     * Traffic pattern analysis
     * QoS management per service type
   - Customer service orchestration (100+ agents):
     * Intent classification
     * Service routing
     * Multi-channel support
     * Response generation
     * Satisfaction monitoring
   - Infrastructure monitoring swarms (200+ agents):
     * Hardware health tracking
     * Software performance monitoring
     * Security threat detection
     * Capacity planning
     * Fault prediction
   - Predictive maintenance coordination (75+ agents):
     * Equipment health monitoring
     * Failure pattern detection
     * Maintenance scheduling
     * Resource allocation
     * Impact assessment

2. **Finance**:
   - Risk assessment swarms (150+ agents):
     * Market risk analysis
     * Credit risk evaluation
     * Operational risk monitoring
     * Compliance risk tracking
     * Model risk validation
   - Fraud detection networks (300+ agents):
     * Transaction monitoring
     * Pattern recognition
     * Anomaly detection
     * Cross-validation
     * Alert management
   - Trading strategy orchestration (250+ agents):
     * Market analysis
     * Strategy execution
     * Risk management
     * Portfolio balancing
     * Performance tracking

3. **Enterprise Operations**:
   - Resource allocation optimization (100+ agents):
     * Demand forecasting
     * Capacity planning
     * Cost optimization
     * Performance monitoring
     * Efficiency analysis
   - Supply chain coordination (200+ agents):
     * Inventory management
     * Logistics optimization
     * Supplier coordination
     * Demand prediction
     * Risk mitigation
   - Process automation orchestration (150+ agents):
     * Workflow monitoring
     * Exception handling
     * Integration management
     * Performance optimization
     * Quality assurance

Each vertical solution requires large numbers of agents because:
1. **Complexity Management**: Breaking down complex problems into manageable units
2. **Specialization**: Each agent handles specific aspects requiring deep expertise
3. **Real-Time Processing**: Parallel processing for immediate response
4. **Redundancy**: Multiple agents for critical functions ensuring reliability
5. **Scale**: Enterprise-level operations requiring distributed processing
6. **Integration**: Cross-system coordination requiring specialized handlers
7. **Compliance**: Industry-specific regulatory requirements needing dedicated monitoring
8. **Security**: Multi-layer security measures with specialized agents
9. **Quality Assurance**: Multiple validation and verification steps
10. **Performance**: Load distribution across agent networks for optimal performance

### Market Timing
- Growing demand for enterprise-scale AI orchestration
- Increasing complexity of multi-model solutions
- Rising need for domain-specific AI adaptation
- Expanding requirements for real-time processing
- Emerging opportunities in vertical markets

## Why NIA?

NIA takes a fundamentally different approach to multi-agent orchestration compared to existing frameworks:

### Beyond Traditional Frameworks

- **TinyTroupe**: While NIA builds on TinyTroupe's foundation, it adds metacognitive capabilities through Nova, enabling agents to reflect on their own performance and adapt their strategies. Unlike basic TinyTroupe agents, NIA agents maintain a self-model in Neo4j and can evolve their capabilities through experience.

- **ChatDev**: ChatDev focuses on software development through predefined agent roles. NIA, in contrast, enables dynamic agent creation through TinyFactory based on emergent task requirements, allowing for more flexible and adaptable solutions across domains.

- **AutoGen/Ignite**: These frameworks provide agent templates and conversation patterns. NIA goes further by implementing domain-aware processing, strict personal/professional boundaries, and sophisticated memory consolidation that enables long-term learning.

- **Streamlit**: While Streamlit excels at rapid UI development, NIA provides a comprehensive architecture with real-time WebSocket communication, thread management, and domain-specific UI adaptations through SvelteKit.

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

### Real-World Applications

NIA's architecture is particularly suited for:
- Complex system design and architecture
- Cross-domain knowledge integration
- Long-term project evolution
- Collaborative solution refinement
- Domain-sensitive processing
- Real-time multi-agent coordination

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
- Understand user context through multi-modal intake
- Manage personal vs. professional domain boundaries
- Coordinate specialized agents for complex tasks
- Generate and manage emergent tasks through agent collaboration
- Create new agents dynamically via TinyFactory
- Provide skill access through SkillsAgent

#### Initialization Protocol
1. System Identity
   * Loads self-model and capabilities
   * Initializes specialized agents
   * Configures tool access and memory layers

2. User Context
   * Gathers user profile and preferences
   * Analyzes work/personal domain boundaries
   * Establishes security and privacy settings

3. Memory Initialization
   * Verifies episodic (vector) and semantic (Neo4j) stores
   * Loads relevant conversation history
   * Prepares domain-specific knowledge partitions

4. Agent Reflection
   * ReflectionAgent analyzes user context
   * BeliefAgent updates system beliefs
   * Specialized agents prepare domain-specific strategies

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

Example agent creation flow:
1. Nova receives complex task
2. Task analyzed for required capabilities
3. TinyFactory designs optimal agent configuration
4. New agent spawned with specific skills
5. Agent integrated into existing workflow
6. Performance monitored for optimization

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

### Frontend
- SvelteKit for UI framework
- Cytoscape.js for graph visualization
- WebSocket for real-time updates
- Domain-aware UI components

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
- Python 3.8+
- Node.js 14+
- Neo4j 4.4+
- Vector store (FAISS/Qdrant)

### Installation
1. Clone the repository
2. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```
4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```
5. Start the services:
   ```bash
   # Start Neo4j
   docker-compose up -d neo4j
   
   # Start the FastAPI server
   python scripts/run_server.py
   
   # Start the frontend
   cd frontend
   npm run dev
   ```

## Architecture

```
                                Nova Intelligence Architecture
                                ===========================

+------------------------+    WebSocket    +-------------------------+
|      Svelte UI         |<--------------->|     FastAPI Backend     |
|  +-----------------+   |     Events     |  +------------------+    |
|  |  Thread View    |   |                |  |   API Endpoints  |    |
|  |  - Main Channel |   |                |  |   - Analytics    |    |
|  |  - Sub-threads  |   |                |  |   - Thread Mgmt  |    |
|  |  - Task Status  |   |                |  |   - Memory Ops   |    |
|  +-----------------+   |                |  +------------------+    |
+------------------------+                +-------------------------+
           ^                                          |
           |                                          v
           |                              +-------------------------+
           |                              |    Nova Orchestrator    |
           |                              |  +------------------+   |
           |                              |  |   TinyFactory    |   |
           |                              |  |   - Agent Creation|   |
           |                              |  |   - Swarm Patterns|   |
           |                              |  +------------------+   |
           |                              +-------------------------+
           |                                          |
           |                                          v
           |                              +-------------------------+
           |                              |    Agent Ecosystem     |
           |                              | +-------------------+  |
           |                              | |  Core Processing  |  |
           |                              | |  - ParsingAgent   |  |
           |                              | |  - AnalysisAgent  |  |
           |                              | |  - ValidationAgent|  |
           |                              | +-------------------+  |
           |                              |                       |
           |                              | +-------------------+ |
           |                              | |  Task Management  | |
           |                              | |  - TaskAgent      | |
           |                              | |  - ExecutionAgent | |
           |                              | |  - Coordination   | |
           |                              | +-------------------+ |
           |                              +-------------------------+
           |                                          |
           |                                          v
           |                              +-------------------------+
           |                              |    Memory System       |
           |                              | +-------------------+  |
           |                              | |   Vector Store    |  |
           |                              | | (Ephemeral Data)  |  |
           |                              | | - Chat History    |  |
           |                              | | - Thread States   |  |
           |                              | +-------------------+  |
           |                              |                       |
           |                              | +-------------------+ |
           |                              | |      Neo4j       | |
           |                              | | (Semantic Data)  | |
           |                              | | - Knowledge Graph| |
           |                              | | - Task Relations | |
           |                              | | - Agent States   | |
           |                              | +-------------------+ |
           |                              +-------------------------+
           |                                          |
           +------------------------------------------+

Swarm Patterns:
===============
[H] = Hierarchical   [P] = Parallel   [S] = Sequential   [M] = Mesh

  [H]                [P]              [S]               [M]
   |                  |                |                 |
   v                  v                v                 v
[Super]          [Worker1]--+     [Stage1]--+      [Agent1]<-->[Agent2]
   |                [Worker2]--+-->   |     |           ^          ^
[Work1]--[Work2]    [Worker3]--+    [Stage2] |      [Agent3]<----+
                                            [Stage3]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
