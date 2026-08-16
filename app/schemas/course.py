"""Request and response contracts for course management."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CourseStatus(str, Enum):
    """Statuses used by the course lifecycle described in the API contract."""

    DRAFT = "DRAFT"
    GENERATING = "GENERATING"
    WAITING_VERIFICATION = "WAITING_VERIFICATION"
    VERIFIED = "VERIFIED"
    PUBLISHED = "PUBLISHED"


class DifficultyLevel(str, Enum):
    """Difficulty choices collected while configuring a knowledge course."""

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class CourseCreateRequest(BaseModel):
    """Fields required when a creator starts a new course."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5_000)
    goal: str = Field(min_length=1, max_length=2_000)
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    certification_enabled: bool = False


class CourseUpdateRequest(BaseModel):
    """Optional course fields that can be changed by its creator."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=5_000)
    goal: str | None = Field(default=None, min_length=1, max_length=2_000)
    difficulty_level: DifficultyLevel | None = None
    certification_enabled: bool | None = None

    @field_validator(
        "title",
        "description",
        "goal",
        "difficulty_level",
        "certification_enabled",
    )
    @classmethod
    def reject_null_update_values(cls, value: object) -> object:
        """Treat explicit nulls as invalid instead of clearing required fields."""
        if value is None:
            raise ValueError("course update fields cannot be null")
        return value

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "CourseUpdateRequest":
        """Reject an update request that would not change anything."""
        if (
            self.title is None
            and self.description is None
            and self.goal is None
            and self.difficulty_level is None
            and self.certification_enabled is None
        ):
            raise ValueError("at least one course field must be provided")
        return self


class CourseResponse(BaseModel):
    """Public course representation returned by the API."""

    id: int
    title: str
    description: str
    goal: str
    difficulty_level: DifficultyLevel
    certification_enabled: bool
    status: CourseStatus
    creator_id: int
    created_at: datetime


class CourseSummary(BaseModel):
    """Compact course representation used by the creator dashboard list."""

    id: int
    title: str
    status: CourseStatus
