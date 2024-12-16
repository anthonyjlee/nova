# NIA (Neural Intelligence Architecture)

A modular system for building intelligent agents with memory, reasoning, and learning capabilities.

## Features

- **Two-Layer Memory System**
  - Episodic memory for experiences
  - Semantic memory for knowledge
  - Graph-based storage with Neo4j
  - Memory consolidation

- **DAG-Based Task Management**
  - Task decomposition
  - Parallel execution
  - Dependency handling
  - State tracking

- **Agent System**
  - Belief management
  - Desire tracking
  - Emotion processing
  - Reflection capabilities
  - Research abilities

- **LLM Integration**
  - Async completion
  - JSON response handling
  - Error recovery
  - Context management

## Installation

1. Install Python 3.9 or higher
2. Clone this repository
3. Run the setup script:

```bash
python scripts/setup.py
```

This will:
- Install Python dependencies
- Install and configure Neo4j
- Set up environment variables
- Create necessary directories

## Neo4j Memory System

The system uses Neo4j for graph-based memory storage, offering:

- **Rich Relationships**
  - Task dependencies
  - Memory connections
  - Concept linking
  - Temporal relationships

- **Interactive Visualization**
  - Memory graphs
  - Task execution flows
  - Knowledge networks
  - Concept maps

- **Powerful Querying**
  - Pattern matching
  - Path finding
  - Similarity search
  - Temporal queries

### Using Neo4j Browser

1. Start Neo4j:
```bash
brew services start neo4j  # macOS
sudo systemctl start neo4j  # Linux
```

2. Open Neo4j Browser:
- Visit http://localhost:7474
- Connect using:
  - URL: bolt://localhost:7687
  - Username: neo4j
  - Password: password (or as configured)

3. Example Queries:

```cypher
// View all memories
MATCH (m:Memory) RETURN m;

// Find related concepts
MATCH (m:Memory)-[:HAS_CONCEPT]->(c:Concept)
WHERE m.type = 'interaction'
RETURN m, c;

// Track task execution
MATCH (t:Task)-[:GENERATED]->(m:Memory)
RETURN t, m;
```

## Examples

1. Test Neo4j Memory:
```bash
python examples/test_neo4j_memory.py
```

2. Test DAG System:
```bash
python examples/test_memory_dag.py
```

## Architecture

The system consists of several key components:

1. **Memory Layer**
   - Neo4j graph database
   - Memory integration
   - Concept extraction
   - Knowledge consolidation

2. **Task Layer**
   - DAG management
   - Task execution
   - State tracking
   - Error handling

3. **Agent Layer**
   - Specialized agents
   - Coordination
   - Response synthesis
   - Learning

4. **Integration Layer**
   - LLM interface
   - Memory access
   - Task routing
   - State management

## Development

1. Install dev dependencies:
```bash
pip install -e ".[dev]"
```

2. Run tests:
```bash
pytest
```

3. Run linting:
```bash
ruff check .
black .
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details
