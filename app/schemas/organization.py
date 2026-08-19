"""Read-only contracts for the mock Organization learning workspace."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OrganizationCourseStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"


class OrganizationLearnerStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    NOT_STARTED = "not-started"


class OrganizationSkillCoverage(str, Enum):
    STRONG = "strong"
    DEVELOPING = "developing"
    NEEDS_ATTENTION = "needs-attention"


class OrganizationIdentityResponse(BaseModel):
    id: str
    name: str
    learning_focus: str


class OrganizationTotalsResponse(BaseModel):
    active_courses: int = Field(ge=0)
    active_learners: int = Field(ge=0)
    completion_rate: float = Field(ge=0, le=100)
    verified_skills: int = Field(ge=0)
    average_improvement: float


class OrganizationFunnelMetricResponse(BaseModel):
    id: str
    label: str
    value: int = Field(ge=0)


class OrganizationAssessmentMetricResponse(BaseModel):
    pre_assessment_average: float = Field(ge=0, le=100)
    post_assessment_average: float = Field(ge=0, le=100)
    average_improvement: float
    practical_pass_rate: float = Field(ge=0, le=100)


class OrganizationSkillMetricResponse(BaseModel):
    skill_id: str
    name: str
    pre_score: float = Field(ge=0, le=100)
    post_score: float = Field(ge=0, le=100)
    improvement: float
    practical_pass_rate: float = Field(ge=0, le=100)
    retry_rate: float = Field(ge=0, le=100)
    common_challenge: str


class OrganizationContentMetricResponse(BaseModel):
    id: str
    title: str
    content_type: str
    completion_rate: float = Field(ge=0, le=100)
    quiz_score: Optional[float] = Field(default=None, ge=0, le=100)
    retry_rate: float = Field(ge=0, le=100)


class OrganizationCourseAnalyticsResponse(BaseModel):
    course_id: str
    title: str
    status: OrganizationCourseStatus
    learner_count: int = Field(ge=0)
    active_learners: int = Field(ge=0)
    course_starts: int = Field(ge=0)
    completions: int = Field(ge=0)
    completion_rate: float = Field(ge=0, le=100)
    average_assessment_score: float = Field(ge=0, le=100)
    practical_pass_rate: float = Field(ge=0, le=100)
    verified_skills: int = Field(ge=0)
    funnel: list[OrganizationFunnelMetricResponse]
    assessment: OrganizationAssessmentMetricResponse
    skills: list[OrganizationSkillMetricResponse]
    content: list[OrganizationContentMetricResponse]


class OrganizationCourseResponse(BaseModel):
    id: str
    title: str
    status: OrganizationCourseStatus
    updated_at: str
    owner_name: str
    analytics: Optional[OrganizationCourseAnalyticsResponse] = None


class OrganizationLearnerCourseResponse(BaseModel):
    course_id: str
    course_title: str
    progress: float = Field(ge=0, le=100)
    status: OrganizationLearnerStatus


class OrganizationLearnerResponse(BaseModel):
    id: str
    name: str
    current_learning: list[OrganizationLearnerCourseResponse]
    completed_courses: int = Field(ge=0)
    verified_skills: list[str]
    last_activity: str


class OrganizationSkillOutcomeResponse(OrganizationSkillMetricResponse):
    learner_count: int = Field(ge=0)
    coverage: OrganizationSkillCoverage


class OrganizationActivityResponse(BaseModel):
    id: str
    label: str
    detail: str
    occurred_at: str


class OrganizationSnapshotResponse(BaseModel):
    organization: OrganizationIdentityResponse
    totals: OrganizationTotalsResponse
    courses: list[OrganizationCourseResponse]
    learners: list[OrganizationLearnerResponse]
    skills: list[OrganizationSkillOutcomeResponse]
    recent_activity: list[OrganizationActivityResponse]
