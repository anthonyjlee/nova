"""Tests for FastAPI error handlers."""

import pytest
from fastapi import FastAPI, Request, status
from fastapi.testclient import TestClient
from datetime import datetime
from uuid import UUID

from nia.nova.core.error_handlers import (
    ErrorLogger,
    validation_exception_handler,
    nova_exception_handler,
    http_exception_handler,
    general_exception_handler,
    RequestContextMiddleware,
    ResponseHeaderMiddleware,
    configure_error_handlers
)
from nia.nova.core.error_handling import (
    NovaError,
    ValidationError,
    ResourceNotFoundError,
    ServiceError
)

@pytest.fixture
def test_app():
    """Create test FastAPI app."""
    app = FastAPI()
    configure_error_handlers(app)
    
    @app.get("/test/validation")
    async def test_validation(required_param: str):
        """Test validation error."""
        return {"message": "Success"}
    
    @app.get("/test/nova-error")
    async def test_nova_error():
        """Test Nova error."""
        raise NovaError("Test Nova error")
    
    @app.get("/test/validation-error")
    async def test_validation_error():
        """Test validation error."""
        raise ValidationError("Test validation error")
    
    @app.get("/test/not-found")
    async def test_not_found():
        """Test resource not found error."""
        raise ResourceNotFoundError("Test resource not found")
    
    @app.get("/test/service-error")
    async def test_service_error():
        """Test service error."""
        raise ServiceError("Test service error")
    
    @app.get("/test/http-error")
    async def test_http_error():
        """Test HTTP error."""
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test HTTP error"
        )
    
    @app.get("/test/general-error")
    async def test_general_error():
        """Test general error."""
        raise Exception("Test general error")
    
    return app

@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)

def test_error_logger():
    """Test error logger functionality."""
    # Create mock request
    request = Request({"type": "http", "method": "GET", "url": "http://test"})
    
    # Test log_error
    error = Exception("Test error")
    ErrorLogger.log_error(
        error=error,
        request=request,
        status_code=500,
        error_code="TEST_ERROR"
    )
    
    # Test format_error_response
    response = ErrorLogger.format_error_response(
        error_code="TEST_ERROR",
        message="Test error message",
        details={"test": "detail"},
        request_id="test-id"
    )
    
    assert response["error"]["code"] == "TEST_ERROR"
    assert response["error"]["message"] == "Test error message"
    assert response["error"]["details"] == {"test": "detail"}
    assert response["error"]["request_id"] == "test-id"
    assert "timestamp" in response["error"]

def test_validation_error(client):
    """Test validation error handling."""
    response = client.get("/test/validation")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "validation_errors" in data["error"]["details"]
    assert "timestamp" in data["error"]
    assert "request_id" in data["error"]

def test_nova_error(client):
    """Test Nova error handling."""
    response = client.get("/test/nova-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    data = response.json()
    assert data["error"]["code"] == "NOVAERROR"
    assert data["error"]["message"] == "Test Nova error"
    assert "timestamp" in data["error"]
    assert "request_id" in data["error"]

def test_validation_error_handler(client):
    """Test validation error handler."""
    response = client.get("/test/validation-error")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    data = response.json()
    assert data["error"]["code"] == "VALIDATIONERROR"
    assert data["error"]["message"] == "Test validation error"
    assert "timestamp" in data["error"]
    assert "request_id" in data["error"]

def test_not_found_error(client):
    """Test resource not found error handling."""
    response = client.get("/test/not-found")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    data = response.json()
    assert data["error"]["code"] == "RESOURCENOTFOUNDERROR"
    assert data["error"]["message"] == "Test resource not found"
    assert "timestamp" in data["error"]
    assert "request_id" in data["error"]

def test_service_error(client):
    """Test service error handling."""
    response = client.get("/test/service-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    data = response.json()
    assert data["error"]["code"] == "SERVICEERROR"
    assert data["error"]["message"] == "Test service error"
    assert "timestamp" in data["error"]
    assert "request_id" in data["error"]

def test_http_error(client):
    """Test HTTP error handling."""
    response = client.get("/test/http-error")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    data = response.json()
    assert data["error"]["code"] == "HTTP_ERROR"
    assert data["error"]["message"] == "Test HTTP error"
    assert "timestamp" in data["error"]
    assert "request_id" in data["error"]

def test_general_error(client):
    """Test general error handling."""
    response = client.get("/test/general-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    data = response.json()
    assert data["error"]["code"] == "INTERNAL_ERROR"
    assert data["error"]["message"] == "An unexpected error occurred"
    assert data["error"]["details"]["error_type"] == "Exception"
    assert "timestamp" in data["error"]
    assert "request_id" in data["error"]

def test_request_context_middleware(client):
    """Test request context middleware."""
    response = client.get("/test/validation")
    
    # Check request ID header
    assert "x-request-id" in response.headers
    request_id = response.headers["x-request-id"]
    
    # Verify UUID format
    UUID(request_id)
    
    # Check process time header
    assert "x-process-time" in response.headers
    process_time = float(response.headers["x-process-time"])
    assert process_time >= 0

def test_response_header_middleware(client):
    """Test response header middleware."""
    response = client.get("/test/validation")
    
    # Check custom headers
    assert "x-request-id" in response.headers
    assert "x-process-time" in response.headers
    
    # Verify header values
    request_id = response.headers["x-request-id"]
    process_time = float(response.headers["x-process-time"])
    
    assert len(request_id) > 0
    assert process_time >= 0

def test_error_response_format(client):
    """Test error response format consistency."""
    endpoints = [
        "/test/validation",
        "/test/nova-error",
        "/test/validation-error",
        "/test/not-found",
        "/test/service-error",
        "/test/http-error",
        "/test/general-error"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        data = response.json()
        
        # Check error structure
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "details" in data["error"]
        assert "request_id" in data["error"]
        assert "timestamp" in data["error"]
        
        # Validate timestamp format
        timestamp = datetime.fromisoformat(data["error"]["timestamp"])
        assert isinstance(timestamp, datetime)
        
        # Validate request ID format
        request_id = data["error"]["request_id"]
        UUID(request_id)
