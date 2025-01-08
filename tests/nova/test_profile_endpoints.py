"""Tests for profile management endpoints."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from nia.core.profiles.profile_types import (
    UserProfile,
    ProfileUpdate,
    BigFiveTraits,
    LearningStyle,
    CommunicationPreferences,
    AutoApprovalSettings,
    ApprovalThresholds
)
from nia.nova.endpoints.profile_endpoints import router
from nia.core.profiles.profile_manager import ProfileManager
from nia.nova.core.dependencies import get_profile_manager

app = FastAPI()
app.include_router(router)

@pytest.fixture
def mock_profile_manager():
    """Create mock profile manager."""
    return AsyncMock(spec=ProfileManager)

@pytest.fixture
def sample_profile_data():
    """Create sample profile data."""
    return {
        "profile_id": "test_user",
        "personality": {
            "openness": 0.8,
            "conscientiousness": 0.7,
            "extraversion": 0.6,
            "agreeableness": 0.9,
            "neuroticism": 0.3
        },
        "learning_style": {
            "visual": 0.8,
            "auditory": 0.4,
            "kinesthetic": 0.6
        },
        "communication": {
            "direct": 0.7,
            "detailed": 0.8,
            "formal": 0.4
        },
        "auto_approval": {
            "auto_approve_domains": ["professional"],
            "approval_thresholds": {
                "task_creation": 0.8,
                "resource_access": 0.9,
                "domain_crossing": 0.95
            },
            "restricted_operations": ["delete", "modify_personal"]
        },
        "domains": {
            "professional": {"confidence": 1.0},
            "personal": {"confidence": 1.0}
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

@pytest.fixture
def client(mock_profile_manager):
    """Create test client."""
    app.dependency_overrides[get_profile_manager] = lambda: mock_profile_manager
    return TestClient(app)

class TestProfileEndpoints:
    """Test profile management endpoints."""

    def test_create_profile(self, client, mock_profile_manager, sample_profile_data):
        """Test profile creation endpoint."""
        mock_profile_manager.create_profile = AsyncMock(return_value=UserProfile(**sample_profile_data))

        response = client.post("/api/profiles/", json=sample_profile_data)

        assert response.status_code == 200
        assert response.json()["profile_id"] == sample_profile_data["profile_id"]

    def test_create_profile_invalid_data(self, client, mock_profile_manager):
        """Test profile creation with invalid data."""
        invalid_data = {
            "profile_id": "test_user",
            "personality": {
                "openness": 1.5,  # Invalid: > 1.0
                "conscientiousness": 0.7,
                "extraversion": 0.6,
                "agreeableness": 0.9,
                "neuroticism": 0.3
            },
            "learning_style": {
                "visual": 0.8,
                "auditory": 0.4,
                "kinesthetic": 0.6
            },
            "communication": {
                "direct": 0.7,
                "detailed": 0.8,
                "formal": 0.4
            },
            "auto_approval": {
                "auto_approve_domains": ["professional"],
                "approval_thresholds": {
                    "task_creation": 0.8,
                    "resource_access": 0.9,
                    "domain_crossing": 0.95
                },
                "restricted_operations": ["delete", "modify_personal"]
            }
        }

        response = client.post("/api/profiles/", json=invalid_data)
        assert response.status_code == 422

    def test_create_profile_missing_fields(self, client, mock_profile_manager):
        """Test profile creation with missing required fields."""
        incomplete_data = {
            "profile_id": "test_user",
            "personality": {
                "openness": 0.8,
                "conscientiousness": 0.7,
                # Missing extraversion
                "agreeableness": 0.9,
                "neuroticism": 0.3
            }
        }

        response = client.post("/api/profiles/", json=incomplete_data)
        assert response.status_code == 422

    def test_get_profile(self, client, mock_profile_manager, sample_profile_data):
        """Test profile retrieval endpoint."""
        mock_profile_manager.get_profile = AsyncMock(return_value=UserProfile(**sample_profile_data))

        response = client.get(f"/api/profiles/{sample_profile_data['profile_id']}")

        assert response.status_code == 200
        assert response.json()["profile_id"] == sample_profile_data["profile_id"]

    def test_get_profile_not_found(self, client, mock_profile_manager):
        """Test profile retrieval when profile doesn't exist."""
        mock_profile_manager.get_profile = AsyncMock(return_value=None)

        response = client.get("/api/profiles/nonexistent")
        assert response.status_code == 404

    def test_update_profile(self, client, mock_profile_manager, sample_profile_data):
        """Test profile update endpoint."""
        update_data = {
            "profile_id": sample_profile_data["profile_id"],
            "communication": {
                "direct": 0.9,
                "detailed": 0.7,
                "formal": 0.8
            }
        }
        updated_data = sample_profile_data.copy()
        updated_data["communication"] = update_data["communication"]
        mock_profile_manager.update_profile = AsyncMock(return_value=UserProfile(**updated_data))

        response = client.put(
            f"/api/profiles/{sample_profile_data['profile_id']}",
            json=update_data
        )

        assert response.status_code == 200
        assert response.json()["communication"] == update_data["communication"]

    def test_update_profile_partial(self, client, mock_profile_manager, sample_profile_data):
        """Test partial profile update."""
        update_data = {
            "profile_id": sample_profile_data["profile_id"],
            "communication": {
                "direct": 0.9,
                "detailed": 0.7,
                "formal": 0.8
            }
        }
        updated_data = sample_profile_data.copy()
        updated_data["communication"] = update_data["communication"]
        mock_profile_manager.update_profile = AsyncMock(return_value=UserProfile(**updated_data))

        response = client.put(
            f"/api/profiles/{sample_profile_data['profile_id']}",
            json=update_data
        )

        assert response.status_code == 200
        assert response.json()["communication"] == update_data["communication"]
        assert "personality" in response.json()  # Original fields preserved

    def test_update_profile_not_found(self, client, mock_profile_manager):
        """Test profile update when profile doesn't exist."""
        mock_profile_manager.update_profile = AsyncMock(return_value=None)

        response = client.put(
            "/api/profiles/nonexistent",
            json={"profile_id": "nonexistent"}
        )
        assert response.status_code == 404

    def test_delete_profile(self, client, mock_profile_manager, sample_profile_data):
        """Test profile deletion endpoint."""
        mock_profile_manager.delete_profile = AsyncMock(return_value=True)

        response = client.delete(f"/api/profiles/{sample_profile_data['profile_id']}")

        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_delete_profile_not_found(self, client, mock_profile_manager):
        """Test profile deletion when profile doesn't exist."""
        mock_profile_manager.delete_profile = AsyncMock(return_value=False)

        response = client.delete("/api/profiles/nonexistent")
        assert response.status_code == 404

    def test_list_profiles(self, client, mock_profile_manager, sample_profile_data):
        """Test profile listing endpoint."""
        mock_profile_manager.list_profiles = AsyncMock(return_value=[UserProfile(**sample_profile_data)])

        response = client.get("/api/profiles/")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["profile_id"] == sample_profile_data["profile_id"]

    def test_list_profiles_by_domain(self, client, mock_profile_manager, sample_profile_data):
        """Test profile listing filtered by domain."""
        mock_profile_manager.list_profiles = AsyncMock(return_value=[UserProfile(**sample_profile_data)])

        response = client.get("/api/profiles/?domain=professional")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert "professional" in response.json()[0]["domains"]

    def test_adapt_task(self, client, mock_profile_manager, sample_profile_data):
        """Test task adaptation endpoint."""
        task = {
            "type": "analysis",
            "complexity": "high"
        }
        adapted_task = {
            **task,
            "granularity": "detailed",
            "visualization_preference": "high"
        }
        mock_profile_manager.adapt_task = AsyncMock(return_value=adapted_task)

        response = client.post(
            f"/api/profiles/{sample_profile_data['profile_id']}/adapt-task",
            json={
                "task": task,
                "domain": "professional"
            }
        )

        assert response.status_code == 200
        assert response.json()["granularity"] == "detailed"

    def test_adapt_task_invalid_domain(self, client, mock_profile_manager, sample_profile_data):
        """Test task adaptation with invalid domain."""
        mock_profile_manager.adapt_task = AsyncMock(side_effect=ValueError("Invalid domain"))

        response = client.post(
            f"/api/profiles/{sample_profile_data['profile_id']}/adapt-task",
            json={
                "task": {"type": "analysis"},
                "domain": "invalid_domain"
            }
        )
        assert response.status_code == 404

    def test_get_domain_confidence(self, client, mock_profile_manager, sample_profile_data):
        """Test domain confidence retrieval endpoint."""
        mock_profile_manager.get_domain_confidence = AsyncMock(return_value=0.8)

        response = client.get(
            f"/api/profiles/{sample_profile_data['profile_id']}/domain-confidence/professional"
        )

        assert response.status_code == 200
        assert response.json()["confidence"] == 0.8

    def test_get_domain_confidence_invalid_domain(self, client, mock_profile_manager):
        """Test domain confidence retrieval with invalid domain."""
        mock_profile_manager.get_domain_confidence = AsyncMock(side_effect=ValueError("Invalid domain"))

        response = client.get("/api/profiles/test_user/domain-confidence/invalid_domain")
        assert response.status_code == 404

    def test_check_operation_approval(self, client, mock_profile_manager, sample_profile_data):
        """Test operation approval check endpoint."""
        mock_profile_manager.check_auto_approval = AsyncMock(return_value=True)

        response = client.post(
            f"/api/profiles/{sample_profile_data['profile_id']}/check-approval",
            json={
                "operation": "task_creation",
                "domain": "professional",
                "confidence": 0.9
            }
        )

        assert response.status_code == 200
        assert response.json()["approved"] is True

    def test_check_operation_approval_invalid_operation(self, client, mock_profile_manager):
        """Test operation approval check with invalid operation."""
        mock_profile_manager.check_auto_approval = AsyncMock(side_effect=ValueError("Invalid operation"))

        response = client.post(
            "/api/profiles/test_user/check-approval",
            json={
                "operation": "invalid_operation",
                "domain": "professional",
                "confidence": 0.9
            }
        )
        assert response.status_code == 404

    def test_update_domain_confidence(self, client, mock_profile_manager, sample_profile_data):
        """Test domain confidence update endpoint."""
        mock_profile_manager.update_domain_confidence = AsyncMock()

        response = client.post(
            f"/api/profiles/{sample_profile_data['profile_id']}/update-confidence",
            json={
                "domain": "professional",
                "confidence": 0.8,
                "operation_success": True
            }
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_update_domain_confidence_invalid_domain(self, client, mock_profile_manager):
        """Test domain confidence update with invalid domain."""
        mock_profile_manager.update_domain_confidence = AsyncMock(side_effect=ValueError("Invalid domain"))

        response = client.post(
            "/api/profiles/test_user/update-confidence",
            json={
                "domain": "invalid_domain",
                "confidence": 0.8,
                "operation_success": True
            }
        )
        assert response.status_code == 404
