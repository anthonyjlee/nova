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
    assert isinstance(result, OrchestrationResult)
    assert result.orchestration["type"] == "sequential"
    assert len(result.orchestration["agents"]) == 2
    assert len(result.decisions) == 1
    assert len(result.issues) == 1
    assert result.confidence > 0
    assert "domain" in result.metadata

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
    assert isinstance(result, OrchestrationResult)
    assert result.orchestration["type"] == "sequential"
    assert "agents" in result.orchestration
    assert result.confidence >= 0
    assert result.is_valid is True  # All basic checks should pass

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
    assert len(orchestrations) == 1
    assert "content" in orchestrations[0]
    assert orchestrations[0]["similarity"] == 0.9

def test_basic_orchestration_sequential(orchestration_agent):
    """Test basic sequential orchestration."""
    content = {
        "order": ["agent1"],
        "dependencies": {"agent1": []},
        "transitions": {}
    }
    
    result = orchestration_agent._basic_orchestration(content, "sequential", [])
    
    assert "orchestration" in result
    assert "decisions" in result
    assert "issues" in result
    assert result["orchestration"]["type"] == "sequential"
    assert len(result["decisions"]) > 0
    assert all(d["type"] in ["has_order", "has_dependencies", "has_transitions"] for d in result["decisions"])

def test_basic_orchestration_parallel(orchestration_agent):
    """Test basic parallel orchestration."""
    content = {
        "groups": ["group1"],
        "coordination": {"group1": []},
        "synchronization": {}
    }
    
    result = orchestration_agent._basic_orchestration(content, "parallel", [])
    
    assert "orchestration" in result
    assert "decisions" in result
    assert "issues" in result
    assert result["orchestration"]["type"] == "parallel"
    assert len(result["decisions"]) > 0
    assert all(d["type"] in ["has_groups", "has_coordination", "has_synchronization"] for d in result["decisions"])

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
    assert orchestration_agent._check_rule("has_order", content) is True
    assert orchestration_agent._check_rule("has_dependencies", content) is True
    assert orchestration_agent._check_rule("has_transitions", content) is True
    
    # Test parallel rules
    assert orchestration_agent._check_rule("has_groups", content) is True
    assert orchestration_agent._check_rule("has_coordination", content) is True
    assert orchestration_agent._check_rule("has_synchronization", content) is True
    
    # Test adaptive rules
    assert orchestration_agent._check_rule("has_conditions", content) is True
    assert orchestration_agent._check_rule("has_fallbacks", content) is True
    assert orchestration_agent._check_rule("has_adaptations", content) is True

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
    
    assert result["type"] == "sequential"
    assert len(result["agents"]) == 2
    assert result["agents"]["main"]["priority"] == 0.8
    assert "description" in result["agents"]["main"]
    assert "flows" in result
    assert "metadata" in result

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
    
    assert len(decisions) == 2  # Invalid one should be filtered out
    assert all("type" in d for d in decisions)
    assert all("description" in d for d in decisions)
    assert all("confidence" in d for d in decisions)
    assert any("domain_relevance" in d for d in decisions)

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
    
    assert len(issues) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in issues)
    assert all("severity" in i for i in issues)
    assert all("description" in i for i in issues)
    assert any("domain_impact" in i for i in issues)

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
    
    assert 0 <= confidence <= 1
    # Should include:
    # - Orchestration confidence (0.2 from agents + flows)
    # - Decision confidence (0.7 average)
    # - Issue impact (0.2 from low + medium severity)
    assert 0.45 <= confidence <= 0.55

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
    
    is_valid = orchestration_agent._determine_validity(orchestration, decisions, issues, 0.7)
    assert is_valid is True  # High confidence, mostly passed decisions
    
    # Test with critical issue
    issues.append({
        "severity": "high",
        "type": "critical"
    })
    
    is_valid = orchestration_agent._determine_validity(orchestration, decisions, issues, 0.7)
    assert is_valid is False  # Critical issue should fail validation

@pytest.mark.asyncio
async def test_error_handling(orchestration_agent):
    """Test error handling during orchestration."""
    # Make LLM raise an error
    orchestration_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await orchestration_agent.orchestrate_agents({"content": "test"}, "sequential")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, OrchestrationResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.decisions) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_awareness(orchestration_agent):
    """Test domain awareness in orchestration."""
    content = {"content": "test"}
    result = await orchestration_agent.orchestrate_agents(content, "sequential")
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    orchestration_agent.domain = "personal"
    result = await orchestration_agent.orchestrate_agents(content, "sequential")
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
