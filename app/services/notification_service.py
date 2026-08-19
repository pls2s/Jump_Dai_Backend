"""Thread-safe, process-local notification feed and read-receipt service."""

from __future__ import annotations

from threading import RLock

from fastapi import HTTPException, status

from app.data.mock_notifications import MOCK_NOTIFICATION_DEFINITIONS
from app.schemas.notification import NotificationAudience
from app.schemas.user import UserRole, WorkspaceType
from app.services.auth_service import MockUser


class MockNotificationService:
    """Serve fixed notifications while retaining only read receipts per mock user."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._read_ids_by_user: dict[int, set[str]] = {}

    @staticmethod
    def audience_for(user: MockUser) -> NotificationAudience:
        if UserRole.ADMIN in user.roles:
            return NotificationAudience.ADMIN
        if user.workspace_type is WorkspaceType.ORGANIZATION:
            return NotificationAudience.ORGANIZATION
        if user.workspace_type is WorkspaceType.LEARNER:
            return NotificationAudience.LEARNER
        return NotificationAudience.CREATOR

    def feed(self, user: MockUser) -> dict:
        with self._lock:
            audience = self.audience_for(user)
            read_ids = self._read_ids_by_user.get(user.id, set())
            items = [
                {**definition, "read": definition["id"] in read_ids}
                for definition in MOCK_NOTIFICATION_DEFINITIONS
                if definition["audience"] == audience.value
            ]
            return {
                "audience": audience,
                "items": items,
                "unread_count": sum(not item["read"] for item in items),
            }

    def mark_read(self, user: MockUser, notification_id: str) -> dict:
        with self._lock:
            audience = self.audience_for(user)
            visible_ids = {
                definition["id"]
                for definition in MOCK_NOTIFICATION_DEFINITIONS
                if definition["audience"] == audience.value
            }
            if notification_id not in visible_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "NOTIFICATION_NOT_FOUND",
                        "message": "This notification is not available for the current workspace",
                    },
                )
            self._read_ids_by_user.setdefault(user.id, set()).add(notification_id)
            return self.feed(user)

    def mark_all_read(self, user: MockUser) -> dict:
        with self._lock:
            audience = self.audience_for(user)
            self._read_ids_by_user.setdefault(user.id, set()).update(
                definition["id"]
                for definition in MOCK_NOTIFICATION_DEFINITIONS
                if definition["audience"] == audience.value
            )
            return self.feed(user)


mock_notification_service = MockNotificationService()
