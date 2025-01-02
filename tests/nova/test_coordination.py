"""Tests for Nova's coordination functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.coordination import CoordinationAgent, CoordinationResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "groups": {
            "group1": {
                "name": "Test Group 1",
                "type": "task",
                "status": "active",
                "description": "Test group",
                "priority": 0.8,
                "dependencies": ["group2"],
                "metadata": {"key": "value"}
            }
        },
        "assignments": {
            "agent1": ["group1"],
            "agent2": ["group1", "group2"]
        },
        "resources": {
            "resource1": {
                "type": "compute",
                "amount": 100,
                "assigned_to": ["agent1"],
                "priority": 0.9,
                "constraints": {"min": 50},
                "metadata": {"unit": "cpu"}
            }
        },
        "issues": [
            {
                "type": "resource_conflict",
                "severity": "medium",
                "description": "Resource overlap",
                "impact": 0.5,
                "suggested_fix": "Reallocate"
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
            "content": {
                "content": "Previous coordination",
                "resources": {
                    "resource1": {
                        "amount": 50,
                        "assigned_to": ["agent2"]
                    }
                }
            },
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def coordination_agent(mock_llm, mock_vector_store):
    """Create a CoordinationAgent instance with mock dependencies."""
    return CoordinationAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_coordination_with_llm(coordination_agent, mock_llm):
    """Test coordination processing using LLM."""
    content = {
        "group_id": "group1",
        "type": "task_coordination",
        "metadata": {"key": "value"}
    }
    
    result = await coordination_agent.process_coordination(content)
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, CoordinationResult)
    assert "group1" in result.groups
    assert "agent1" in result.assignments
    assert "resource1" in result.resources
    assert len(result.issues) == 1
    assert result.is_valid is True
    assert "domain" in result.metadata

@pytest.mark.asyncio
async def test_process_coordination_without_llm():
    """Test coordination processing without LLM (fallback mode)."""
    agent = CoordinationAgent()  # No LLM provided
    content = {
        "groups": {
            "group1": {
                "name": "Test Group",
                "type": "task",
                "status": "active"
            }
        },
        "assignments": {
            "agent1": ["group1"]
        },
        "resources": {
            "resource1": {
                "type": "compute",
                "amount": 100,
                "assigned_to": ["agent1"]
            }
        }
    }
    
    result = await agent.process_coordination(content)
    
    # Verify basic coordination worked
    assert isinstance(result, CoordinationResult)
    assert "group1" in result.groups
    assert "agent1" in result.assignments
    assert "resource1" in result.resources
    assert result.is_valid is True

@pytest.mark.asyncio
async def test_get_coordination_history(coordination_agent, mock_vector_store):
    """Test coordination history retrieval."""
    content = {"group_id": "group1"}
    
    history = await coordination_agent._get_coordination_history(content)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "group1",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "coordination"
        }
    )
    assert len(history) == 1
    assert "content" in history[0]
    assert history[0]["similarity"] == 0.9

def test_basic_coordination(coordination_agent):
    """Test basic coordination processing."""
    content = {
        "groups": {
            "group1": {
                "name": "Test Group",
                "type": "task",
                "status": "active"
            }
        },
        "assignments": {
            "agent1": ["group1"]
        },
        "resources": {
            "resource1": {
                "type": "compute",
                "amount": 100,
                "assigned_to": ["agent1"]
            }
        }
    }
    
    coordination_history = [
        {
            "content": {
                "resources": {
                    "resource1": {
                        "amount": 50,
                        "assigned_to": ["agent2"]
                    }
                }
            }
        }
    ]
    
    result = coordination_agent._basic_coordination(content, coordination_history)
    
    assert "groups" in result
    assert "assignments" in result
    assert "resources" in result
    assert "issues" in result
    assert len(result["issues"]) == 1  # Resource conflict detected
    assert result["issues"][0]["type"] == "resource_conflict"

def test_extract_groups(coordination_agent):
    """Test group extraction and validation."""
    coordination = {
        "groups": {
            "group1": {
                "name": "Test Group",
                "type": "task",
                "status": "active",
                "description": "Test description",
                "priority": 0.8,
                "dependencies": ["group2"],
                "metadata": {"key": "value"}
            }
        }
    }
    
    groups = coordination_agent._extract_groups(coordination)
    
    assert "group1" in groups
    assert groups["group1"]["name"] == "Test Group"
    assert groups["group1"]["type"] == "task"
    assert groups["group1"]["status"] == "active"
    assert "description" in groups["group1"]
    assert "priority" in groups["group1"]
    assert "dependencies" in groups["group1"]
    assert "metadata" in groups["group1"]

def test_extract_assignments(coordination_agent):
    """Test assignment extraction and validation."""
    coordination = {
        "assignments": {
            "agent1": ["group1", "group2"],
            "agent2": ["group1"]
        }
    }
    
    assignments = coordination_agent._extract_assignments(coordination)
    
    assert "agent1" in assignments
    assert "agent2" in assignments
    assert len(assignments["agent1"]) == 2
    assert len(assignments["agent2"]) == 1
    assert all(isinstance(group_id, str) for group_id in assignments["agent1"])

def test_extract_resources(coordination_agent):
    """Test resource extraction and validation."""
    coordination = {
        "resources": {
            "resource1": {
                "type": "compute",
                "amount": 100,
                "assigned_to": ["agent1"],
                "priority": 0.9,
                "constraints": {"min": 50},
                "metadata": {"unit": "cpu"}
            }
        }
    }
    
    resources = coordination_agent._extract_resources(coordination)
    
    assert "resource1" in resources
    assert resources["resource1"]["type"] == "compute"
    assert resources["resource1"]["amount"] == 100
    assert "agent1" in resources["resource1"]["assigned_to"]
    assert "priority" in resources["resource1"]
    assert "constraints" in resources["resource1"]
    assert "metadata" in resources["resource1"]

def test_extract_issues(coordination_agent):
    """Test issue extraction and validation."""
    coordination = {
        "issues": [
            {
                "type": "resource_conflict",
                "severity": "medium",
                "description": "Resource overlap",
                "details": "Multiple assignments",
                "impact": 0.5,
                "suggested_fix": "Reallocate"
            }
        ]
    }
    
    issues = coordination_agent._extract_issues(coordination)
    
    assert len(issues) == 1
    assert issues[0]["type"] == "resource_conflict"
    assert issues[0]["severity"] == "medium"
    assert "description" in issues[0]
    assert "details" in issues[0]
    assert "impact" in issues[0]
    assert "suggested_fix" in issues[0]

def test_determine_validity(coordination_agent):
    """Test validity determination."""
    # Valid case
    groups = {
        "group1": {"status": "active"}
    }
    assignments = {
        "agent1": ["group1"]
    }
    resources = {
        "resource1": {
            "amount": 100,
            "assigned_to": ["agent1"]
        }
    }
    issues = [
        {
            "type": "minor",
            "severity": "low"
        }
    ]
    
    is_valid = coordination_agent._determine_validity(
        groups, assignments, resources, issues
    )
    assert is_valid is True
    
    # Invalid cases
    # Case 1: No groups
    is_valid = coordination_agent._determine_validity(
        {}, assignments, resources, issues
    )
    assert is_valid is False
    
    # Case 2: Critical issue
    issues.append({
        "type": "major",
        "severity": "high"
    })
    is_valid = coordination_agent._determine_validity(
        groups, assignments, resources, issues
    )
    assert is_valid is False
    
    # Case 3: Invalid group assignment
    assignments["agent1"].append("nonexistent_group")
    is_valid = coordination_agent._determine_validity(
        groups, assignments, resources, issues
    )
    assert is_valid is False
    
    # Case 4: Invalid resource allocation
    resources["resource1"]["amount"] = -1
    is_valid = coordination_agent._determine_validity(
        groups, assignments, resources, issues
    )
    assert is_valid is False

@pytest.mark.asyncio
async def test_error_handling(coordination_agent):
    """Test error handling during coordination."""
    # Make LLM raise an error
    coordination_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await coordination_agent.process_coordination({"content": "test"})
    
    # Verify error handling
    assert isinstance(result, CoordinationResult)
    assert result.is_valid is False
    assert not result.groups
    assert not result.assignments
    assert not result.resources
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_awareness(coordination_agent):
    """Test domain awareness in coordination."""
    content = {"group_id": "group1"}
    result = await coordination_agent.process_coordination(content)
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    coordination_agent.domain = "personal"
    result = await coordination_agent.process_coordination(content)
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
