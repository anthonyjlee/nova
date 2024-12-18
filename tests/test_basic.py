"""Basic tests for system functionality."""

import pytest
from nia.memory.agents.meta_agent import MetaAgent
from nia.memory.llm_interface import LLMInterface
from nia.memory.neo4j_store import Neo4jMemoryStore
from nia.memory.vector_store import VectorStore
from nia.memory.embeddings import EmbeddingService

def test_imports():
    """Test that core modules can be imported."""
    from nia.memory import memory_types
    from nia.memory import memory_integration
    from nia.memory import llm_interface
    from nia.memory import vector_store
    from nia.memory import neo4j_store
    from nia.memory.agents import meta_agent
    from nia.memory.agents import belief_agent
    from nia.memory.agents import emotion_agent
    from nia.memory.agents import reflection_agent

def test_meta_agent_creation():
    """Test that a MetaAgent can be instantiated."""
    llm = LLMInterface()
    embedding_service = EmbeddingService()
    vector_store = VectorStore(embedding_service)
    store = Neo4jMemoryStore()
    agent = MetaAgent(llm, store, vector_store)
    assert agent is not None
    assert agent.llm is not None
    assert agent.store is not None
    assert agent.vector_store is not None
