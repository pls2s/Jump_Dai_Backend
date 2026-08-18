"""Integration tests for Function 2 course configuration."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import mock_auth_service
from app.services.course_service import mock_course_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_stores() -> None:
    """Keep authentication and course state isolated between test cases."""
    mock_auth_service.reset()
    mock_course_service.reset()


def _login(email: str = "creator@skillsync.local") -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def _course_payload() -> dict[str, object]:
    return {
        "title": "ER Diagram Fundamentals",
        "description": "Learn the core concepts of entity relationship diagrams.",
        "target_learner": "Beginning software-development learners.",
        "difficulty_level": "INTERMEDIATE",
        "learning_objective": "Create a correct ER diagram from a short requirements brief.",
    }


def test_creator_can_create_function_two_course_configuration() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/courses",
        headers=headers,
        json=_course_payload(),
    )

    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["status"] == "DRAFT"
    assert created["creator_id"] == 2
    assert created["difficulty_level"] == "INTERMEDIATE"
    assert created["certificate_available"] is False
    assert created["target_learner"] == _course_payload()["target_learner"]
    assert created["learning_objective"] == _course_payload()["learning_objective"]

    assert client.get("/api/courses", headers=headers).status_code == 405
    assert client.put(f"/api/courses/{created['id']}", headers=headers).status_code == 404
    assert client.delete(f"/api/courses/{created['id']}", headers=headers).status_code == 404


def test_course_routes_require_bearer_authentication() -> None:
    response = client.post("/api/courses", json=_course_payload())

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_learner_cannot_configure_a_knowledge_course() -> None:
    token = _login("demo@skillsync.local")
    response = client.post(
        "/api/courses",
        headers={"Authorization": f"Bearer {token}"},
        json=_course_payload(),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_course_payload_validation_returns_422_envelope() -> None:
    token = _login()
    response = client.post(
        "/api/courses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "",
            "description": "",
            "target_learner": "",
            "learning_objective": "",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_advanced_course_makes_a_certificate_available() -> None:
    token = _login()
    payload = _course_payload() | {"difficulty_level": "ADVANCED"}

    response = client.post(
        "/api/courses",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["data"]["certificate_available"] is True
