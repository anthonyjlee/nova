"""Tests for Nova's orchestration functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.orchestration import OrchestrationAgent, OrchestrationResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "orchestration": {
            "type": "sequential",
            "agents": {
                "main": {
                    "type": "processor",
                    "priority": 0.8,
                    "description": "Main agent",
                    "flows": ["flow1", "flow2"]
                },
                "sub": {
                    "type": "helper",
                    "priority": 0.6,
                    "metadata": {
                        "key": "value"
                    }
                }
            },
            "flows": {
                "primary": ["flow1"],
                "secondary": ["flow2"]
            },
            "metadata": {
                "version": "1.0"
            }
        },
        "decisions": [
            {
                "type": "flow",
                "description": "Flow analysis",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "flows": ["flow1"]
            }
        ],
        "issues": [
            {
                "type": "missing_flow",
                "severity": "medium",
                "description": "Missing flow",
                "domain_impact": 0.3,
                "suggested_fix": "Add flow",
                "related_flows": ["flow3"]
            }
        ]
    })
    return llm

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = MagicMock()
    store.search = AsyncMock(return_value=[
        {
            "content": {"content": "Similar orchestration"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def orchestration_agent(mock_llm, mock_vector_store):
    """Create an OrchestrationAgent instance with mock dependencies."""
    return OrchestrationAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_orchestrate_agents_with_llm(orchestration_agent, mock_llm):
    """Test agent orchestration using LLM."""
    content = {
        "content": "Test content",
        "type": "sequential",
        "metadata": {"key": "value"}
    }
    
    result = await orchestration_agent.orchestrate_agents(content, "sequential")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, OrchestrationResult), "Result should be an OrchestrationResult instance"
    
    # Verify orchestration details
    assert isinstance(result.orchestration, dict), "Orchestration should be a dictionary"
    assert result.orchestration["type"] == "sequential", "Orchestration type should be sequential"
    assert len(result.orchestration["agents"]) >= 2, "Should have at least two orchestration agents"
    
    # Verify decisions
    assert isinstance(result.decisions, list), "Decisions should be a list"
    assert len(result.decisions) >= 1, "Should have at least one decision"
    
    # Verify issues
    assert isinstance(result.issues, list), "Issues should be a list"
    assert len(result.issues) >= 1, "Should have at least one issue"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify metadata
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "domain" in result.metadata and result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional'"

@pytest.mark.asyncio
async def test_orchestrate_agents_without_llm():
    """Test agent orchestration without LLM (fallback mode)."""
    agent = OrchestrationAgent()  # No LLM provided
    content = {
        "order": ["agent1"],
        "dependencies": {"agent1": []},
        "transitions": {}
    }
    
    result = await agent.orchestrate_agents(content, "sequential")
    
    # Verify basic orchestration worked
    assert isinstance(result, OrchestrationResult), "Result should be an OrchestrationResult instance"
    
    # Verify orchestration details
    assert isinstance(result.orchestration, dict), "Orchestration should be a dictionary"
    assert result.orchestration["type"] == "sequential", "Orchestration type should be sequential"
    assert "agents" in result.orchestration, "Orchestration should contain agents"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify validity
    assert result.is_valid is True, "Result should be valid with basic content"
    
    # Verify no LLM-specific fields
    assert not any(d.get("domain_relevance") for d in result.decisions), \
        "Decisions should not have LLM-specific fields"

@pytest.mark.asyncio
async def test_get_similar_orchestrations(orchestration_agent, mock_vector_store):
    """Test similar orchestration retrieval."""
    content = {"content": "test content"}
    orchestration_type = "sequential"
    
    orchestrations = await orchestration_agent._get_similar_orchestrations(content, orchestration_type)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "orchestration",
            "orchestration_type": "sequential"
        }
    )
    
    # Verify we got orchestrations back
    assert isinstance(orchestrations, list), "Should return a list of orchestrations"
    assert len(orchestrations) >= 1, "Should have at least one similar orchestration"
    
    # Verify orchestration item structure
    orchestration_item = orchestrations[0]
    assert isinstance(orchestration_item, dict), "Each orchestration item should be a dictionary"
    assert "content" in orchestration_item, "Each orchestration item should have content"
    assert "similarity" in orchestration_item, "Each orchestration item should have similarity score"
    assert isinstance(orchestration_item["similarity"], (int, float)), \
        "Similarity should be numeric"
    assert 0 <= orchestration_item["similarity"] <= 1, \
        "Similarity should be between 0 and 1"

def test_basic_orchestration_sequential(orchestration_agent):
    """Test basic sequential orchestration."""
    content = {
        "order": ["agent1"],
        "dependencies": {"agent1": []},
        "transitions": {}
    }
    
    result = orchestration_agent._basic_orchestration(content, "sequential", [])
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "orchestration" in result, "Result should contain orchestration"
    assert "decisions" in result, "Result should contain decisions"
    assert "issues" in result, "Result should contain issues"
    
    # Verify orchestration details
    assert isinstance(result["orchestration"], dict), "Orchestration should be a dictionary"
    assert result["orchestration"]["type"] == "sequential", "Orchestration type should be sequential"
    
    # Verify decisions
    assert isinstance(result["decisions"], list), "Decisions should be a list"
    assert len(result["decisions"]) >= 1, "Should have at least one decision"
    assert all(d["type"] in ["has_order", "has_dependencies", "has_transitions"] for d in result["decisions"]), \
        "Each decision should have a valid sequential type"
    
    # Verify issues
    assert isinstance(result["issues"], list), "Issues should be a list"

def test_basic_orchestration_parallel(orchestration_agent):
    """Test basic parallel orchestration."""
    content = {
        "groups": ["group1"],
        "coordination": {"group1": []},
        "synchronization": {}
    }
    
    result = orchestration_agent._basic_orchestration(content, "parallel", [])
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "orchestration" in result, "Result should contain orchestration"
    assert "decisions" in result, "Result should contain decisions"
    assert "issues" in result, "Result should contain issues"
    
    # Verify orchestration details
    assert isinstance(result["orchestration"], dict), "Orchestration should be a dictionary"
    assert result["orchestration"]["type"] == "parallel", "Orchestration type should be parallel"
    
    # Verify decisions
    assert isinstance(result["decisions"], list), "Decisions should be a list"
    assert len(result["decisions"]) >= 1, "Should have at least one decision"
    assert all(d["type"] in ["has_groups", "has_coordination", "has_synchronization"] for d in result["decisions"]), \
        "Each decision should have a valid parallel type"
    
    # Verify issues
    assert isinstance(result["issues"], list), "Issues should be a list"

def test_check_rule(orchestration_agent):
    """Test orchestration rule checking."""
    content = {
        "order": ["agent1"],
        "dependencies": {"agent1": []},
        "transitions": {},
        "groups": ["group1"],
        "coordination": {"group1": []},
        "synchronization": {},
        "conditions": {"agent1": []},
        "fallbacks": {"agent1": []},
        "adaptations": {}
    }
    
    # Test sequential rules
    assert orchestration_agent._check_rule("has_order", content) is True, \
        "Should validate order rule"
    assert orchestration_agent._check_rule("has_dependencies", content) is True, \
        "Should validate dependencies rule"
    assert orchestration_agent._check_rule("has_transitions", content) is True, \
        "Should validate transitions rule"
    
    # Test parallel rules
    assert orchestration_agent._check_rule("has_groups", content) is True, \
        "Should validate groups rule"
    assert orchestration_agent._check_rule("has_coordination", content) is True, \
        "Should validate coordination rule"
    assert orchestration_agent._check_rule("has_synchronization", content) is True, \
        "Should validate synchronization rule"
    
    # Test adaptive rules
    assert orchestration_agent._check_rule("has_conditions", content) is True, \
        "Should validate conditions rule"
    assert orchestration_agent._check_rule("has_fallbacks", content) is True, \
        "Should validate fallbacks rule"
    assert orchestration_agent._check_rule("has_adaptations", content) is True, \
        "Should validate adaptations rule"
    
    # Test invalid rule
    assert orchestration_agent._check_rule("invalid_rule", content) is False, \
        "Should return False for invalid rules"

def test_extract_orchestration(orchestration_agent):
    """Test orchestration extraction and validation."""
    orchestration = {
        "orchestration": {
            "type": "sequential",
            "agents": {
                "main": {
                    "type": "processor",
                    "priority": 0.8,
                    "description": "Main agent"
                },
                "sub": {
                    "type": "helper",
                    "priority": 0.6
                }
            },
            "flows": {
                "primary": ["flow1"]
            },
            "metadata": {
                "version": "1.0"
            }
        }
    }
    
    result = orchestration_agent._extract_orchestration(orchestration)
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "type" in result, "Result should contain type"
    assert result["type"] == "sequential", "Type should be sequential"
    
    # Verify agents
    assert "agents" in result, "Result should contain agents"
    assert isinstance(result["agents"], dict), "Agents should be a dictionary"
    assert len(result["agents"]) >= 2, "Should have at least two agents"
    
    # Verify main agent details
    main_agent = result["agents"]["main"]
    assert isinstance(main_agent, dict), "Main agent should be a dictionary"
    assert main_agent["type"] == "processor", "Main agent should be a processor"
    assert isinstance(main_agent["priority"], (int, float)), "Priority should be numeric"
    assert 0 <= main_agent["priority"] <= 1, "Priority should be between 0 and 1"
    assert "description" in main_agent, "Main agent should have a description"
    
    # Verify flows and metadata
    assert "flows" in result, "Result should contain flows"
    assert isinstance(result["flows"], dict), "Flows should be a dictionary"
    assert "metadata" in result, "Result should contain metadata"
    assert isinstance(result["metadata"], dict), "Metadata should be a dictionary"

def test_extract_decisions(orchestration_agent):
    """Test decision extraction and validation."""
    orchestration = {
        "decisions": [
            {
                "type": "flow",
                "description": "Test decision",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "flows": ["flow1"]
            },
            {
                "type": "basic",
                "description": "Basic decision",
                "confidence": 0.6
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    decisions = orchestration_agent._extract_decisions(orchestration)
    
    # Verify we got valid decisions (filtering out invalid ones)
    assert isinstance(decisions, list), "Should return a list of decisions"
    assert len(decisions) >= 2, "Should have at least two valid decisions"
    
    # Verify each decision has required fields
    for decision in decisions:
        assert isinstance(decision, dict), "Each decision should be a dictionary"
        assert "type" in decision, "Each decision should have a type"
        assert "description" in decision, "Each decision should have a description"
        assert "confidence" in decision, "Each decision should have a confidence score"
        assert isinstance(decision["confidence"], (int, float)), \
            "Confidence should be numeric"
        assert 0 <= decision["confidence"] <= 1, \
            "Confidence should be between 0 and 1"
    
    # Verify at least one decision has extended fields
    assert any("domain_relevance" in d for d in decisions), \
        "At least one decision should have domain relevance"
    assert any("importance" in d for d in decisions), \
        "At least one decision should have importance"
    assert any("flows" in d for d in decisions), \
        "At least one decision should have flows"

def test_extract_issues(orchestration_agent):
    """Test issue extraction and validation."""
    orchestration = {
        "issues": [
            {
                "type": "missing_flow",
                "severity": "high",
                "description": "Missing flow",
                "details": "Details",
                "domain_impact": 0.8,
                "suggested_fix": "Add flow",
                "related_flows": ["flow1"]
            },
            {
                "type": "basic_issue",
                "description": "Basic"
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    issues = orchestration_agent._extract_issues(orchestration)
    
    # Verify we got valid issues (filtering out invalid ones)
    assert isinstance(issues, list), "Should return a list of issues"
    assert len(issues) >= 2, "Should have at least two valid issues"
    
    # Verify each issue has required fields
    for issue in issues:
        assert isinstance(issue, dict), "Each issue should be a dictionary"
        assert "type" in issue, "Each issue should have a type"
        assert "severity" in issue, "Each issue should have a severity"
        assert "description" in issue, "Each issue should have a description"
    
    # Verify at least one issue has extended fields
    assert any("domain_impact" in i for i in issues), \
        "At least one issue should have domain impact"
    assert any("details" in i for i in issues), \
        "At least one issue should have details"
    assert any("suggested_fix" in i for i in issues), \
        "At least one issue should have a suggested fix"
    assert any("related_flows" in i for i in issues), \
        "At least one issue should have related flows"

def test_calculate_confidence(orchestration_agent):
    """Test confidence calculation."""
    orchestration = {
        "agents": {
            "main": {"type": "processor"},
            "sub": {"type": "helper"}
        },
        "flows": {
            "primary": ["flow1"],
            "secondary": ["flow2"]
        }
    }
    
    decisions = [
        {
            "confidence": 0.8,
            "importance": 0.7
        },
        {
            "confidence": 0.6,
            "importance": 0.5
        }
    ]
    
    issues = [
        {
            "severity": "low",
            "type": "minor"
        },
        {
            "severity": "medium",
            "type": "warning"
        }
    ]
    
    confidence = orchestration_agent._calculate_confidence(orchestration, decisions, issues)
    
    # Verify confidence is a valid number
    assert isinstance(confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify confidence calculation is reasonable
    # Given high confidence decisions (0.8, 0.6) and a structured orchestration,
    # confidence should be above threshold
    assert confidence >= 0.5, f"Confidence {confidence} should be >= 0.5 given strong input values"
    
    # Test with empty inputs
    empty_confidence = orchestration_agent._calculate_confidence({}, [], [])
    assert isinstance(empty_confidence, (int, float)), "Empty confidence should be numeric"
    assert 0 <= empty_confidence <= 1, "Empty confidence should be between 0 and 1"
    assert empty_confidence < confidence, \
        "Empty input should result in lower confidence than valid input"
    
    # Test with partial inputs
    partial_confidence = orchestration_agent._calculate_confidence(orchestration, [], [])
    assert isinstance(partial_confidence, (int, float)), "Partial confidence should be numeric"
    assert 0 <= partial_confidence <= 1, "Partial confidence should be between 0 and 1"
    assert partial_confidence < confidence, \
        "Partial input should result in lower confidence than full input"

def test_determine_validity(orchestration_agent):
    """Test validity determination."""
    orchestration = {
        "agents": {
            "main": {"type": "processor"}
        },
        "flows": {
            "primary": ["flow1"]
        }
    }
    
    decisions = [
        {
            "confidence": 0.8,
            "importance": 0.7
        },
        {
            "confidence": 0.7,
            "importance": 0.6
        },
        {
            "confidence": 0.6,
            "importance": 0.5
        }
    ]
    
    # Test with no critical issues
    issues = [
        {
            "severity": "low",
            "type": "minor"
        }
    ]
    
    # Test with no critical issues
    is_valid = orchestration_agent._determine_validity(orchestration, decisions, issues, 0.7)
    assert is_valid is True, \
        "Should be valid with high confidence and no critical issues"
    
    # Test with critical issue
    critical_issues = issues + [{
        "severity": "high",
        "type": "critical"
    }]
    is_valid = orchestration_agent._determine_validity(orchestration, decisions, critical_issues, 0.7)
    assert is_valid is False, \
        "Should be invalid with critical issue"
    
    # Test with low confidence
    is_valid = orchestration_agent._determine_validity(orchestration, decisions, issues, 0.3)
    assert is_valid is False, \
        "Should be invalid with low confidence"
    
    # Test with empty inputs
    is_valid = orchestration_agent._determine_validity({}, [], [], 0.7)
    assert is_valid is False, \
        "Should be invalid with empty inputs"

@pytest.mark.asyncio
async def test_error_handling(orchestration_agent):
    """Test error handling during orchestration."""
    # Make LLM raise an error
    orchestration_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await orchestration_agent.orchestrate_agents({"content": "test"}, "sequential")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, OrchestrationResult), "Result should be an OrchestrationResult instance"
    assert result.is_valid is False, "Result should be invalid when error occurs"
    assert result.confidence == 0.0, "Confidence should be 0.0 when error occurs"
    assert len(result.decisions) == 0, "Should have no decisions when error occurs"
    assert len(result.issues) >= 1, "Should have at least one issue indicating error"
    
    # Verify error details
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "error" in result.metadata, "Metadata should contain error information"
    assert isinstance(result.metadata["error"], str), "Error should be a string message"
    assert "Test error" in result.metadata["error"], \
        "Error message should contain original error text"

@pytest.mark.asyncio
async def test_domain_awareness(orchestration_agent):
    """Test domain awareness in orchestration."""
    content = {"content": "test"}
    
    # Test initial domain
    result = await orchestration_agent.orchestrate_agents(content, "sequential")
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional' initially"
    
    # Test domain change
    orchestration_agent.domain = "personal"
    result = await orchestration_agent.orchestrate_agents(content, "sequential")
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "personal", \
        "Domain should be updated to 'personal'"
    
    # Verify domain affects orchestration
    assert isinstance(result.orchestration, dict), "Result should have orchestration dictionary"
    assert result.orchestration is not None, "Orchestration should not be null after domain change"

if __name__ == "__main__":
    pytest.main([__file__])
