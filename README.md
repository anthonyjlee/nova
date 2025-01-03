# NIA (Nova Intelligence Architecture)

NIA is a sophisticated multi-agent system built on TinyTroupe that combines metacognition (Nova) with domain-specific tasks. The system features a FastAPI backend, Svelte frontend, and a two-layer memory system using vector storage and Neo4j.

## System Overview

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

- **AnalysisAgent**: 
  * Pattern detection with domain boundaries
  * Insight generation and validation
  * Real-time analysis state tracking
  * Analysis strategy system
  * Trend detector management

- **SynthesisAgent**: 
  * Theme identification across domains
  * Conclusion generation and validation
  * Pattern-based synthesis
  * Domain-aware content synthesis
  * Enhanced theme identification

- **ValidationAgent**: 
  * Rule-based validation with domain context
  * Issue detection and reporting
  * Validation rules with domain boundaries
  * Enhanced error handling
  * Comprehensive validation coverage

- **SchemaAgent**: 
  * Schema validation with domain boundaries
  * Pydantic model generation
  * Schema evolution tracking
  * Enhanced model validation
  * Domain-aware schema analysis

### Cognitive Agents
- **BeliefAgent**: 
  * Evidence validation with domain boundaries
  * Belief system management
  * Confidence-based validation
  * Domain-specific belief tracking
  * Enhanced evidence validation

- **DesireAgent**: 
  * Motivation tracking with domain boundaries
  * Priority management and validation
  * Domain-aware desire analysis
  * Enhanced motivation tracking
  * Priority validation system

- **EmotionAgent**: 
  * Intensity tracking with domain context
  * Emotional state processing
  * Domain-aware emotion analysis
  * Enhanced intensity tracking
  * Emotional validation system

- **ReflectionAgent**: 
  * Pattern recognition with domain boundaries
  * Insight generation and validation
  * Domain-aware reflection analysis
  * Enhanced pattern recognition
  * Reflection recording system

- **MetaAgent**: 
  * Meta-level orchestration and synthesis
  * Domain-aware agent coordination
  * Multi-domain agent orchestration
  * Enhanced response gathering
  * Domain-specific reflection recording

### Task Management
- **TaskAgent**: 
  * Dependency tracking with domain boundaries
  * Task state management
  * Domain-aware task analysis
  * Enhanced dependency tracking
  * Task validation system

- **ExecutionAgent**: 
  * Sequence optimization with error recovery
  * Real-time sequence state tracking
  * Resource utilization monitoring
  * Priority queue management
  * Retry mechanism with limits

- **OrchestrationAgent**: 
  * Flow coordination with domain boundaries
  * Real-time flow state tracking
  * Resource utilization monitoring
  * Task dependency management
  * Automated issue detection

- **CoordinationAgent**: 
  * Resource allocation with conflict detection
  * Group management and task dependencies
  * State tracking with emotional responses
  * Memory integration with reflections
  * Enhanced resource management

### Communication
- **DialogueAgent**: 
  * Real-time conversation state tracking
  * Multi-agent conversation coordination
  * Flow control and intervention
  * Pattern recognition and recording
  * Enhanced memory integration

- **ResponseAgent**: 
  * Component validation with domain boundaries
  * Response quality assessment
  * Domain-aware response analysis
  * Enhanced component validation
  * Quality validation system

- **IntegrationAgent**: 
  * Relationship identification with domain boundaries
  * Connection generation and validation
  * Domain-aware content integration
  * Enhanced relationship handling
  * Integration evolution tracking

### Research & Context
- **ResearchAgent**: 
  * Source validation with domain boundaries
  * Information gathering and verification
  * Domain-aware research analysis
  * Enhanced source validation
  * Finding validation system

- **ContextAgent**: 
  * Environment tracking with domain boundaries
  * Context-aware state management
  * Domain-aware context analysis
  * Enhanced environment tracking
  * Context validation system

- **StructureAgent**: 
  * Pattern analysis with domain boundaries
  * Schema validation and evolution
  * Domain-aware structure analysis
  * Enhanced pattern detection
  * Structure validation system

### System Operations
- **MonitoringAgent**: 
  * Real-time metric state tracking
  * Health check automation
  * Alert generation and management
  * Incident lifecycle tracking
  * Trend analysis and aggregation

- **AlertingAgent**: 
  * Real-time alert state tracking
  * Rule-based routing system
  * Delivery status monitoring
  * Retry mechanism with escalation
  * Filter-based noise reduction

- **LoggingAgent**: 
  * Real-time log state tracking
  * Format template system
  * Context enrichment rules
  * Storage policy management
  * Rotation policy handling

- **MetricsAgent**: 
  * Real-time metric state tracking
  * Collection strategy system
  * Aggregation rule management
  * Calculation template handling
  * Retention policy management

- **AnalyticsAgent**: 
  * Real-time analysis state tracking
  * Analysis strategy system
  * Pattern template management
  * Insight model handling
  * Trend detector management

- **VisualizationAgent**: 
  * Real-time visualization state tracking
  * Visualization strategy system
  * Layout template management
  * Chart template handling
  * Rendering engine management

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

## Development

### API Documentation
- OpenAPI docs available at `/docs`
- WebSocket endpoints for real-time updates
- Authentication using API keys
- Rate limiting with sliding window

### Testing
```bash
# Run backend tests
python -m pytest

# Run frontend tests
cd frontend
npm test
```

## Architecture

```
          +-------------------+        +--------------------+
          |    Svelte UI     | <----> |   FastAPI Backend  | <----> [Nova + TinyTroupe Agents]
          +-------------------+        +--------------------+
                     |                           |
                     v                           v
          [Vector DB: ephemeral]          [Neo4j: semantic memory]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
