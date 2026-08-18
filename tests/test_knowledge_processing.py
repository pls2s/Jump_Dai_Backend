"""Integration tests for Function 3 local knowledge processing and retrieval."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import mock_auth_service
from app.services.course_service import mock_course_service
from app.services.document_service import mock_document_service
from app.services.knowledge_service import mock_knowledge_processing_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_stores() -> None:
    """Keep authentication, course, source, and chunk state isolated per test."""
    mock_auth_service.reset()
    mock_course_service.reset()
    mock_document_service.reset()
    mock_knowledge_processing_service.reset()


def _creator_headers() -> dict[str, str]:
    login_response = client.post(
        "/api/auth/login",
        json={"email": "creator@skillsync.local", "password": "password123"},
    )
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['data']['access_token']}"}


def _create_course(headers: dict[str, str]) -> int:
    response = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Database Fundamentals",
            "description": "A course configured before knowledge is processed.",
            "target_learner": "Beginning database learners.",
            "difficulty_level": "BEGINNER",
            "learning_objective": "Understand relational database design.",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def test_creator_can_process_text_and_retrieve_source_grounded_chunks() -> None:
    headers = _creator_headers()
    course_id = _create_course(headers)
    source_text = (
        "A relational database stores data in related tables. "
        "A primary key uniquely identifies each row. "
        "A foreign key connects a child table to a parent table. "
    ) * 12
    upload_response = client.post(
        f"/api/courses/{course_id}/documents",
        headers=headers,
        files={"file": ("database-notes.md", source_text.encode(), "text/markdown")},
    )
    source_id = upload_response.json()["data"]["id"]

    process_response = client.post(
        f"/api/knowledge-sources/{source_id}/process",
        headers=headers,
    )

    assert process_response.status_code == 200
    process_data = process_response.json()["data"]
    assert process_data["source"]["status"] == "READY"
    assert process_data["chunks_created"] >= 2
    assert process_data["source"]["chunk_count"] == process_data["chunks_created"]
    assert process_data["source"]["processing_error"] is None

    chunks_response = client.get(
        f"/api/knowledge-sources/{source_id}/chunks",
        headers=headers,
    )
    assert chunks_response.status_code == 200
    chunks = chunks_response.json()["data"]
    assert len(chunks) == process_data["chunks_created"]
    assert chunks[0]["source_filename"] == "database-notes.md"
    assert chunks[0]["chunk_index"] == 1

    search_response = client.get(
        f"/api/courses/{course_id}/knowledge-search",
        headers=headers,
        params={"query": "primary key", "limit": 3},
    )
    assert search_response.status_code == 200
    results = search_response.json()["data"]
    assert results
    assert results[0]["source_id"] == source_id
    assert results[0]["score"] == 1.0
    assert "primary key" in results[0]["content"].lower()


def test_unsupported_source_is_marked_failed_and_never_indexed() -> None:
    headers = _creator_headers()
    course_id = _create_course(headers)
    upload_response = client.post(
        f"/api/courses/{course_id}/documents",
        headers=headers,
        files={"file": ("slides.pdf", b"%PDF-1.7 mock", "application/pdf")},
    )
    source_id = upload_response.json()["data"]["id"]

    process_response = client.post(
        f"/api/knowledge-sources/{source_id}/process",
        headers=headers,
    )

    assert process_response.status_code == 422
    assert process_response.json()["error"]["code"] == "KNOWLEDGE_SOURCE_PROCESSING_FAILED"

    sources_response = client.get(
        f"/api/courses/{course_id}/knowledge-sources",
        headers=headers,
    )
    source = sources_response.json()["data"][0]
    assert source["status"] == "FAILED"
    assert source["chunk_count"] == 0
    assert source["processing_error"] == "Local processing currently supports only .txt and .md files"

    chunks_response = client.get(
        f"/api/knowledge-sources/{source_id}/chunks",
        headers=headers,
    )
    assert chunks_response.status_code == 200
    assert chunks_response.json()["data"] == []
