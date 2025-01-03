"""Tests for the enhanced DialogueAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.dialogue_agent import DialogueAgent
from src.nia.nova.core.dialogue import DialogueResult

@pytest.fixture
def dialogue_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Create a DialogueAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestDialogue_{request.node.name}"
    
    # Update mock memory system for dialogue agent
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "utterances": [
            {
                "statement": "Let's discuss the project",
                "type": "initiation",
                "confidence": 0.8,
                "domain_relevance": 0.9
            }
        ],
        "context": {
            "flow_factors": [
                {
                    "factor": "topic_transition",
                    "weight": 0.8
                }
            ],
            "participants": ["agent1", "agent2"],
            "topics": ["project", "planning"]
        }
    })
    
    # Configure domain access
    mock_memory_system.semantic.store.get_domain_access = AsyncMock(
        side_effect=lambda agent, domain: domain == "professional"
    )
    
    # Create agent with updated config
    config = base_agent_config.copy()
    config["name"] = agent_name
    config["domain"] = "professional"
    
    return DialogueAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain=config["domain"]
    )

@pytest.mark.asyncio
async def test_initialization(dialogue_agent):
    """Test agent initialization with enhanced attributes."""
    assert "TestDialogue" in dialogue_agent.name
    assert dialogue_agent.domain == "professional"
    assert dialogue_agent.agent_type == "dialogue"
    
    # Verify attributes were initialized
    attributes = dialogue_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify enhanced attributes
    assert "Coordinate multi-agent interactions" in attributes["desires"]
    assert "towards_coordination" in attributes["emotions"]
    assert "interaction_coordination" in attributes["capabilities"]
    
    # Verify interaction state initialization
    assert isinstance(dialogue_agent.active_conversations, dict)
    assert isinstance(dialogue_agent.participating_agents, dict)
    assert isinstance(dialogue_agent.interaction_states, dict)
    assert isinstance(dialogue_agent.flow_controllers, dict)

@pytest.mark.asyncio
async def test_start_conversation(dialogue_agent, mock_world):
    """Test conversation initialization."""
    conversation_id = "test_conv_1"
    participants = ["agent1", "agent2"]
    metadata = {"purpose": "testing"}
    
    await dialogue_agent.start_conversation(conversation_id, participants, metadata)
    
    # Verify conversation state
    assert conversation_id in dialogue_agent.active_conversations
    assert dialogue_agent.active_conversations[conversation_id]["state"] == "active"
    assert dialogue_agent.active_conversations[conversation_id]["metadata"] == metadata
    
    # Verify participant tracking
    assert dialogue_agent.participating_agents[conversation_id] == set(participants)
    
    # Verify interaction state
    assert dialogue_agent.interaction_states[conversation_id]["turn_count"] == 0
    assert not dialogue_agent.interaction_states[conversation_id]["pending_responses"]
    
    # Verify flow controller
    assert dialogue_agent.flow_controllers[conversation_id]["current_phase"] == "initiation"
    
    # Verify coordination notification
    mock_world.notify_agent.assert_called_once()

@pytest.mark.asyncio
async def test_end_conversation(dialogue_agent, mock_memory_system):
    """Test conversation cleanup."""
    # Setup active conversation
    conversation_id = "test_conv_1"
    await dialogue_agent.start_conversation(conversation_id, ["agent1"])
    
    # End conversation
    await dialogue_agent.end_conversation(conversation_id, "test complete")
    
    # Verify cleanup
    assert conversation_id not in dialogue_agent.active_conversations
    assert conversation_id not in dialogue_agent.participating_agents
    assert conversation_id not in dialogue_agent.interaction_states
    assert conversation_id not in dialogue_agent.flow_controllers
    
    # Verify memory storage
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_update_interaction_state(dialogue_agent):
    """Test interaction state updates."""
    conversation_id = "test_conv_1"
    await dialogue_agent.start_conversation(conversation_id, ["agent1", "agent2"])
    
    content = {
        "speaker": "agent1",
        "topics": ["testing", "interaction"],
        "context": {"phase": "discussion"},
        "completes_exchange": True,
        "exchange_type": "question_answer"
    }
    
    await dialogue_agent._update_interaction_state(conversation_id, content)
    
    state = dialogue_agent.interaction_states[conversation_id]
    assert state["turn_count"] == 1
    assert state["last_speaker"] == "agent1"
    assert "testing" in state["active_topics"]
    assert len(state["context_stack"]) == 1
    assert len(state["completed_exchanges"]) == 1

@pytest.mark.asyncio
async def test_update_flow_state(dialogue_agent):
    """Test flow state updates."""
    conversation_id = "test_conv_1"
    await dialogue_agent.start_conversation(conversation_id, ["agent1"])
    
    flow_concept = {
        "suggested_phase": "discussion",
        "expected_responses": ["agent2"],
        "blocked_topics": ["off_topic"],
        "priorities": ["main_topic"],
        "needs_intervention": True,
        "intervention_reason": "topic_drift"
    }
    
    await dialogue_agent._update_flow_state(conversation_id, flow_concept)
    
    controller = dialogue_agent.flow_controllers[conversation_id]
    assert controller["current_phase"] == "discussion"
    assert "agent2" in controller["expected_responses"]
    assert "off_topic" in controller["blocked_topics"]
    assert controller["priority_queue"] == ["main_topic"]
    assert controller["intervention_needed"]

@pytest.mark.asyncio
async def test_handle_flow_intervention(dialogue_agent, mock_world):
    """Test flow intervention handling."""
    conversation_id = "test_conv_1"
    await dialogue_agent.start_conversation(conversation_id, ["agent1"])
    
    flow_concept = {
        "intervention_reason": "topic_drift",
        "suggested_action": "redirect",
        "intervention_priority": "high"
    }
    
    await dialogue_agent._handle_flow_intervention(conversation_id, flow_concept)
    
    # Verify coordination notification
    mock_world.notify_agent.assert_called_with(
        "coordination",
        {
            "type": "dialogue_event",
            "conversation_id": conversation_id,
            "event_type": "flow_intervention_needed",
            "event_data": {
                "reason": "topic_drift",
                "suggested_action": "redirect",
                "priority": "high"
            },
            "timestamp": mock_world.notify_agent.call_args[0][1]["timestamp"],
            "source_agent": dialogue_agent.name,
            "domain": "professional"
        }
    )

@pytest.mark.asyncio
async def test_record_interaction_patterns(dialogue_agent, mock_memory_system):
    """Test interaction pattern recording."""
    conversation_id = "test_conv_1"
    
    # Configure mock LLM response
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "utterances": [
            {
                "statement": "Important point",
                "confidence": 0.9,
                "type": "key_point"
            }
        ],
        "context": {
            "flow_factors": [
                {
                    "factor": "topic_focus",
                    "weight": 0.8
                }
            ]
        }
    })
    
    analysis_result = DialogueResult(
        utterances=[
            {
                "statement": "Important point",
                "confidence": 0.9,
                "type": "key_point"
            }
        ],
        confidence=0.8,
        context={
            "flow_factors": [
                {
                    "factor": "topic_focus",
                    "weight": 0.8
                }
            ]
        }
    )
    
    await dialogue_agent._record_interaction_patterns(conversation_id, analysis_result)
    
    # Verify pattern storage
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Interaction pattern recorded in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_with_interaction_updates(dialogue_agent, mock_memory_system):
    """Test content processing with interaction updates."""
    conversation_id = "test_conv_1"
    await dialogue_agent.start_conversation(conversation_id, ["agent1"])
    
    # Configure mock LLM response
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "utterances": [
            {
                "statement": "Test message",
                "type": "message",
                "confidence": 0.9,
                "domain_relevance": 0.8
            }
        ],
        "context": {
            "flow_factors": [
                {
                    "factor": "topic_focus",
                    "weight": 0.8
                }
            ],
            "participants": ["agent1"],
            "topics": ["test"]
        }
    })
    
    content = {
        "conversation_id": conversation_id,
        "speaker": "agent1",
        "content": "Test message",
        "topics": ["test"]
    }
    
    response = await dialogue_agent.process(content)
    
    # Verify state updates
    assert dialogue_agent.interaction_states[conversation_id]["turn_count"] == 1
    assert "test" in dialogue_agent.interaction_states[conversation_id]["active_topics"]
    assert "analysis_state" in dialogue_agent.emotions
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Interaction processed in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_and_store_with_patterns(dialogue_agent, mock_memory_system):
    """Test analysis with pattern recording."""
    content = {
        "conversation_id": "test_conv_1",
        "content": "Test content",
        "type": "message"
    }
    
    result = await dialogue_agent.analyze_and_store(content)
    
    # Verify analysis result
    assert isinstance(result, DialogueResult)
    assert len(result.utterances) > 0
    
    # Verify memory storage
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_error_handling(dialogue_agent, mock_memory_system):
    """Test error handling during processing."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await dialogue_agent.analyze_and_store({"content": "test"})
    
    # Verify error handling
    assert isinstance(result, DialogueResult)
    assert result.confidence == 0.0
    assert len(result.utterances) == 0
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_validation(dialogue_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await dialogue_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await dialogue_agent.validate_domain_access("restricted")

if __name__ == "__main__":
    pytest.main([__file__])
