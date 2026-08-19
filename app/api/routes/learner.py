"""Learner enrollment, lesson access, and progress endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.learner import (
    EnrollmentResponse,
    LearnerCourseLearningPathResponse,
    LearnerLessonResponse,
    LearningProgressResponse,
)
from app.schemas.user import SuccessResponse, UserRole
from app.services.auth_service import MockUser, mock_auth_service
from app.services.course_service import mock_course_service
from app.services.learner_service import mock_learner_course_service

router = APIRouter(tags=["learner-learning"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: object) -> dict:
    """Keep learner-learning responses in the common success envelope."""
    return {"success": True, "data": data}


def _require_learner(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> MockUser:
    """Authenticate a caller and require the learner role."""
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"
    user = mock_auth_service.current_user(authorization)
    if UserRole.LEARNER not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "A learner workspace is required for learning access",
            },
        )
    return user


@router.post(
    "/courses/{course_id}/enroll",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[EnrollmentResponse],
)
def enroll_in_course(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Enroll the authenticated learner in a published course."""
    user = _require_learner(credentials)
    course = mock_course_service.get_published(course_id=course_id)
    enrollment = mock_learner_course_service.enroll(learner_id=user.id, course=course)
    return _success(
        mock_learner_course_service.enrollment_response(
            enrollment=enrollment,
            course=course,
        )
    )


@router.get(
    "/learning/courses/{course_id}/path",
    response_model=SuccessResponse[LearnerCourseLearningPathResponse],
)
def read_enrolled_course_learning_path(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return the published course path with the caller's completion state."""
    user = _require_learner(credentials)
    return _success(mock_learner_course_service.path_for(learner_id=user.id, course_id=course_id))


@router.get(
    "/lessons/{lesson_id}",
    response_model=SuccessResponse[LearnerLessonResponse],
)
def read_lesson(
    lesson_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Read one lesson only when it belongs to a course the learner enrolled in."""
    user = _require_learner(credentials)
    return _success(mock_learner_course_service.lesson_for(learner_id=user.id, lesson_id=lesson_id))


@router.post("/lessons/{lesson_id}/complete")
def complete_lesson(
    lesson_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Record a completed lesson and return updated course progress."""
    user = _require_learner(credentials)
    return _success(
        mock_learner_course_service.complete_lesson(learner_id=user.id, lesson_id=lesson_id)
    )


@router.get(
    "/learning/courses/{course_id}/progress",
    response_model=SuccessResponse[LearningProgressResponse],
)
def read_learning_progress(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return the learner's completion percentage for one enrolled course."""
    user = _require_learner(credentials)
    return _success(
        mock_learner_course_service.progress_for(learner_id=user.id, course_id=course_id)
    )
