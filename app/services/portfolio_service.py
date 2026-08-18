"""Temporary in-memory Skill Evidence / Portfolio implementation for Function 9.7."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from secrets import token_urlsafe
from threading import RLock
from typing import Optional

from fastapi import HTTPException, status

from app.schemas.portfolio import CompetencyLevel, CredentialStatus, CredentialType


@dataclass(frozen=True)
class MockSkillEvidence:
    """A practical-assessment submission tied to one learner and one skill."""

    id: int
    learner_id: int
    course_id: int
    course_title: str
    assessment_id: str
    assessment_title: str
    skill: str
    score: float
    passing_score: float
    evidence_title: str
    evidence_url: Optional[str]
    is_course_final_assessment: bool
    submitted_at: datetime

    @property
    def verified(self) -> bool:
        """A skill is proven only when its practical score reaches the threshold."""
        return self.score >= self.passing_score


@dataclass(frozen=True)
class MockCredential:
    """A verifiable badge or certificate derived from passing evidence."""

    id: str
    learner_id: int
    learner_name: str
    credential_type: CredentialType
    course_id: Optional[int]
    course_title: Optional[str]
    skill: Optional[str]
    competency_score: Optional[float]
    status: CredentialStatus
    issued_at: datetime


@dataclass(frozen=True)
class MockPortfolioShare:
    """A public share token owned by one learner."""

    token: str
    learner_id: int
    learner_name: str
    created_at: datetime


class MockSkillPortfolioService:
    """Thread-safe mock persistence for practical evidence and learner credentials."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reset()

    def reset(self) -> None:
        """Clear process-local evidence, credentials, and portfolio links."""
        with self._lock:
            self._evidence: dict[int, MockSkillEvidence] = {}
            self._credentials: dict[str, MockCredential] = {}
            self._shares_by_token: dict[str, MockPortfolioShare] = {}
            self._share_token_by_learner: dict[int, str] = {}
            self._next_evidence_id = 1
            self._next_credential_id = 1

    def record_evidence(
        self,
        *,
        learner_id: int,
        learner_name: str,
        course_id: int,
        course_title: str,
        assessment_id: str,
        assessment_title: str,
        skill: str,
        score: float,
        passing_score: float,
        evidence_title: str,
        evidence_url: Optional[str],
        is_course_final_assessment: bool,
    ) -> tuple[MockSkillEvidence, Optional[MockCredential], Optional[MockCredential]]:
        """Store practical evidence and issue eligible badge/certificate credentials."""
        with self._lock:
            evidence = MockSkillEvidence(
                id=self._next_evidence_id,
                learner_id=learner_id,
                course_id=course_id,
                course_title=course_title,
                assessment_id=assessment_id,
                assessment_title=assessment_title,
                skill=skill,
                score=score,
                passing_score=passing_score,
                evidence_title=evidence_title,
                evidence_url=evidence_url,
                is_course_final_assessment=is_course_final_assessment,
                submitted_at=datetime.now(timezone.utc),
            )
            self._evidence[evidence.id] = evidence
            self._next_evidence_id += 1

            badge = None
            certificate = None
            if evidence.verified:
                badge = self._issue_badge_if_needed(
                    learner_id=learner_id,
                    learner_name=learner_name,
                    evidence=evidence,
                )
                if evidence.is_course_final_assessment:
                    certificate = self._issue_certificate_if_needed(
                        learner_id=learner_id,
                        learner_name=learner_name,
                        evidence=evidence,
                    )
            return evidence, badge, certificate

    def portfolio_for(self, *, learner_id: int, learner_name: str) -> dict:
        """Build the current portfolio from only verified skill evidence."""
        with self._lock:
            return self._portfolio_locked(learner_id=learner_id, learner_name=learner_name)

    def create_share(self, *, learner_id: int, learner_name: str) -> MockPortfolioShare:
        """Create one stable public link per learner for this mock implementation."""
        with self._lock:
            existing_token = self._share_token_by_learner.get(learner_id)
            if existing_token is not None:
                return self._shares_by_token[existing_token]

            share = MockPortfolioShare(
                token=token_urlsafe(18),
                learner_id=learner_id,
                learner_name=learner_name,
                created_at=datetime.now(timezone.utc),
            )
            self._shares_by_token[share.token] = share
            self._share_token_by_learner[learner_id] = share.token
            return share

    def shared_portfolio(self, *, share_token: str) -> dict:
        """Resolve a public portfolio link without requiring authentication."""
        with self._lock:
            share = self._shares_by_token.get(share_token)
            if share is None:
                self._raise_not_found(
                    "PORTFOLIO_SHARE_NOT_FOUND",
                    "This portfolio share link is invalid or no longer available",
                )
            portfolio = self._portfolio_locked(
                learner_id=share.learner_id,
                learner_name=share.learner_name,
            )
            return {"share_token": share.token, **portfolio}

    def verify_credential(self, *, credential_id: str) -> MockCredential:
        """Return the credential's current status for a public verification page."""
        with self._lock:
            credential = self._credentials.get(credential_id)
            if credential is None:
                self._raise_not_found(
                    "CREDENTIAL_NOT_FOUND",
                    "No Digital Badge or Certificate exists for this credential ID",
                )
            return credential

    def _portfolio_locked(self, *, learner_id: int, learner_name: str) -> dict:
        evidence_by_skill: dict[str, list[MockSkillEvidence]] = defaultdict(list)
        for evidence in self._evidence.values():
            if evidence.learner_id == learner_id and evidence.verified:
                evidence_by_skill[evidence.skill].append(evidence)

        skills = []
        for skill, evidence_items in evidence_by_skill.items():
            competency_score = round(max(item.score for item in evidence_items), 2)
            skills.append(
                {
                    "skill": skill,
                    "competency_score": competency_score,
                    "competency_level": self.competency_level(competency_score),
                    "evidence": [
                        self.evidence_response(item)
                        for item in sorted(evidence_items, key=lambda item: item.submitted_at)
                    ],
                }
            )

        credentials = [
            self.credential_response(credential)
            for credential in self._credentials.values()
            if credential.learner_id == learner_id
        ]
        return {
            "learner_id": learner_id,
            "learner_name": learner_name,
            "skills": sorted(skills, key=lambda item: item["skill"].casefold()),
            "credentials": sorted(credentials, key=lambda item: item["issued_at"]),
            "generated_at": datetime.now(timezone.utc),
        }

    def _issue_badge_if_needed(
        self,
        *,
        learner_id: int,
        learner_name: str,
        evidence: MockSkillEvidence,
    ) -> Optional[MockCredential]:
        if self._has_credential(
            learner_id=learner_id,
            credential_type=CredentialType.DIGITAL_BADGE,
            course_id=evidence.course_id,
            skill=evidence.skill,
        ):
            return None
        return self._create_credential(
            learner_id=learner_id,
            learner_name=learner_name,
            credential_type=CredentialType.DIGITAL_BADGE,
            course_id=evidence.course_id,
            course_title=evidence.course_title,
            skill=evidence.skill,
            competency_score=evidence.score,
        )

    def _issue_certificate_if_needed(
        self,
        *,
        learner_id: int,
        learner_name: str,
        evidence: MockSkillEvidence,
    ) -> Optional[MockCredential]:
        if self._has_credential(
            learner_id=learner_id,
            credential_type=CredentialType.CERTIFICATE,
            course_id=evidence.course_id,
            skill=None,
        ):
            return None
        return self._create_credential(
            learner_id=learner_id,
            learner_name=learner_name,
            credential_type=CredentialType.CERTIFICATE,
            course_id=evidence.course_id,
            course_title=evidence.course_title,
            skill=None,
            competency_score=evidence.score,
        )

    def _has_credential(
        self,
        *,
        learner_id: int,
        credential_type: CredentialType,
        course_id: Optional[int],
        skill: Optional[str],
    ) -> bool:
        for credential in self._credentials.values():
            if (
                credential.learner_id != learner_id
                or credential.credential_type is not credential_type
            ):
                continue
            if credential_type is CredentialType.DIGITAL_BADGE:
                if credential.skill == skill:
                    return True
            elif credential.course_id == course_id:
                return True
        return False

    def _create_credential(
        self,
        *,
        learner_id: int,
        learner_name: str,
        credential_type: CredentialType,
        course_id: Optional[int],
        course_title: Optional[str],
        skill: Optional[str],
        competency_score: Optional[float],
    ) -> MockCredential:
        credential = MockCredential(
            id=f"credential-{self._next_credential_id}",
            learner_id=learner_id,
            learner_name=learner_name,
            credential_type=credential_type,
            course_id=course_id,
            course_title=course_title,
            skill=skill,
            competency_score=competency_score,
            status=CredentialStatus.VALID,
            issued_at=datetime.now(timezone.utc),
        )
        self._credentials[credential.id] = credential
        self._next_credential_id += 1
        return credential

    @staticmethod
    def competency_level(score: float) -> CompetencyLevel:
        """Map a 0-100 assessment score to the portfolio competency label."""
        if score >= 85:
            return CompetencyLevel.ADVANCED
        if score >= 70:
            return CompetencyLevel.PROFICIENT
        if score >= 50:
            return CompetencyLevel.DEVELOPING
        return CompetencyLevel.FOUNDATION

    def evidence_response(self, evidence: MockSkillEvidence) -> dict:
        """Serialize private evidence data into the public API representation."""
        return {
            "id": evidence.id,
            "course_id": evidence.course_id,
            "course_title": evidence.course_title,
            "assessment_id": evidence.assessment_id,
            "assessment_title": evidence.assessment_title,
            "skill": evidence.skill,
            "score": evidence.score,
            "passing_score": evidence.passing_score,
            "verified": evidence.verified,
            "competency_level": self.competency_level(evidence.score),
            "evidence_title": evidence.evidence_title,
            "evidence_url": evidence.evidence_url,
            "is_course_final_assessment": evidence.is_course_final_assessment,
            "submitted_at": evidence.submitted_at,
        }

    @staticmethod
    def credential_response(credential: MockCredential) -> dict:
        """Serialize a verifiable credential for private or public portfolio views."""
        return {
            "id": credential.id,
            "credential_type": credential.credential_type,
            "status": credential.status,
            "learner_name": credential.learner_name,
            "course_id": credential.course_id,
            "course_title": credential.course_title,
            "skill": credential.skill,
            "competency_score": credential.competency_score,
            "issued_at": credential.issued_at,
        }

    @staticmethod
    def _raise_not_found(code: str, message: str) -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": code, "message": message},
        )


mock_skill_portfolio_service = MockSkillPortfolioService()
