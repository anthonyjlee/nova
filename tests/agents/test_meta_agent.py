"""Tests for the specialized MetaAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.meta_agent import MetaAgent
from src.nia.nova.core.meta import MetaResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "response": "Synthesized response",
        "concepts": [
            {
                "name": "TestConcept",
                "type": "synthesis_quality",
                "description": "excellent",
                "confidence": 0.9
            },
            {
                "name": "DomainConcept",
                "type": "domain_complexity",
                "description": "moderate",
                "confidence": 0.7
            },
            {
                "name": "SwarmConcept",
                "type": "swarm_architecture",
                "description": "hierarchical",
                "confidence": 0.8
            }
        ],
        "key_points": ["Test point"],
        "swarm_operations": {
            "architecture": "hierarchical",
            "type": "MajorityVoting",
            "status": "active"
        }
    })
    
    # Mock semantic store
    memory.semantic = MagicMock()
    memory.semantic.store = MagicMock()
    memory.semantic.store.record_reflection = AsyncMock()
    memory.semantic.store.get_domain_access = AsyncMock(return_value=True)
    
    # Mock episodic store
    memory.episodic = MagicMock()
    memory.episodic.store = MagicMock()
    
    return memory

@pytest.fixture
def mock_world():
    """Create a mock world environment."""
    return MagicMock()

@pytest.fixture
def mock_agent():
    """Create a mock specialized agent."""
    agent = MagicMock()
    agent.process = AsyncMock(return_value=MagicMock(
        concepts=[{"name": "AgentConcept", "type": "test"}],
        key_points=["Agent key point"],
        confidence=0.7,
        metadata={
            "swarm_operations": {
                "architecture": "hierarchical",
                "role": "worker",
                "status": "active"
            }
        }
    ))
    agent.get_domain_access = AsyncMock(return_value=True)
    agent.get_attributes = MagicMock(return_value={
        "capabilities": {
            "swarm": {
                "architectures": ["hierarchical", "parallel"],
                "types": ["MajorityVoting", "RoundRobin"]
            }
        }
    })
    return agent

@pytest.fixture
def meta_agent(mock_memory_system, mock_world, request):
    """Create a MetaAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestMeta_{request.node.name}"
    return MetaAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        agents={"test_agent": mock_agent()},
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(meta_agent):
    """Test agent initialization."""
    assert "TestMeta" in meta_agent.name
    assert meta_agent.domain == "professional"
    assert meta_agent.agent_type == "meta"
    
    # Verify attributes were initialized
    attributes = meta_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify domain-specific attributes
    assert "Respect domain boundaries" in attributes["desires"]
    assert "towards_domains" in attributes["emotions"]
    assert "domain_management" in attributes["capabilities"]
    
    # Verify swarm capabilities
    assert "swarm" in attributes["capabilities"]
    assert "architectures" in attributes["capabilities"]["swarm"]
    assert "hierarchical" in attributes["capabilities"]["swarm"]["architectures"]
    assert "types" in attributes["capabilities"]["swarm"]
    assert "MajorityVoting" in attributes["capabilities"]["swarm"]["types"]

@pytest.mark.asyncio
async def test_swarm_decision_making(meta_agent, mock_memory_system):
    """Test swarm-based decision making."""
    content = {
        "text": "Test content",
        "swarm": {
            "type": "MajorityVoting",
            "votes": [
                {"agent": "agent1", "vote": "approve", "confidence": 0.8},
                {"agent": "agent2", "vote": "approve", "confidence": 0.9},
                {"agent": "agent3", "vote": "reject", "confidence": 0.4}
            ]
        }
    }
    
    result = await meta_agent.process_swarm_decision(content)
    
    # Verify decision
    assert result["decision"] == "approve"
    assert result["confidence"] > 0.8  # High confidence from majority
    assert "voting_summary" in result
    assert len(result["voting_summary"]) == 3

@pytest.mark.asyncio
async def test_swarm_strategy_adaptation(meta_agent):
    """Test swarm strategy adaptation."""
    # Test strategy selection
    strategy = await meta_agent.select_swarm_strategy({
        "task_complexity": "high",
        "agent_count": 5,
        "resource_constraints": "medium"
    })
    
    # Verify strategy selection
    assert strategy["architecture"] in ["hierarchical", "parallel", "mesh"]
    assert strategy["type"] in ["MajorityVoting", "RoundRobin", "GraphWorkflow"]
    assert "communication_pattern" in strategy
    
    # Test strategy adaptation
    adapted = await meta_agent.adapt_swarm_strategy(
        strategy,
        {"performance": 0.6, "bottlenecks": ["communication"]}
    )
    
    # Verify adaptation
    assert adapted["architecture"] != strategy["architecture"]
    assert "adaptation_reason" in adapted
    assert "previous_strategy" in adapted

@pytest.mark.asyncio
async def test_process_content(meta_agent, mock_memory_system):
    """Test content processing with domain and swarm awareness."""
    content = {
        "text": "Test content",
        "swarm": {
            "architecture": "hierarchical",
            "type": "MajorityVoting"
        }
    }
    metadata = {"source": "test"}
    
    response = await meta_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "synthesis_state" in meta_agent.emotions
    assert "domain_state" in meta_agent.emotions
    
    # Verify swarm operation tracking
    assert "swarm_operations" in response.metadata
    assert response.metadata["swarm_operations"]["architecture"] == "hierarchical"

@pytest.mark.asyncio
async def test_orchestrate_and_store(meta_agent, mock_memory_system):
    """Test orchestration with domain and swarm awareness."""
    content = {
        "content": "Test content",
        "metadata": {"source": "test"},
        "swarm": {
            "architecture": "hierarchical",
            "type": "MajorityVoting"
        }
    }
    
    result = await meta_agent.orchestrate_and_store(
        content,
        dialogue_context={"turn": 1},
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, MetaResult)
    assert result.response == "Synthesized response"
    assert len(result.concepts) > 0
    assert len(result.key_points) > 0
    
    # Verify memory storage
    assert hasattr(meta_agent, "store_memory")
    
    # Verify swarm operations
    assert "swarm_operations" in result.metadata
    assert result.metadata["swarm_operations"]["type"] == "MajorityVoting"
    
    # Verify reflection was recorded (high confidence case)
    if result.confidence > 0.8:
        mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(meta_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await meta_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await meta_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_orchestrate_with_different_domains(meta_agent):
    """Test orchestration with different domain configurations."""
    content = {
        "content": "Test content",
        "swarm": {
            "architecture": "hierarchical",
            "type": "MajorityVoting"
        }
    }
    
    # Test professional domain
    prof_result = await meta_agent.orchestrate_and_store(
        content,
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    assert prof_result.metadata["swarm_operations"]["architecture"] == "hierarchical"
    
    # Test personal domain (assuming access)
    pers_result = await meta_agent.orchestrate_and_store(
        content,
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"
    assert pers_result.metadata["swarm_operations"]["architecture"] == "hierarchical"

@pytest.mark.asyncio
async def test_error_handling(meta_agent, mock_memory_system):
    """Test error handling during orchestration."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await meta_agent.orchestrate_and_store({
        "content": "Test content",
        "swarm": {
            "architecture": "hierarchical",
            "type": "MajorityVoting"
        }
    })
    
    # Verify error handling
    assert isinstance(result, MetaResult)
    assert result.confidence == 0.0
    assert "error" in result.metadata
    
    # Verify swarm error handling
    assert "swarm_operations" in result.metadata
    assert result.metadata["swarm_operations"]["status"] == "error"

@pytest.mark.asyncio
async def test_reflection_recording(meta_agent, mock_memory_system):
    """Test reflection recording with domain and swarm awareness."""
    content = {
        "content": "Test content",
        "swarm": {
            "architecture": "hierarchical",
            "type": "MajorityVoting"
        }
    }
    
    # Force high confidence result
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.9
    
    result = await meta_agent.orchestrate_and_store(content)
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test low confidence case
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.2
    
    result = await meta_agent.orchestrate_and_store(content)
    
    # Verify low confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Low confidence" in str(call) for call in reflection_calls)
    
    # Verify swarm reflections
    assert any("swarm architecture" in str(call).lower() for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(meta_agent):
    """Test emotion updates based on synthesis, domain complexity, and swarm state."""
    content = {
        "content": "Test content",
        "swarm": {
            "architecture": "hierarchical",
            "type": "MajorityVoting",
            "status": "active"
        }
    }
    
    await meta_agent.process(content)
    
    # Verify emotion updates
    assert meta_agent.emotions["synthesis_state"] == "excellent"
    assert meta_agent.emotions["domain_state"] == "moderate"
    assert meta_agent.emotions["swarm_state"] == "active"

if __name__ == "__main__":
    pytest.main([__file__])
