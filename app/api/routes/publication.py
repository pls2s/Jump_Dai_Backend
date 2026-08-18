"""Function 6 course-publication and public catalog endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.ai import GeneratedLearningPath
from app.schemas.catalog import (
    CoursePublicationResponse,
    PublishedCourseDetail,
    PublishedCourseSummary,
)
from app.schemas.user import SuccessResponse, UserRole
from app.services.auth_service import MockUser, mock_auth_service
from app.services.course_service import MockCourse, mock_course_service

router = APIRouter(tags=["course-publication"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: object) -> dict:
    """Keep publication and catalog responses in the shared API envelope."""
    return {"success": True, "data": data}


def _require_creator(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> MockUser:
    """Authenticate one creator before allowing a publishing action."""
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"
    user = mock_auth_service.current_user(authorization)
    if UserRole.CREATOR not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "A creator workspace is required to publish a course",
            },
        )
    return user


def _learning_path(course: MockCourse) -> GeneratedLearningPath:
    """Convert the validated stored draft into the public response contract."""
    if course.generated_learning_path is None:
        raise RuntimeError("A published course must have a learning path")
    return GeneratedLearningPath.model_validate(course.generated_learning_path)


def _summary(course: MockCourse) -> dict:
    """Build catalog data without exposing Creator identity or source payloads."""
    learning_path = _learning_path(course)
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "target_learner": course.target_learner,
        "difficulty_level": course.difficulty_level,
        "learning_objective": course.learning_objective,
        "status": course.status,
        "module_count": len(learning_path.modules),
        "lesson_count": sum(len(module.lessons) for module in learning_path.modules),
        "published_at": course.published_at,
    }


@router.post(
    "/courses/{course_id}/publish",
    response_model=SuccessResponse[CoursePublicationResponse],
)
def publish_course(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Publish a Creator-owned course after its AI draft has been verified."""
    user = _require_creator(credentials)
    course = mock_course_service.publish_course(course_id=course_id, creator_id=user.id)
    return _success(
        {
            "course_id": course.id,
            "status": course.status,
            "published_at": course.published_at,
        }
    )


@router.get(
    "/catalog/courses",
    response_model=SuccessResponse[list[PublishedCourseSummary]],
)
def list_published_courses() -> dict:
    """List every published course; this endpoint intentionally needs no login."""
    courses = mock_course_service.list_published()
    return _success([_summary(course) for course in courses])


@router.get(
    "/catalog/courses/{course_id}",
    response_model=SuccessResponse[PublishedCourseDetail],
)
def read_published_course(course_id: int) -> dict:
    """Read a single published course and its verified learning path publicly."""
    course = mock_course_service.get_published(course_id=course_id)
    return _success({**_summary(course), "learning_path": _learning_path(course).model_dump(mode="json")})
