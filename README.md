# NIA (Neural Intelligence Architecture)

A modular system for building intelligent agents with memory, reasoning, and learning capabilities.

## Features

- **Two-Layer Memory System**
  - Semantic Search Layer (Qdrant + LMStudio embeddings)
  - Graph Knowledge Layer (Neo4j)
  - Memory consolidation and integration
  - Hybrid retrieval system

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
  - LMStudio chat completions
  - LMStudio embeddings
  - Structured JSON responses
  - Error recovery
  - Context management

## Prerequisites

1. Python 3.9 or higher
2. Docker and Docker Compose
3. Git
4. LMStudio running locally

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

The system implements a two-layer memory architecture:

### 1. Semantic Search Layer (Qdrant + LMStudio)

The semantic layer uses Qdrant vector store with LMStudio embeddings for fast similarity search:

```python
# Generate embeddings through LMStudio
curl http://127.0.0.1:1234/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-nomic-embed-text-v1.5@q8_0",
    "input": "Memory content to embed"
  }'

# Store in Qdrant
await vector_store.store_vector(
    content={
        'text': 'Memory content',
        'type': 'interaction'
    },
    metadata={'timestamp': '2024-01-01T00:00:00'}
)

# Semantic search
similar_memories = await vector_store.search_vectors(
    content="Query text",
    limit=5,
    score_threshold=0.7
)
```

### 2. Graph Knowledge Layer (Neo4j)

The graph layer uses Neo4j to store structured knowledge and relationships:

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
- Memory: Episodic experiences with content and metadata
- Concept: Extracted insights and patterns
- State: System states (beliefs, emotions, desires)
- Task: Execution units with status tracking

Relationship Types:
- SIMILAR_TO: Links semantically similar memories
- HAS_CONCEPT: Connects memories to concepts
- RELATED_TO: Shows concept relationships
- INFLUENCES/AFFECTS/MODIFIES: State changes
```

### Memory Integration

The system combines both layers for comprehensive memory operations:

```python
# Store new memory
async def store_memory(content: Dict[str, Any]) -> str:
    # 1. Store in vector store for semantic search
    vector_id = await vector_store.store_vector(content)
    
    # 2. Find similar memories using embeddings
    similar = await vector_store.search_vectors(content)
    
    # 3. Store in graph with relationships
    memory_id = await graph_store.store_memory(
        content=content,
        similar_memories=similar
    )
    
    return memory_id

# Retrieve memories
async def search_memories(query: str) -> List[Dict]:
    # 1. Search vector store
    vector_results = await vector_store.search_vectors(query)
    
    # 2. Search graph store
    graph_results = await graph_store.search_memories(query)
    
    # 3. Combine and deduplicate results
    return combine_results(vector_results, graph_results)
```

## LLM Integration

The system uses LMStudio for both text generation and embeddings:

### Chat Completions

```python
# Agent responses through LMStudio chat
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "System prompt"},
      {"role": "user", "content": "User message"}
    ]
  }'
```

### Embeddings

```python
# Generate embeddings for semantic search
curl http://localhost:1234/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-nomic-embed-text-v1.5@q8_0",
    "input": "Text to embed"
  }'
```

## Development

1. Start services:
```bash
# Start Neo4j and Qdrant
docker compose up -d

# Start LMStudio
# Run LMStudio application and load desired model
```

2. Install dev dependencies:
```bash
pip install -e ".[dev]"
```

3. Run tests:
```bash
pytest
```

4. Run linting:
```bash
ruff check .
black .
mypy .
```

## Docker Commands

1. Start services:
```bash
docker compose up -d
```

2. Stop services:
```bash
docker compose down
```

3. View logs:
```bash
docker compose logs -f
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
