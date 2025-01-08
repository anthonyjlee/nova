"""Basic import test for TinyTroupe integration."""

import pytest
from nia.agents.tinytroupe_agent import TinyTroupeAgent
from nia.agents.base import BaseAgent

def test_tinytroupe_imports():
    """Test that TinyTroupe components can be imported."""
    # Verify TinyTroupe agent can be imported and is a subclass of BaseAgent
    assert issubclass(TinyTroupeAgent, BaseAgent)
    
    # Verify basic attributes are defined
    assert hasattr(TinyTroupeAgent, "store_memory")
    assert hasattr(TinyTroupeAgent, "recall_memories")
    assert hasattr(TinyTroupeAgent, "process")
    assert hasattr(TinyTroupeAgent, "reflect")
