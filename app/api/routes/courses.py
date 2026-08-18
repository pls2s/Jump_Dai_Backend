"""Function 2 course-configuration endpoint."""

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.course import (
    CourseCreateRequest,
    CourseResponse,
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
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
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
    )
    return _success(course.to_public_dict())
