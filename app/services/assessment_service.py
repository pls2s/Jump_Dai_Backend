"""In-memory competency, quiz, and practical-assessment service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Optional

from fastapi import HTTPException, status

from app.schemas.assessment import AssessmentType
from app.schemas.ai import GeneratedLearningPath
from app.services.course_service import MockCourse


@dataclass(frozen=True)
class MockAssessmentDefinition:
    """A creator-owned assessment for one course."""

    id: int
    course_id: int
    creator_id: int
    title: str
    assessment_type: AssessmentType
    topics: list[str]
    passing_score: float
    is_final_assessment: bool
    created_at: datetime


@dataclass
class MockAssessmentAttempt:
    """One learner result, with an optional creator score adjustment."""

    id: int
    assessment_id: int
    learner_id: int
    topic_scores: list[tuple[str, float]]
    evidence_url: Optional[str]
    evidence_text: Optional[str]
    submitted_at: datetime
    adjusted_score: Optional[float] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    review_reason: Optional[str] = None


class MockAssessmentService:
    """Thread-safe assessment definitions, learner attempts, and review decisions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reset()

    def reset(self) -> None:
        """Clear assessment definitions and submitted results."""
        with self._lock:
            self._assessments: dict[int, MockAssessmentDefinition] = {}
            self._attempts: dict[int, MockAssessmentAttempt] = {}
            self._next_assessment_id = 1
            self._next_attempt_id = 1

    def create(
        self,
        *,
        course_id: int,
        creator_id: int,
        title: str,
        assessment_type: AssessmentType,
        topics: list[str],
        passing_score: float,
        is_final_assessment: bool,
    ) -> MockAssessmentDefinition:
        """Create a creator-configured quiz, post assessment, or practical task."""
        with self._lock:
            assessment = MockAssessmentDefinition(
                id=self._next_assessment_id,
                course_id=course_id,
                creator_id=creator_id,
                title=title,
                assessment_type=assessment_type,
                topics=list(topics),
                passing_score=passing_score,
                is_final_assessment=is_final_assessment,
                created_at=datetime.now(timezone.utc),
            )
            self._assessments[assessment.id] = assessment
            self._next_assessment_id += 1
            return assessment

    def generate_for_course(self, *, course: MockCourse, creator_id: int) -> list[MockAssessmentDefinition]:
        """Create deterministic assessment definitions from a generated course draft."""
        if course.generated_learning_path is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ASSESSMENT_GENERATION_REQUIRES_LEARNING_PATH",
                    "message": "Generate a course learning path before creating assessments",
                },
            )
        learning_path = GeneratedLearningPath.model_validate(course.generated_learning_path)
        topics = [lesson.title for module in learning_path.modules for lesson in module.lessons]
        return [
            self.create(
                course_id=course.id,
                creator_id=creator_id,
                title=f"{course.title} knowledge quiz",
                assessment_type=AssessmentType.QUIZ,
                topics=topics,
                passing_score=70,
                is_final_assessment=False,
            ),
            self.create(
                course_id=course.id,
                creator_id=creator_id,
                title=f"{course.title} post-assessment",
                assessment_type=AssessmentType.POST_ASSESSMENT,
                topics=topics,
                passing_score=70,
                is_final_assessment=True,
            ),
            self.create(
                course_id=course.id,
                creator_id=creator_id,
                title=f"{course.title} practical task",
                assessment_type=AssessmentType.PRACTICAL,
                topics=topics,
                passing_score=70,
                is_final_assessment=True,
            ),
        ]

    def list_for_course(self, *, course_id: int) -> list[MockAssessmentDefinition]:
        """List definitions in creation order for one course."""
        with self._lock:
            return [
                assessment
                for assessment in self._assessments.values()
                if assessment.course_id == course_id
            ]

    def get(self, *, assessment_id: int) -> MockAssessmentDefinition:
        """Return an assessment definition or a shared not-found response."""
        with self._lock:
            assessment = self._assessments.get(assessment_id)
            if assessment is None:
                self._raise_assessment_not_found()
            return assessment

    def submit(
        self,
        *,
        assessment_id: int,
        learner_id: int,
        topic_scores: list[tuple[str, float]],
        evidence_url: Optional[str],
        evidence_text: Optional[str],
    ) -> MockAssessmentAttempt:
        """Store a learner result after ensuring it covers the configured topics."""
        with self._lock:
            assessment = self.get(assessment_id=assessment_id)
            expected_topics = {topic.casefold() for topic in assessment.topics}
            submitted_topics = {topic.casefold() for topic, _ in topic_scores}
            if expected_topics != submitted_topics:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "code": "ASSESSMENT_TOPICS_MISMATCH",
                        "message": "Submit one score for every topic in this assessment",
                    },
                )
            if assessment.assessment_type is AssessmentType.PRACTICAL and not (
                evidence_url or evidence_text
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "code": "PRACTICAL_EVIDENCE_REQUIRED",
                        "message": "A practical assessment requires evidence_url or evidence_text",
                    },
                )
            attempt = MockAssessmentAttempt(
                id=self._next_attempt_id,
                assessment_id=assessment_id,
                learner_id=learner_id,
                topic_scores=list(topic_scores),
                evidence_url=evidence_url,
                evidence_text=evidence_text,
                submitted_at=datetime.now(timezone.utc),
            )
            self._attempts[attempt.id] = attempt
            self._next_attempt_id += 1
            return attempt

    def attempts_for_creator(
        self,
        *,
        assessment_id: int,
        creator_id: int,
    ) -> list[MockAssessmentAttempt]:
        """List attempts only when the caller owns the assessment's course."""
        with self._lock:
            assessment = self.get(assessment_id=assessment_id)
            if assessment.creator_id != creator_id:
                self._raise_assessment_not_found()
            return [
                attempt
                for attempt in self._attempts.values()
                if attempt.assessment_id == assessment_id
            ]

    def attempts_for_learner(
        self,
        *,
        assessment_id: int,
        learner_id: int,
    ) -> list[MockAssessmentAttempt]:
        """Return only the signed-in learner's submissions for one assessment."""
        with self._lock:
            self.get(assessment_id=assessment_id)
            return [
                attempt
                for attempt in self._attempts.values()
                if attempt.assessment_id == assessment_id and attempt.learner_id == learner_id
            ]

    def review(
        self,
        *,
        assessment_id: int,
        attempt_id: int,
        creator_id: int,
        adjusted_score: float,
        reason: str,
    ) -> MockAssessmentAttempt:
        """Apply a creator-authorized documented adjustment to one learner result."""
        with self._lock:
            assessment = self.get(assessment_id=assessment_id)
            if assessment.creator_id != creator_id:
                self._raise_assessment_not_found()
            attempt = self._attempts.get(attempt_id)
            if attempt is None or attempt.assessment_id != assessment_id:
                self._raise_attempt_not_found()
            attempt.adjusted_score = adjusted_score
            attempt.reviewed_by = creator_id
            attempt.review_reason = reason
            attempt.reviewed_at = datetime.now(timezone.utc)
            return attempt

    def assessment_response(self, assessment: MockAssessmentDefinition) -> dict:
        """Serialize an assessment definition."""
        return {
            "id": assessment.id,
            "course_id": assessment.course_id,
            "title": assessment.title,
            "assessment_type": assessment.assessment_type,
            "topics": assessment.topics,
            "passing_score": assessment.passing_score,
            "is_final_assessment": assessment.is_final_assessment,
            "created_at": assessment.created_at,
        }

    def attempt_response(self, attempt: MockAssessmentAttempt) -> dict:
        """Serialize one result with calculated score, feedback, and skill gaps."""
        assessment = self.get(assessment_id=attempt.assessment_id)
        raw_score = round(
            sum(score for _, score in attempt.topic_scores) / len(attempt.topic_scores),
            2,
        )
        score = attempt.adjusted_score if attempt.adjusted_score is not None else raw_score
        strengths = [topic for topic, topic_score in attempt.topic_scores if topic_score >= 85]
        improvements = [
            topic
            for topic, topic_score in attempt.topic_scores
            if topic_score < assessment.passing_score
        ]
        feedback = (
            "You met the assessment target. Continue strengthening advanced topics."
            if score >= assessment.passing_score
            else "Focus on the listed improvement topics before your next attempt."
        )
        if attempt.review_reason:
            feedback = f"{feedback} Creator review: {attempt.review_reason}"
        return {
            "id": attempt.id,
            "assessment_id": assessment.id,
            "learner_id": attempt.learner_id,
            "topic_scores": [
                {"topic": topic, "score": score} for topic, score in attempt.topic_scores
            ],
            "score": score,
            "passing_score": assessment.passing_score,
            "passed": score >= assessment.passing_score,
            "skill_score": score,
            "strengths": strengths,
            "improvements": improvements,
            "feedback": feedback,
            "evidence_url": attempt.evidence_url,
            "evidence_text": attempt.evidence_text,
            "submitted_at": attempt.submitted_at,
            "reviewed_at": attempt.reviewed_at,
            "reviewed_by": attempt.reviewed_by,
            "review_reason": attempt.review_reason,
        }

    @staticmethod
    def _raise_assessment_not_found() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ASSESSMENT_NOT_FOUND",
                "message": "No accessible assessment exists with this ID",
            },
        )

    @staticmethod
    def _raise_attempt_not_found() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ASSESSMENT_ATTEMPT_NOT_FOUND",
                "message": "No attempt exists for this assessment and ID",
            },
        )


mock_assessment_service = MockAssessmentService()
