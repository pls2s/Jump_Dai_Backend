"""Integration tests for enrollment, assessment, progress, and account-management APIs."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.assessment_service import mock_assessment_service
from app.services.auth_service import mock_auth_service
from app.services.course_service import mock_course_service
from app.services.document_service import mock_document_service
from app.services.knowledge_service import mock_knowledge_processing_service
from app.services.learner_service import mock_learner_course_service
from app.services.learning_service import mock_personalized_learning_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_stores() -> None:
    """Keep each end-to-end delivery test independent."""
    mock_auth_service.reset()
    mock_course_service.reset()
    mock_document_service.reset()
    mock_knowledge_processing_service.reset()
    mock_learner_course_service.reset()
    mock_assessment_service.reset()
    mock_personalized_learning_service.reset()


def _headers(email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def _published_course() -> int:
    creator_headers = _headers("creator@skillsync.local")
    response = client.post(
        "/api/courses",
        headers=creator_headers,
        json={
            "title": "Backend Foundations",
            "description": "Core backend concepts.",
            "target_learner": "New backend developers.",
            "difficulty_level": "BEGINNER",
            "learning_objective": "Build a small backend API.",
        },
    )
    assert response.status_code == 201
    course_id = response.json()["data"]["id"]
    course = mock_course_service.get_for_creator(course_id=course_id, creator_id=2)
    learning_path = {
        "course_id": course_id,
        "title": course.title,
        "overview": "Learn the foundations in two focused lessons.",
        "modules": [
            {
                "title": "Backend Basics",
                "description": "Foundational concepts.",
                "learning_objectives": ["Use SQL joins and Python functions."],
                "lessons": [
                    {
                        "title": "SQL joins",
                        "summary": "Combine related rows safely.",
                        "source_references": ["source-1-chunk-1"],
                    },
                    {
                        "title": "Python functions",
                        "summary": "Organize reusable backend logic.",
                        "source_references": ["source-1-chunk-2"],
                    },
                ],
            }
        ],
    }
    mock_course_service.start_generation(course_id=course_id, creator_id=2)
    mock_course_service.complete_generation(
        course_id=course_id,
        creator_id=2,
        learning_path=learning_path,
    )
    mock_course_service.verify_learning_path(course_id=course_id, creator_id=2)
    mock_course_service.publish_course(course_id=course_id, creator_id=2)
    return course_id


def test_enrollment_lesson_progress_and_assessment_adapt_a_personal_path() -> None:
    course_id = _published_course()
    creator_headers = _headers("creator@skillsync.local")
    learner_headers = _headers("demo@skillsync.local")

    enrollment_response = client.post(
        f"/api/courses/{course_id}/enroll",
        headers=learner_headers,
    )
    assert enrollment_response.status_code == 201

    path_response = client.get(
        f"/api/learning/courses/{course_id}/path",
        headers=learner_headers,
    )
    assert path_response.status_code == 200
    path = path_response.json()["data"]
    first_lesson_id = path["lessons"][0]["id"]
    assert path["total_lesson_count"] == 2

    assert client.get(f"/api/lessons/{first_lesson_id}", headers=learner_headers).status_code == 200
    completion_response = client.post(
        f"/api/lessons/{first_lesson_id}/complete",
        headers=learner_headers,
    )
    assert completion_response.status_code == 200
    assert completion_response.json()["data"]["progress"]["progress_percentage"] == 50

    profile_response = client.put(
        "/api/learning/profile",
        headers=learner_headers,
        json={
            "learning_goal": "Become a backend developer.",
            "learning_styles": ["VISUAL"],
        },
    )
    assert profile_response.status_code == 200
    pre_assessment = client.post(
        "/api/learning/pre-assessments",
        headers=learner_headers,
        json={
            "assessment_title": "Initial backend baseline",
            "topic_scores": [
                {"topic": "SQL joins", "score": 50},
                {"topic": "Python functions", "score": 80},
            ],
        },
    )
    assert pre_assessment.status_code == 201
    assert client.post("/api/learning/paths", headers=learner_headers, json={}).status_code == 201

    assessment_response = client.post(
        f"/api/courses/{course_id}/assessments",
        headers=creator_headers,
        json={
            "title": "Backend practical task",
            "assessment_type": "PRACTICAL",
            "topics": ["SQL joins", "Python functions"],
            "is_final_assessment": True,
        },
    )
    assert assessment_response.status_code == 201
    assessment_id = assessment_response.json()["data"]["id"]

    submit_response = client.post(
        f"/api/assessments/{assessment_id}/submit",
        headers=learner_headers,
        json={
            "topic_scores": [
                {"topic": "SQL joins", "score": 88},
                {"topic": "Python functions", "score": 64},
            ],
            "evidence_url": "https://example.com/backend-project",
        },
    )
    assert submit_response.status_code == 201
    submitted = submit_response.json()["data"]
    assert submitted["result"]["improvements"] == ["Python functions"]
    assert submitted["adapted_learning_path"]["is_adaptive"] is True
    assert submitted["adapted_learning_path"]["version"] == 2

    learner_attempts_response = client.get(
        f"/api/assessments/{assessment_id}/my-attempts",
        headers=learner_headers,
    )
    assert learner_attempts_response.status_code == 200
    assert learner_attempts_response.json()["data"][0]["id"] == submitted["result"]["id"]

    attempts_response = client.get(
        f"/api/assessments/{assessment_id}/attempts",
        headers=creator_headers,
    )
    assert attempts_response.status_code == 200
    attempt_id = attempts_response.json()["data"][0]["id"]
    review_response = client.patch(
        f"/api/assessments/{assessment_id}/attempts/{attempt_id}/review",
        headers=creator_headers,
        json={"adjusted_score": 75, "reason": "Manual rubric review completed."},
    )
    assert review_response.status_code == 200
    assert review_response.json()["data"]["score"] == 75


def test_manual_text_source_and_user_account_management_apis() -> None:
    creator_headers = _headers("creator@skillsync.local")
    course_response = client.post(
        "/api/courses",
        headers=creator_headers,
        json={
            "title": "Manual Source Course",
            "description": "A course with creator-authored content.",
            "target_learner": "New learners.",
            "difficulty_level": "BEGINNER",
            "learning_objective": "Understand a manual source.",
        },
    )
    course_id = course_response.json()["data"]["id"]
    text_response = client.post(
        f"/api/courses/{course_id}/knowledge-sources/text",
        headers=creator_headers,
        json={
            "title": "SQL note",
            "content": "SQL joins combine rows from related tables.",
        },
    )
    assert text_response.status_code == 201
    source_id = text_response.json()["data"]["id"]
    assert text_response.json()["data"]["source_type"] == "TEXT"
    assert client.post(
        f"/api/knowledge-sources/{source_id}/process",
        headers=creator_headers,
    ).status_code == 200

    learner_headers = _headers("demo@skillsync.local")
    profile_response = client.put(
        "/api/users/me",
        headers=learner_headers,
        json={"name": "Updated Learner"},
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["data"]["name"] == "Updated Learner"

    admin_headers = _headers("admin@skillsync.local")
    users_response = client.get("/api/users", headers=admin_headers)
    assert users_response.status_code == 200
    assert len(users_response.json()["data"]) == 4
    role_response = client.put(
        "/api/users/1/roles",
        headers=admin_headers,
        json={"roles": ["LEARNER", "CREATOR"]},
    )
    assert role_response.status_code == 200
    assert role_response.json()["data"]["roles"] == ["LEARNER", "CREATOR"]

    logout_response = client.post("/api/auth/logout", headers=learner_headers)
    assert logout_response.status_code == 200
    assert client.get("/api/users/me", headers=learner_headers).status_code == 401
