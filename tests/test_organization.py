"""Integration tests for the Organization workspace mock API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import mock_auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_auth_store() -> None:
    mock_auth_service.reset()


def _headers(email: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_organization_workspace_reads_its_learning_snapshot_only() -> None:
    organization_headers = _headers("organization@skillsync.local")

    snapshot_response = client.get("/api/organization", headers=organization_headers)
    assert snapshot_response.status_code == 200
    snapshot = snapshot_response.json()["data"]
    assert snapshot["organization"]["name"] == "SkillSync Demo Organization"
    assert len(snapshot["courses"]) == 5
    assert len(snapshot["learners"]) == 6
    assert snapshot["skills"][0]["coverage"] == "strong"

    course_response = client.get(
        "/api/organization/courses/digital-marketing-foundations",
        headers=organization_headers,
    )
    assert course_response.status_code == 200
    assert course_response.json()["data"]["analytics"]["completion_rate"] == 72

    learner_response = client.get(
        "/api/organization/learners/learner-maya-chen",
        headers=organization_headers,
    )
    assert learner_response.status_code == 200
    assert learner_response.json()["data"]["verified_skills"] == [
        "Customer Journey",
        "Marketing Fundamentals",
        "Channel Strategy",
    ]


def test_non_organization_workspace_cannot_read_organization_data() -> None:
    response = client.get("/api/organization", headers=_headers("creator@skillsync.local"))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
