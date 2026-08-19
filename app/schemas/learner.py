"""Learner enrollment, lesson access, and progress API contracts."""

from datetime import datetime

from pydantic import BaseModel, Field


class EnrollmentResponse(BaseModel):
    """A learner's enrollment in one published course."""

    course_id: int
    course_title: str
    enrolled_at: datetime


class LearnerLessonResponse(BaseModel):
    """A generated course lesson as presented to an enrolled learner."""

    id: str
    course_id: int
    module_title: str
    title: str
    summary: str
    source_references: list[str]
    completed: bool


class LearnerCourseLearningPathResponse(BaseModel):
    """The enrolled learner's path, including completion state for each lesson."""

    course_id: int
    course_title: str
    overview: str
    enrolled_at: datetime
    progress_percentage: float = Field(ge=0, le=100)
    completed_lesson_count: int = Field(ge=0)
    total_lesson_count: int = Field(ge=1)
    lessons: list[LearnerLessonResponse]


class LearningProgressResponse(BaseModel):
    """A compact current-progress result for an enrolled course."""

    course_id: int
    progress_percentage: float = Field(ge=0, le=100)
    completed_lesson_count: int = Field(ge=0)
    total_lesson_count: int = Field(ge=1)
    completed: bool
    last_activity_at: datetime
