"""Public catalog contracts for verified, published AI courses."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.ai import GeneratedLearningPath
from app.schemas.course import CourseStatus, DifficultyLevel


class PublishedCourseSummary(BaseModel):
    """Safe course metadata shown in the learner-facing catalog."""

    id: int
    title: str
    description: str
    target_learner: str
    difficulty_level: DifficultyLevel
    learning_objective: str
    status: CourseStatus
    module_count: int = Field(ge=1)
    lesson_count: int = Field(ge=1)
    published_at: datetime


class PublishedCourseDetail(PublishedCourseSummary):
    """Catalog details including the Creator-verified learning path."""

    learning_path: GeneratedLearningPath


class CoursePublicationResponse(BaseModel):
    """Confirmation that a verified course is now visible to Learners."""

    course_id: int
    status: CourseStatus
    published_at: datetime
