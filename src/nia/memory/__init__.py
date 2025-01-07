"""Memory system initialization."""

# Import all types from memory_types
from ..core.types.memory_types import (
    AgentResponse,
    DialogueMessage,
    DialogueContext,
    Memory,
    EpisodicMemory,
    SemanticMemory,
    ProceduralMemory,
    Concept,
    Relationship,
    Belief,
    MemoryType,
    MemoryQuery,
    ConsolidationRule,
    MemoryBatch
)

# Import core memory components
from .two_layer import TwoLayerMemorySystem
from .consolidation import ConsolidationManager
from ..core.vector.embeddings import EmbeddingService

# Import stores
from ..core.neo4j.neo4j_store import Neo4jMemoryStore
from ..core.vector.vector_store import VectorStore

__all__ = [
    # Memory types
    'AgentResponse',
    'DialogueMessage',
    'DialogueContext',
    'Memory',
    'EpisodicMemory',
    'SemanticMemory',
    'ProceduralMemory',
    'Concept',
    'Relationship',
    'Belief',
    'MemoryType',
    'MemoryQuery',
    'ConsolidationRule',
    'MemoryBatch',
    
    # Core components
    'TwoLayerMemorySystem',
    'ConsolidationManager',
    'EmbeddingService',
    
    # Stores
    'Neo4jMemoryStore',
    'VectorStore'
]
