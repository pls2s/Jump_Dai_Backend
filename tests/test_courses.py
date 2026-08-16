"""Integration tests for the temporary course-management flow."""

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


def _course_payload() -> dict[str, str]:
    return {
        "title": "ER Diagram Fundamentals",
        "description": "Learn the core concepts of entity relationship diagrams.",
        "goal": "Create a correct ER diagram from a short requirements brief.",
        "difficulty_level": "INTERMEDIATE",
        "certification_enabled": True,
    }


def test_creator_can_create_list_update_and_delete_a_course() -> None:
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
    assert created["certification_enabled"] is True

    list_response = client.get("/api/courses", headers=headers)
    assert list_response.status_code == 200
    assert [course["id"] for course in list_response.json()["data"]] == [created["id"]]

    detail_response = client.get(f"/api/courses/{created['id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["title"] == _course_payload()["title"]

    update_response = client.put(
        f"/api/courses/{created['id']}",
        headers=headers,
        json={"title": "Updated ER Diagram Fundamentals"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["title"] == "Updated ER Diagram Fundamentals"

    delete_response = client.delete(f"/api/courses/{created['id']}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json() == {"success": True}

    missing_response = client.get(f"/api/courses/{created['id']}", headers=headers)
    assert missing_response.status_code == 404
    assert missing_response.json()["error"]["code"] == "COURSE_NOT_FOUND"


def test_course_routes_require_bearer_authentication() -> None:
    response = client.get("/api/courses")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_learner_cannot_manage_courses() -> None:
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
        json={"title": "", "description": "", "goal": ""},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
