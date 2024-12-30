# Cleanup Plan

## Overview

This cleanup plan aligns with our implementation plan to ensure consistent code organization and proper reuse of existing components.

## Directory Structure Cleanup

### Current Structure
```
src/nia/
├── memory/
│   ├── agents/          # To be moved
│   ├── consolidation.py
│   ├── embeddings.py
│   ├── two_layer.py
│   └── vector_store.py
└── ui/                  # To be reorganized
```

### Target Structure (Aligned with Implementation Plan)
```
src/nia/
├── nova/                 # Nova's core capabilities
│   ├── core/            # Core processing modules
│   │   ├── parsing.py   # From ParsingAgent
│   │   ├── meta.py      # From MetaAgent
│   │   ├── structure.py # From StructureAgent
│   │   ├── context.py   # From ContextAgent
│   │   └── processor.py # From ResponseProcessor
│   ├── tasks/           # Task management
│   │   ├── planner.py   # From TaskPlannerAgent
│   │   └── context.py   # From ContextBuilder
│   └── orchestrator.py  # Main Nova class
├── agents/              # Agent implementations
│   ├── specialized/     # TinyTroupe-integrated agents
│   │   ├── dialogue_agent.py
│   │   ├── emotion_agent.py
│   │   ├── belief_agent.py
│   │   ├── research_agent.py
│   │   ├── reflection_agent.py
│   │   ├── desire_agent.py
│   │   └── task_agent.py
│   ├── base.py         # Base agent implementation
│   ├── tinytroupe_agent.py
│   ├── skills_agent.py
│   ├── coordination_agent.py
│   └── factory.py
├── memory/             # Memory system
│   ├── neo4j/          # Neo4j integration
│   ├── vector/         # Vector store management
│   ├── types/          # Memory type definitions
│   ├── consolidation.py
│   ├── embeddings.py
│   └── two_layer.py
└── ui/                 # User interface
    ├── components/     # UI building blocks
    ├── handlers/       # Event handlers
    ├── visualization/  # Agent visualization
    └── state.py       # UI state management
```

## File Movement Plan

1. Core Agent Migration:
```bash
# Create nova directory structure
mkdir -p src/nia/nova/{core,tasks}

# Move core agent functionality
mv src/nia/memory/agents/parsing_agent.py src/nia/nova/core/parsing.py
mv src/nia/memory/agents/meta_agent.py src/nia/nova/core/meta.py
mv src/nia/memory/agents/structure_agent.py src/nia/nova/core/structure.py
mv src/nia/memory/agents/context_agent.py src/nia/nova/core/context.py
mv src/nia/memory/agents/response_processor.py src/nia/nova/core/processor.py

# Move task management
mv src/nia/memory/agents/task_planner_agent.py src/nia/nova/tasks/planner.py
mv src/nia/memory/agents/context_builder.py src/nia/nova/tasks/context.py
```

2. Specialized Agent Organization:
```bash
# Create specialized agents directory
mkdir -p src/nia/agents/specialized

# Move specialized agents
mv src/nia/memory/agents/dialogue_agent.py src/nia/agents/specialized/
mv src/nia/memory/agents/emotion_agent.py src/nia/agents/specialized/
mv src/nia/memory/agents/belief_agent.py src/nia/agents/specialized/
mv src/nia/memory/agents/research_agent.py src/nia/agents/specialized/
mv src/nia/memory/agents/reflection_agent.py src/nia/agents/specialized/
mv src/nia/memory/agents/desire_agent.py src/nia/agents/specialized/
mv src/nia/memory/agents/task_agent.py src/nia/agents/specialized/
```

3. Memory System Organization:
```bash
# Create memory system directories
mkdir -p src/nia/memory/{neo4j,vector,types}

# Move memory components
mv src/nia/memory/memory_types.py src/nia/memory/types/
mv src/nia/memory/neo4j_store.py src/nia/memory/neo4j/
mv src/nia/memory/vector_store.py src/nia/memory/vector/
```

4. UI Reorganization:
```bash
# Create UI directories
mkdir -p src/nia/ui/{components,handlers,visualization}

# Move UI components
mv src/nia/ui/base.py src/nia/ui/components/
mv src/nia/ui/chat.py src/nia/ui/components/
mv src/nia/ui/graph.py src/nia/ui/components/
mv src/nia/ui/handlers.py src/nia/ui/handlers/
mv src/nia/ui/message_handlers.py src/nia/ui/handlers/
```

## Code Updates Required

1. Update Import Statements:
   - Update all imports to reflect new file locations
   - Use absolute imports for clarity
   - Example:
```python
# Old import
from ..agents.parsing_agent import ParsingAgent

# New import
from nia.nova.core.parsing import NovaParser
```

2. Update Class References:
   - Update class names to reflect new roles
   - Maintain inheritance structure
   - Example:
```python
# Old implementation
class ParsingAgent(BaseAgent):
    ...

# New implementation
class NovaParser:
    """Core parsing functionality from ParsingAgent."""
    def __init__(self):
        self.schema_validator = self.load_existing_schema_validator()
        self.orson_parser = self.initialize_orson_parser()
```

## Memory System Preservation

1. Maintain Existing Functionality:
   - Keep TwoLayerMemorySystem implementation
   - Preserve ConsolidationManager
   - Maintain current memory patterns
   - Example:
```python
# This stays in src/nia/memory/two_layer.py
class TwoLayerMemorySystem:
    """Implements episodic and semantic memory layers."""
    def __init__(self, neo4j_store, vector_store):
        self.episodic = EpisodicLayer(vector_store)
        self.semantic = SemanticLayer(neo4j_store)
```

2. Add TinyTroupe Integration:
   - Add TinyTroupe-specific patterns
   - Maintain backward compatibility
   - Example:
```python
# Add to consolidation.py
class TinyTroupePattern(ConsolidationPattern):
    """Pattern for extracting TinyTroupe-specific knowledge."""
    def __init__(self):
        super().__init__("tinytroupe", threshold=0.7)
```

## Testing Strategy

1. Pre-Cleanup Tests:
   - Run current test suite
   - Document baseline performance
   - Capture current behavior

2. During Cleanup:
   - Test each file movement
   - Verify import updates
   - Check class functionality

3. Post-Cleanup Tests:
   - Run full test suite
   - Compare with baseline
   - Verify no regressions

## Success Criteria

1. Code Organization:
   - Clean directory structure
   - Logical file placement
   - Clear component boundaries

2. Functionality:
   - All tests passing
   - No broken imports
   - Maintained features

3. Documentation:
   - Updated import examples
   - Clear file structure
   - Maintained docstrings

## Next Steps

1. Execute file movements
2. Update import statements
3. Run tests
4. Update documentation
5. Verify functionality
6. Commit changes

## Notes

- Keep backup of original files
- Test each step
- Document all changes
- Maintain test coverage
