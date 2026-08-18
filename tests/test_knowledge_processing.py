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


def _text_pdf_bytes(text: str) -> bytes:
    """Create a minimal valid PDF containing selectable text for parser coverage."""
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT\n/F1 12 Tf\n72 720 Td\n({escaped_text}) Tj\nET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_number, object_data in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_number} 0 obj\n".encode())
        pdf.extend(object_data)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_offset).encode()
        + b"\n%%EOF\n"
    )
    return bytes(pdf)


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


def test_creator_can_process_selectable_pdf_text() -> None:
    headers = _creator_headers()
    course_id = _create_course(headers)
    upload_response = client.post(
        f"/api/courses/{course_id}/documents",
        headers=headers,
        files={
            "file": (
                "database-guide.pdf",
                _text_pdf_bytes("A primary key uniquely identifies each database row."),
                "application/pdf",
            )
        },
    )
    source_id = upload_response.json()["data"]["id"]

    process_response = client.post(
        f"/api/knowledge-sources/{source_id}/process",
        headers=headers,
    )
    search_response = client.get(
        f"/api/courses/{course_id}/knowledge-search",
        headers=headers,
        params={"query": "primary key"},
    )

    assert process_response.status_code == 200
    assert process_response.json()["data"]["source"]["status"] == "READY"
    assert search_response.status_code == 200
    assert search_response.json()["data"][0]["source_filename"] == "database-guide.pdf"


def test_unsupported_source_is_marked_failed_and_never_indexed() -> None:
    headers = _creator_headers()
    course_id = _create_course(headers)
    upload_response = client.post(
        f"/api/courses/{course_id}/documents",
        headers=headers,
        files={"file": ("slides.pptx", b"mock slide content", "application/octet-stream")},
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
    assert source["processing_error"] == "Local processing currently supports only .txt, .md, and .pdf files"

    chunks_response = client.get(
        f"/api/knowledge-sources/{source_id}/chunks",
        headers=headers,
    )
    assert chunks_response.status_code == 200
    assert chunks_response.json()["data"] == []
