# NIA (Nova Intelligence Architecture)

> **Project Status (2025-01-09)**: Memory system testing and integration. Preparing for frontend development.

NIA is a sophisticated multi-agent system that combines:
- Two-layer memory architecture (episodic/semantic)
- Profile-based task adaptations
- Domain-aware processing
- Swarm-based agent collaboration

## Why NIA?

NIA takes a fundamentally different approach to multi-agent orchestration:

1. **Beyond Traditional Frameworks**:
   - Adds meta-cognitive capabilities through "Nova" the default agent
   - Enables dynamic agent creation through TinyFactory (+100 agents)
   - Implements domain-aware processing (i.e., finance, retail, healthcare)
   - Features sophisticated memory consolidation (qdrant+neo4j)

2. **Key Differentiators**:
   - Co-Creation Focus: Agents participate in multi agentic solution design
   - Meta-cognitive Architecture: Self-aware agents that reflect
   - Emergent Task Detection: Proactive agent project/task identification through conversations
   - Domain Intelligence: Strict personal/professional separation

## Research Foundations

Building on Well-E's research, NIA addresses fundamental challenges:

1. **Theoretical Framework**:
   - Information-theoretic bounds on agent communication
   - Formal verification of emergent behaviors
   - Convergence guarantees in distributed learning
   - Game-theoretic equilibria in agent networks

## Core Architecture

### Memory System

1. Two-Layer Storage:
```python
class TwoLayerMemorySystem:
    def __init__(self):
        self.episodic = EpisodicLayer(vector_store)  # Recent, context-rich
        self.semantic = SemanticLayer(neo4j_store)   # Long-term knowledge
```

2. Memory Integration:
- Episodic layer for recent context
- Semantic layer for validated knowledge
- Pattern-based consolidation
- Domain boundary enforcement

### Agent Inheritance

1. Base Memory (BaseAgent):
```python
class BaseAgent:
    """Core memory operations."""
    async def store_memory(self, content: Any):
        memory = EpisodicMemory(
            content=content,
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat()
        )
        return await self.memory_system.store_experience(memory)
```

2. TinyTroupe Layer:
```python
class TinyTroupeAgent(TinyPerson, BaseAgent):
    """Adds state and learning."""
    async def process(self, content: Dict):
        # Store memory
        memory_id = await self.store_memory(...)
        
        # Update TinyTroupe state
        if "concepts" in content:
            for concept in content["concepts"]:
                await self.learn_concept(...)
```

3. Specialized Agents:
```python
class BeliefAgent(NovaBeliefAgent, TinyTroupeAgent):
    """Domain-specific capabilities."""
    async def analyze_and_store(self, content: Dict):
        # Validate domain access
        await self.validate_domain_access(target_domain)
        
        # Store analysis
        await self.store_memory({
            "type": "belief_analysis",
            "content": content,
            "analysis": result
        })
```

### Graph Integration

1. DAG System:
```python
class SwarmGraphIntegration:
    async def instantiate_pattern(self, pattern_id: str):
        """Convert Neo4j pattern to DAG."""
        pattern = await self.store.get_pattern(pattern_id)
        dag = SwarmDAG()
        
        # Create task nodes
        for task in pattern_config["tasks"]:
            task_id = await dag.add_task_node(
                task_type=task["type"],
                config=task["config"]
            )
```

2. Pattern Storage:
```python
async def persist_execution(self, dag: SwarmDAG):
    """Store execution results in Neo4j."""
    await self.store.execute_query("""
    MATCH (p:SwarmPattern {id: $pattern_id})
    CREATE (e:PatternExecution {
        graph_state: $graph_state,
        metrics: $metrics
    })
    CREATE (p)-[:HAS_EXECUTION]->(e)
    """)
```

### Profile System

1. User Profiling:
```python
class ProfileAgent(TinyTroupeAgent):
    async def adapt_task(self, task: Dict, profile: Dict):
        """Adapt task based on user profile."""
        return {
            "content": task["content"],
            "user_profile_id": profile["id"],
            "adaptation": {
                "granularity": profile["conscientiousness"],
                "style": profile["learning_style"],
                "communication": profile["communication_preference"]
            }
        }
```

2. Task Adaptation:
```python
class TaskOutput:
    # Vector Store Fields
    content: str  # actual output content
    type: str    # code, media, skill, doc, api
    importance: float  # for consolidation
    
    # Neo4j Fields
    task_id: str
    user_profile_id: str
    adaptation: Dict[str, Any]  # How task was adapted
    
    # Metadata
    created_at: datetime
    domain: str  # knowledge vertical
```

## Swarm Patterns

Each pattern represents a dynamic agent collaboration strategy:

1. Hierarchical:
```python
hierarchical_config = {
    "name": "test_hierarchical",
    "agents": ["agent1", "agent2", "agent3"],
    "supervisor_id": "agent1",
    "worker_ids": ["agent2", "agent3"]
}
```

2. Parallel:
```python
parallel_config = {
    "name": "test_parallel",
    "agents": ["agent1", "agent2", "agent3"],
    "batch_size": 2,
    "load_balancing": True
}
```

3. Sequential:
```python
sequential_config = {
    "name": "test_sequential",
    "agents": ["agent1", "agent2", "agent3"],
    "stages": [
        {"stage": "parse", "agent": "agent1"},
        {"stage": "analyze", "agent": "agent2"},
        {"stage": "validate", "agent": "agent3"}
    ]
}
```

## Getting Started

### Prerequisites
- Python 3.9+
- Docker Desktop
- LMStudio (for LLM inference)

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/NIA.git
cd NIA

# Install dependencies
pip install -r requirements.txt

# Start services
python scripts/manage.py start
```

### Development
```bash
# Start all services (Neo4j, Qdrant, FastAPI, Frontend)
python scripts/manage.py start

# Check service status
python scripts/manage.py status

# Stop all services
python scripts/manage.py stop

# Restart all services
python scripts/manage.py restart

# Run tests
pytest tests/memory/integration/  # Memory tests
pytest tests/nova/               # Nova tests
```

### Service Dependencies

1. **Neo4j (Graph Database)**
   - Purpose: Semantic memory storage
   - Port: 7474 (HTTP), 7687 (Bolt)
   - Status Check: http://localhost:7474

2. **Qdrant (Vector Store)**
   - Purpose: Ephemeral memory & embeddings
   - Port: 6333
   - Status Check: http://localhost:6333/dashboard

3. **LMStudio (LLM Server)**
   - Purpose: Local LLM inference
   - Port: 1234
   - Status Check: http://localhost:1234/v1/models

4. **FastAPI Server**
   - Purpose: Main application server
   - Port: 8000
   - Status Check: http://localhost:8000/docs

## Architecture Diagram

```
                    NIA Architecture
                    ================

+-------------+        +-----------------+
|  Interface  |  <-->  |  Nova System   |
|  (FastAPI)  |        |  (Orchestrator)|
+-------------+        +-----------------+
                              |
                              v
+------------------+  +----------------+  +-----------------+
|   Memory System  |  |  Agent System  |  |  Graph System  |
| +--------------+|  |  (Inheritance) |  | +--------------+|
| |   Episodic   ||  |  BaseAgent    |  | |     DAG      ||
| |   (Vector)   ||  |  TinyTroupe   |  | |   (Runtime)  ||
| +--------------+|  |  Specialized  |  | +--------------+|
| |   Semantic   ||  +----------------+  | |    Neo4j     ||
| |   (Neo4j)    ||                     | |  (Storage)   ||
| +--------------+|                     | +--------------+|
+------------------+                    +-----------------+
```

## Common Issues & Solutions

1. **Neo4j Connection Issues**
   ```bash
   # Restart Neo4j container
   docker compose -f scripts/docker/compose/docker-compose.yml restart neo4j
   # Check logs
   docker compose -f scripts/docker/compose/docker-compose.yml logs neo4j
   ```

2. **Qdrant Connection Issues**
   ```bash
   # Restart Qdrant container
   docker compose -f scripts/docker/compose/docker-compose.yml restart qdrant
   # Check logs
   docker compose -f scripts/docker/compose/docker-compose.yml logs qdrant
   ```

3. **LMStudio Issues**
   - Ensure model is loaded
   - Check server is running at http://localhost:1234
   - Verify API key is set to "lm-studio"

4. **FastAPI Server Issues**
   - Check all services are running
   - Verify environment variables
   - Check logs for errors

## License
MIT License - see LICENSE file for details.
