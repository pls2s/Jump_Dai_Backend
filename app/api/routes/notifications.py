"""Role-scoped mock notification endpoints."""

from typing import Optional

from fastapi import APIRouter, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.notification import NotificationFeedResponse
from app.schemas.user import SuccessResponse
from app.services.auth_service import MockUser, mock_auth_service
from app.services.notification_service import mock_notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: object) -> dict:
    return {"success": True, "data": data}


def _current_user(credentials: Optional[HTTPAuthorizationCredentials]) -> MockUser:
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"
    return mock_auth_service.current_user(authorization)


@router.get("", response_model=SuccessResponse[NotificationFeedResponse])
def list_notifications(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return the current user's workspace-scoped mock notification feed."""
    return _success(mock_notification_service.feed(_current_user(credentials)))


@router.post("/read-all", response_model=SuccessResponse[NotificationFeedResponse])
def mark_all_notifications_read(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Mark every notification visible to the current user as read."""
    return _success(mock_notification_service.mark_all_read(_current_user(credentials)))


@router.patch("/{notification_id}/read", response_model=SuccessResponse[NotificationFeedResponse])
def mark_notification_read(
    notification_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Persist one read receipt for the current mock user only."""
    return _success(mock_notification_service.mark_read(_current_user(credentials), notification_id))
