"""Read-only mock Organization workspace endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.organization import (
    OrganizationCourseResponse,
    OrganizationLearnerResponse,
    OrganizationSkillOutcomeResponse,
    OrganizationSnapshotResponse,
)
from app.schemas.user import SuccessResponse, UserRole, WorkspaceType
from app.services.auth_service import MockUser, mock_auth_service
from app.services.organization_service import mock_organization_service

router = APIRouter(prefix="/organization", tags=["organization"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: object) -> dict:
    return {"success": True, "data": data}


def _require_organization(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> MockUser:
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"
    user = mock_auth_service.current_user(authorization)
    if user.workspace_type is not WorkspaceType.ORGANIZATION or UserRole.CREATOR not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "An organization workspace with creator permission is required",
            },
        )
    return user


@router.get("", response_model=SuccessResponse[OrganizationSnapshotResponse])
def read_organization_snapshot(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return courses, learning-only learners, skill outcomes, and recent activity."""
    _require_organization(credentials)
    return _success(mock_organization_service.snapshot())


@router.get("/courses", response_model=SuccessResponse[list[OrganizationCourseResponse]])
def list_organization_courses(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """List learning content associated with the mock organization."""
    _require_organization(credentials)
    return _success(mock_organization_service.snapshot()["courses"])


@router.get("/courses/{course_id}", response_model=SuccessResponse[OrganizationCourseResponse])
def read_organization_course(
    course_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Read one course's lifecycle and available aggregate performance."""
    _require_organization(credentials)
    return _success(mock_organization_service.course(course_id))


@router.get("/learners", response_model=SuccessResponse[list[OrganizationLearnerResponse]])
def list_organization_learners(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """List learning-only learner progress without individual answers."""
    _require_organization(credentials)
    return _success(mock_organization_service.snapshot()["learners"])


@router.get("/learners/{learner_id}", response_model=SuccessResponse[OrganizationLearnerResponse])
def read_organization_learner(
    learner_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Read one learning-only learner outcome record."""
    _require_organization(credentials)
    return _success(mock_organization_service.learner(learner_id))


@router.get("/skills", response_model=SuccessResponse[list[OrganizationSkillOutcomeResponse]])
def list_organization_skills(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """List aggregate organization skill outcomes and coverage indicators."""
    _require_organization(credentials)
    return _success(mock_organization_service.snapshot()["skills"])
