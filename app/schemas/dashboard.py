"""Response contracts for Function 9: Creator Dashboard."""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReportExportFormat(str, Enum):
    """Report formats supported by the mock dashboard export."""

    CSV = "csv"
    JSON = "json"
    PDF = "pdf"


class DashboardFilters(BaseModel):
    """The query filters that produced a dashboard report."""

    course_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


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


class LearnerDashboardFilters(DashboardFilters):
    """Additional filters available on the paginated learner endpoint."""

    search: Optional[str] = None


class DashboardPagination(BaseModel):
    """Paging metadata for a creator's learner list."""

    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class LearnerDashboardResponse(BaseModel):
    """A searchable, paginated learner-progress section of the dashboard."""

    filters: LearnerDashboardFilters
    items: list[LearnerDashboardProgress]
    pagination: DashboardPagination


class CommonErrorDashboardResponse(BaseModel):
    """The independently loadable common-error section of the dashboard."""

    filters: DashboardFilters
    items: list[CommonErrorAnalysis]


class SkillGapDashboardResponse(BaseModel):
    """The independently loadable skill-gap section of the dashboard."""

    filters: DashboardFilters
    items: list[SkillGapOverview]


class CourseImprovementInsightDashboardResponse(BaseModel):
    """The independently loadable course-improvement section of the dashboard."""

    filters: DashboardFilters
    items: list[CourseImprovementInsight]
