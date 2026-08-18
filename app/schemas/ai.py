"""Function 4 contracts for source-grounded AI course generation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.course import CourseStatus


class GeneratedLesson(BaseModel):
    """One teachable unit generated from one or more source chunks."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=2_000)
    source_references: list[str] = Field(min_length=1, max_length=10)


class GeneratedModule(BaseModel):
    """A group of related generated lessons in a learning path."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2_000)
    learning_objectives: list[str] = Field(min_length=1, max_length=6)
    lessons: list[GeneratedLesson] = Field(min_length=1, max_length=8)


class LearningPathContent(BaseModel):
    """Editable content of a source-grounded learning-path draft."""

    overview: str = Field(min_length=1, max_length=3_000)
    modules: list[GeneratedModule] = Field(min_length=1, max_length=8)


class GeneratedLearningPath(LearningPathContent):
    """A creator-reviewable draft that must remain grounded in ready chunks."""

    course_id: int
    title: str = Field(min_length=1, max_length=200)


class LearningPathUpdateRequest(LearningPathContent):
    """Creator changes to an AI draft before it can be verified."""


class CourseGenerationResponse(BaseModel):
    """Completed synchronous generation result for the current MVP."""

    course_id: int
    status: CourseStatus
    progress: int = Field(ge=0, le=100)
    generated_at: datetime
    learning_path: GeneratedLearningPath


class CourseGenerationStatusResponse(BaseModel):
    """Pollable status for a course-generation attempt."""

    course_id: int
    status: CourseStatus
    progress: int = Field(ge=0, le=100)
    error: Optional[str] = None
    generated_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    has_learning_path: bool


class CourseVerificationResponse(BaseModel):
    """Confirmation that a Creator has accepted the reviewed learning path."""

    course_id: int
    status: CourseStatus
    verified_at: datetime
