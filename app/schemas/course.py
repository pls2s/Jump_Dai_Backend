"""Course-configuration contracts used by Function 2: Knowledge Upload."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CourseStatus(str, Enum):
    """A course starts as a draft while its knowledge sources are collected."""

    DRAFT = "DRAFT"


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


class CourseResponse(BaseModel):
    """Public course representation returned by the API."""

    id: int
    title: str
    description: str
    target_learner: str
    difficulty_level: DifficultyLevel
    certificate_available: bool
    learning_objective: str
    status: CourseStatus
    creator_id: int
    created_at: datetime
