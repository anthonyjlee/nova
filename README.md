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

## Prerequisites

1. Python 3.9 or higher
2. Docker and Docker Compose
3. Git

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/nia.git
cd nia
```

2. Run the setup script:
```bash
python scripts/setup.py
```

This will:
- Install Python dependencies
- Set up Neo4j using Docker
- Create necessary directories
- Configure environment variables

## Memory Architecture

The system uses Neo4j to create a rich, interconnected memory graph:

```
Graph Structure:

                                    [:SIMILAR_TO]
                                   /           \
(Task) -[:GENERATED]-> (Memory) <-             -> (Memory)
   |                      |                         |
   |                [:HAS_CONCEPT]            [:HAS_CONCEPT]
   |                      |                         |
   |                      v                         v
   |                  (Concept) -[:RELATED_TO]-> (Concept)
   |                      |
[:DEPENDS_ON]        [:INFLUENCES]
   |                      |
   v                      v
(Task) -[:UPDATES]-> (BeliefState)
         [:AFFECTS]-> (EmotionalState)
         [:MODIFIES]-> (DesireState)

Node Types:
- Task: Execution units with type, status, metadata
- Memory: Episodic experiences or semantic knowledge
- Concept: Extracted insights, patterns, beliefs
- State: System states (beliefs, emotions, desires)

Relationship Types:
- GENERATED: Links tasks to their memory outputs
- HAS_CONCEPT: Connects memories to extracted concepts
- RELATED_TO: Shows concept relationships
- SIMILAR_TO: Links similar memories
- DEPENDS_ON: Shows task dependencies
- INFLUENCES/AFFECTS/MODIFIES: State changes
```

## Neo4j Setup

The system uses Docker to run Neo4j, making it easy to set up and manage:

1. Start Neo4j:
```bash
docker compose up -d
```

2. Access Neo4j Browser:
- Visit http://localhost:7474
- Connect using:
  - URL: bolt://localhost:7687
  - Username: neo4j
  - Password: password (change in production)

3. Example Queries:

```cypher
// View memory structure
MATCH (m:Memory)-[r]->(n)
RETURN m, r, n LIMIT 10;

// Find concept relationships
MATCH (c1:Concept)-[:RELATED_TO]->(c2:Concept)
RETURN c1, c2;

// Track task flow
MATCH (t1:Task)-[:DEPENDS_ON]->(t2:Task)
RETURN t1, t2;

// Analyze state changes
MATCH (t:Task)-[:AFFECTS]->(s:State)
RETURN t, s ORDER BY t.timestamp;
```

## Memory Operations

1. **Storage**
```python
# Store interaction memory
memory_id = await store.store_memory(
    memory_type="interaction",
    content={
        'input': user_input,
        'response': system_response,
        'timestamp': datetime.now()
    }
)
```

2. **Retrieval**
```python
# Get related memories
memories = await store.get_related_memories(
    content="user query",
    memory_type="interaction",
    limit=5
)
```

3. **Concept Extraction**
```python
# Extract and store concepts
await store.extract_concepts(
    memory_id=memory_id,
    content={
        'beliefs': extracted_beliefs,
        'patterns': identified_patterns
    }
)
```

4. **Graph Traversal**
```python
# Get memory graph
graph = await store.get_memory_graph(
    memory_id=memory_id,
    depth=2
)
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

## Docker Commands

1. Start Neo4j:
```bash
docker compose up -d
```

2. Stop Neo4j:
```bash
docker compose down
```

3. View logs:
```bash
docker compose logs -f neo4j
```

4. Reset data:
```bash
docker compose down -v
docker compose up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details
