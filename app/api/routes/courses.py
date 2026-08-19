"""Function 2 course-configuration endpoint."""

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional

from app.schemas.course import (
    CourseCreateRequest,
    CourseResponse,
    CourseUpdateRequest,
)
from app.schemas.user import SuccessResponse, UserRole
from app.services.auth_service import MockUser, mock_auth_service
from app.services.course_service import mock_course_service

router = APIRouter(prefix="/courses", tags=["knowledge-upload"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: object) -> dict:
    """Keep successful Function 2 responses in the documented envelope."""
    return {"success": True, "data": data}


def _require_creator(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> MockUser:
    """Authenticate the request and require the creator role."""
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"

    user = mock_auth_service.current_user(authorization)
    if UserRole.CREATOR not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "A creator workspace is required for knowledge upload",
            },
        )
    return user


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[CourseResponse],
)
def create_course(
    payload: CourseCreateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Create the Function 2 course context before sources are uploaded."""
    user = _require_creator(credentials)
    course = mock_course_service.create(
        creator_id=user.id,
        title=payload.title,
        description=payload.description,
        target_learner=payload.target_learner,
        difficulty_level=payload.difficulty_level,
        learning_objective=payload.learning_objective,
        certificate_available=payload.certificate_available,
        certificate_passing_score=payload.certificate_passing_score,
    )
    return _success(course.to_public_dict())


@router.get("", response_model=SuccessResponse[list[CourseResponse]])
def list_courses(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """List course configurations that belong to the authenticated Creator."""
    user = _require_creator(credentials)
    courses = mock_course_service.list_for_creator(creator_id=user.id)
    return _success([course.to_public_dict() for course in courses])


@router.get("/{course_id}", response_model=SuccessResponse[CourseResponse])
def read_course(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Read one owned course configuration before the source-upload step."""
    user = _require_creator(credentials)
    course = mock_course_service.get_for_creator(course_id=course_id, creator_id=user.id)
    return _success(course.to_public_dict())


@router.put("/{course_id}", response_model=SuccessResponse[CourseResponse])
def update_course(
    course_id: int,
    payload: CourseUpdateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Update an editable draft course and its certificate configuration."""
    user = _require_creator(credentials)
    course = mock_course_service.update(
        course_id=course_id,
        creator_id=user.id,
        title=payload.title,
        description=payload.description,
        target_learner=payload.target_learner,
        difficulty_level=payload.difficulty_level,
        learning_objective=payload.learning_objective,
        certificate_available=payload.certificate_available,
        certificate_passing_score=payload.certificate_passing_score,
    )
    return _success(course.to_public_dict())


@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Delete an editable course; generated/published courses remain protected."""
    user = _require_creator(credentials)
    mock_course_service.delete(course_id=course_id, creator_id=user.id)
    return {"success": True}
