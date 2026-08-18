"""Function 4 AI course-generation endpoints backed by source-grounded chunks."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.ai import CourseGenerationResponse, CourseGenerationStatusResponse
from app.schemas.user import SuccessResponse, UserRole
from app.services.ai_service import (
    AIConfigurationError,
    AIProviderError,
    AIResponseError,
    typhoon_ai_service,
)
from app.services.auth_service import MockUser, mock_auth_service
from app.services.course_service import mock_course_service
from app.services.knowledge_service import mock_knowledge_processing_service

router = APIRouter(tags=["ai-generation"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: object) -> dict:
    """Keep successful Function 4 responses in the shared API envelope."""
    return {"success": True, "data": data}


def _require_creator(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> MockUser:
    """Authenticate the request and require a creator workspace role."""
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"
    user = mock_auth_service.current_user(authorization)
    if UserRole.CREATOR not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "A creator workspace is required for AI generation",
            },
        )
    return user


@router.post(
    "/courses/{course_id}/generate",
    response_model=SuccessResponse[CourseGenerationResponse],
)
def generate_course(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Generate a source-cited learning-path draft with the configured Typhoon model."""
    user = _require_creator(credentials)
    course = mock_course_service.get_for_creator(course_id=course_id, creator_id=user.id)
    chunks = mock_knowledge_processing_service.list_for_course(course_id=course_id)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "AI_GENERATION_REQUIRES_READY_SOURCE",
                "message": "Process at least one text-based knowledge source before generating",
            },
        )

    mock_course_service.start_generation(course_id=course_id, creator_id=user.id)
    try:
        learning_path = typhoon_ai_service.generate_learning_path(course=course, chunks=chunks)
    except AIConfigurationError as exc:
        mock_course_service.fail_generation(
            course_id=course_id,
            creator_id=user.id,
            message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "AI_PROVIDER_NOT_CONFIGURED", "message": str(exc)},
        )
    except AIResponseError as exc:
        mock_course_service.fail_generation(
            course_id=course_id,
            creator_id=user.id,
            message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "AI_RESPONSE_INVALID", "message": str(exc)},
        )
    except AIProviderError as exc:
        mock_course_service.fail_generation(
            course_id=course_id,
            creator_id=user.id,
            message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "AI_PROVIDER_ERROR", "message": str(exc)},
        )

    completed_course = mock_course_service.complete_generation(
        course_id=course_id,
        creator_id=user.id,
        learning_path=learning_path.model_dump(mode="json"),
    )
    return _success(
        {
            "course_id": completed_course.id,
            "status": completed_course.status,
            "progress": completed_course.generation_progress,
            "generated_at": completed_course.generated_at,
            "learning_path": learning_path.model_dump(mode="json"),
        }
    )


@router.get(
    "/courses/{course_id}/generation-status",
    response_model=SuccessResponse[CourseGenerationStatusResponse],
)
def read_generation_status(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return the latest Typhoon generation state for a creator-owned course."""
    user = _require_creator(credentials)
    course = mock_course_service.generation_status(course_id=course_id, creator_id=user.id)
    return _success(
        {
            "course_id": course.id,
            "status": course.status,
            "progress": course.generation_progress,
            "error": course.generation_error,
            "generated_at": course.generated_at,
            "has_learning_path": course.generated_learning_path is not None,
        }
    )
