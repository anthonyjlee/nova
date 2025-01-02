"""Tests for Nova's execution functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.execution import ExecutionAgent, ExecutionResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "execution": {
            "type": "sequential",
            "steps": {
                "main": {
                    "type": "processor",
                    "priority": 0.8,
                    "description": "Main step",
                    "actions": ["action1", "action2"]
                },
                "sub": {
                    "type": "helper",
                    "priority": 0.6,
                    "metadata": {
                        "key": "value"
                    }
                }
            },
            "actions": {
                "primary": ["action1"],
                "secondary": ["action2"]
            },
            "metadata": {
                "version": "1.0"
            }
        },
        "actions": [
            {
                "type": "step",
                "description": "Step execution",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "steps": ["step1"]
            }
        ],
        "issues": [
            {
                "type": "missing_step",
                "severity": "medium",
                "description": "Missing step",
                "domain_impact": 0.3,
                "suggested_fix": "Add step",
                "related_steps": ["step3"]
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
            "content": {"content": "Similar execution"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def execution_agent(mock_llm, mock_vector_store):
    """Create an ExecutionAgent instance with mock dependencies."""
    return ExecutionAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_execute_actions_with_llm(execution_agent, mock_llm):
    """Test action execution using LLM."""
    content = {
        "content": "Test content",
        "type": "sequential",
        "metadata": {"key": "value"}
    }
    
    result = await execution_agent.execute_actions(content, "sequential")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, ExecutionResult)
    assert result.execution["type"] == "sequential"
    assert len(result.execution["steps"]) == 2
    assert len(result.actions) == 1
    assert len(result.issues) == 1
    assert result.confidence > 0
    assert "domain" in result.metadata

@pytest.mark.asyncio
async def test_execute_actions_without_llm():
    """Test action execution without LLM (fallback mode)."""
    agent = ExecutionAgent()  # No LLM provided
    content = {
        "steps": ["step1"],
        "dependencies": {"step1": []},
        "transitions": {}
    }
    
    result = await agent.execute_actions(content, "sequential")
    
    # Verify basic execution worked
    assert isinstance(result, ExecutionResult)
    assert result.execution["type"] == "sequential"
    assert "steps" in result.execution
    assert result.confidence >= 0
    assert result.is_valid is True  # All basic checks should pass

@pytest.mark.asyncio
async def test_get_similar_executions(execution_agent, mock_vector_store):
    """Test similar execution retrieval."""
    content = {"content": "test content"}
    execution_type = "sequential"
    
    executions = await execution_agent._get_similar_executions(content, execution_type)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "execution",
            "execution_type": "sequential"
        }
    )
    assert len(executions) == 1
    assert "content" in executions[0]
    assert executions[0]["similarity"] == 0.9

def test_basic_execution_sequential(execution_agent):
    """Test basic sequential execution."""
    content = {
        "steps": ["step1"],
        "dependencies": {"step1": []},
        "transitions": {}
    }
    
    result = execution_agent._basic_execution(content, "sequential", [])
    
    assert "execution" in result
    assert "actions" in result
    assert "issues" in result
    assert result["execution"]["type"] == "sequential"
    assert len(result["actions"]) > 0
    assert all(a["type"] in ["has_steps", "has_dependencies", "has_transitions"] for a in result["actions"])

def test_basic_execution_parallel(execution_agent):
    """Test basic parallel execution."""
    content = {
        "tasks": ["task1"],
        "coordination": {"task1": []},
        "synchronization": {}
    }
    
    result = execution_agent._basic_execution(content, "parallel", [])
    
    assert "execution" in result
    assert "actions" in result
    assert "issues" in result
    assert result["execution"]["type"] == "parallel"
    assert len(result["actions"]) > 0
    assert all(a["type"] in ["has_tasks", "has_coordination", "has_synchronization"] for a in result["actions"])

def test_check_rule(execution_agent):
    """Test execution rule checking."""
    content = {
        "steps": ["step1"],
        "dependencies": {"step1": []},
        "transitions": {},
        "tasks": ["task1"],
        "coordination": {"task1": []},
        "synchronization": {},
        "conditions": {"step1": []},
        "fallbacks": {"step1": []},
        "adaptations": {}
    }
    
    # Test sequential rules
    assert execution_agent._check_rule("has_steps", content) is True
    assert execution_agent._check_rule("has_dependencies", content) is True
    assert execution_agent._check_rule("has_transitions", content) is True
    
    # Test parallel rules
    assert execution_agent._check_rule("has_tasks", content) is True
    assert execution_agent._check_rule("has_coordination", content) is True
    assert execution_agent._check_rule("has_synchronization", content) is True
    
    # Test adaptive rules
    assert execution_agent._check_rule("has_conditions", content) is True
    assert execution_agent._check_rule("has_fallbacks", content) is True
    assert execution_agent._check_rule("has_adaptations", content) is True

def test_extract_execution(execution_agent):
    """Test execution extraction and validation."""
    execution = {
        "execution": {
            "type": "sequential",
            "steps": {
                "main": {
                    "type": "processor",
                    "priority": 0.8,
                    "description": "Main step"
                },
                "sub": {
                    "type": "helper",
                    "priority": 0.6
                }
            },
            "actions": {
                "primary": ["action1"]
            },
            "metadata": {
                "version": "1.0"
            }
        }
    }
    
    result = execution_agent._extract_execution(execution)
    
    assert result["type"] == "sequential"
    assert len(result["steps"]) == 2
    assert result["steps"]["main"]["priority"] == 0.8
    assert "description" in result["steps"]["main"]
    assert "actions" in result
    assert "metadata" in result

def test_extract_actions(execution_agent):
    """Test action extraction and validation."""
    execution = {
        "actions": [
            {
                "type": "step",
                "description": "Test action",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "steps": ["step1"]
            },
            {
                "type": "basic",
                "description": "Basic action",
                "confidence": 0.6
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    actions = execution_agent._extract_actions(execution)
    
    assert len(actions) == 2  # Invalid one should be filtered out
    assert all("type" in a for a in actions)
    assert all("description" in a for a in actions)
    assert all("confidence" in a for a in actions)
    assert any("domain_relevance" in a for a in actions)

def test_extract_issues(execution_agent):
    """Test issue extraction and validation."""
    execution = {
        "issues": [
            {
                "type": "missing_step",
                "severity": "high",
                "description": "Missing step",
                "details": "Details",
                "domain_impact": 0.8,
                "suggested_fix": "Add step",
                "related_steps": ["step1"]
            },
            {
                "type": "basic_issue",
                "description": "Basic"
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    issues = execution_agent._extract_issues(execution)
    
    assert len(issues) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in issues)
    assert all("severity" in i for i in issues)
    assert all("description" in i for i in issues)
    assert any("domain_impact" in i for i in issues)

def test_calculate_confidence(execution_agent):
    """Test confidence calculation."""
    execution = {
        "steps": {
            "main": {"type": "processor"},
            "sub": {"type": "helper"}
        },
        "actions": {
            "primary": ["action1"],
            "secondary": ["action2"]
        }
    }
    
    actions = [
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
    
    confidence = execution_agent._calculate_confidence(execution, actions, issues)
    
    assert 0 <= confidence <= 1
    # Should include:
    # - Execution confidence (0.2 from steps + actions)
    # - Action confidence (0.7 average)
    # - Issue impact (0.2 from low + medium severity)
    assert 0.45 <= confidence <= 0.55

def test_determine_validity(execution_agent):
    """Test validity determination."""
    execution = {
        "steps": {
            "main": {"type": "processor"}
        },
        "actions": {
            "primary": ["action1"]
        }
    }
    
    actions = [
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
    
    is_valid = execution_agent._determine_validity(execution, actions, issues, 0.7)
    assert is_valid is True  # High confidence, mostly passed actions
    
    # Test with critical issue
    issues.append({
        "severity": "high",
        "type": "critical"
    })
    
    is_valid = execution_agent._determine_validity(execution, actions, issues, 0.7)
    assert is_valid is False  # Critical issue should fail validation

@pytest.mark.asyncio
async def test_error_handling(execution_agent):
    """Test error handling during execution."""
    # Make LLM raise an error
    execution_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await execution_agent.execute_actions({"content": "test"}, "sequential")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, ExecutionResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.actions) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_awareness(execution_agent):
    """Test domain awareness in execution."""
    content = {"content": "test"}
    result = await execution_agent.execute_actions(content, "sequential")
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    execution_agent.domain = "personal"
    result = await execution_agent.execute_actions(content, "sequential")
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
