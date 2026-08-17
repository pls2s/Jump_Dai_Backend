"""Response contracts for Function 9: Creator Dashboard."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class ReportExportFormat(str, Enum):
    """Report formats supported by the mock dashboard export."""

    CSV = "csv"
    JSON = "json"
    PDF = "pdf"


class DashboardFilters(BaseModel):
    """The query filters that produced a dashboard report."""

    course_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None


class DashboardSummary(BaseModel):
    """Top-level aggregate metrics shown to a creator."""

    course_count: int
    learner_count: int
    completed_learner_count: int
    completion_rate: float = Field(ge=0, le=100)
    average_assessment_score: float = Field(ge=0, le=100)


class CourseDashboardMetric(BaseModel):
    """Dashboard metrics grouped by an owned course."""

    course_id: int
    course_title: str
    learner_count: int
    completed_learner_count: int
    completion_rate: float = Field(ge=0, le=100)
    average_assessment_score: float = Field(ge=0, le=100)


class LearnerDashboardProgress(BaseModel):
    """Per-learner progress and assessment data visible to the course owner."""

    learner_id: int
    learner_name: str
    course_id: int
    course_title: str
    progress_percentage: float = Field(ge=0, le=100)
    assessment_score: float = Field(ge=0, le=100)
    completed: bool
    last_activity_at: datetime
    common_errors: list[str]
    skill_gaps: list[str]


class CommonErrorAnalysis(BaseModel):
    """A frequently missed topic calculated from assessment attempts."""

    course_id: int
    course_title: str
    topic: str
    occurrence_count: int
    affected_learner_count: int


class SkillGapOverview(BaseModel):
    """A skill area where one or more learners need additional support."""

    course_id: int
    course_title: str
    skill: str
    affected_learner_count: int


class CourseImprovementInsight(BaseModel):
    """A data-driven recommendation for a creator's course."""

    course_id: int
    course_title: str
    code: str
    severity: str
    message: str
    recommendation: str


class CreatorDashboardResponse(BaseModel):
    """Complete Function 9 dashboard payload for a creator."""

    filters: DashboardFilters
    summary: DashboardSummary
    courses: list[CourseDashboardMetric]
    learners: list[LearnerDashboardProgress]
    common_errors: list[CommonErrorAnalysis]
    skill_gaps: list[SkillGapOverview]
    course_improvement_insights: list[CourseImprovementInsight]
