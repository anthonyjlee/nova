"""Basic tests for system functionality."""

import pytest
from nia.nova.core.meta import MetaAgent
from nia.memory.llm_interface import LLMInterface
from nia.memory.neo4j.neo4j_store import Neo4jMemoryStore
from nia.memory.vector.vector_store import VectorStore
from nia.memory.vector.embeddings import EmbeddingService

def test_imports():
    """Test that core modules can be imported."""
    from nia.memory.types import memory_types
    from nia.memory import memory_integration
    from nia.memory import llm_interface
    from nia.memory.vector import vector_store
    from nia.memory.neo4j import neo4j_store
    from nia.nova.core import meta
    from nia.agents.specialized import belief_agent
    from nia.agents.specialized import emotion_agent
    from nia.agents.specialized import reflection_agent

def test_meta_agent_creation():
    """Test that a MetaAgent can be instantiated."""
    llm = LLMInterface()
    embedding_service = EmbeddingService()
    vector_store = VectorStore(embedding_service)
    store = Neo4jMemoryStore()
    from nia.agents.specialized.belief_agent import BeliefAgent
    from nia.agents.specialized.desire_agent import DesireAgent
    from nia.agents.specialized.emotion_agent import EmotionAgent
    from nia.agents.specialized.reflection_agent import ReflectionAgent
    from nia.agents.specialized.research_agent import ResearchAgent
    from nia.nova.tasks.planner import TaskPlannerAgent

    # Create sub-agents
    agents = {
        'belief': BeliefAgent(llm, store, vector_store),
        'desire': DesireAgent(llm, store, vector_store),
        'emotion': EmotionAgent(llm, store, vector_store),
        'reflection': ReflectionAgent(llm, store, vector_store),
        'research': ResearchAgent(llm, store, vector_store),
        'task_planner': TaskPlannerAgent(llm, store, vector_store)
    }
    
    agent = MetaAgent(llm, store, vector_store, agents)
    assert agent is not None
    assert agent.llm is not None
    assert agent.store is not None
    assert agent.vector_store is not None
