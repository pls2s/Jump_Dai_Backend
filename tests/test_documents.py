"""Integration tests for Function 2: Knowledge Upload."""

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
    """Keep authentication, course, and source state isolated between tests."""
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
    token = login_response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_course(headers: dict[str, str]) -> int:
    response = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Database Fundamentals",
            "description": "A course configured before knowledge is uploaded.",
            "target_learner": "Beginning database learners.",
            "difficulty_level": "BEGINNER",
            "learning_objective": "Understand how to model a relational database.",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def test_creator_can_manage_file_and_url_knowledge_sources() -> None:
    headers = _creator_headers()
    course_id = _create_course(headers)

    upload_response = client.post(
        f"/api/courses/{course_id}/documents",
        headers=headers,
        files={"file": ("database-lecture.pdf", b"%PDF-1.7 mock", "application/pdf")},
    )

    assert upload_response.status_code == 201
    uploaded = upload_response.json()["data"]
    assert uploaded["filename"] == "database-lecture.pdf"
    assert uploaded["file_type"] == "pdf"
    assert uploaded["source_type"] == "FILE"
    assert uploaded["status"] == "UPLOADED"

    documents_response = client.get(
        f"/api/courses/{course_id}/documents",
        headers=headers,
    )
    assert documents_response.status_code == 200
    assert documents_response.json()["data"] == [
        {
            "id": uploaded["id"],
            "filename": "database-lecture.pdf",
            "status": "UPLOADED",
        }
    ]

    url_response = client.post(
        f"/api/courses/{course_id}/knowledge-sources/url",
        headers=headers,
        json={"title": "Database reference", "url": "https://example.com/database"},
    )

    assert url_response.status_code == 201
    assert url_response.json()["data"]["source_type"] == "URL"
    assert url_response.json()["data"]["version"] == 1

    same_content_different_filename_response = client.post(
        f"/api/courses/{course_id}/documents",
        headers=headers,
        files={"file": ("duplicate-database.pdf", b"%PDF-1.7 mock", "application/pdf")},
    )
    duplicate_filename_response = client.post(
        f"/api/courses/{course_id}/documents",
        headers=headers,
        files={"file": ("DATABASE-LECTURE.pdf", b"different file content", "application/pdf")},
    )
    duplicate_url_response = client.post(
        f"/api/courses/{course_id}/knowledge-sources/url",
        headers=headers,
        json={"title": "Repeated reference", "url": "https://example.com/database"},
    )

    assert same_content_different_filename_response.status_code == 201

    for duplicate_response in (
        duplicate_filename_response,
        duplicate_url_response,
    ):
        assert duplicate_response.status_code == 409
        assert duplicate_response.json()["error"]["code"] == "DUPLICATE_KNOWLEDGE_SOURCE"

    sources_response = client.get(
        f"/api/courses/{course_id}/knowledge-sources",
        headers=headers,
    )
    assert sources_response.status_code == 200
    assert [source["source_type"] for source in sources_response.json()["data"]] == [
        "FILE",
        "URL",
        "FILE",
    ]

    delete_response = client.delete(f"/api/documents/{uploaded['id']}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json() == {"success": True}


def test_creator_can_update_url_knowledge_sources_and_manual_routes_are_unavailable() -> None:
    headers = _creator_headers()
    course_id = _create_course(headers)

    url_response = client.post(
        f"/api/courses/{course_id}/knowledge-sources/url",
        headers=headers,
        json={"title": "Original reference", "url": "https://example.com/original"},
    )
    assert url_response.status_code == 201

    updated_url_response = client.put(
        f"/api/knowledge-sources/{url_response.json()['data']['id']}/url",
        headers=headers,
        json={
            "title": "Revised reference",
            "url": "https://example.com/revised",
        },
    )

    assert updated_url_response.status_code == 200
    updated_url = updated_url_response.json()["data"]
    assert updated_url["filename"] == "Revised reference"
    assert updated_url["version"] == 2

    duplicate_url_response = client.post(
        f"/api/courses/{course_id}/knowledge-sources/url",
        headers=headers,
        json={"title": "Duplicate reference", "url": "https://example.com/revised"},
    )
    removed_manual_response = client.post(
        f"/api/courses/{course_id}/knowledge-sources/manual",
        headers=headers,
        json={"title": "Removed", "content": "Manual content is unsupported."},
    )

    assert duplicate_url_response.status_code == 409
    assert duplicate_url_response.json()["error"]["code"] == "DUPLICATE_KNOWLEDGE_SOURCE"
    assert removed_manual_response.status_code == 404


def test_document_upload_validates_file_and_access() -> None:
    headers = _creator_headers()
    course_id = _create_course(headers)

    unsupported_file_response = client.post(
        f"/api/courses/{course_id}/documents",
        headers=headers,
        files={"file": ("program.exe", b"binary", "application/octet-stream")},
    )
    unauthenticated_response = client.get(f"/api/courses/{course_id}/documents")
    invalid_url_response = client.post(
        f"/api/courses/{course_id}/knowledge-sources/url",
        headers=headers,
        json={"url": "not-a-url"},
    )

    assert unsupported_file_response.status_code == 400
    assert unsupported_file_response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json()["error"]["code"] == "UNAUTHORIZED"
    assert invalid_url_response.status_code == 422
    assert invalid_url_response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_course_can_contain_at_most_ten_file_and_url_knowledge_sources() -> None:
    headers = _creator_headers()
    course_id = _create_course(headers)

    for index in range(5):
        response = client.post(
            f"/api/courses/{course_id}/documents",
            headers=headers,
            files={
                "file": (
                    f"source-{index}.txt",
                    f"unique file content {index}".encode(),
                    "text/plain",
                )
            },
        )
        assert response.status_code == 201

    for index in range(5):
        response = client.post(
            f"/api/courses/{course_id}/knowledge-sources/url",
            headers=headers,
            json={
                "title": f"Reference {index}",
                "url": f"https://example.com/reference-{index}",
            },
        )
        assert response.status_code == 201

    limit_response = client.post(
        f"/api/courses/{course_id}/documents",
        headers=headers,
        files={"file": ("source-6.txt", b"unique file content 6", "text/plain")},
    )

    assert limit_response.status_code == 400
    assert limit_response.json()["error"]["code"] == "KNOWLEDGE_SOURCE_LIMIT_EXCEEDED"
