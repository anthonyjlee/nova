"""Tests for TinyTroupe agent initialization."""

import pytest
from nia.agents.tinytroupe_agent import TinyTroupeAgent

@pytest.mark.asyncio
async def test_tinytroupe_agent_initialization():
    """Test TinyTroupe agent initialization."""
    agent = TinyTroupeAgent(
        name="test_agent",
        attributes={
            "occupation": "Tester",
            "desires": ["Run tests"],
            "emotions": {"baseline": "focused"}
        }
    )
    
    # Verify TinyTroupe attributes
    assert agent.name == "test_agent"
    assert agent.occupation == "Tester"
    assert "Run tests" in agent.desires
    assert agent.emotions["baseline"] == "focused"
    
    # Verify memory system attributes
    assert agent.agent_type == "base"
    assert hasattr(agent, "store_memory")
    assert hasattr(agent, "recall_memories")
