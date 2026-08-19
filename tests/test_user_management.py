"""Integration coverage for the protected mock Admin user-management API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import mock_auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_auth_store() -> None:
    """Keep account changes made by one test out of another test."""
    mock_auth_service.reset()


def _headers(email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_only_an_admin_can_list_and_manage_accounts() -> None:
    learner_headers = _headers("demo@skillsync.local")
    admin_headers = _headers("admin@skillsync.local")

    forbidden_response = client.get("/api/users", headers=learner_headers)
    assert forbidden_response.status_code == 403

    list_response = client.get("/api/users", headers=admin_headers)
    assert list_response.status_code == 200
    learner = next(user for user in list_response.json()["data"] if user["id"] == 1)
    assert learner["roles"] == ["LEARNER"]
    assert learner["is_active"] is True

    roles_response = client.put(
        "/api/users/1/roles",
        headers=admin_headers,
        json={"roles": ["LEARNER", "CREATOR"]},
    )
    assert roles_response.status_code == 200
    assert roles_response.json()["data"]["roles"] == ["LEARNER", "CREATOR"]

    suspend_response = client.patch(
        "/api/users/1/status",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert suspend_response.status_code == 200
    assert suspend_response.json()["data"]["is_active"] is False

    # Suspending an account invalidates the token it already held.
    assert client.get("/api/users/me", headers=learner_headers).status_code == 401

    reactivate_response = client.patch(
        "/api/users/1/status",
        headers=admin_headers,
        json={"is_active": True},
    )
    assert reactivate_response.status_code == 200
    assert reactivate_response.json()["data"]["is_active"] is True
