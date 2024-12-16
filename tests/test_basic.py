import pytest
from nia.memory.agents.meta_agent import MetaAgent
from nia.memory.agents.belief_agent import BeliefAgent
from nia.memory.agents.reflection_agent import ReflectionAgent
from nia.memory.agents.research_agent import ResearchAgent

def test_imports():
    """Test that core components can be imported."""
    assert MetaAgent
    assert BeliefAgent
    assert ReflectionAgent
    assert ResearchAgent

def test_meta_agent_creation():
    """Test that a MetaAgent can be instantiated."""
    agent = MetaAgent()
    assert agent is not None
