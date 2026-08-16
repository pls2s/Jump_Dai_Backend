"""Course management endpoints."""

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.course import (
    CourseCreateRequest,
    CourseResponse,
    CourseSummary,
    CourseUpdateRequest,
)
from app.schemas.user import SuccessResponse, UserRole
from app.services.auth_service import MockUser, mock_auth_service
from app.services.course_service import mock_course_service

router = APIRouter(prefix="/courses", tags=["courses"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: object) -> dict:
    """Keep every successful course response in the documented envelope."""
    return {"success": True, "data": data}


def _require_creator(
    credentials: HTTPAuthorizationCredentials | None,
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
                "message": "A creator workspace is required for course management",
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
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    """Create a course in DRAFT status for the current creator."""
    user = _require_creator(credentials)
    course = mock_course_service.create(
        creator_id=user.id,
        title=payload.title,
        description=payload.description,
        goal=payload.goal,
        difficulty_level=payload.difficulty_level,
        certification_enabled=payload.certification_enabled,
    )
    return _success(course.to_public_dict())


@router.get("", response_model=SuccessResponse[list[CourseSummary]])
def list_courses(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    """List courses owned by the current creator."""
    user = _require_creator(credentials)
    courses = mock_course_service.list_for_creator(creator_id=user.id)
    return _success(
        [
            {"id": course.id, "title": course.title, "status": course.status}
            for course in courses
        ]
    )


@router.get(
    "/{course_id}",
    response_model=SuccessResponse[CourseResponse],
)
def get_course(
    course_id: int,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    """Return one course after checking creator ownership."""
    user = _require_creator(credentials)
    course = mock_course_service.get_for_creator(
        course_id=course_id,
        creator_id=user.id,
    )
    return _success(course.to_public_dict())


@router.put(
    "/{course_id}",
    response_model=SuccessResponse[CourseResponse],
)
def update_course(
    course_id: int,
    payload: CourseUpdateRequest,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    """Update course metadata after checking creator ownership."""
    user = _require_creator(credentials)
    course = mock_course_service.update(
        course_id=course_id,
        creator_id=user.id,
        updates=payload.model_dump(exclude_unset=True),
    )
    return _success(course.to_public_dict())


@router.delete(
    "/{course_id}",
)
def delete_course(
    course_id: int,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    """Delete an owned course and return a confirmation envelope."""
    user = _require_creator(credentials)
    mock_course_service.delete(course_id=course_id, creator_id=user.id)
    return {"success": True}
