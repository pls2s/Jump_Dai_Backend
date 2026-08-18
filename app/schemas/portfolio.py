"""Request and response contracts for Function 9.7 Skill Evidence / Portfolio."""

from datetime import datetime
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompetencyLevel(str, Enum):
    """Learner competency bands calculated from verified assessment scores."""

    FOUNDATION = "FOUNDATION"
    DEVELOPING = "DEVELOPING"
    PROFICIENT = "PROFICIENT"
    ADVANCED = "ADVANCED"


class CredentialType(str, Enum):
    """Verifiable credentials that can appear in a learner portfolio."""

    DIGITAL_BADGE = "DIGITAL_BADGE"
    CERTIFICATE = "CERTIFICATE"


class CredentialStatus(str, Enum):
    """The current validity state returned by public credential verification."""

    VALID = "VALID"
    REVOKED = "REVOKED"


class SkillEvidenceCreateRequest(BaseModel):
    """A learner's practical-assessment evidence submitted to the mock MVP."""

    model_config = ConfigDict(str_strip_whitespace=True)

    course_id: int = Field(ge=1)
    course_title: str = Field(min_length=1, max_length=200)
    assessment_id: str = Field(min_length=1, max_length=100)
    assessment_title: str = Field(min_length=1, max_length=200)
    skill: str = Field(min_length=1, max_length=120)
    score: float = Field(ge=0, le=100)
    passing_score: float = Field(default=70, ge=0, le=100)
    evidence_title: str = Field(min_length=1, max_length=200)
    evidence_url: Optional[str] = Field(default=None, max_length=2_048)
    is_course_final_assessment: bool = False

    @field_validator("evidence_url")
    @classmethod
    def validate_evidence_url(cls, value: Optional[str]) -> Optional[str]:
        """Permit an optional HTTP(S) link to the submitted practical work."""
        if value is None:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("evidence_url must be an absolute HTTP or HTTPS address")
        return value


class EvidenceResponse(BaseModel):
    """A practical-assessment record preserved for a learner."""

    id: int
    course_id: int
    course_title: str
    assessment_id: str
    assessment_title: str
    skill: str
    score: float = Field(ge=0, le=100)
    passing_score: float = Field(ge=0, le=100)
    verified: bool
    competency_level: CompetencyLevel
    evidence_title: str
    evidence_url: Optional[str] = None
    is_course_final_assessment: bool
    submitted_at: datetime


class VerifiedSkillResponse(BaseModel):
    """A skill proven by one or more passing practical assessments."""

    skill: str
    competency_score: float = Field(ge=0, le=100)
    competency_level: CompetencyLevel
    evidence: list[EvidenceResponse]


class CredentialResponse(BaseModel):
    """A Digital Badge or Certificate issued from verified learner evidence."""

    id: str
    credential_type: CredentialType
    status: CredentialStatus
    learner_name: str
    course_id: Optional[int] = None
    course_title: Optional[str] = None
    skill: Optional[str] = None
    competency_score: Optional[float] = Field(default=None, ge=0, le=100)
    issued_at: datetime


class SkillEvidenceSubmissionResponse(BaseModel):
    """Evidence result plus credentials newly issued by this submission."""

    evidence: EvidenceResponse
    verified_skill: Optional[VerifiedSkillResponse] = None
    issued_badge: Optional[CredentialResponse] = None
    issued_certificate: Optional[CredentialResponse] = None


class SkillPortfolioResponse(BaseModel):
    """A learner-facing portfolio generated from verified evidence and credentials."""

    learner_id: int
    learner_name: str
    skills: list[VerifiedSkillResponse]
    credentials: list[CredentialResponse]
    generated_at: datetime


class PortfolioShareResponse(BaseModel):
    """The public, revocable-in-a-future-version link for a learner portfolio."""

    share_token: str
    share_url: str
    created_at: datetime


class SharedSkillPortfolioResponse(SkillPortfolioResponse):
    """A portfolio resolved through a public share link."""

    share_token: str


class CredentialVerificationResponse(BaseModel):
    """Public verification result for a Digital Badge or Certificate."""

    credential: CredentialResponse
    verified_at: datetime
