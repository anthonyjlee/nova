"""Tests for Nova's initialization protocol and self-model."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from src.nia.nova.core.self_model import NovaSelfModel
from src.nia.nova.core.initialization import NovaInitializer

@pytest.fixture
def mock_neo4j_store():
    """Create a mock Neo4j store."""
    store = MagicMock()
    # Mock session context manager
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    session.run = AsyncMock()
    store.session = MagicMock(return_value=session)
    return store

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = MagicMock()
    store.store_vector = AsyncMock(return_value="test_id")
    return store

@pytest.fixture
def self_model(mock_neo4j_store):
    """Create a NovaSelfModel instance with mock store."""
    return NovaSelfModel(mock_neo4j_store)

@pytest.fixture
def initializer(mock_neo4j_store, mock_vector_store):
    """Create a NovaInitializer instance with mock stores."""
    return NovaInitializer(mock_neo4j_store, mock_vector_store)

@pytest.mark.asyncio
async def test_self_model_initialization(self_model, mock_neo4j_store):
    """Test basic self-model initialization."""
    # Mock the data return for node_id
    mock_neo4j_store.session.return_value.__aenter__.return_value.run.return_value.data = \
        AsyncMock(return_value=[{"node_id": "test_node_id"}])
    
    await self_model.initialize()
    
    # Verify system node creation
    assert mock_neo4j_store.session.return_value.__aenter__.return_value.run.called
    
    # Verify capabilities were initialized
    calls = mock_neo4j_store.session.return_value.__aenter__.return_value.run.call_args_list
    assert any("MERGE (c:Capability" in str(call) for call in calls)
    
    # Verify domains were initialized
    assert any("MERGE (d:Domain" in str(call) for call in calls)

@pytest.mark.asyncio
async def test_domain_access_control(self_model):
    """Test domain access control functionality."""
    await self_model.grant_domain_access("TestAgent", "personal")
    await self_model.get_domain_access("TestAgent", "personal")
    await self_model.revoke_domain_access("TestAgent", "personal")
    
    # Verify all operations were called
    session = self_model.store.session.return_value.__aenter__.return_value
    assert session.run.call_count == 3

@pytest.mark.asyncio
async def test_reflection_recording(self_model):
    """Test recording reflections."""
    test_content = "Test reflection"
    test_domain = "personal"
    
    await self_model.record_reflection(test_content, test_domain)
    
    # Verify reflection was recorded
    session = self_model.store.session.return_value.__aenter__.return_value
    call_args = session.run.call_args[1]
    assert test_content in str(call_args)
    assert test_domain in str(call_args)

@pytest.mark.asyncio
async def test_complete_initialization(initializer):
    """Test the complete initialization sequence."""
    test_context = {
        "preferences": {"theme": "dark"},
        "environment": "development",
        "professional_context": "software_development"
    }
    
    await initializer.initialize(test_context)
    
    # Verify initialization completed successfully
    assert initializer.initialized
    
    # Verify all initialization steps were called
    session = initializer.neo4j_store.session.return_value.__aenter__.return_value
    calls = session.run.call_args_list
    
    # Check for key initialization steps
    assert any("SystemSelf" in str(call) for call in calls)  # Self-model initialization
    assert any("Domain" in str(call) for call in calls)      # Domain initialization
    assert any("AutoApprovalRules" in str(call) for call in calls)  # Auto-approval setup

@pytest.mark.asyncio
async def test_initialization_failure_handling(initializer):
    """Test handling of initialization failures."""
    # Make Neo4j connection fail
    initializer.neo4j_store.session.return_value.__aenter__.return_value.run.side_effect = \
        Exception("Connection failed")
    
    with pytest.raises(Exception):
        await initializer.initialize()
    
    # Verify error state was recorded
    assert not initializer.initialized
    
    # Verify error reflection was attempted
    session = initializer.neo4j_store.session.return_value.__aenter__.return_value
    error_calls = [call for call in session.run.call_args_list if "error" in str(call)]
    assert len(error_calls) > 0

@pytest.mark.asyncio
async def test_auto_approval_rules(initializer):
    """Test auto-approval rules initialization."""
    await initializer._init_auto_approval()
    
    # Verify rules were created
    session = initializer.neo4j_store.session.return_value.__aenter__.return_value
    call_args = session.run.call_args[1]
    
    # Check for required rule types
    rules = call_args.get("rules", [])
    rule_types = {rule["type"] for rule in rules}
    assert "task_creation" in rule_types
    assert "memory_access" in rule_types
    assert "agent_communication" in rule_types

@pytest.mark.asyncio
async def test_domain_initialization(initializer):
    """Test domain initialization and access control setup."""
    await initializer._init_domains()
    
    # Verify domain access was set up for all agents
    session = initializer.neo4j_store.session.return_value.__aenter__.return_value
    calls = session.run.call_args_list
    
    # Check for key agents and their domain access
    assert any("DialogueAgent" in str(call) and "personal" in str(call) for call in calls)
    assert any("ResearchAgent" in str(call) and "professional" in str(call) for call in calls)
    assert any("EmotionAgent" in str(call) and "personal" in str(call) for call in calls)

if __name__ == "__main__":
    pytest.main([__file__])
