# NIA (Neural Intelligence Assistant)

A sophisticated multi-agent system that combines metacognitive capabilities with domain task execution, built on TinyTroupe framework.

## Overview

NIA is designed to be a self-reflective, adaptive system that can:
- Maintain introspective capabilities through specialized agents
- Handle external domain tasks without compromising metacognition
- Scale to manage large numbers of agents efficiently
- Preserve conversation abilities during task pauses
- Provide intuitive visualization of complex agent interactions

### Key Features

- **Metacognitive Core**:
  - Self-reflection through specialized agents
  - Memory consolidation and learning
  - Goal and emotion awareness
  - Belief system management

- **Domain Task Capabilities**:
  - Dynamic agent spawning for specific tasks
  - Efficient agent grouping and management
  - Task pause/resume without affecting conversations
  - Clear separation between metacognitive and domain tasks

- **Advanced Memory Architecture**:
  - Dual-layer system with Neo4j and Qdrant
  - Domain-aware memory categorization
  - Efficient consolidation strategies
  - Memory access control and isolation
  - Personal vs. Professional domain separation

- **Modern UI**:
  - FastAPI backend with WebSocket support
  - React frontend with real-time updates
  - Knowledge graph visualization
  - Domain-specific views
  - Real-time agent relationship visualization

## Requirements

- Docker and Docker Compose
- Python 3.8+
- Node.js 18+
- Neo4j
- Qdrant
- LMStudio (for LLM capabilities)

## Setup

1. Start the required services:
```bash
docker-compose up -d
```

This will start:
- Neo4j on port 7687 (Bolt) and 7474 (HTTP)
- Qdrant on port 6333 (HTTP) and 6334 (GRPC)

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Start the backend server:
```bash
uvicorn main:app --reload
```

5. Start the frontend development server:
```bash
cd frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Architecture

### Core Components

- **Nova (Meta-Orchestrator)**:
  - Coordinates both metacognitive and domain tasks
  - Manages agent spawning and lifecycle
  - Handles task delegation and memory operations
  - Maintains UI awareness and updates
  - Acts as user proxy for auto-approval

- **Memory System**: 
  - Neo4j for concept storage and relationships
  - Qdrant for vector storage and similarity search
  - Domain-aware memory categorization (Personal/Professional)
  - Efficient consolidation strategies

- **Agent System**:
  - **Specialized Agents**:
    - Dialogue Agent: Manages conversation flow
    - Emotion Agent: Handles affective analysis
    - Belief Agent: Manages knowledge and beliefs
    - Research Agent: Gathers and analyzes information
    - Reflection Agent: Handles pattern recognition
    - Desire Agent: Tracks goals and motivations
    - Task Agent: Manages planning and execution
  
  - **Task Management**:
    - Dynamic task allocation
    - Domain-specific handling
    - Pause/resume capabilities
    - Resource management

### Current Structure

```
src/nia/
├── agents/
│   ├── specialized/
│   │   ├── dialogue_agent.py
│   │   ├── emotion_agent.py
│   │   ├── belief_agent.py
│   │   ├── research_agent.py
│   │   ├── reflection_agent.py
│   │   ├── desire_agent.py
│   │   └── task_agent.py
│   ├── base.py
│   └── tinytroupe_agent.py
├── nova/
│   ├── core/
│   │   ├── parsing.py
│   │   ├── meta.py
│   │   ├── structure.py
│   │   ├── context.py
│   │   └── processor.py
│   ├── tasks/
│   │   ├── planner.py
│   │   └── context.py
│   └── orchestrator.py
├── memory/
│   ├── neo4j/
│   ├── vector/
│   ├── types/
│   ├── consolidation.py
│   └── two_layer.py
└── ui/
    ├── backend/
    │   ├── api/
    │   ├── websocket/
    │   └── main.py
    └── frontend/
        ├── src/
        │   ├── components/
        │   ├── pages/
        │   └── services/
        └── package.json
```

### Integration with TinyTroupe

The system leverages TinyTroupe's capabilities through:
- TinyTroupeAgent base class combining:
  * Original BaseAgent memory capabilities
  * TinyTroupe simulation features
  * Emotion and desire tracking
- NIAWorld extending TinyWorld for:
  * Resource management
  * Domain handling
  * Task coordination

## Development Status

### Completed
- Core agent system implementation
- Memory system integration
- World environment setup
- Specialized agent implementations
- Base TinyTroupe integration
- Memory domain separation

### In Progress
- FastAPI + React UI development
- Testing implementation
- Documentation updates
- Performance optimization

### Upcoming
- Deployment configuration
- Monitoring tools
- Security enhancements
- Production readiness

## Troubleshooting

1. Memory System Issues:
   - Ensure Neo4j and Qdrant services are running (`docker ps`)
   - Check Neo4j connection at http://localhost:7474
   - Verify Qdrant health at http://localhost:6333/collections

2. Agent Response Issues:
   - Check the debug output tab for errors
   - Ensure LMStudio is running and accessible
   - Verify all required agents are initialized
   - Check memory system connectivity

3. UI Issues:
   - Check both frontend and backend logs
   - Verify WebSocket connection
   - Monitor React component updates
   - Check browser console for errors
   - Verify API endpoints using Swagger UI

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

[MIT License](LICENSE)
