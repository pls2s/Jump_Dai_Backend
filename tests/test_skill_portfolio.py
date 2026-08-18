"""Integration tests for Function 9.7 Skill Evidence / Portfolio."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import mock_auth_service
from app.services.portfolio_service import mock_skill_portfolio_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_stores() -> None:
    """Keep learner evidence, credentials, links, and tokens isolated between tests."""
    mock_auth_service.reset()
    mock_skill_portfolio_service.reset()


def _headers(email: str = "demo@skillsync.local") -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def _evidence_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "course_id": 10,
        "course_title": "Database Fundamentals",
        "assessment_id": "practical-sql-1",
        "assessment_title": "Practical SQL Project",
        "skill": "SQL joins",
        "score": 88,
        "passing_score": 70,
        "evidence_title": "Customer reporting query",
        "evidence_url": "https://portfolio.example/sql-joins",
        "is_course_final_assessment": True,
    }
    payload.update(overrides)
    return payload


def test_learner_can_create_evidence_portfolio_share_and_verifiable_credentials() -> None:
    headers = _headers()
    evidence_response = client.post(
        "/api/skill-evidence",
        headers=headers,
        json=_evidence_payload(),
    )

    assert evidence_response.status_code == 201
    submitted = evidence_response.json()["data"]
    assert submitted["evidence"]["verified"] is True
    assert submitted["evidence"]["competency_level"] == "ADVANCED"
    assert submitted["verified_skill"]["skill"] == "SQL joins"
    assert submitted["verified_skill"]["evidence"][0]["assessment_id"] == "practical-sql-1"
    assert submitted["issued_badge"]["credential_type"] == "DIGITAL_BADGE"
    assert submitted["issued_certificate"]["credential_type"] == "CERTIFICATE"

    portfolio_response = client.get("/api/skill-portfolio", headers=headers)
    assert portfolio_response.status_code == 200
    portfolio = portfolio_response.json()["data"]
    assert portfolio["learner_name"] == "Learner Demo"
    assert portfolio["skills"][0]["competency_score"] == 88
    assert portfolio["skills"][0]["evidence"][0]["evidence_url"] == (
        "https://portfolio.example/sql-joins"
    )
    assert {credential["credential_type"] for credential in portfolio["credentials"]} == {
        "DIGITAL_BADGE",
        "CERTIFICATE",
    }

    share_response = client.post("/api/skill-portfolio/share", headers=headers)
    assert share_response.status_code == 200
    share = share_response.json()["data"]
    assert share["share_url"].endswith(
        f"/api/skill-portfolio/shared/{share['share_token']}"
    )

    shared_response = client.get(f"/api/skill-portfolio/shared/{share['share_token']}")
    assert shared_response.status_code == 200
    assert shared_response.json()["data"]["skills"][0]["skill"] == "SQL joins"

    for credential in (submitted["issued_badge"], submitted["issued_certificate"]):
        verification_response = client.get(f"/api/credentials/{credential['id']}/verify")
        assert verification_response.status_code == 200
        verified_credential = verification_response.json()["data"]["credential"]
        assert verified_credential["id"] == credential["id"]
        assert verified_credential["status"] == "VALID"


def test_only_passing_evidence_creates_verified_skills_and_credentials() -> None:
    headers = _headers()
    response = client.post(
        "/api/skill-evidence",
        headers=headers,
        json=_evidence_payload(score=65, passing_score=70),
    )

    assert response.status_code == 201
    submitted = response.json()["data"]
    assert submitted["evidence"]["verified"] is False
    assert submitted["evidence"]["competency_level"] == "DEVELOPING"
    assert submitted["verified_skill"] is None
    assert submitted["issued_badge"] is None
    assert submitted["issued_certificate"] is None

    portfolio = client.get("/api/skill-portfolio", headers=headers).json()["data"]
    assert portfolio["skills"] == []
    assert portfolio["credentials"] == []


def test_portfolio_enforces_learner_access_and_validates_public_ids() -> None:
    creator_headers = _headers("creator@skillsync.local")

    unauthenticated_response = client.get("/api/skill-portfolio")
    creator_response = client.post(
        "/api/skill-evidence",
        headers=creator_headers,
        json=_evidence_payload(),
    )
    missing_share_response = client.get("/api/skill-portfolio/shared/not-a-real-token")
    missing_credential_response = client.get("/api/credentials/credential-999/verify")

    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json()["error"]["code"] == "UNAUTHORIZED"
    assert creator_response.status_code == 403
    assert creator_response.json()["error"]["code"] == "FORBIDDEN"
    assert missing_share_response.status_code == 404
    assert missing_share_response.json()["error"]["code"] == "PORTFOLIO_SHARE_NOT_FOUND"
    assert missing_credential_response.status_code == 404
    assert missing_credential_response.json()["error"]["code"] == "CREDENTIAL_NOT_FOUND"


def test_credentials_are_not_issued_twice_for_the_same_skill_or_course() -> None:
    headers = _headers()
    first_response = client.post(
        "/api/skill-evidence",
        headers=headers,
        json=_evidence_payload(),
    )
    second_response = client.post(
        "/api/skill-evidence",
        headers=headers,
        json=_evidence_payload(
            assessment_id="practical-sql-2",
            assessment_title="Practical SQL Project Revision",
            score=92,
        ),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert second_response.json()["data"]["issued_badge"] is None
    assert second_response.json()["data"]["issued_certificate"] is None
    portfolio = client.get("/api/skill-portfolio", headers=headers).json()["data"]
    assert len(portfolio["skills"][0]["evidence"]) == 2
    assert portfolio["skills"][0]["competency_score"] == 92
    assert len(portfolio["credentials"]) == 2
