# NIA (Neural Intelligence Architecture)

A self-reflective, adaptive, and evolving multi-agent system that explores its own existence, processes external data, and cultivates an enriched internal understanding of its identity, goals, and potential.

## Features

### Memory System
- Two-layer memory architecture with short-term and long-term storage
- Vector-based storage using Qdrant for semantic search
- Indexed fields for efficient retrieval:
  - memory_type: Type of memory (belief, emotion, desire, etc.)
  - timestamp: When the memory was created
  - importance: Memory significance score

### Agent System
- BeliefAgent: Ensures logical consistency and factual accuracy
- DesireAgent: Explores and refines system goals and aspirations
- EmotionAgent: Interprets and expresses system emotional states
- ReflectionAgent: Synthesizes insights from past experiences
- ResearchAgent: Gathers and integrates external data
- MetaAgent: Coordinates interactions and synthesizes outputs

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Qdrant running locally (default: http://localhost:6333)
- LM Studio or similar LLM server running locally (default: http://localhost:1234)

### Installation
```bash
# Clone the repository
git clone [repository-url]

# Install the package
pip install -e .
```

### Running the Interactive System
```bash
python examples/interactive_memory_system.py
```

Available commands in the interactive system:
- `status`: Show system state
- `logs`: Show memory state and agent responses
- `reset`: Reset memory system
- `clean`: Clean memory system
- `exit`: End session

## Project Structure
```
nia/
├── docs/
│   ├── architecture.md   # Detailed system architecture
│   └── DEVLOG.md        # Development log
├── examples/
│   └── interactive_memory_system.py
├── src/
│   └── nia/
│       └── memory/      # Core memory system
│           ├── agents/  # Agent implementations
│           └── ...      # Memory management modules
└── tests/
    └── test_basic.py
```

## Development Status
- [x] Memory system with vector store integration
- [x] Core agent system implementation
- [x] Interactive CLI for testing
- [x] Basic test framework
- [ ] Advanced memory consolidation
- [ ] Enhanced agent capabilities
- [ ] Web interface

## License
MIT License
