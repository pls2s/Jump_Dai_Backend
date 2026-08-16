"""Integration tests for the temporary user-and-authentication flow."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import mock_auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_auth_store() -> None:
    """Ensure test users and tokens cannot leak between test cases."""
    mock_auth_service.reset()


def test_demo_user_can_sign_in_and_read_own_profile() -> None:
    login_response = client.post(
        "/api/auth/login",
        json={"email": "demo@skillsync.local", "password": "password123"},
    )

    assert login_response.status_code == 200
    login_data = login_response.json()["data"]
    assert login_data["next_step"] == "complete"
    assert login_data["user"]["roles"] == ["LEARNER"]

    profile_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {login_data['access_token']}"},
    )

    assert profile_response.status_code == 200
    assert profile_response.json()["data"]["email"] == "demo@skillsync.local"


@pytest.mark.parametrize(
    ("email", "expected_workspace", "expected_role"),
    [
        ("demo@skillsync.local", "learner", "LEARNER"),
        ("creator@skillsync.local", "creator", "CREATOR"),
        ("organization@skillsync.local", "organization", "CREATOR"),
    ],
)
def test_all_seeded_workspace_demos_can_sign_in(
    email: str,
    expected_workspace: str,
    expected_role: str,
) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )

    assert response.status_code == 200
    user = response.json()["data"]["user"]
    assert user["workspace_type"] == expected_workspace
    assert user["roles"] == [expected_role]


def test_register_verify_and_select_creator_workspace() -> None:
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Peer", "email": "peer@example.com", "password": "password123"},
    )

    assert register_response.status_code == 201
    register_data = register_response.json()["data"]
    assert register_data["next_step"] == "email_verification"
    assert register_data["mock_verification_code"] == "123456"
    assert register_data["user"]["email_verified"] is False

    verification_response = client.post(
        "/api/auth/verify-email",
        json={"email": "peer@example.com", "code": "123456"},
    )

    assert verification_response.status_code == 200
    verification_data = verification_response.json()["data"]
    assert verification_data["next_step"] == "workspace_selection"

    workspace_response = client.post(
        "/api/auth/workspace",
        headers={"Authorization": f"Bearer {verification_data['access_token']}"},
        json={"workspace_type": "creator"},
    )

    assert workspace_response.status_code == 200
    user = workspace_response.json()["data"]["user"]
    assert user["workspace_type"] == "creator"
    assert user["roles"] == ["CREATOR"]
    assert user["onboarding_completed"] is True


def test_register_rejects_duplicate_email_and_invalid_verification_code() -> None:
    payload = {"name": "Peer", "email": "peer@example.com", "password": "password123"}
    client.post("/api/auth/register", json=payload)

    duplicate_response = client.post("/api/auth/register", json=payload)
    invalid_code_response = client.post(
        "/api/auth/verify-email",
        json={"email": "peer@example.com", "code": "999999"},
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"
    assert invalid_code_response.status_code == 400
    assert invalid_code_response.json()["error"]["code"] == "INVALID_VERIFICATION_CODE"


def test_openapi_declares_bearer_security_for_protected_auth_routes() -> None:
    schema = client.get("/openapi.json").json()

    assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
    assert schema["paths"]["/api/auth/workspace"]["post"]["security"] == [{"HTTPBearer": []}]
