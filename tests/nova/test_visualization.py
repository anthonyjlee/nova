"""Tests for Nova's visualization functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.visualization import VisualizationAgent, VisualizationResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "visualization": {
            "type": "chart",
            "visualization": {
                "main": {
                    "type": "bar",
                    "data": {
                        "labels": ["A", "B", "C"],
                        "values": [1, 2, 3]
                    },
                    "style": {
                        "color": "blue",
                        "width": 800
                    },
                    "description": "Main chart",
                    "layout": {
                        "position": "center",
                        "size": "large"
                    }
                },
                "sub": {
                    "type": "line",
                    "data": {
                        "x": [1, 2, 3],
                        "y": [4, 5, 6]
                    },
                    "style": {
                        "color": "red",
                        "width": 400
                    },
                    "metadata": {
                        "key": "value"
                    }
                }
            },
            "metadata": {
                "version": "1.0"
            }
        },
        "elements": [
            {
                "type": "chart",
                "description": "Chart analysis",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "layout": {
                    "position": "center",
                    "size": "large"
                }
            }
        ],
        "issues": [
            {
                "type": "missing_legend",
                "severity": "medium",
                "description": "Missing legend",
                "domain_impact": 0.3,
                "suggested_fix": "Add legend",
                "layout": {
                    "position": "right",
                    "size": "medium"
                }
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
            "content": {"content": "Similar visualization"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def visualization_agent(mock_llm, mock_vector_store):
    """Create a VisualizationAgent instance with mock dependencies."""
    return VisualizationAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_visualization_with_llm(visualization_agent, mock_llm):
    """Test visualization processing using LLM."""
    content = {
        "content": "Test content",
        "type": "chart",
        "metadata": {"key": "value"}
    }
    
    result = await visualization_agent.process_visualization(content, "chart")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, VisualizationResult)
    assert result.visualization["type"] == "chart"
    assert len(result.visualization["visualization"]) == 2
    assert len(result.elements) == 1
    assert len(result.issues) == 1
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert "domain" in result.metadata

@pytest.mark.asyncio
async def test_process_visualization_without_llm():
    """Test visualization processing without LLM (fallback mode)."""
    agent = VisualizationAgent()  # No LLM provided
    content = {
        "data": ["data1"],
        "axes": {"x": [], "y": []},
        "labels": {}
    }
    
    result = await agent.process_visualization(content, "chart")
    
    # Verify basic visualization worked
    assert isinstance(result, VisualizationResult)
    assert result.visualization["type"] == "chart"
    assert "visualization" in result.visualization
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert result.is_valid is True  # All basic checks should pass

@pytest.mark.asyncio
async def test_get_similar_visualization(visualization_agent, mock_vector_store):
    """Test similar visualization retrieval."""
    content = {"content": "test content"}
    visualization_type = "chart"
    
    visualization = await visualization_agent._get_similar_visualization(content, visualization_type)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "visualization",
            "visualization_type": "chart"
        }
    )
    assert len(visualization) == 1
    assert "content" in visualization[0]
    assert visualization[0]["similarity"] == 0.9

def test_basic_visualization_chart(visualization_agent):
    """Test basic chart visualization."""
    content = {
        "data": ["data1"],
        "axes": {"x": [], "y": []},
        "labels": {}
    }
    
    result = visualization_agent._basic_visualization(content, "chart", [])
    
    assert "visualization" in result
    assert "elements" in result
    assert "issues" in result
    assert result["visualization"]["type"] == "chart"
    assert len(result["elements"]) > 0
    assert all(e["type"] in ["has_data", "has_axes", "has_labels"] for e in result["elements"])

def test_basic_visualization_graph(visualization_agent):
    """Test basic graph visualization."""
    content = {
        "nodes": {"node1": []},
        "edges": {"edge1": []},
        "layout": {}
    }
    
    result = visualization_agent._basic_visualization(content, "graph", [])
    
    assert "visualization" in result
    assert "elements" in result
    assert "issues" in result
    assert result["visualization"]["type"] == "graph"
    assert len(result["elements"]) > 0
    assert all(e["type"] in ["has_nodes", "has_edges", "has_layout"] for e in result["elements"])

def test_check_rule(visualization_agent):
    """Test visualization rule checking."""
    content = {
        "data": ["data1"],
        "axes": {"x": [], "y": []},
        "labels": {},
        "nodes": {"node1": []},
        "edges": {"edge1": []},
        "layout": {},
        "shapes": {"shape1": []},
        "connections": {"conn1": []},
        "annotations": {}
    }
    
    # Test chart rules
    assert visualization_agent._check_rule("has_data", content) is True
    assert visualization_agent._check_rule("has_axes", content) is True
    assert visualization_agent._check_rule("has_labels", content) is True
    
    # Test graph rules
    assert visualization_agent._check_rule("has_nodes", content) is True
    assert visualization_agent._check_rule("has_edges", content) is True
    assert visualization_agent._check_rule("has_layout", content) is True
    
    # Test diagram rules
    assert visualization_agent._check_rule("has_shapes", content) is True
    assert visualization_agent._check_rule("has_connections", content) is True
    assert visualization_agent._check_rule("has_annotations", content) is True

def test_extract_visualization(visualization_agent):
    """Test visualization extraction and validation."""
    visualization = {
        "visualization": {
            "type": "chart",
            "visualization": {
                "main": {
                    "type": "bar",
                    "data": {"values": [1, 2, 3]},
                    "style": {"color": "blue"},
                    "description": "Main chart"
                },
                "sub": {
                    "type": "line",
                    "data": {"values": [4, 5, 6]},
                    "style": {"color": "red"}
                }
            },
            "metadata": {
                "version": "1.0"
            }
        }
    }
    
    result = visualization_agent._extract_visualization(visualization)
    
    assert result["type"] == "chart"
    assert len(result["visualization"]) == 2
    assert result["visualization"]["main"]["type"] == "bar"
    assert "description" in result["visualization"]["main"]
    assert "metadata" in result
    assert "style" in result["visualization"]["sub"]

def test_extract_elements(visualization_agent):
    """Test element extraction and validation."""
    visualization = {
        "elements": [
            {
                "type": "chart",
                "description": "Test element",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "layout": {
                    "position": "center",
                    "size": "large"
                }
            },
            {
                "type": "basic",
                "description": "Basic element",
                "confidence": 0.6
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    elements = visualization_agent._extract_elements(visualization)
    
    assert len(elements) == 2  # Invalid one should be filtered out
    assert all("type" in e for e in elements)
    assert all("description" in e for e in elements)
    assert all("confidence" in e for e in elements)
    assert all(isinstance(e["confidence"], (int, float)) for e in elements)
    assert all(0 <= e["confidence"] <= 1 for e in elements)
    assert any("domain_relevance" in e for e in elements)

def test_extract_issues(visualization_agent):
    """Test issue extraction and validation."""
    visualization = {
        "issues": [
            {
                "type": "missing_legend",
                "severity": "high",
                "description": "Missing legend",
                "details": "Details",
                "domain_impact": 0.8,
                "suggested_fix": "Add legend",
                "layout": {
                    "position": "right",
                    "size": "medium"
                }
            },
            {
                "type": "basic_issue",
                "description": "Basic"
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    issues = visualization_agent._extract_issues(visualization)
    
    assert len(issues) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in issues)
    assert all("severity" in i for i in issues)
    assert all("description" in i for i in issues)
    assert any("domain_impact" in i for i in issues)

def test_calculate_confidence(visualization_agent):
    """Test confidence calculation."""
    visualization = {
        "visualization": {
            "main": {"type": "chart"},
            "sub": {"type": "graph"}
        },
        "metadata": {
            "version": "1.0",
            "environment": "test"
        }
    }
    
    elements = [
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
    
    confidence = visualization_agent._calculate_confidence(visualization, elements, issues)
    
    assert isinstance(confidence, (int, float))
    assert 0 <= confidence <= 1
    # Should include:
    # - Visualization confidence (0.2 from visualization + metadata)
    # - Element confidence (0.7 average)
    # - Issue impact (0.2 from low + medium severity)
    assert 0.45 <= confidence <= 0.55

def test_determine_validity(visualization_agent):
    """Test validity determination."""
    visualization = {
        "visualization": {
            "main": {"type": "chart"}
        },
        "metadata": {
            "version": "1.0"
        }
    }
    
    elements = [
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
    
    is_valid = visualization_agent._determine_validity(visualization, elements, issues, 0.7)
    assert is_valid is True  # High confidence, mostly passed elements
    
    # Test with critical issue
    issues.append({
        "severity": "high",
        "type": "critical"
    })
    
    is_valid = visualization_agent._determine_validity(visualization, elements, issues, 0.7)
    assert is_valid is False  # Critical issue should fail validation

@pytest.mark.asyncio
async def test_error_handling(visualization_agent):
    """Test error handling during visualization processing."""
    # Make LLM raise an error
    visualization_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await visualization_agent.process_visualization({"content": "test"}, "chart")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, VisualizationResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.elements) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_awareness(visualization_agent):
    """Test domain awareness in visualization processing."""
    content = {"content": "test"}
    result = await visualization_agent.process_visualization(content, "chart")
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    visualization_agent.domain = "personal"
    result = await visualization_agent.process_visualization(content, "chart")
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
