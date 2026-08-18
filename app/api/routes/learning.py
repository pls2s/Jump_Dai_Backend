"""Function 9.5 Personalized Learning Path endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.learning import (
    LearningPathAdaptRequest,
    LearningPathAdaptationResponse,
    LearningPathGenerateRequest,
    LearningProfileResponse,
    LearningProfileUpdateRequest,
    PersonalizedLearningPathResponse,
    PreAssessmentCreateRequest,
    PreAssessmentResponse,
    SkillGapAnalysisResponse,
)
from app.schemas.user import SuccessResponse, UserRole
from app.services.auth_service import MockUser, mock_auth_service
from app.services.learning_service import mock_personalized_learning_service

router = APIRouter(prefix="/learning", tags=["personalized-learning-path"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: object) -> dict:
    """Keep personalized-learning responses in the shared success envelope."""
    return {"success": True, "data": data}


def _require_learner(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> MockUser:
    """Authenticate the caller and require the learner application role."""
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"
    user = mock_auth_service.current_user(authorization)
    if UserRole.LEARNER not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "A learner workspace is required for Personalized Learning Path",
            },
        )
    return user


@router.put(
    "/profile",
    response_model=SuccessResponse[LearningProfileResponse],
)
def save_learning_profile(
    payload: LearningProfileUpdateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Save the learner's learning goal and preferred learning styles."""
    user = _require_learner(credentials)
    profile = mock_personalized_learning_service.save_profile(
        learner_id=user.id,
        learning_goal=payload.learning_goal,
        target_role=payload.target_role,
        learning_styles=payload.learning_styles,
        weekly_learning_hours=payload.weekly_learning_hours,
    )
    return _success(mock_personalized_learning_service.profile_response(profile))


@router.get(
    "/profile",
    response_model=SuccessResponse[LearningProfileResponse],
)
def read_learning_profile(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return the current learner's saved personalized-learning preferences."""
    user = _require_learner(credentials)
    profile = mock_personalized_learning_service.profile_for(learner_id=user.id)
    return _success(mock_personalized_learning_service.profile_response(profile))


@router.post(
    "/pre-assessments",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[PreAssessmentResponse],
)
def submit_pre_assessment(
    payload: PreAssessmentCreateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Record baseline topic scores before generating a personalized path."""
    user = _require_learner(credentials)
    assessment = mock_personalized_learning_service.record_pre_assessment(
        learner_id=user.id,
        assessment_title=payload.assessment_title,
        topic_scores=[(item.topic, item.score) for item in payload.topic_scores],
        passing_score=payload.passing_score,
    )
    return _success(mock_personalized_learning_service.assessment_response(assessment))


@router.get(
    "/skill-gap-analysis",
    response_model=SuccessResponse[SkillGapAnalysisResponse],
)
def read_skill_gap_analysis(
    pre_assessment_id: Optional[int] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Analyze knowledge gaps, inferred skill gaps, and weak topics from assessment scores."""
    user = _require_learner(credentials)
    return _success(
        mock_personalized_learning_service.gap_analysis_for(
            learner_id=user.id,
            assessment_id=pre_assessment_id,
        )
    )


@router.post(
    "/paths",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[PersonalizedLearningPathResponse],
)
def generate_personalized_learning_path(
    payload: LearningPathGenerateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Generate a learner-specific mock AI path from goals, styles, and assessment data."""
    user = _require_learner(credentials)
    path = mock_personalized_learning_service.generate_path(
        learner_id=user.id,
        assessment_id=payload.pre_assessment_id,
    )
    return _success(mock_personalized_learning_service.path_response(path))


@router.get(
    "/paths/current",
    response_model=SuccessResponse[PersonalizedLearningPathResponse],
)
def read_current_personalized_learning_path(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return the learner's latest generated or adaptively revised learning path."""
    user = _require_learner(credentials)
    path = mock_personalized_learning_service.current_path_for(learner_id=user.id)
    return _success(mock_personalized_learning_service.path_response(path))


@router.post(
    "/paths/current/adapt",
    response_model=SuccessResponse[LearningPathAdaptationResponse],
)
def adapt_current_personalized_learning_path(
    payload: LearningPathAdaptRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Revise the current path from the latest assessment and identify changed topics."""
    user = _require_learner(credentials)
    path, previous_assessment_id, latest_assessment, changed_topics = (
        mock_personalized_learning_service.adapt_current_path(
            learner_id=user.id,
            assessment_title=payload.assessment_title,
            topic_scores=[(item.topic, item.score) for item in payload.topic_scores],
            passing_score=payload.passing_score,
        )
    )
    return _success(
        {
            "path": mock_personalized_learning_service.path_response(path),
            "previous_assessment_id": previous_assessment_id,
            "latest_assessment": mock_personalized_learning_service.assessment_response(
                latest_assessment
            ),
            "changed_topics": changed_topics,
        }
    )
