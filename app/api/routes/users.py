"""Self-service user profile and administrator account-management endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.user import (
    SuccessResponse,
    UserProfileUpdateRequest,
    UserResponse,
    UserRole,
    UserRoleUpdateRequest,
    UserStatusUpdateRequest,
)
from app.services.auth_service import MockUser, mock_auth_service

router = APIRouter(prefix="/users", tags=["users"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: object) -> dict:
    return {"success": True, "data": data}


def _current_user(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> MockUser:
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"
    return mock_auth_service.current_user(authorization)


def _require_admin(credentials: Optional[HTTPAuthorizationCredentials]) -> MockUser:
    user = _current_user(credentials)
    if UserRole.ADMIN not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "An administrator role is required"},
        )
    return user


@router.get("/me", response_model=SuccessResponse[UserResponse])
def read_user_profile(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Read the authenticated user's profile through the users API."""
    return _success(_current_user(credentials).to_public_dict())


@router.put("/me", response_model=SuccessResponse[UserResponse])
def update_user_profile(
    payload: UserProfileUpdateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Update the authenticated user's display name."""
    user = _current_user(credentials)
    return _success(mock_auth_service.update_profile(user=user, name=payload.name).to_public_dict())


@router.get("", response_model=SuccessResponse[list[UserResponse]])
def list_users(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """List accounts for the mock administrator console."""
    _require_admin(credentials)
    return _success([user.to_public_dict() for user in mock_auth_service.list_users()])


@router.put("/{user_id}/roles", response_model=SuccessResponse[UserResponse])
def update_user_roles(
    user_id: int,
    payload: UserRoleUpdateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Replace an account's roles from the administrator console."""
    _require_admin(credentials)
    return _success(
        mock_auth_service.update_roles(user_id=user_id, roles=payload.roles).to_public_dict()
    )


@router.patch("/{user_id}/status", response_model=SuccessResponse[UserResponse])
def update_user_status(
    user_id: int,
    payload: UserStatusUpdateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Suspend or reactivate an account; suspension invalidates its tokens."""
    _require_admin(credentials)
    return _success(
        mock_auth_service.update_status(
            user_id=user_id,
            is_active=payload.is_active,
        ).to_public_dict()
    )
