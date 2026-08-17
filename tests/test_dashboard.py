"""Integration tests for Function 9: Creator Dashboard."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import mock_auth_service
from app.services.course_service import mock_course_service
from app.services.dashboard_service import mock_dashboard_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_stores() -> None:
    """Keep courses and generated analytics isolated between test cases."""
    mock_auth_service.reset()
    mock_course_service.reset()
    mock_dashboard_service.reset()


def _headers(email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def _create_course(headers: dict[str, str], title: str = "Database Fundamentals") -> int:
    response = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": title,
            "description": "A course used to demonstrate dashboard analytics.",
            "target_learner": "Beginning database learners.",
            "difficulty_level": "BEGINNER",
            "learning_objective": "Understand relational database design.",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def test_creator_can_read_filtered_dashboard_and_all_required_metrics() -> None:
    headers = _headers("creator@skillsync.local")
    course_id = _create_course(headers)

    response = client.get(
        "/api/creator/dashboard",
        headers=headers,
        params={"course_id": course_id},
    )

    assert response.status_code == 200
    report = response.json()["data"]
    assert report["filters"]["course_id"] == course_id
    assert report["summary"] == {
        "course_count": 1,
        "learner_count": 3,
        "completed_learner_count": 1,
        "completion_rate": 33.33,
        "average_assessment_score": 63.67,
    }
    assert len(report["courses"]) == 1
    assert len(report["learners"]) == 3
    assert report["common_errors"][0]["topic"] == "JOIN conditions"
    assert report["skill_gaps"][0]["skill"] == "Database normalization"
    assert {insight["code"] for insight in report["course_improvement_insights"]} == {
        "LOW_COMPLETION_RATE",
        "LOW_ASSESSMENT_SCORE",
        "COMMON_ERROR_PATTERN",
        "SKILL_GAP_PATTERN",
    }

    latest_activity_date = report["learners"][0]["last_activity_at"][:10]
    daily_response = client.get(
        "/api/creator/dashboard",
        headers=headers,
        params={
            "course_id": course_id,
            "date_from": latest_activity_date,
            "date_to": latest_activity_date,
        },
    )
    assert daily_response.status_code == 200
    assert daily_response.json()["data"]["summary"]["learner_count"] == 1


def test_creator_can_export_filtered_dashboard_as_csv_and_json() -> None:
    headers = _headers("creator@skillsync.local")
    course_id = _create_course(headers)

    csv_response = client.get(
        "/api/creator/dashboard/export",
        headers=headers,
        params={"course_id": course_id, "format": "csv"},
    )
    json_response = client.get(
        "/api/creator/dashboard/export",
        headers=headers,
        params={"course_id": course_id, "format": "json"},
    )
    pdf_response = client.get(
        "/api/creator/dashboard/export",
        headers=headers,
        params={"course_id": course_id, "format": "pdf"},
    )

    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    assert 'filename="creator-dashboard-report.csv"' in csv_response.headers[
        "content-disposition"
    ]
    assert "learner_name" in csv_response.text
    assert "Aom Learner" in csv_response.text

    assert json_response.status_code == 200
    assert json_response.headers["content-type"].startswith("application/json")
    assert json_response.json()["summary"]["learner_count"] == 3

    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"].startswith("application/pdf")
    assert 'filename="creator-dashboard-report.pdf"' in pdf_response.headers[
        "content-disposition"
    ]
    assert pdf_response.content.startswith(b"%PDF-1.4")


def test_dashboard_validates_access_and_date_range() -> None:
    creator_headers = _headers("creator@skillsync.local")
    _create_course(creator_headers)
    learner_headers = _headers("demo@skillsync.local")

    unauthenticated_response = client.get("/api/creator/dashboard")
    learner_response = client.get("/api/creator/dashboard", headers=learner_headers)
    invalid_range_response = client.get(
        "/api/creator/dashboard",
        headers=creator_headers,
        params={"date_from": "2026-08-18", "date_to": "2026-08-17"},
    )
    missing_course_response = client.get(
        "/api/creator/dashboard",
        headers=creator_headers,
        params={"course_id": 999},
    )

    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json()["error"]["code"] == "UNAUTHORIZED"
    assert learner_response.status_code == 403
    assert learner_response.json()["error"]["code"] == "FORBIDDEN"
    assert invalid_range_response.status_code == 400
    assert invalid_range_response.json()["error"]["code"] == "INVALID_DATE_RANGE"
    assert missing_course_response.status_code == 404
    assert missing_course_response.json()["error"]["code"] == "COURSE_NOT_FOUND"
