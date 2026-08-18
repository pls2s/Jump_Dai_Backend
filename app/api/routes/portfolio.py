"""Function 9.7 Skill Evidence / Portfolio endpoints."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.portfolio import (
    CredentialVerificationResponse,
    PortfolioShareResponse,
    SharedSkillPortfolioResponse,
    SkillEvidenceCreateRequest,
    SkillEvidenceSubmissionResponse,
    SkillPortfolioResponse,
)
from app.schemas.user import SuccessResponse, UserRole
from app.services.auth_service import MockUser, mock_auth_service
from app.services.portfolio_service import mock_skill_portfolio_service

router = APIRouter(tags=["skill-portfolio"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: object) -> dict:
    """Keep successful evidence and portfolio responses in the common envelope."""
    return {"success": True, "data": data}


def _require_learner(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> MockUser:
    """Authenticate the current user and require the learner application role."""
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"
    user = mock_auth_service.current_user(authorization)
    if UserRole.LEARNER not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "A learner workspace is required for Skill Evidence and Portfolio",
            },
        )
    return user


@router.post(
    "/skill-evidence",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[SkillEvidenceSubmissionResponse],
)
def submit_practical_evidence(
    payload: SkillEvidenceCreateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Store practical work, verify eligible skills, and issue mock credentials."""
    user = _require_learner(credentials)
    evidence, badge, certificate = mock_skill_portfolio_service.record_evidence(
        learner_id=user.id,
        learner_name=user.name,
        course_id=payload.course_id,
        course_title=payload.course_title,
        assessment_id=payload.assessment_id,
        assessment_title=payload.assessment_title,
        skill=payload.skill,
        score=payload.score,
        passing_score=payload.passing_score,
        evidence_title=payload.evidence_title,
        evidence_url=payload.evidence_url,
        is_course_final_assessment=payload.is_course_final_assessment,
    )
    evidence_response = mock_skill_portfolio_service.evidence_response(evidence)
    verified_skill = None
    if evidence.verified:
        portfolio = mock_skill_portfolio_service.portfolio_for(
            learner_id=user.id,
            learner_name=user.name,
        )
        verified_skill = next(
            skill for skill in portfolio["skills"] if skill["skill"] == evidence.skill
        )
    return _success(
        {
            "evidence": evidence_response,
            "verified_skill": verified_skill,
            "issued_badge": (
                mock_skill_portfolio_service.credential_response(badge)
                if badge is not None
                else None
            ),
            "issued_certificate": (
                mock_skill_portfolio_service.credential_response(certificate)
                if certificate is not None
                else None
            ),
        }
    )


@router.get(
    "/skill-portfolio",
    response_model=SuccessResponse[SkillPortfolioResponse],
)
def read_skill_portfolio(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return the current learner's verified skills, linked evidence, and credentials."""
    user = _require_learner(credentials)
    return _success(
        mock_skill_portfolio_service.portfolio_for(
            learner_id=user.id,
            learner_name=user.name,
        )
    )


@router.post(
    "/skill-portfolio/share",
    response_model=SuccessResponse[PortfolioShareResponse],
)
def create_skill_portfolio_share_link(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Create or retrieve the learner's public Skill Portfolio link."""
    user = _require_learner(credentials)
    share = mock_skill_portfolio_service.create_share(
        learner_id=user.id,
        learner_name=user.name,
    )
    share_path = f"/api/skill-portfolio/shared/{share.token}"
    return _success(
        {
            "share_token": share.token,
            "share_url": f"{str(request.base_url).rstrip('/')}{share_path}",
            "created_at": share.created_at,
        }
    )


@router.get(
    "/skill-portfolio/shared/{share_token}",
    response_model=SuccessResponse[SharedSkillPortfolioResponse],
)
def read_shared_skill_portfolio(share_token: str) -> dict:
    """Return a portfolio intentionally shared by its learner without authentication."""
    return _success(mock_skill_portfolio_service.shared_portfolio(share_token=share_token))


@router.get(
    "/credentials/{credential_id}/verify",
    response_model=SuccessResponse[CredentialVerificationResponse],
)
def verify_credential(credential_id: str) -> dict:
    """Verify the authenticity and current status of a public credential."""
    credential = mock_skill_portfolio_service.verify_credential(credential_id=credential_id)
    return _success(
        {
            "credential": mock_skill_portfolio_service.credential_response(credential),
            "verified_at": datetime.now(timezone.utc),
        }
    )
