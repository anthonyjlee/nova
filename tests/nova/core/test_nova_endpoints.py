"""Tests for Nova endpoints."""

import pytest
import logging
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime
from pathlib import Path

# Configure logging
LOGS_DIR = Path("logs/tests")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / f"test_nova_endpoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Configure logger - file only, no console output
logger = logging.getLogger("test-nova-endpoints")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.propagate = False  # Prevent propagation to root logger

from nia.nova.core.nova_endpoints import nova_router

@pytest.fixture(scope="module")
def app():
    """Test app fixture."""
    logger.info("Setting up test app")
    app = FastAPI()
    app.include_router(nova_router)
    return app

@pytest.fixture(scope="module")
def test_client(app):
    """Test client fixture."""
    logger.info("Setting up test client")
    with TestClient(app) as client:
        yield client
    logger.info("Cleaning up test client")

def test_initial_processing(test_client):
    """Test initial processing phase."""
    logger.info("Testing initial processing phase")
    try:
        response = test_client.post("/api/nova/ask", 
            headers={"X-API-Key": "test-key"},
            json={
            "content": "test query",
            "workspace": "personal"
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
    
    except Exception as e:
        logger.error(f"Error in initial processing test: {str(e)}")
        raise

    logger.info("Verifying initial processing assertions")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    response_data = response.json()
    assert response_data["message"]["content"], "Response should have message content"
    assert response_data["message"]["metadata"], "Response should have metadata"

def test_task_detection(test_client):
    """Test task detection phase."""
    logger.info("Testing task detection phase")
    try:
        response = test_client.post("/api/nova/ask", 
            headers={"X-API-Key": "test-key"},
            json={
            "content": "create a test",
            "workspace": "personal"
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
    
    except Exception as e:
        logger.error(f"Error in task detection test: {str(e)}")
        raise

    logger.info("Verifying task detection assertions")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    response_data = response.json()
    assert response_data["message"]["content"], "Response should have message content"
    assert response_data["message"]["metadata"], "Response should have metadata"

def test_cognitive_processing(test_client):
    """Test cognitive processing phase."""
    logger.info("Testing cognitive processing phase")
    try:
        response = test_client.post("/api/nova/ask", 
            headers={"X-API-Key": "test-key"},
            json={
            "content": "test query",
            "workspace": "personal"
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
    
    except Exception as e:
        logger.error(f"Error in cognitive processing test: {str(e)}")
        raise

    logger.info("Verifying cognitive processing assertions")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    response_data = response.json()
    assert response_data["message"]["content"], "Response should have message content"
    assert response_data["message"]["metadata"], "Response should have metadata"

def test_response_generation(test_client):
    """Test response generation phase."""
    logger.info("Testing response generation phase")
    try:
        response = test_client.post("/api/nova/ask", 
            headers={"X-API-Key": "test-key"},
            json={
            "content": "test query",
            "workspace": "personal"
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
    
    except Exception as e:
        logger.error(f"Error in response generation test: {str(e)}")
        raise

    logger.info("Verifying response generation assertions")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    response_data = response.json()
    assert response_data["message"]["content"], "Response should have message content"
    assert response_data["message"]["metadata"], "Response should have metadata"

def test_schema_validation_failure(test_client):
    """Test handling of schema validation failure."""
    logger.info("Testing schema validation failure")
    try:
        # Test with invalid workspace
        response = test_client.post("/api/nova/ask", 
            headers={"X-API-Key": "test-key"},
            json={
            "content": "test query",
            "workspace": "invalid"  # Invalid workspace value
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
    
    except Exception as e:
        logger.error(f"Error in schema validation failure test: {str(e)}")
        raise

    logger.info("Verifying schema validation failure assertions")
    assert response.status_code == 422, f"Expected status code 422, got {response.status_code}"
    response_data = response.json()
    assert "detail" in response_data, "Response should have validation error details"

def test_memory_storage(test_client):
    """Test memory storage operations."""
    logger.info("Testing memory storage operations")
    try:
        response = test_client.post("/api/nova/ask", 
            headers={"X-API-Key": "test-key"},
            json={
            "content": "test query",
            "workspace": "personal"
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
    
    except Exception as e:
        logger.error(f"Error in memory storage test: {str(e)}")
        raise

    logger.info("Verifying memory storage assertions")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    response_data = response.json()
    assert response_data["message"]["content"], "Response should have message content"
    assert response_data["message"]["metadata"], "Response should have metadata"

def test_concurrent_initialization(test_client):
    """Test concurrent agent initialization safety."""
    logger.info("Testing concurrent initialization")
    try:
        # Make multiple concurrent requests to test initialization safety
        import asyncio
        import aiohttp
        
        async def make_request():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://testserver/api/nova/ask",
                    headers={"X-API-Key": "test-key"},
                    json={
                        "content": "test concurrent init",
                        "workspace": "personal"
                    }
                ) as response:
                    return await response.json()
        
        # Run multiple requests concurrently
        responses = asyncio.run(asyncio.gather(*[make_request() for _ in range(5)]))
        
        logger.debug(f"Concurrent responses: {responses}")
        
        # Verify all requests succeeded
        for response in responses:
            assert response["message"]["content"], "All concurrent requests should succeed"
            assert response["message"]["metadata"], "All responses should have metadata"
            
    except Exception as e:
        logger.error(f"Error in concurrent initialization test: {str(e)}")
        raise

def test_initialization_order(test_client):
    """Test agent initialization order."""
    logger.info("Testing initialization order")
    try:
        # Request that requires multiple agent initializations
        response = test_client.post("/api/nova/ask", 
            headers={"X-API-Key": "test-key"},
            json={
            "content": "complex task requiring multiple agents",
            "workspace": "personal",
            "debug_flags": {
                "trace_initialization": True  # Enable initialization tracing
            }
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
        
        # Verify initialization order from metadata
        metadata = response.json()["message"]["metadata"]
        init_sequence = metadata.get("initialization_sequence", [])
        
        # Memory system should initialize first
        assert init_sequence[0]["component"] == "memory_system", "Memory system should initialize first"
        
        # Base agents should initialize before specialized
        base_indices = [i for i, x in enumerate(init_sequence) if "base" in x["component"]]
        specialized_indices = [i for i, x in enumerate(init_sequence) if "specialized" in x["component"]]
        assert all(b < s for b in base_indices for s in specialized_indices), "Base should initialize before specialized"
        
    except Exception as e:
        logger.error(f"Error in initialization order test: {str(e)}")
        raise

def test_initialization_error_handling(test_client):
    """Test error handling during initialization."""
    logger.info("Testing initialization error handling")
    try:
        # Request with simulated initialization errors
        response = test_client.post("/api/nova/ask", 
            headers={"X-API-Key": "test-key"},
            json={
            "content": "test initialization errors",
            "workspace": "personal",
            "debug_flags": {
                "simulate_errors": {
                    "memory_system": True,  # Simulate memory system error
                    "belief_agent": True    # Simulate belief agent error
                }
            }
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
        
        # Should return 500 with error details
        assert response.status_code == 500, "Should return 500 on initialization error"
        error_data = response.json()
        assert "error" in error_data, "Should include error details"
        assert "initialization_errors" in error_data, "Should list initialization errors"
        
        # Verify error recovery
        recovery_response = test_client.post("/api/nova/ask", 
            headers={"X-API-Key": "test-key"},
            json={
            "content": "test recovery",
            "workspace": "personal"
        })
        assert recovery_response.status_code == 200, "Should recover after initialization errors"
        
    except Exception as e:
        logger.error(f"Error in initialization error handling test: {str(e)}")
        raise

def test_cross_agent_initialization(test_client):
    """Test initialization across multiple interdependent agents."""
    logger.info("Testing cross-agent initialization")
    try:
        # Request requiring complex agent interactions
        response = test_client.post("/api/nova/ask", 
            headers={"X-API-Key": "test-key"},
            json={
            "content": "task requiring agent cooperation",
            "workspace": "personal",
            "debug_flags": {
                "trace_dependencies": True  # Enable dependency tracing
            }
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
        
        # Verify dependency resolution
        metadata = response.json()["message"]["metadata"]
        dependencies = metadata.get("agent_dependencies", {})
        
        # Check dependency resolution order
        for agent, deps in dependencies.items():
            for dep in deps:
                assert dep in metadata.get("initialization_sequence", []), f"Dependency {dep} should initialize before {agent}"
        
        # Verify no circular dependencies
        def has_cycle(graph, node, visited, rec_stack):
            visited[node] = True
            rec_stack[node] = True
            for neighbor in graph.get(node, []):
                if not visited.get(neighbor, False):
                    if has_cycle(graph, neighbor, visited, rec_stack):
                        return True
                elif rec_stack[neighbor]:
                    return True
            rec_stack[node] = False
            return False
            
        visited = {}
        rec_stack = {}
        for agent in dependencies:
            if not visited.get(agent, False):
                if has_cycle(dependencies, agent, visited, rec_stack):
                    assert False, "Circular dependencies detected"
        
    except Exception as e:
        logger.error(f"Error in cross-agent initialization test: {str(e)}")
        raise
