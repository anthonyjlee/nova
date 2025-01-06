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
    assert isinstance(result, ExecutionResult), "Result should be an ExecutionResult instance"
    
    # Verify execution details
    assert isinstance(result.execution, dict), "Execution should be a dictionary"
    assert result.execution["type"] == "sequential", "Execution type should be sequential"
    assert len(result.execution["steps"]) >= 2, "Should have at least two execution steps"
    
    # Verify actions
    assert isinstance(result.actions, list), "Actions should be a list"
    assert len(result.actions) >= 1, "Should have at least one action"
    
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
    assert isinstance(result, ExecutionResult), "Result should be an ExecutionResult instance"
    
    # Verify execution details
    assert isinstance(result.execution, dict), "Execution should be a dictionary"
    assert result.execution["type"] == "sequential", "Execution type should be sequential"
    assert "steps" in result.execution, "Execution should contain steps"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify validity
    assert result.is_valid is True, "Result should be valid with basic content"
    
    # Verify no LLM-specific fields
    assert not any(a.get("domain_relevance") for a in result.actions), \
        "Actions should not have LLM-specific fields"

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
    
    # Verify we got executions back
    assert isinstance(executions, list), "Should return a list of executions"
    assert len(executions) >= 1, "Should have at least one similar execution"
    
    # Verify execution item structure
    execution_item = executions[0]
    assert isinstance(execution_item, dict), "Each execution item should be a dictionary"
    assert "content" in execution_item, "Each execution item should have content"
    assert "similarity" in execution_item, "Each execution item should have similarity score"
    assert isinstance(execution_item["similarity"], (int, float)), \
        "Similarity should be numeric"
    assert 0 <= execution_item["similarity"] <= 1, \
        "Similarity should be between 0 and 1"

def test_basic_execution_sequential(execution_agent):
    """Test basic sequential execution."""
    content = {
        "steps": ["step1"],
        "dependencies": {"step1": []},
        "transitions": {}
    }
    
    result = execution_agent._basic_execution(content, "sequential", [])
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "execution" in result, "Result should contain execution"
    assert "actions" in result, "Result should contain actions"
    assert "issues" in result, "Result should contain issues"
    
    # Verify execution details
    assert isinstance(result["execution"], dict), "Execution should be a dictionary"
    assert result["execution"]["type"] == "sequential", "Execution type should be sequential"
    
    # Verify actions
    assert isinstance(result["actions"], list), "Actions should be a list"
    assert len(result["actions"]) >= 1, "Should have at least one action"
    assert all(a["type"] in ["has_steps", "has_dependencies", "has_transitions"] for a in result["actions"]), \
        "Each action should have a valid sequential type"
    
    # Verify issues
    assert isinstance(result["issues"], list), "Issues should be a list"

def test_basic_execution_parallel(execution_agent):
    """Test basic parallel execution."""
    content = {
        "tasks": ["task1"],
        "coordination": {"task1": []},
        "synchronization": {}
    }
    
    result = execution_agent._basic_execution(content, "parallel", [])
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "execution" in result, "Result should contain execution"
    assert "actions" in result, "Result should contain actions"
    assert "issues" in result, "Result should contain issues"
    
    # Verify execution details
    assert isinstance(result["execution"], dict), "Execution should be a dictionary"
    assert result["execution"]["type"] == "parallel", "Execution type should be parallel"
    
    # Verify actions
    assert isinstance(result["actions"], list), "Actions should be a list"
    assert len(result["actions"]) >= 1, "Should have at least one action"
    assert all(a["type"] in ["has_tasks", "has_coordination", "has_synchronization"] for a in result["actions"]), \
        "Each action should have a valid parallel type"
    
    # Verify issues
    assert isinstance(result["issues"], list), "Issues should be a list"

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
    assert execution_agent._check_rule("has_steps", content) is True, \
        "Should validate steps rule"
    assert execution_agent._check_rule("has_dependencies", content) is True, \
        "Should validate dependencies rule"
    assert execution_agent._check_rule("has_transitions", content) is True, \
        "Should validate transitions rule"
    
    # Test parallel rules
    assert execution_agent._check_rule("has_tasks", content) is True, \
        "Should validate tasks rule"
    assert execution_agent._check_rule("has_coordination", content) is True, \
        "Should validate coordination rule"
    assert execution_agent._check_rule("has_synchronization", content) is True, \
        "Should validate synchronization rule"
    
    # Test adaptive rules
    assert execution_agent._check_rule("has_conditions", content) is True, \
        "Should validate conditions rule"
    assert execution_agent._check_rule("has_fallbacks", content) is True, \
        "Should validate fallbacks rule"
    assert execution_agent._check_rule("has_adaptations", content) is True, \
        "Should validate adaptations rule"
    
    # Test invalid rule
    assert execution_agent._check_rule("invalid_rule", content) is False, \
        "Should return False for invalid rules"

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
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "type" in result, "Result should contain type"
    assert result["type"] == "sequential", "Type should be sequential"
    
    # Verify steps
    assert "steps" in result, "Result should contain steps"
    assert isinstance(result["steps"], dict), "Steps should be a dictionary"
    assert len(result["steps"]) >= 2, "Should have at least two steps"
    
    # Verify main step details
    main_step = result["steps"]["main"]
    assert isinstance(main_step, dict), "Main step should be a dictionary"
    assert main_step["type"] == "processor", "Main step should be a processor"
    assert isinstance(main_step["priority"], (int, float)), "Priority should be numeric"
    assert 0 <= main_step["priority"] <= 1, "Priority should be between 0 and 1"
    assert "description" in main_step, "Main step should have a description"
    
    # Verify actions and metadata
    assert "actions" in result, "Result should contain actions"
    assert isinstance(result["actions"], dict), "Actions should be a dictionary"
    assert "metadata" in result, "Result should contain metadata"
    assert isinstance(result["metadata"], dict), "Metadata should be a dictionary"

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
    
    # Verify we got valid actions (filtering out invalid ones)
    assert isinstance(actions, list), "Should return a list of actions"
    assert len(actions) >= 2, "Should have at least two valid actions"
    
    # Verify each action has required fields
    for action in actions:
        assert isinstance(action, dict), "Each action should be a dictionary"
        assert "type" in action, "Each action should have a type"
        assert "description" in action, "Each action should have a description"
        assert "confidence" in action, "Each action should have a confidence score"
        assert isinstance(action["confidence"], (int, float)), \
            "Confidence should be numeric"
        assert 0 <= action["confidence"] <= 1, \
            "Confidence should be between 0 and 1"
    
    # Verify at least one action has extended fields
    assert any("domain_relevance" in a for a in actions), \
        "At least one action should have domain relevance"
    assert any("importance" in a for a in actions), \
        "At least one action should have importance"
    assert any("steps" in a for a in actions), \
        "At least one action should have steps"

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
    assert any("related_steps" in i for i in issues), \
        "At least one issue should have related steps"

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
    
    # Verify confidence is a valid number
    assert isinstance(confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify confidence calculation is reasonable
    # Given high confidence actions (0.8, 0.6) and a structured execution,
    # confidence should be above threshold
    assert confidence >= 0.5, f"Confidence {confidence} should be >= 0.5 given strong input values"
    
    # Test with empty inputs
    empty_confidence = execution_agent._calculate_confidence({}, [], [])
    assert isinstance(empty_confidence, (int, float)), "Empty confidence should be numeric"
    assert 0 <= empty_confidence <= 1, "Empty confidence should be between 0 and 1"
    assert empty_confidence < confidence, \
        "Empty input should result in lower confidence than valid input"
    
    # Test with partial inputs
    partial_confidence = execution_agent._calculate_confidence(execution, [], [])
    assert isinstance(partial_confidence, (int, float)), "Partial confidence should be numeric"
    assert 0 <= partial_confidence <= 1, "Partial confidence should be between 0 and 1"
    assert partial_confidence < confidence, \
        "Partial input should result in lower confidence than full input"

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
    
    # Test with no critical issues
    is_valid = execution_agent._determine_validity(execution, actions, issues, 0.7)
    assert is_valid is True, \
        "Should be valid with high confidence and no critical issues"
    
    # Test with critical issue
    critical_issues = issues + [{
        "severity": "high",
        "type": "critical"
    }]
    is_valid = execution_agent._determine_validity(execution, actions, critical_issues, 0.7)
    assert is_valid is False, \
        "Should be invalid with critical issue"
    
    # Test with low confidence
    is_valid = execution_agent._determine_validity(execution, actions, issues, 0.3)
    assert is_valid is False, \
        "Should be invalid with low confidence"
    
    # Test with empty inputs
    is_valid = execution_agent._determine_validity({}, [], [], 0.7)
    assert is_valid is False, \
        "Should be invalid with empty inputs"

@pytest.mark.asyncio
async def test_error_handling(execution_agent):
    """Test error handling during execution."""
    # Make LLM raise an error
    execution_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await execution_agent.execute_actions({"content": "test"}, "sequential")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, ExecutionResult), "Result should be an ExecutionResult instance"
    assert result.is_valid is False, "Result should be invalid when error occurs"
    assert result.confidence == 0.0, "Confidence should be 0.0 when error occurs"
    assert len(result.actions) == 0, "Should have no actions when error occurs"
    assert len(result.issues) >= 1, "Should have at least one issue indicating error"
    
    # Verify error details
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "error" in result.metadata, "Metadata should contain error information"
    assert isinstance(result.metadata["error"], str), "Error should be a string message"
    assert "Test error" in result.metadata["error"], \
        "Error message should contain original error text"

@pytest.mark.asyncio
async def test_domain_awareness(execution_agent):
    """Test domain awareness in execution."""
    content = {"content": "test"}
    
    # Test initial domain
    result = await execution_agent.execute_actions(content, "sequential")
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional' initially"
    
    # Test domain change
    execution_agent.domain = "personal"
    result = await execution_agent.execute_actions(content, "sequential")
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "personal", \
        "Domain should be updated to 'personal'"
    
    # Verify domain affects execution
    assert isinstance(result.execution, dict), "Result should have execution dictionary"
    assert result.execution is not None, "Execution should not be null after domain change"

if __name__ == "__main__":
    pytest.main([__file__])
