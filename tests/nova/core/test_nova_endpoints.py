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
