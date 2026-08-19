"""Competency, quiz, and practical-assessment endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.assessment import (
    AssessmentAttemptResponse,
    AssessmentCreateRequest,
    AssessmentResponse,
    AssessmentReviewRequest,
    AssessmentSubmissionResponse,
    AssessmentSubmitRequest,
)
from app.schemas.user import SuccessResponse, UserRole
from app.services.assessment_service import mock_assessment_service
from app.services.auth_service import MockUser, mock_auth_service
from app.services.course_service import mock_course_service
from app.services.learner_service import mock_learner_course_service
from app.services.learning_service import mock_personalized_learning_service

router = APIRouter(tags=["assessments"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: object) -> dict:
    """Keep assessment responses in the common success envelope."""
    return {"success": True, "data": data}


def _current_user(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> MockUser:
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"
    return mock_auth_service.current_user(authorization)


def _require_creator(credentials: Optional[HTTPAuthorizationCredentials]) -> MockUser:
    user = _current_user(credentials)
    if UserRole.CREATOR not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "A creator workspace is required"},
        )
    return user


def _require_learner(credentials: Optional[HTTPAuthorizationCredentials]) -> MockUser:
    user = _current_user(credentials)
    if UserRole.LEARNER not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "A learner workspace is required"},
        )
    return user


@router.post(
    "/courses/{course_id}/assessments",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[AssessmentResponse],
)
def create_assessment(
    course_id: int,
    payload: AssessmentCreateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Let a Creator create a quiz, post-assessment, or practical task."""
    user = _require_creator(credentials)
    mock_course_service.get_for_creator(course_id=course_id, creator_id=user.id)
    assessment = mock_assessment_service.create(
        course_id=course_id,
        creator_id=user.id,
        title=payload.title,
        assessment_type=payload.assessment_type,
        topics=payload.topics,
        passing_score=payload.passing_score,
        is_final_assessment=payload.is_final_assessment,
    )
    return _success(mock_assessment_service.assessment_response(assessment))


@router.post(
    "/courses/{course_id}/assessments/generate",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[list[AssessmentResponse]],
)
def generate_course_assessments(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Create deterministic quiz, post-assessment, and practical-task definitions."""
    user = _require_creator(credentials)
    course = mock_course_service.get_for_creator(course_id=course_id, creator_id=user.id)
    assessments = mock_assessment_service.generate_for_course(course=course, creator_id=user.id)
    return _success(
        [mock_assessment_service.assessment_response(assessment) for assessment in assessments]
    )


@router.get(
    "/courses/{course_id}/assessments",
    response_model=SuccessResponse[list[AssessmentResponse]],
)
def list_course_assessments(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """List a Creator's assessments or the assessments for an enrolled learner."""
    user = _current_user(credentials)
    if UserRole.CREATOR in user.roles:
        mock_course_service.get_for_creator(course_id=course_id, creator_id=user.id)
    elif UserRole.LEARNER in user.roles:
        mock_learner_course_service.enrollment_for(learner_id=user.id, course_id=course_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "No assessment access for this role"},
        )
    return _success(
        [
            mock_assessment_service.assessment_response(assessment)
            for assessment in mock_assessment_service.list_for_course(course_id=course_id)
        ]
    )


@router.post(
    "/assessments/{assessment_id}/submit",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[AssessmentSubmissionResponse],
)
def submit_assessment(
    assessment_id: int,
    payload: AssessmentSubmitRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Record assessment evidence, feedback, and a personalized-path adaptation."""
    user = _require_learner(credentials)
    assessment = mock_assessment_service.get(assessment_id=assessment_id)
    mock_learner_course_service.enrollment_for(learner_id=user.id, course_id=assessment.course_id)
    attempt = mock_assessment_service.submit(
        assessment_id=assessment_id,
        learner_id=user.id,
        topic_scores=[(item.topic, item.score) for item in payload.topic_scores],
        evidence_url=payload.evidence_url,
        evidence_text=payload.evidence_text,
    )
    adapted_learning_path = None
    if mock_personalized_learning_service.has_current_path_for(learner_id=user.id):
        path, _, _, _ = mock_personalized_learning_service.adapt_current_path(
            learner_id=user.id,
            assessment_title=assessment.title,
            topic_scores=attempt.topic_scores,
            passing_score=assessment.passing_score,
        )
        adapted_learning_path = mock_personalized_learning_service.path_response(path)
    return _success(
        {
            "result": mock_assessment_service.attempt_response(attempt),
            "adapted_learning_path": adapted_learning_path,
        }
    )


@router.get(
    "/assessments/{assessment_id}/attempts",
    response_model=SuccessResponse[list[AssessmentAttemptResponse]],
)
def list_assessment_attempts(
    assessment_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Show a course owner the learner submissions for one assessment."""
    user = _require_creator(credentials)
    return _success(
        [
            mock_assessment_service.attempt_response(attempt)
            for attempt in mock_assessment_service.attempts_for_creator(
                assessment_id=assessment_id,
                creator_id=user.id,
            )
        ]
    )


@router.patch(
    "/assessments/{assessment_id}/attempts/{attempt_id}/review",
    response_model=SuccessResponse[AssessmentAttemptResponse],
)
def review_assessment_attempt(
    assessment_id: int,
    attempt_id: int,
    payload: AssessmentReviewRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Let an authorized Creator adjust an attempt with a recorded reason."""
    user = _require_creator(credentials)
    attempt = mock_assessment_service.review(
        assessment_id=assessment_id,
        attempt_id=attempt_id,
        creator_id=user.id,
        adjusted_score=payload.adjusted_score,
        reason=payload.reason,
    )
    return _success(mock_assessment_service.attempt_response(attempt))
