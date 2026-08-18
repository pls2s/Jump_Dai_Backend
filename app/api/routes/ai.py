"""Function 4 AI course-generation endpoints backed by source-grounded chunks."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.ai import (
    CourseGenerationResponse,
    CourseGenerationStatusResponse,
    CourseVerificationResponse,
    GeneratedLearningPath,
    LearningPathUpdateRequest,
)
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
            "verified_at": course.verified_at,
            "has_learning_path": course.generated_learning_path is not None,
        }
    )


def _get_learning_path_or_raise(course_id: int, creator_id: int) -> GeneratedLearningPath:
    """Load an owned generated draft, or describe why a review cannot begin."""
    course = mock_course_service.get_for_creator(course_id=course_id, creator_id=creator_id)
    if course.generated_learning_path is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "LEARNING_PATH_NOT_READY_FOR_VERIFICATION",
                "message": "Generate a learning path before reviewing it",
            },
        )
    return GeneratedLearningPath.model_validate(course.generated_learning_path)


@router.get(
    "/courses/{course_id}/learning-path",
    response_model=SuccessResponse[GeneratedLearningPath],
)
def read_learning_path(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Read the generated learning path that belongs to the authenticated Creator."""
    user = _require_creator(credentials)
    learning_path = _get_learning_path_or_raise(course_id=course_id, creator_id=user.id)
    return _success(learning_path.model_dump(mode="json"))


@router.put(
    "/courses/{course_id}/learning-path",
    response_model=SuccessResponse[GeneratedLearningPath],
)
def update_learning_path(
    course_id: int,
    payload: LearningPathUpdateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Save a Creator's edits while enforcing references to ready source chunks."""
    user = _require_creator(credentials)
    course = mock_course_service.get_for_creator(course_id=course_id, creator_id=user.id)
    learning_path = GeneratedLearningPath(
        course_id=course.id,
        title=course.title,
        overview=payload.overview,
        modules=payload.modules,
    )
    chunks = mock_knowledge_processing_service.list_for_course(course_id=course_id)
    try:
        typhoon_ai_service.validate_learning_path(learning_path=learning_path, chunks=chunks)
    except AIResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "LEARNING_PATH_INVALID_SOURCE_REFERENCE", "message": str(exc)},
        )

    mock_course_service.update_learning_path(
        course_id=course_id,
        creator_id=user.id,
        learning_path=learning_path.model_dump(mode="json"),
    )
    return _success(learning_path.model_dump(mode="json"))


@router.post(
    "/courses/{course_id}/verify",
    response_model=SuccessResponse[CourseVerificationResponse],
)
def verify_learning_path(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Mark an edited AI draft as verified; publishing is intentionally separate."""
    user = _require_creator(credentials)
    course = mock_course_service.verify_learning_path(
        course_id=course_id,
        creator_id=user.id,
    )
    return _success(
        {
            "course_id": course.id,
            "status": course.status,
            "verified_at": course.verified_at,
        }
    )
