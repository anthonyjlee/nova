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
    assert isinstance(result, TaskResult), "Result should be a TaskResult instance"
    
    # Verify tasks
    assert isinstance(result.tasks, list), "Tasks should be a list"
    assert len(result.tasks) >= 1, "Should have at least one task"
    
    # Verify task structure
    task = result.tasks[0]
    assert isinstance(task, dict), "Each task should be a dictionary"
    assert "statement" in task, "Each task should have a statement"
    assert "type" in task, "Each task should have a type"
    assert "description" in task, "Each task should have a description"
    assert "confidence" in task, "Each task should have a confidence score"
    assert isinstance(task["confidence"], (int, float)), \
        "Confidence should be numeric"
    assert 0 <= task["confidence"] <= 1, \
        "Confidence should be between 0 and 1"
    
    # Verify task metadata
    assert "domain_relevance" in task, "Task should have domain relevance"
    assert "priority" in task, "Task should have priority"
    assert "complexity" in task, "Task should have complexity"
    assert "status" in task, "Task should have status"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify metadata
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional'"
    
    # Verify dependencies
    assert result.dependencies is not None, "Dependencies should be present"
    assert isinstance(result.dependencies, dict), "Dependencies should be a dictionary"
    assert "sequential" in result.dependencies, "Should have sequential dependencies"
    assert "parallel" in result.dependencies, "Should have parallel dependencies"
    assert "blockers" in result.dependencies, "Should have blockers"
    assert "domain_factors" in result.dependencies, "Should have domain factors"
    assert "priority_factors" in result.dependencies, "Should have priority factors"

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
    assert isinstance(result, TaskResult), "Result should be a TaskResult instance"
    
    # Verify tasks
    assert isinstance(result.tasks, list), "Tasks should be a list"
    assert len(result.tasks) > 0, "Should have at least one task"
    
    # Verify task types
    assert all(isinstance(t, dict) for t in result.tasks), \
        "Each task should be a dictionary"
    assert all("type" in t for t in result.tasks), \
        "Each task should have a type"
    assert any(t["type"] == "inferred_task" for t in result.tasks), \
        "Should have at least one inferred task"
    
    # Verify task structure
    for task in result.tasks:
        assert "statement" in task, "Each task should have a statement"
        assert isinstance(task["statement"], str), "Statement should be a string"
        assert len(task["statement"]) > 0, "Statement should not be empty"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify dependencies
    assert isinstance(result.dependencies, dict), "Dependencies should be a dictionary"
    assert "sequential" not in result.dependencies, \
        "Should not have sequential dependencies without sequence indicators"
    assert "parallel" in result.dependencies, \
        "Should have parallel tasks for independent statements"

def test_basic_analysis(task_agent):
    """Test basic task analysis without LLM."""
    content = {
        "content": "We need to do this and must do that after completing the first task",
        "context": {
            "setting": "discussion"
        }
    }
    
    result = task_agent._basic_analysis(content)
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "tasks" in result, "Result should contain tasks"
    assert "dependencies" in result, "Result should contain dependencies"
    
    # Verify tasks
    assert isinstance(result["tasks"], list), "Tasks should be a list"
    assert len(result["tasks"]) == 2, "Should extract exactly two tasks ('need to' and 'must')"
    
    # Verify task structure
    for task in result["tasks"]:
        assert isinstance(task, dict), "Each task should be a dictionary"
        assert "type" in task, "Each task should have a type"
        assert task["type"] == "inferred_task", "Each task should be inferred type"
        assert "statement" in task, "Each task should have a statement"
        assert isinstance(task["statement"], str), "Statement should be a string"
        assert len(task["statement"]) > 0, "Statement should not be empty"
    
    # Verify dependencies
    assert isinstance(result["dependencies"], dict), "Dependencies should be a dictionary"
    assert "sequential" in result["dependencies"], \
        "Should detect sequential dependency from 'after' keyword"
    assert isinstance(result["dependencies"]["sequential"], list), \
        "Sequential dependencies should be a list"
    assert len(result["dependencies"]["sequential"]) > 0, \
        "Should have at least one sequential dependency"
    
    # Verify task ordering
    task_statements = [t["statement"] for t in result["tasks"]]
    assert any("first task" in s.lower() for s in task_statements), \
        "Should identify first task"
    assert any("that" in s.lower() for s in task_statements), \
        "Should identify dependent task"

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
    
    # Verify basic structure
    assert isinstance(tasks, list), "Should return a list of tasks"
    assert len(tasks) == 2, "Should have exactly two valid tasks (invalid one filtered)"
    
    # Verify each task
    for task in tasks:
        assert isinstance(task, dict), "Each task should be a dictionary"
        assert "type" in task, "Each task should have a type"
        assert "statement" in task, "Each task should have a statement"
        assert "confidence" in task, "Each task should have a confidence score"
        assert isinstance(task["confidence"], (int, float)), \
            "Confidence should be numeric"
        assert 0 <= task["confidence"] <= 1, \
            "Confidence should be between 0 and 1"
    
    # Verify core task fields
    core_task = next(t for t in tasks if t["type"] == "core_task")
    assert "domain_relevance" in core_task, "Core task should have domain relevance"
    assert "priority" in core_task, "Core task should have priority"
    assert "complexity" in core_task, "Core task should have complexity"
    assert "status" in core_task, "Core task should have status"
    
    # Verify default type assignment
    basic_task = next(t for t in tasks if t["type"] == "task")
    assert basic_task is not None, "Should assign default type to basic task"
    
    # Verify no invalid tasks included
    assert all(isinstance(t, dict) for t in tasks), \
        "Should filter out non-dictionary tasks"
    assert all("type" in t and isinstance(t["type"], str) for t in tasks), \
        "Each task should have a valid type string"

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
    
    # Verify basic structure
    assert isinstance(dependencies, dict), "Should return a dictionary of dependencies"
    assert "invalid" not in dependencies, "Invalid fields should be filtered out"
    
    # Verify task dependencies
    assert "sequential" in dependencies, "Should have sequential dependencies"
    assert isinstance(dependencies["sequential"], list), \
        "Sequential dependencies should be a list"
    assert len(dependencies["sequential"]) == 2, \
        "Should have exactly two sequential dependencies"
    
    assert "parallel" in dependencies, "Should have parallel dependencies"
    assert isinstance(dependencies["parallel"], list), \
        "Parallel dependencies should be a list"
    assert len(dependencies["parallel"]) == 1, \
        "Should have exactly one parallel dependency"
    
    assert "blockers" in dependencies, "Should have blockers"
    assert isinstance(dependencies["blockers"], list), \
        "Blockers should be a list"
    assert len(dependencies["blockers"]) == 1, \
        "Should have exactly one blocker"
    
    # Verify domain factors
    assert "domain_factors" in dependencies, "Should have domain factors"
    assert isinstance(dependencies["domain_factors"], dict), \
        "Domain factors should be a dictionary"
    assert len(dependencies["domain_factors"]) == 2, \
        "Should have exactly two domain factors"
    assert all(isinstance(v, str) for v in dependencies["domain_factors"].values()), \
        "Domain factor values should be strings"
    
    # Verify priority factors
    assert "priority_factors" in dependencies, "Should have priority factors"
    assert isinstance(dependencies["priority_factors"], list), \
        "Priority factors should be a list"
    assert len(dependencies["priority_factors"]) == 1, \
        "Should have exactly one priority factor"
    
    # Verify priority factor structure
    priority_factor = dependencies["priority_factors"][0]
    assert isinstance(priority_factor, dict), "Priority factor should be a dictionary"
    assert "factor" in priority_factor, "Priority factor should have a factor name"
    assert "weight" in priority_factor, "Priority factor should have a weight"
    assert isinstance(priority_factor["weight"], (int, float)), \
        "Priority factor weight should be numeric"
    assert 0 <= priority_factor["weight"] <= 1, \
        "Priority factor weight should be between 0 and 1"

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
    
    # Verify confidence is a valid number
    assert isinstance(confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify confidence calculation is reasonable
    # Given high confidence tasks and well-structured dependencies,
    # confidence should be above threshold but not maximum
    assert confidence >= 0.5, \
        f"Confidence {confidence} should be >= 0.5 given strong input values"
    assert confidence < 1.0, \
        f"Confidence {confidence} should be < 1.0 with mixed priorities"
    
    # Test with empty inputs
    empty_confidence = task_agent._calculate_confidence([], {})
    assert isinstance(empty_confidence, (int, float)), \
        "Empty confidence should be numeric"
    assert 0 <= empty_confidence <= 1, \
        "Empty confidence should be between 0 and 1"
    assert empty_confidence < confidence, \
        "Empty input should result in lower confidence than valid input"
    
    # Test with low confidence tasks
    low_tasks = [
        {"confidence": 0.3, "priority": 0.3},
        {"confidence": 0.2, "priority": 0.2}
    ]
    low_confidence = task_agent._calculate_confidence(low_tasks, dependencies)
    assert isinstance(low_confidence, (int, float)), \
        "Low confidence should be numeric"
    assert 0 <= low_confidence <= 1, \
        "Low confidence should be between 0 and 1"
    assert low_confidence < confidence, \
        "Low confidence tasks should result in lower overall confidence"
    
    # Test with fewer dependencies
    simple_deps = {
        "sequential": ["task1"],
        "domain_factors": {"factor1": "value1"}
    }
    simple_confidence = task_agent._calculate_confidence(tasks, simple_deps)
    assert isinstance(simple_confidence, (int, float)), \
        "Simple confidence should be numeric"
    assert 0 <= simple_confidence <= 1, \
        "Simple confidence should be between 0 and 1"
    assert simple_confidence < confidence, \
        "Fewer dependencies should result in lower confidence"

@pytest.mark.asyncio
async def test_error_handling(task_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    task_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await task_agent.analyze_tasks({"content": "test"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, TaskResult), "Result should be a TaskResult instance"
    
    # Verify error state
    assert result.confidence == 0.0, "Confidence should be 0.0 when error occurs"
    assert len(result.tasks) == 0, "Should have no tasks when error occurs"
    
    # Verify error metadata
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "error" in result.metadata, "Metadata should contain error information"
    assert isinstance(result.metadata["error"], str), "Error should be a string message"
    assert "Test error" in result.metadata["error"], \
        "Error message should contain original error text"
    
    # Verify error dependencies
    assert isinstance(result.dependencies, dict), "Dependencies should be a dictionary"
    assert "error" in result.dependencies, "Dependencies should contain error information"
    assert isinstance(result.dependencies["error"], str), "Error should be a string message"
    assert "Test error" in result.dependencies["error"], \
        "Error message should contain original error text"

@pytest.mark.asyncio
async def test_domain_awareness(task_agent):
    """Test domain awareness in analysis."""
    content = {"content": "test"}
    
    # Test initial domain
    result = await task_agent.analyze_tasks(content)
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional' initially"
    
    # Test domain change
    task_agent.domain = "personal"
    result = await task_agent.analyze_tasks(content)
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "personal", \
        "Domain should update to 'personal' after change"
    
    # Verify domain affects analysis
    assert isinstance(result.tasks, list), "Result should have tasks list"
    assert isinstance(result.dependencies, dict), "Result should have dependencies dictionary"
    assert result.dependencies is not None, "Dependencies should not be null after domain change"

if __name__ == "__main__":
    pytest.main([__file__])
