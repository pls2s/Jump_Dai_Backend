"""Integration tests for Function 9.5 Personalized Learning Path."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import mock_auth_service
from app.services.learning_service import mock_personalized_learning_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_stores() -> None:
    """Keep learner preferences, assessments, and paths isolated between tests."""
    mock_auth_service.reset()
    mock_personalized_learning_service.reset()


def _headers(email: str = "demo@skillsync.local") -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def _profile_payload() -> dict[str, object]:
    return {
        "learning_goal": "Become confident building data-driven web applications.",
        "target_role": "Junior backend developer",
        "learning_styles": ["VISUAL", "KINESTHETIC"],
        "weekly_learning_hours": 6,
    }


def _pre_assessment_payload() -> dict[str, object]:
    return {
        "assessment_title": "Backend foundations pre-assessment",
        "passing_score": 70,
        "topic_scores": [
            {"topic": "SQL joins", "score": 42},
            {"topic": "Git workflows", "score": 65},
            {"topic": "Python functions", "score": 78},
        ],
    }


def _set_up_path(headers: dict[str, str]) -> int:
    profile_response = client.put(
        "/api/learning/profile",
        headers=headers,
        json=_profile_payload(),
    )
    assert profile_response.status_code == 200
    assessment_response = client.post(
        "/api/learning/pre-assessments",
        headers=headers,
        json=_pre_assessment_payload(),
    )
    assert assessment_response.status_code == 201
    assessment_id = assessment_response.json()["data"]["id"]
    path_response = client.post(
        "/api/learning/paths",
        headers=headers,
        json={"pre_assessment_id": assessment_id},
    )
    assert path_response.status_code == 201
    return assessment_id


def test_learner_can_save_profile_analyze_gaps_and_generate_personalized_path() -> None:
    headers = _headers()
    profile_response = client.put(
        "/api/learning/profile",
        headers=headers,
        json=_profile_payload(),
    )

    assert profile_response.status_code == 200
    profile = profile_response.json()["data"]
    assert profile["learning_goal"].startswith("Become confident")
    assert profile["learning_styles"] == ["VISUAL", "KINESTHETIC"]

    assessment_response = client.post(
        "/api/learning/pre-assessments",
        headers=headers,
        json=_pre_assessment_payload(),
    )

    assert assessment_response.status_code == 201
    assessment = assessment_response.json()["data"]
    assert assessment["overall_score"] == 61.67
    assert assessment["learner_level"] == "BEGINNER"

    analysis_response = client.get("/api/learning/skill-gap-analysis", headers=headers)
    assert analysis_response.status_code == 200
    analysis = analysis_response.json()["data"]
    assert [gap["topic"] for gap in analysis["knowledge_gaps"]] == [
        "SQL joins",
        "Git workflows",
    ]
    assert [gap["skill"] for gap in analysis["skill_gaps"]] == [
        "SQL joins",
        "Git workflows",
    ]
    assert analysis["weak_topics"][0]["severity"] == "CRITICAL"

    path_response = client.post(
        "/api/learning/paths",
        headers=headers,
        json={"pre_assessment_id": assessment["id"]},
    )

    assert path_response.status_code == 201
    path = path_response.json()["data"]
    assert path["learning_goal"] == _profile_payload()["learning_goal"]
    assert path["is_adaptive"] is False
    assert path["lessons"][0]["topic"] == "SQL joins"
    assert path["lessons"][0]["level"] == "FOUNDATION"
    assert len(path["additional_content_recommendations"]) == 6

    current_path_response = client.get("/api/learning/paths/current", headers=headers)
    assert current_path_response.status_code == 200
    assert current_path_response.json()["data"]["id"] == path["id"]


def test_latest_assessment_adapts_the_current_personalized_path() -> None:
    headers = _headers()
    initial_assessment_id = _set_up_path(headers)

    response = client.post(
        "/api/learning/paths/current/adapt",
        headers=headers,
        json={
            "assessment_title": "Backend checkpoint 1",
            "passing_score": 70,
            "topic_scores": [
                {"topic": "SQL joins", "score": 88},
                {"topic": "Git workflows", "score": 48},
                {"topic": "Python functions", "score": 78},
            ],
        },
    )

    assert response.status_code == 200
    adapted = response.json()["data"]
    assert adapted["previous_assessment_id"] == initial_assessment_id
    assert adapted["latest_assessment"]["assessment_title"] == "Backend checkpoint 1"
    assert adapted["path"]["version"] == 2
    assert adapted["path"]["is_adaptive"] is True
    assert [topic["topic"] for topic in adapted["path"]["weak_topics"]] == ["Git workflows"]
    assert adapted["path"]["additional_content_recommendations"][0]["topic"] == "Git workflows"
    assert set(adapted["changed_topics"]) == {"SQL joins", "Git workflows"}


def test_learning_path_requires_a_learner_profile_and_valid_input() -> None:
    learner_headers = _headers()
    creator_headers = _headers("creator@skillsync.local")

    unauthenticated_response = client.put(
        "/api/learning/profile",
        json=_profile_payload(),
    )
    creator_response = client.put(
        "/api/learning/profile",
        headers=creator_headers,
        json=_profile_payload(),
    )
    missing_profile_response = client.post(
        "/api/learning/paths",
        headers=learner_headers,
        json={},
    )
    duplicate_topics_response = client.post(
        "/api/learning/pre-assessments",
        headers=learner_headers,
        json={
            "assessment_title": "Duplicate topic check",
            "topic_scores": [
                {"topic": "Python", "score": 60},
                {"topic": "python", "score": 70},
            ],
        },
    )

    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json()["error"]["code"] == "UNAUTHORIZED"
    assert creator_response.status_code == 403
    assert creator_response.json()["error"]["code"] == "FORBIDDEN"
    assert missing_profile_response.status_code == 404
    assert missing_profile_response.json()["error"]["code"] == "LEARNING_PROFILE_NOT_FOUND"
    assert duplicate_topics_response.status_code == 422
    assert duplicate_topics_response.json()["error"]["code"] == "VALIDATION_ERROR"
