# NIA (Neural Intelligence Assistant)

A chat interface with advanced memory and agent capabilities.

## Requirements

- Docker and Docker Compose
- Python 3.8+
- Neo4j
- Qdrant

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
pip install -r src/nia/ui/requirements.txt
```

3. Run the chat interface:
```bash
python main.py
```

## Architecture

The system consists of several key components:

- **UI Layer**: Mobile and desktop interfaces using Gradio
- **Memory System**: 
  - Neo4j for concept storage and relationships
  - Qdrant for vector storage and similarity search
- **Agent System**:
  - Meta Agent: Coordinates other agents and synthesizes responses
  - Belief Agent: Handles knowledge validation
  - Desire Agent: Manages goals and aspirations
  - Emotion Agent: Processes emotional context
  - Reflection Agent: Analyzes patterns and provides insights
  - Research Agent: Gathers and validates information
  - Task Planner Agent: Coordinates complex tasks

## Troubleshooting

1. If persistence isn't working:
   - Ensure Neo4j and Qdrant services are running (`docker ps`)
   - Check Neo4j connection at http://localhost:7474
   - Verify Qdrant health at http://localhost:6333/collections

2. If agent responses aren't appearing:
   - Check the debug output tab for errors
   - Ensure all required agents are initialized
   - Verify memory system connectivity

## Development

The project structure follows a modular design:

```
src/nia/
├── ui/              # User interface components
├── memory/          # Memory system implementation
│   ├── agents/     # Agent implementations
│   ├── neo4j/      # Neo4j integration
│   └── concept_utils/ # Concept handling utilities
└── dag/             # Task planning and execution
```

## License

[Add your license information here]
