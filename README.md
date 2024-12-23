# NIA (Neural Intelligence Architecture)

A modular system for building intelligent agents with memory, reasoning, and learning capabilities.

> **Recent Changes (2023-12-22)**  
> - Fixed syntax error in BaseAgent content extraction
> - Improved content string handling in base agent
> - Enhanced type checking for content dictionary
> - Improved error handling for content extraction
> - Enhanced type safety in agent base class
>
> **Known Issues**  
> - Database connectivity issues may occur with Neo4j and Qdrant
> - Some tests are failing due to LLM response parsing
> - Storage space issues with Qdrant need to be addressed
> - See [devlog](docs/devlog/2024-12-18.md) for detailed todo list

## Features

- **Two-Layer Memory System**
  - Semantic Search Layer (Qdrant + LMStudio embeddings)
  - Rich Knowledge Graph Layer (Neo4j)
  - Concept extraction and linking
  - Memory consolidation and integration
  - Hybrid retrieval system
  - Robust datetime handling and serialization

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
  - Consistent datetime handling across agents
  - Structured JSON communication
  - Example-based error recovery

- **LLM Integration**
  - LMStudio chat completions
  - LMStudio embeddings
  - Concept extraction
  - Structured JSON responses
  - Example-based prompts
  - Robust error recovery
  - Context management
  - Default behaviors

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

## Documentation

- Architecture: See [architecture.md](docs/architecture.md)
- Development Log: See daily logs in [docs/devlog/](docs/devlog/)
- Memory Architecture: Detailed below
- LLM Integration: Detailed below

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

# Store in Qdrant with proper datetime handling
await vector_store.store_vector(
    content=serialize_datetime({
        'text': 'Memory content',
        'type': 'interaction',
        'timestamp': datetime.now()
    }),
    metadata=serialize_datetime({
        'created_at': datetime.now(),
        'type': 'memory'
    })
)

# Semantic search with datetime serialization
similar_memories = await vector_store.search_vectors(
    content=serialize_datetime({
        'text': "Query text",
        'timestamp': datetime.now()
    }),
    limit=5,
    score_threshold=0.7
)
```

### 2. Knowledge Graph Layer (Neo4j)

The graph layer uses Neo4j to store structured knowledge with rich relationships:

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
   |                      |                         |
   |                [:HAS_TOPIC]              [:HAS_TOPIC]
   |                      |                         |
   |                      v                         v
   |                   (Topic) -[:RELATED_TO]-> (Topic)
   |                      |
[:DEPENDS_ON]        [:INFLUENCES]
   |                      |
   v                      v
(Task) -[:UPDATES]-> (BeliefState)
         [:AFFECTS]-> (EmotionalState)
         [:MODIFIES]-> (DesireState)

Node Types:
- Memory: Episodic experiences with content and metadata
- Concept: Extracted insights and patterns (LLM extracted)
- Topic: High-level categories and themes
- State: System states (beliefs, emotions, desires)
- Task: Execution units with status tracking
- AISystem: System versions and capabilities
- Capability: System capabilities and functions

Relationship Types:
- SIMILAR_TO: Links semantically similar memories
- HAS_CONCEPT: Connects memories to extracted concepts
- RELATED_TO: Shows relationships between nodes
- HAS_TOPIC: Categorizes memories and concepts
- INFLUENCES/AFFECTS/MODIFIES: State changes
- CREATED_BY: Links memories to creating system
- HAS_CAPABILITY: Links systems to capabilities
- PREDECESSOR_OF: Shows system evolution
```

### Memory Integration

The system combines both layers for comprehensive memory operations:

```python
# Store new memory with concept extraction and datetime handling
async def store_memory(content: Dict[str, Any]) -> str:
    # 1. Store in vector store for semantic search
    vector_id = await vector_store.store_vector(
        content=serialize_datetime(content)
    )
    
    # 2. Find similar memories using embeddings
    similar = await vector_store.search_vectors(
        content=serialize_datetime(content)
    )
    
    # 3. Extract concepts using LLM
    concepts = await extract_concepts(content)
    
    # 4. Store in graph with relationships
    memory_id = await graph_store.store_memory(
        content=serialize_datetime(content),
        similar_memories=serialize_datetime(similar),
        concepts=serialize_datetime(concepts)
    )
    
    return memory_id

# Retrieve memories with concepts
async def search_memories(query: str) -> List[Dict]:
    # 1. Search vector store
    vector_results = await vector_store.search_vectors(
        content=serialize_datetime({'content': query})
    )
    
    # 2. Search graph store with concepts
    graph_results = await graph_store.search_memories(
        content_pattern=query,
        include_concepts=True
    )
    
    # 3. Combine and deduplicate results
    return serialize_datetime(
        combine_results(vector_results, graph_results)
    )
```

## LLM Integration

The system uses LMStudio for text generation, embeddings, and concept extraction:

### Chat Completions with Examples

```python
# Agent responses through LMStudio with example-based prompts
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "System prompt with examples"},
      {"role": "user", "content": "Here is an example of the format I want:"},
      {"role": "assistant", "content": "Example response in correct format"},
      {"role": "user", "content": "User message"}
    ]
  }'
```

### Structured JSON Output

```python
# Extract structured data using LLM
async def extract_structured_data(content: str) -> Dict:
    prompt = """Extract information in this exact JSON format:
    {
        "concepts": [{
            "name": "concept name",
            "type": "concept type",
            "description": "description",
            "confidence": 0.8,
            "validation": {
                "supported_by": ["evidence"],
                "contradicted_by": [],
                "needs_verification": []
            }
        }],
        "key_points": ["main insights"],
        "implications": ["areas needing discussion"]
    }"""
    
    response = await llm.get_completion(prompt)
    
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Example-based error recovery
        return await llm.get_completion(
            f"Fix JSON format:\n{response}\n\nExample:\n{example_json}"
        )
```

### Error Recovery

```python
# Robust error handling with examples
async def handle_llm_error(error: Exception, context: str) -> Dict:
    # 1. Try to extract JSON from markdown
    json_match = re.search(r'```json\s*(.*?)\s*```', context)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            pass
    
    # 2. Example-based recovery
    fix_prompt = f"""Fix this response to match example:
    
    Example:
    {example_json}
    
    Response to fix:
    {context}"""
    
    fixed = await llm.get_completion(fix_prompt)
    return json.loads(fixed)
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
