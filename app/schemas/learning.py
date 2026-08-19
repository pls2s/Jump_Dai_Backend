"""Request and response contracts for Function 9.5 Personalized Learning Path."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LearningStyle(str, Enum):
    """Learning preferences a learner can use to tailor recommendations."""

    VISUAL = "VISUAL"
    AUDITORY = "AUDITORY"
    READING_WRITING = "READING_WRITING"
    KINESTHETIC = "KINESTHETIC"
    MIXED = "MIXED"


class LearnerLevel(str, Enum):
    """Level calculated from an assessment's overall score."""

    FOUNDATION = "FOUNDATION"
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class GapSeverity(str, Enum):
    """Severity used to prioritize a learner's knowledge and skill gaps."""

    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendationType(str, Enum):
    """Types of extra content offered for weak topics."""

    LESSON = "LESSON"
    EXERCISE = "EXERCISE"
    REFERENCE = "REFERENCE"


class TopicScoreInput(BaseModel):
    """A score for one topic in a learner assessment."""

    model_config = ConfigDict(str_strip_whitespace=True)

    topic: str = Field(min_length=1, max_length=120)
    score: float = Field(ge=0, le=100)


class LearningProfileUpdateRequest(BaseModel):
    """Goal and learning-style settings that personalize a learner's path."""

    model_config = ConfigDict(str_strip_whitespace=True)

    learning_goal: str = Field(min_length=1, max_length=300)
    target_role: Optional[str] = Field(default=None, max_length=120)
    learning_styles: list[LearningStyle] = Field(min_length=1, max_length=5)
    weekly_learning_hours: int = Field(default=4, ge=1, le=40)

    @model_validator(mode="after")
    def reject_duplicate_learning_styles(self) -> "LearningProfileUpdateRequest":
        if len(set(self.learning_styles)) != len(self.learning_styles):
            raise ValueError("learning_styles must not contain duplicates")
        return self


class PreAssessmentCreateRequest(BaseModel):
    """Scores from a learner's baseline pre-assessment."""

    model_config = ConfigDict(str_strip_whitespace=True)

    assessment_title: str = Field(min_length=1, max_length=200)
    topic_scores: list[TopicScoreInput] = Field(min_length=1, max_length=30)
    passing_score: float = Field(default=70, ge=1, le=100)

    @model_validator(mode="after")
    def reject_duplicate_topics(self) -> "PreAssessmentCreateRequest":
        normalized_topics = [item.topic.casefold() for item in self.topic_scores]
        if len(set(normalized_topics)) != len(normalized_topics):
            raise ValueError("topic_scores must not contain duplicate topics")
        return self


class LearningPathGenerateRequest(BaseModel):
    """Optionally select a prior pre-assessment when generating a path."""

    pre_assessment_id: Optional[int] = Field(default=None, ge=1)


class LearningPathAdaptRequest(BaseModel):
    """Latest assessment results used to adapt the learner's current path."""

    model_config = ConfigDict(str_strip_whitespace=True)

    assessment_title: str = Field(min_length=1, max_length=200)
    topic_scores: list[TopicScoreInput] = Field(min_length=1, max_length=30)
    passing_score: float = Field(default=70, ge=1, le=100)

    @model_validator(mode="after")
    def reject_duplicate_topics(self) -> "LearningPathAdaptRequest":
        normalized_topics = [item.topic.casefold() for item in self.topic_scores]
        if len(set(normalized_topics)) != len(normalized_topics):
            raise ValueError("topic_scores must not contain duplicate topics")
        return self


class LearningProfileResponse(BaseModel):
    """The learner's saved personalization preferences."""

    learner_id: int
    learning_goal: str
    target_role: Optional[str] = None
    learning_styles: list[LearningStyle]
    weekly_learning_hours: int
    updated_at: datetime


class TopicScoreResponse(TopicScoreInput):
    """A persisted topic score with no input-only changes."""


class PreAssessmentResponse(BaseModel):
    """A submitted baseline or adaptive assessment result."""

    id: int
    assessment_title: str
    topic_scores: list[TopicScoreResponse]
    passing_score: float = Field(ge=1, le=100)
    overall_score: float = Field(ge=0, le=100)
    learner_level: LearnerLevel
    submitted_at: datetime


class KnowledgeGapResponse(BaseModel):
    """A topic whose knowledge score is below the required threshold."""

    topic: str
    score: float = Field(ge=0, le=100)
    target_score: float = Field(ge=1, le=100)
    gap_score: float = Field(gt=0, le=100)
    severity: GapSeverity


class SkillGapResponse(BaseModel):
    """A skill area inferred as weak from a topic-level assessment result."""

    skill: str
    score: float = Field(ge=0, le=100)
    target_score: float = Field(ge=1, le=100)
    gap_score: float = Field(gt=0, le=100)
    severity: GapSeverity


class WeakTopicResponse(KnowledgeGapResponse):
    """A prioritized topic that needs remediation in the current path."""


class SkillGapAnalysisResponse(BaseModel):
    """Knowledge/skill gaps and weak topics calculated from an assessment."""

    assessment: PreAssessmentResponse
    knowledge_gaps: list[KnowledgeGapResponse]
    skill_gaps: list[SkillGapResponse]
    weak_topics: list[WeakTopicResponse]


class RecommendedLessonResponse(BaseModel):
    """A lesson selected for a learner based on one topic score."""

    id: str
    title: str
    topic: str
    level: LearnerLevel
    estimated_minutes: int = Field(gt=0)
    reason: str
    study_recommendations: list[str] = Field(min_length=1)


class AdditionalContentRecommendationResponse(BaseModel):
    """Extra lesson, exercise, or reference for a weak topic."""

    id: str
    topic: str
    content_type: RecommendationType
    title: str
    reason: str


class PersonalizedLearningPathResponse(BaseModel):
    """A learner-specific path generated from preferences and assessment results."""

    id: int
    learner_id: int
    learning_goal: str
    target_role: Optional[str] = None
    learning_styles: list[LearningStyle]
    weekly_learning_hours: int
    assessment_id: int
    assessment_title: str
    overall_score: float = Field(ge=0, le=100)
    learner_level: LearnerLevel
    version: int = Field(ge=1)
    is_adaptive: bool
    lessons: list[RecommendedLessonResponse]
    weak_topics: list[WeakTopicResponse]
    additional_content_recommendations: list[AdditionalContentRecommendationResponse]
    generated_at: datetime
    updated_at: datetime


class LearningPathAdaptationResponse(BaseModel):
    """A revised current path generated from the newest assessment results."""

    path: PersonalizedLearningPathResponse
    previous_assessment_id: int
    latest_assessment: PreAssessmentResponse
    changed_topics: list[str]
