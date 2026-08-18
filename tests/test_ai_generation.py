"""Integration tests for Function 4 source-grounded AI course generation."""

import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.ai_service import typhoon_ai_service
from app.services.auth_service import mock_auth_service
from app.services.course_service import mock_course_service
from app.services.document_service import mock_document_service
from app.services.knowledge_service import mock_knowledge_processing_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_stores() -> None:
    """Keep the in-memory stores isolated and never call Typhoon in tests."""
    mock_auth_service.reset()
    mock_course_service.reset()
    mock_document_service.reset()
    mock_knowledge_processing_service.reset()


def _creator_headers() -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": "creator@skillsync.local", "password": "password123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def _create_course(headers: dict[str, str]) -> int:
    response = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Database Fundamentals",
            "description": "A course generated from the creator's source material.",
            "target_learner": "Beginning database learners.",
            "difficulty_level": "BEGINNER",
            "learning_objective": "Understand relational database design.",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_ready_source(headers: dict[str, str], course_id: int) -> int:
    upload_response = client.post(
        f"/api/courses/{course_id}/documents",
        headers=headers,
        files={
            "file": (
                "database-notes.md",
                (
                    "A relational database stores information in related tables. "
                    "A primary key uniquely identifies each row. "
                    "A foreign key connects a child table to a parent table."
                ).encode(),
                "text/markdown",
            )
        },
    )
    assert upload_response.status_code == 201
    source_id = upload_response.json()["data"]["id"]

    process_response = client.post(
        f"/api/knowledge-sources/{source_id}/process",
        headers=headers,
    )
    assert process_response.status_code == 200
    return source_id


def test_creator_can_generate_a_source_cited_learning_path(monkeypatch: pytest.MonkeyPatch) -> None:
    headers = _creator_headers()
    course_id = _create_course(headers)
    _create_ready_source(headers, course_id)
    monkeypatch.setattr(settings, "typhoon_api_key", "test-key")

    def fake_completion(*, messages: list[dict[str, str]]) -> str:
        assert "source-1-chunk-1" in messages[1]["content"]
        return json.dumps(
            {
                "overview": "Learn the foundations of relational database design.",
                "modules": [
                    {
                        "title": "Relational foundations",
                        "description": "Understand tables and their keys.",
                        "learning_objectives": [
                            "Identify primary and foreign keys.",
                        ],
                        "lessons": [
                            {
                                "title": "Keys and relationships",
                                "summary": "Use primary and foreign keys to connect tables.",
                                "source_references": ["source-1-chunk-1"],
                            }
                        ],
                    }
                ],
            }
        )

    monkeypatch.setattr(typhoon_ai_service, "_create_completion", fake_completion)

    response = client.post(f"/api/courses/{course_id}/generate", headers=headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["course_id"] == course_id
    assert data["status"] == "WAITING_VERIFICATION"
    assert data["progress"] == 100
    assert data["learning_path"]["modules"][0]["lessons"][0]["source_references"] == [
        "source-1-chunk-1"
    ]

    learning_path_response = client.get(
        f"/api/courses/{course_id}/learning-path",
        headers=headers,
    )
    assert learning_path_response.status_code == 200
    assert learning_path_response.json()["data"]["title"] == "Database Fundamentals"

    update_response = client.put(
        f"/api/courses/{course_id}/learning-path",
        headers=headers,
        json={
            "overview": "Creator-reviewed relational database foundations.",
            "modules": [
                {
                    "title": "Keys and relationships",
                    "description": "A Creator edited this description.",
                    "learning_objectives": ["Recognize a foreign key."],
                    "lessons": [
                        {
                            "title": "Connecting related tables",
                            "summary": "Foreign keys connect child and parent tables.",
                            "source_references": ["source-1-chunk-1"],
                        }
                    ],
                }
            ],
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["overview"].startswith("Creator-reviewed")

    verify_response = client.post(f"/api/courses/{course_id}/verify", headers=headers)
    assert verify_response.status_code == 200
    assert verify_response.json()["data"]["status"] == "VERIFIED"

    status_response = client.get(
        f"/api/courses/{course_id}/generation-status",
        headers=headers,
    )
    assert status_response.status_code == 200
    assert status_response.json()["data"]["status"] == "VERIFIED"
    assert status_response.json()["data"]["has_learning_path"] is True
    assert status_response.json()["data"]["verified_at"] is not None


def test_generation_requires_at_least_one_processed_source() -> None:
    headers = _creator_headers()
    course_id = _create_course(headers)

    response = client.post(f"/api/courses/{course_id}/generate", headers=headers)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "AI_GENERATION_REQUIRES_READY_SOURCE"


def test_invalid_typhoon_citations_fail_without_saving_a_draft(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = _creator_headers()
    course_id = _create_course(headers)
    _create_ready_source(headers, course_id)
    monkeypatch.setattr(settings, "typhoon_api_key", "test-key")

    def fake_completion(*, messages: list[dict[str, str]]) -> str:
        return json.dumps(
            {
                "overview": "A generated draft.",
                "modules": [
                    {
                        "title": "Module",
                        "description": "Description.",
                        "learning_objectives": ["Objective."],
                        "lessons": [
                            {
                                "title": "Lesson",
                                "summary": "Summary.",
                                "source_references": ["made-up-chunk"],
                            }
                        ],
                    }
                ],
            }
        )

    monkeypatch.setattr(typhoon_ai_service, "_create_completion", fake_completion)

    response = client.post(f"/api/courses/{course_id}/generate", headers=headers)
    status_response = client.get(
        f"/api/courses/{course_id}/generation-status",
        headers=headers,
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "AI_RESPONSE_INVALID"
    assert status_response.json()["data"] == {
        "course_id": course_id,
        "status": "FAILED",
        "progress": 0,
        "error": "Typhoon cited source chunks that were not supplied",
        "generated_at": None,
        "verified_at": None,
        "has_learning_path": False,
    }
