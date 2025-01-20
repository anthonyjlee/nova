"""Core type definitions for NIA."""

from .memory_types import (
    Memory,
    MemoryType,
    EpisodicMemory,
    ValidationSchema,
    CrossDomainSchema,
)

from .domain_types import (
    KnowledgeVertical,
    BaseDomain,
    DomainContext,
    DomainTransfer,
)

from .agent_types import (
    AgentResponse,
    DialogueMessage,
    DialogueContext,
    SemanticMemory,
    ProceduralMemory,
    Concept,
    Relationship,
    Belief,
    TaskState,
    MemoryQuery,
    ConsolidationRule,
    MemoryBatch,
    MockMemory,
)

__all__ = [
    # Memory types
    'Memory',
    'MemoryType',
    'EpisodicMemory',
    'ValidationSchema',
    'CrossDomainSchema',
    
    # Domain types
    'KnowledgeVertical',
    'BaseDomain',
    'DomainContext',
    'DomainTransfer',
    
    # Agent types
    'AgentResponse',
    'DialogueMessage',
    'DialogueContext',
    'SemanticMemory',
    'ProceduralMemory',
    'Concept',
    'Relationship',
    'Belief',
    'TaskState',
    'MemoryQuery',
    'ConsolidationRule',
    'MemoryBatch',
    'MockMemory',
]
