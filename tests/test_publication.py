"""Integration tests for Function 6 course publication and public catalog."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import mock_auth_service
from app.services.course_service import mock_course_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_stores() -> None:
    """Keep catalog and authentication state isolated between test cases."""
    mock_auth_service.reset()
    mock_course_service.reset()


def _login(email: str = "creator@skillsync.local") -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def _create_course(headers: dict[str, str]) -> int:
    response = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "ER Diagram Fundamentals",
            "description": "Learn the core concepts of entity relationship diagrams.",
            "target_learner": "Beginning software-development learners.",
            "difficulty_level": "INTERMEDIATE",
            "learning_objective": "Create a correct ER diagram from a requirements brief.",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _mark_waiting_for_verification(course_id: int) -> None:
    """Create a validated Function 4 result without a network model request."""
    mock_course_service.complete_generation(
        course_id=course_id,
        creator_id=2,
        learning_path={
            "course_id": course_id,
            "title": "ER Diagram Fundamentals",
            "overview": "A Creator-reviewable ER diagram learning path.",
            "modules": [
                {
                    "title": "ER diagram basics",
                    "description": "Identify entities and relationships.",
                    "learning_objectives": ["Identify entities."],
                    "lessons": [
                        {
                            "title": "Entities and relationships",
                            "summary": "An ER diagram models entities and their relationships.",
                            "source_references": ["source-1-chunk-1"],
                        }
                    ],
                }
            ],
        },
    )


def test_verified_course_can_be_published_and_read_from_public_catalog() -> None:
    creator_headers = _login()
    course_id = _create_course(creator_headers)

    premature_publish = client.post(
        f"/api/courses/{course_id}/publish",
        headers=creator_headers,
    )
    assert premature_publish.status_code == 409
    assert premature_publish.json()["error"]["code"] == "COURSE_NOT_READY_TO_PUBLISH"

    _mark_waiting_for_verification(course_id)
    verify_response = client.post(
        f"/api/courses/{course_id}/verify",
        headers=creator_headers,
    )
    assert verify_response.status_code == 200

    publish_response = client.post(
        f"/api/courses/{course_id}/publish",
        headers=creator_headers,
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["data"]["status"] == "PUBLISHED"

    catalog_response = client.get("/api/catalog/courses")
    assert catalog_response.status_code == 200
    assert catalog_response.json()["data"] == [
        {
            "id": course_id,
            "title": "ER Diagram Fundamentals",
            "description": "Learn the core concepts of entity relationship diagrams.",
            "target_learner": "Beginning software-development learners.",
            "difficulty_level": "INTERMEDIATE",
            "learning_objective": "Create a correct ER diagram from a requirements brief.",
            "status": "PUBLISHED",
            "module_count": 1,
            "lesson_count": 1,
            "published_at": publish_response.json()["data"]["published_at"],
        }
    ]

    detail_response = client.get(f"/api/catalog/courses/{course_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert detail["learning_path"]["overview"].startswith("A Creator-reviewable")
    assert detail["learning_path"]["modules"][0]["lessons"][0]["title"] == "Entities and relationships"


def test_catalog_hides_unpublished_courses_and_learners_cannot_publish() -> None:
    creator_headers = _login()
    learner_headers = _login("demo@skillsync.local")
    course_id = _create_course(creator_headers)

    unpublished_response = client.get(f"/api/catalog/courses/{course_id}")
    learner_publish_response = client.post(
        f"/api/courses/{course_id}/publish",
        headers=learner_headers,
    )

    assert unpublished_response.status_code == 404
    assert unpublished_response.json()["error"]["code"] == "PUBLISHED_COURSE_NOT_FOUND"
    assert learner_publish_response.status_code == 403
    assert learner_publish_response.json()["error"]["code"] == "FORBIDDEN"
