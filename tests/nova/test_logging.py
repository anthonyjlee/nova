"""Tests for Nova's logging functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.logging import LoggingAgent, LoggingResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "logging": {
            "type": "debug",
            "logs": {
                "main": {
                    "type": "processor",
                    "level": "debug",
                    "message": "Main log",
                    "context": {
                        "function": "process_data",
                        "line": 42
                    }
                },
                "sub": {
                    "type": "helper",
                    "level": "info",
                    "message": "Helper log",
                    "metadata": {
                        "key": "value"
                    }
                }
            },
            "metadata": {
                "version": "1.0"
            }
        },
        "logs": [
            {
                "type": "log",
                "description": "Log analysis",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "context": {"key": "value"}
            }
        ],
        "issues": [
            {
                "type": "missing_context",
                "severity": "medium",
                "description": "Missing context",
                "domain_impact": 0.3,
                "suggested_fix": "Add context",
                "context": {"key": "value"}
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
            "content": {"content": "Similar logging"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def logging_agent(mock_llm, mock_vector_store):
    """Create a LoggingAgent instance with mock dependencies."""
    return LoggingAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_logs_with_llm(logging_agent, mock_llm):
    """Test log processing using LLM."""
    content = {
        "content": "Test content",
        "type": "debug",
        "metadata": {"key": "value"}
    }
    
    result = await logging_agent.process_logs(content, "debug")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, LoggingResult)
    assert result.logging["type"] == "debug"
    assert len(result.logging["logs"]) == 2
    assert len(result.logs) == 1
    assert len(result.issues) == 1
    assert result.confidence > 0
    assert "domain" in result.metadata

@pytest.mark.asyncio
async def test_process_logs_without_llm():
    """Test log processing without LLM (fallback mode)."""
    agent = LoggingAgent()  # No LLM provided
    content = {
        "message": "Test log",
        "level": "debug",
        "context": {"key": "value"}
    }
    
    result = await agent.process_logs(content, "debug")
    
    # Verify basic logging worked
    assert isinstance(result, LoggingResult)
    assert result.logging["type"] == "debug"
    assert "logs" in result.logging
    assert result.confidence >= 0
    assert result.is_valid is True  # All basic checks should pass

@pytest.mark.asyncio
async def test_get_similar_logging(logging_agent, mock_vector_store):
    """Test similar logging retrieval."""
    content = {"content": "test content"}
    logging_type = "debug"
    
    logging = await logging_agent._get_similar_logging(content, logging_type)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "logging",
            "logging_type": "debug"
        }
    )
    assert len(logging) == 1
    assert "content" in logging[0]
    assert logging[0]["similarity"] == 0.9

def test_basic_logging_debug(logging_agent):
    """Test basic debug logging."""
    content = {
        "message": "Test log",
        "level": "debug",
        "context": {"key": "value"}
    }
    
    result = logging_agent._basic_logging(content, "debug", [])
    
    assert "logging" in result
    assert "logs" in result
    assert "issues" in result
    assert result["logging"]["type"] == "debug"
    assert len(result["logs"]) > 0
    assert all(l["type"] in ["has_message", "has_level", "has_context"] for l in result["logs"])

def test_basic_logging_error(logging_agent):
    """Test basic error logging."""
    content = {
        "message": "Test error",
        "stacktrace": "Error details",
        "context": {"key": "value"}
    }
    
    result = logging_agent._basic_logging(content, "error", [])
    
    assert "logging" in result
    assert "logs" in result
    assert "issues" in result
    assert result["logging"]["type"] == "error"
    assert len(result["logs"]) > 0
    assert all(l["type"] in ["has_message", "has_stacktrace", "has_context"] for l in result["logs"])

def test_check_rule(logging_agent):
    """Test logging rule checking."""
    content = {
        "message": "Test log",
        "level": "debug",
        "context": {"key": "value"},
        "metadata": {"version": "1.0"},
        "stacktrace": "Error details"
    }
    
    # Test debug rules
    assert logging_agent._check_rule("has_message", content) is True
    assert logging_agent._check_rule("has_level", content) is True
    assert logging_agent._check_rule("has_context", content) is True
    
    # Test info rules
    assert logging_agent._check_rule("has_message", content) is True
    assert logging_agent._check_rule("has_level", content) is True
    assert logging_agent._check_rule("has_metadata", content) is True
    
    # Test error rules
    assert logging_agent._check_rule("has_message", content) is True
    assert logging_agent._check_rule("has_stacktrace", content) is True
    assert logging_agent._check_rule("has_context", content) is True

def test_extract_logging(logging_agent):
    """Test logging extraction and validation."""
    logging = {
        "logging": {
            "type": "debug",
            "logs": {
                "main": {
                    "type": "processor",
                    "level": "debug",
                    "message": "Main log",
                    "context": {"key": "value"}
                },
                "sub": {
                    "type": "helper",
                    "level": "info",
                    "message": "Helper log"
                }
            },
            "metadata": {
                "version": "1.0"
            }
        }
    }
    
    result = logging_agent._extract_logging(logging)
    
    assert result["type"] == "debug"
    assert len(result["logs"]) == 2
    assert result["logs"]["main"]["level"] == "debug"
    assert "context" in result["logs"]["main"]
    assert "metadata" in result
    assert "message" in result["logs"]["sub"]

def test_extract_logs(logging_agent):
    """Test log extraction and validation."""
    logging = {
        "logs": [
            {
                "type": "log",
                "description": "Test log",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "context": {"key": "value"}
            },
            {
                "type": "basic",
                "description": "Basic log",
                "confidence": 0.6
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    logs = logging_agent._extract_logs(logging)
    
    assert len(logs) == 2  # Invalid one should be filtered out
    assert all("type" in l for l in logs)
    assert all("description" in l for l in logs)
    assert all("confidence" in l for l in logs)
    assert any("domain_relevance" in l for l in logs)

def test_extract_issues(logging_agent):
    """Test issue extraction and validation."""
    logging = {
        "issues": [
            {
                "type": "missing_context",
                "severity": "high",
                "description": "Missing context",
                "details": "Details",
                "domain_impact": 0.8,
                "suggested_fix": "Add context",
                "context": {"key": "value"}
            },
            {
                "type": "basic_issue",
                "description": "Basic"
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    issues = logging_agent._extract_issues(logging)
    
    assert len(issues) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in issues)
    assert all("severity" in i for i in issues)
    assert all("description" in i for i in issues)
    assert any("domain_impact" in i for i in issues)

def test_calculate_confidence(logging_agent):
    """Test confidence calculation."""
    logging = {
        "logs": {
            "main": {"type": "processor"},
            "sub": {"type": "helper"}
        },
        "metadata": {
            "version": "1.0",
            "environment": "test"
        }
    }
    
    logs = [
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
    
    confidence = logging_agent._calculate_confidence(logging, logs, issues)
    
    assert 0 <= confidence <= 1
    # Should include:
    # - Logging confidence (0.2 from logs + metadata)
    # - Log confidence (0.7 average)
    # - Issue impact (0.2 from low + medium severity)
    assert 0.45 <= confidence <= 0.55

def test_determine_validity(logging_agent):
    """Test validity determination."""
    logging = {
        "logs": {
            "main": {"type": "processor"}
        },
        "metadata": {
            "version": "1.0"
        }
    }
    
    logs = [
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
    
    is_valid = logging_agent._determine_validity(logging, logs, issues, 0.7)
    assert is_valid is True  # High confidence, mostly passed logs
    
    # Test with critical issue
    issues.append({
        "severity": "high",
        "type": "critical"
    })
    
    is_valid = logging_agent._determine_validity(logging, logs, issues, 0.7)
    assert is_valid is False  # Critical issue should fail validation

@pytest.mark.asyncio
async def test_error_handling(logging_agent):
    """Test error handling during logging."""
    # Make LLM raise an error
    logging_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await logging_agent.process_logs({"content": "test"}, "debug")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, LoggingResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.logs) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_awareness(logging_agent):
    """Test domain awareness in logging."""
    content = {"content": "test"}
    result = await logging_agent.process_logs(content, "debug")
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    logging_agent.domain = "personal"
    result = await logging_agent.process_logs(content, "debug")
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
