"""Integration coverage for the role-scoped mock notification feed."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import mock_auth_service
from app.services.notification_service import mock_notification_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_stores() -> None:
    mock_auth_service.reset()
    mock_notification_service.reset()


def _headers(email: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_feed_is_limited_to_the_authenticated_users_audience() -> None:
    creator_response = client.get("/api/notifications", headers=_headers("creator@skillsync.local"))
    assert creator_response.status_code == 200
    creator_feed = creator_response.json()["data"]
    assert creator_feed["audience"] == "creator"
    assert creator_feed["unread_count"] == 4
    assert all(item["audience"] == "creator" for item in creator_feed["items"])

    organization_response = client.get("/api/notifications", headers=_headers("organization@skillsync.local"))
    assert organization_response.status_code == 200
    assert organization_response.json()["data"]["audience"] == "organization"
    assert len(organization_response.json()["data"]["items"]) == 2


def test_read_receipts_are_scoped_to_the_current_user() -> None:
    creator_headers = _headers("creator@skillsync.local")
    learner_headers = _headers("demo@skillsync.local")

    marked = client.patch("/api/notifications/creator-generation-complete/read", headers=creator_headers)
    assert marked.status_code == 200
    assert marked.json()["data"]["unread_count"] == 3

    creator_feed = client.get("/api/notifications", headers=creator_headers).json()["data"]
    assert creator_feed["items"][0]["read"] is True

    inaccessible = client.patch("/api/notifications/creator-generation-complete/read", headers=learner_headers)
    assert inaccessible.status_code == 404
    assert inaccessible.json()["error"]["code"] == "NOTIFICATION_NOT_FOUND"

    all_read = client.post("/api/notifications/read-all", headers=creator_headers)
    assert all_read.status_code == 200
    assert all_read.json()["data"]["unread_count"] == 0
