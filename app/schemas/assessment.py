"""Competency, quiz, and practical-assessment API contracts."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.learning import PersonalizedLearningPathResponse, TopicScoreInput, TopicScoreResponse


class AssessmentType(str, Enum):
    """Assessment variants required by the MVP specification."""

    QUIZ = "QUIZ"
    POST_ASSESSMENT = "POST_ASSESSMENT"
    PRACTICAL = "PRACTICAL"


class AssessmentCreateRequest(BaseModel):
    """Creator-defined assessment metadata and topics to evaluate."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    assessment_type: AssessmentType
    topics: list[str] = Field(min_length=1, max_length=30)
    passing_score: float = Field(default=70, ge=1, le=100)
    is_final_assessment: bool = False

    @model_validator(mode="after")
    def reject_duplicate_topics(self) -> "AssessmentCreateRequest":
        normalized = [topic.casefold() for topic in self.topics]
        if len(set(normalized)) != len(normalized):
            raise ValueError("topics must not contain duplicates")
        return self


class AssessmentResponse(BaseModel):
    """Assessment available to the creator or to an enrolled learner."""

    id: int
    course_id: int
    title: str
    assessment_type: AssessmentType
    topics: list[str]
    passing_score: float = Field(ge=1, le=100)
    is_final_assessment: bool
    created_at: datetime


class AssessmentSubmitRequest(BaseModel):
    """A learner's topic scores and optional practical-work evidence."""

    model_config = ConfigDict(str_strip_whitespace=True)

    topic_scores: list[TopicScoreInput] = Field(min_length=1, max_length=30)
    evidence_url: Optional[str] = Field(default=None, max_length=2_048)
    evidence_text: Optional[str] = Field(default=None, max_length=5_000)

    @model_validator(mode="after")
    def reject_duplicate_topics(self) -> "AssessmentSubmitRequest":
        normalized = [item.topic.casefold() for item in self.topic_scores]
        if len(set(normalized)) != len(normalized):
            raise ValueError("topic_scores must not contain duplicate topics")
        return self


class AssessmentReviewRequest(BaseModel):
    """Creator's documented adjustment to a learner assessment result."""

    adjusted_score: float = Field(ge=0, le=100)
    reason: str = Field(min_length=1, max_length=1_000)


class AssessmentAttemptResponse(BaseModel):
    """Result, competency feedback, and any creator review for one submission."""

    id: int
    assessment_id: int
    learner_id: int
    topic_scores: list[TopicScoreResponse]
    score: float = Field(ge=0, le=100)
    passing_score: float = Field(ge=1, le=100)
    passed: bool
    skill_score: float = Field(ge=0, le=100)
    strengths: list[str]
    improvements: list[str]
    feedback: str
    evidence_url: Optional[str] = None
    evidence_text: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    review_reason: Optional[str] = None


class AssessmentSubmissionResponse(BaseModel):
    """A completed result, optionally accompanied by an adapted personal path."""

    result: AssessmentAttemptResponse
    adapted_learning_path: Optional[PersonalizedLearningPathResponse] = None
