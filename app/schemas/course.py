"""Course-configuration contracts used by Function 2: Knowledge Upload."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CourseStatus(str, Enum):
    """Lifecycle state for a course and its generated learning-path draft."""

    DRAFT = "DRAFT"
    GENERATING = "GENERATING"
    WAITING_VERIFICATION = "WAITING_VERIFICATION"
    VERIFIED = "VERIFIED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class DifficultyLevel(str, Enum):
    """Difficulty choices collected while configuring a knowledge course."""

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class CourseCreateRequest(BaseModel):
    """Function 2 metadata collected before adding knowledge sources."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5_000)
    target_learner: str = Field(min_length=1, max_length=500)
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    learning_objective: str = Field(min_length=1, max_length=2_000)
    certificate_available: Optional[bool] = None
    certificate_passing_score: Optional[float] = Field(default=None, ge=1, le=100)

    @model_validator(mode="after")
    def validate_certificate_fields(self) -> "CourseCreateRequest":
        if self.certificate_available is False and self.certificate_passing_score is not None:
            raise ValueError("certificate_passing_score requires certificate_available")
        return self


class CourseUpdateRequest(BaseModel):
    """Creator changes to an editable draft course configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=1, max_length=5_000)
    target_learner: Optional[str] = Field(default=None, min_length=1, max_length=500)
    difficulty_level: Optional[DifficultyLevel] = None
    learning_objective: Optional[str] = Field(default=None, min_length=1, max_length=2_000)
    certificate_available: Optional[bool] = None
    certificate_passing_score: Optional[float] = Field(default=None, ge=1, le=100)

    @model_validator(mode="after")
    def require_change_and_validate_certificate_fields(self) -> "CourseUpdateRequest":
        if all(value is None for value in self.model_dump().values()):
            raise ValueError("provide at least one course field to update")
        if self.certificate_available is False and self.certificate_passing_score is not None:
            raise ValueError("certificate_passing_score requires certificate_available")
        return self


class CourseResponse(BaseModel):
    """Public course representation returned by the API."""

    id: int
    title: str
    description: str
    target_learner: str
    difficulty_level: DifficultyLevel
    certificate_available: bool
    certificate_passing_score: Optional[float] = Field(default=None, ge=1, le=100)
    learning_objective: str
    status: CourseStatus
    creator_id: int
    created_at: datetime
