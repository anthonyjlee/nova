"""Tests for Nova's task analysis functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.task import TaskAgent, TaskResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "tasks": [
            {
                "statement": "Complete this task",
                "type": "core_task",
                "description": "Primary task",
                "confidence": 0.8,
                "source": "analysis",
                "domain_relevance": 0.9,
                "priority": 0.8,
                "complexity": 0.7,
                "status": "pending"
            }
        ],
        "dependencies": {
            "sequential": ["task1", "task2"],
            "parallel": ["task3"],
            "blockers": ["blocker1"],
            "domain_factors": {
                "relevance": "high",
                "impact": "medium"
            },
            "priority_factors": [
                {
                    "factor": "urgency",
                    "weight": 0.8
                }
            ]
        }
    })
    return llm

@pytest.fixture
def task_agent(mock_llm):
    """Create a TaskAgent instance with mock dependencies."""
    return TaskAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=MagicMock(),
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_tasks_with_llm(task_agent, mock_llm):
    """Test task analysis using LLM."""
    content = {
        "content": "We need to complete this task",
        "type": "statement"
    }
    
    result = await task_agent.analyze_tasks(content)
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, TaskResult)
    assert len(result.tasks) == 1
    assert result.confidence > 0
    assert "domain" in result.metadata
    assert result.dependencies is not None

@pytest.mark.asyncio
async def test_analyze_tasks_without_llm():
    """Test task analysis without LLM (fallback mode)."""
    agent = TaskAgent()  # No LLM provided
    content = {
        "content": "We need to do this and must complete that",
        "context": {"setting": "meeting"}
    }
    
    result = await agent.analyze_tasks(content)
    
    # Verify basic analysis worked
    assert isinstance(result, TaskResult)
    assert len(result.tasks) > 0
    assert any(t["type"] == "inferred_task" for t in result.tasks)
    assert result.confidence >= 0
    assert "sequential" not in result.dependencies  # No "after" in text

def test_basic_analysis(task_agent):
    """Test basic task analysis without LLM."""
    content = {
        "content": "We need to do this and must do that after completing the first task",
        "context": {
            "setting": "discussion"
        }
    }
    
    result = task_agent._basic_analysis(content)
    
    assert "tasks" in result
    assert "dependencies" in result
    assert len(result["tasks"]) == 2  # "need to" and "must"
    assert all(t["type"] == "inferred_task" for t in result["tasks"])
    assert "sequential" in result["dependencies"]

def test_extract_tasks(task_agent):
    """Test task extraction and validation."""
    analysis = {
        "tasks": [
            {
                "statement": "Valid",
                "type": "core_task",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "priority": 0.7,
                "complexity": 0.8,
                "status": "pending"
            },
            {
                "statement": "Basic",
                "confidence": 0.6  # Missing type should get default
            },
            "Invalid"  # Not a dict, should be ignored
        ]
    }
    
    tasks = task_agent._extract_tasks(analysis)
    
    assert len(tasks) == 2  # Invalid one should be filtered out
    assert all("type" in t for t in tasks)
    assert any(t["type"] == "task" for t in tasks)  # Default type
    assert any("domain_relevance" in t for t in tasks)
    assert any("priority" in t for t in tasks)

def test_extract_dependencies(task_agent):
    """Test dependency extraction and validation."""
    analysis = {
        "dependencies": {
            "sequential": ["task1", "task2"],
            "parallel": ["task3"],
            "blockers": ["blocker1"],
            "domain_factors": {
                "relevance": "high",
                "impact": "medium"
            },
            "priority_factors": [
                {
                    "factor": "urgency",
                    "weight": 0.8
                }
            ],
            "invalid": object()  # Should be ignored
        }
    }
    
    dependencies = task_agent._extract_dependencies(analysis)
    
    assert "sequential" in dependencies
    assert "parallel" in dependencies
    assert "blockers" in dependencies
    assert "domain_factors" in dependencies
    assert "priority_factors" in dependencies
    assert len(dependencies["sequential"]) == 2
    assert len(dependencies["priority_factors"]) == 1
    assert "invalid" not in dependencies

def test_calculate_confidence(task_agent):
    """Test confidence calculation."""
    tasks = [
        {
            "confidence": 0.8,
            "priority": 0.7
        },
        {
            "confidence": 0.6,
            "priority": 0.8
        }
    ]
    
    dependencies = {
        "sequential": ["task1", "task2"],
        "parallel": ["task3"],
        "blockers": ["blocker1"],
        "domain_factors": {
            "factor1": "value1",
            "factor2": "value2"
        },
        "priority_factors": [
            {
                "factor": "urgency",
                "weight": 0.8
            }
        ]
    }
    
    confidence = task_agent._calculate_confidence(tasks, dependencies)
    
    assert 0 <= confidence <= 1
    # Should include:
    # - Task confidence (0.7 average)
    # - Sequential (0.4 from 2 tasks)
    # - Parallel (0.15 from 1 task)
    # - Blockers (0.1 from 1 blocker)
    # - Domain factors (0.2 from 2 factors)
    # - Priority factors (0.15 from 1 factor)
    assert 0.65 <= confidence <= 0.75

@pytest.mark.asyncio
async def test_error_handling(task_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    task_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await task_agent.analyze_tasks({"content": "test"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, TaskResult)
    assert result.confidence == 0.0
    assert len(result.tasks) == 0
    assert "error" in result.metadata
    assert "error" in result.dependencies

@pytest.mark.asyncio
async def test_domain_awareness(task_agent):
    """Test domain awareness in analysis."""
    content = {"content": "test"}
    result = await task_agent.analyze_tasks(content)
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    task_agent.domain = "personal"
    result = await task_agent.analyze_tasks(content)
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
