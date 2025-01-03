# NIA (Nova Intelligence Architecture)

NIA is a sophisticated multi-agent system built on TinyTroupe that combines metacognition (Nova) with domain-specific tasks. The system features a FastAPI backend, Svelte frontend, and a two-layer memory system using vector storage and Neo4j.

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
The system supports dynamic swarm architectures for agent collaboration:

#### Swarm Patterns
- **Hierarchical**: Tree-structured command flow
- **Parallel**: Independent concurrent processing
- **Sequential**: Ordered task processing chain
- **Mesh**: Free-form agent communication

#### Swarm Types
- **MajorityVoting**: Consensus-based decisions
- **RoundRobin**: Cyclic task distribution
- **GraphWorkflow**: DAG-based task execution

#### Communication Patterns
- **Broadcast**: One-to-many messaging
- **Direct**: Point-to-point communication
- **Group**: Targeted multi-agent messaging

#### Resource Management
- Dynamic resource allocation
- Load balancing across agents
- Performance monitoring
- Bottleneck detection
- Automatic scaling

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

[Previous agent sections remain unchanged...]

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

[Previous sections remain unchanged...]

## Architecture

```
          +-------------------+        +--------------------+
          |    Svelte UI     | <----> |   FastAPI Backend  | <----> [Nova + TinyTroupe Agents]
          +-------------------+        +--------------------+
                     |                           |
                     v                           v
          [Vector DB: ephemeral]          [Neo4j: semantic memory]

Swarm Architecture:
[Coordinator Agent] ---> [Worker Agents]
       |                      |
       v                      v
[Resource Pool] <--> [Task Queue]
```

## Contributing

[Previous sections remain unchanged...]

## License

This project is licensed under the MIT License - see the LICENSE file for details.
