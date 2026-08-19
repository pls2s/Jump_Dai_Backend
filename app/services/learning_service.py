"""Temporary in-memory Personalized Learning Path implementation for Function 9.5."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from threading import RLock
from typing import Optional

from fastapi import HTTPException, status

from app.schemas.learning import (
    GapSeverity,
    LearnerLevel,
    LearningStyle,
    RecommendationType,
)


@dataclass(frozen=True)
class MockLearningProfile:
    """Learner preferences used to tailor lesson selection."""

    learner_id: int
    learning_goal: str
    target_role: Optional[str]
    learning_styles: list[LearningStyle]
    weekly_learning_hours: int
    updated_at: datetime


@dataclass(frozen=True)
class MockAssessment:
    """A baseline or latest-assessment score set held for one learner."""

    id: int
    learner_id: int
    assessment_title: str
    topic_scores: list[tuple[str, float]]
    passing_score: float
    submitted_at: datetime


@dataclass(frozen=True)
class MockLearningPath:
    """A generated path whose current assessment can later be replaced adaptively."""

    id: int
    learner_id: int
    assessment_id: int
    version: int
    is_adaptive: bool
    generated_at: datetime
    updated_at: datetime


class MockPersonalizedLearningService:
    """Thread-safe mock persistence and deterministic path generation for Function 9.5."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reset()

    def reset(self) -> None:
        """Clear process-local learner settings, assessments, and generated paths."""
        with self._lock:
            self._profiles: dict[int, MockLearningProfile] = {}
            self._assessments: dict[int, MockAssessment] = {}
            self._assessment_ids_by_learner: dict[int, list[int]] = {}
            self._paths_by_learner: dict[int, MockLearningPath] = {}
            self._next_assessment_id = 1
            self._next_path_id = 1

    def save_profile(
        self,
        *,
        learner_id: int,
        learning_goal: str,
        target_role: Optional[str],
        learning_styles: list[LearningStyle],
        weekly_learning_hours: int,
    ) -> MockLearningProfile:
        """Create or replace the current learner's goal and learning preferences."""
        with self._lock:
            profile = MockLearningProfile(
                learner_id=learner_id,
                learning_goal=learning_goal,
                target_role=target_role,
                learning_styles=list(learning_styles),
                weekly_learning_hours=weekly_learning_hours,
                updated_at=datetime.now(timezone.utc),
            )
            self._profiles[learner_id] = profile
            return profile

    def profile_for(self, *, learner_id: int) -> MockLearningProfile:
        """Return a learner's saved preferences or the shared not-found error."""
        with self._lock:
            return self._profile_locked(learner_id)

    def record_pre_assessment(
        self,
        *,
        learner_id: int,
        assessment_title: str,
        topic_scores: list[tuple[str, float]],
        passing_score: float,
    ) -> MockAssessment:
        """Persist a baseline assessment that may subsequently generate a path."""
        with self._lock:
            return self._record_assessment_locked(
                learner_id=learner_id,
                assessment_title=assessment_title,
                topic_scores=topic_scores,
                passing_score=passing_score,
            )

    def assessment_for(
        self,
        *,
        learner_id: int,
        assessment_id: Optional[int] = None,
    ) -> MockAssessment:
        """Resolve an owned assessment, defaulting to the learner's most recent one."""
        with self._lock:
            if assessment_id is not None:
                assessment = self._assessments.get(assessment_id)
                if assessment is None or assessment.learner_id != learner_id:
                    self._raise_not_found(
                        "PRE_ASSESSMENT_NOT_FOUND",
                        "No pre-assessment exists for this learner and assessment ID",
                    )
                return assessment
            assessment_ids = self._assessment_ids_by_learner.get(learner_id, [])
            if not assessment_ids:
                self._raise_not_found(
                    "PRE_ASSESSMENT_NOT_FOUND",
                    "Submit a pre-assessment before requesting gap analysis or a learning path",
                )
            return self._assessments[assessment_ids[-1]]

    def gap_analysis_for(
        self,
        *,
        learner_id: int,
        assessment_id: Optional[int] = None,
    ) -> dict:
        """Calculate knowledge gaps, inferred skill gaps, and weak topics."""
        with self._lock:
            assessment = self.assessment_for(
                learner_id=learner_id,
                assessment_id=assessment_id,
            )
            return self._gap_analysis_locked(assessment)

    def generate_path(
        self,
        *,
        learner_id: int,
        assessment_id: Optional[int],
    ) -> MockLearningPath:
        """Generate a deterministic mock AI path from profile and assessment inputs."""
        with self._lock:
            self._profile_locked(learner_id)
            assessment = self.assessment_for(
                learner_id=learner_id,
                assessment_id=assessment_id,
            )
            now = datetime.now(timezone.utc)
            path = MockLearningPath(
                id=self._next_path_id,
                learner_id=learner_id,
                assessment_id=assessment.id,
                version=1,
                is_adaptive=False,
                generated_at=now,
                updated_at=now,
            )
            self._paths_by_learner[learner_id] = path
            self._next_path_id += 1
            return path

    def current_path_for(self, *, learner_id: int) -> MockLearningPath:
        """Return the learner's current generated path."""
        with self._lock:
            path = self._paths_by_learner.get(learner_id)
            if path is None:
                self._raise_not_found(
                    "LEARNING_PATH_NOT_FOUND",
                    "Generate a personalized learning path before viewing or adapting it",
                )
            return path

    def has_current_path_for(self, *, learner_id: int) -> bool:
        """Check whether an assessment result can adapt an existing learner path."""
        with self._lock:
            return learner_id in self._paths_by_learner

    def adapt_current_path(
        self,
        *,
        learner_id: int,
        assessment_title: str,
        topic_scores: list[tuple[str, float]],
        passing_score: float,
    ) -> tuple[MockLearningPath, int, MockAssessment, list[str]]:
        """Replace the current path's source assessment with the latest learner results."""
        with self._lock:
            existing_path = self.current_path_for(learner_id=learner_id)
            previous_assessment = self._assessments[existing_path.assessment_id]
            latest_assessment = self._record_assessment_locked(
                learner_id=learner_id,
                assessment_title=assessment_title,
                topic_scores=topic_scores,
                passing_score=passing_score,
            )
            updated_path = replace(
                existing_path,
                assessment_id=latest_assessment.id,
                version=existing_path.version + 1,
                is_adaptive=True,
                updated_at=datetime.now(timezone.utc),
            )
            self._paths_by_learner[learner_id] = updated_path
            previous_topics = dict(previous_assessment.topic_scores)
            changed_topics = [
                topic
                for topic, score in latest_assessment.topic_scores
                if previous_topics.get(topic) != score
            ]
            return updated_path, previous_assessment.id, latest_assessment, changed_topics

    def profile_response(self, profile: MockLearningProfile) -> dict:
        """Serialize saved learner preferences."""
        return {
            "learner_id": profile.learner_id,
            "learning_goal": profile.learning_goal,
            "target_role": profile.target_role,
            "learning_styles": profile.learning_styles,
            "weekly_learning_hours": profile.weekly_learning_hours,
            "updated_at": profile.updated_at,
        }

    def assessment_response(self, assessment: MockAssessment) -> dict:
        """Serialize an assessment with its calculated overall level."""
        overall_score = self._overall_score(assessment)
        return {
            "id": assessment.id,
            "assessment_title": assessment.assessment_title,
            "topic_scores": [
                {"topic": topic, "score": score}
                for topic, score in assessment.topic_scores
            ],
            "passing_score": assessment.passing_score,
            "overall_score": overall_score,
            "learner_level": self.learner_level(overall_score),
            "submitted_at": assessment.submitted_at,
        }

    def path_response(self, path: MockLearningPath) -> dict:
        """Build the current personalized lesson and additional-content selection."""
        with self._lock:
            profile = self._profile_locked(path.learner_id)
            assessment = self._assessments[path.assessment_id]
            analysis = self._gap_analysis_locked(assessment)
            overall_score = self._overall_score(assessment)
            return {
                "id": path.id,
                "learner_id": path.learner_id,
                "learning_goal": profile.learning_goal,
                "target_role": profile.target_role,
                "learning_styles": profile.learning_styles,
                "weekly_learning_hours": profile.weekly_learning_hours,
                "assessment_id": assessment.id,
                "assessment_title": assessment.assessment_title,
                "overall_score": overall_score,
                "learner_level": self.learner_level(overall_score),
                "version": path.version,
                "is_adaptive": path.is_adaptive,
                "lessons": self._recommended_lessons(
                    assessment=assessment,
                    learning_styles=profile.learning_styles,
                ),
                "weak_topics": analysis["weak_topics"],
                "additional_content_recommendations": self._additional_content(assessment),
                "generated_at": path.generated_at,
                "updated_at": path.updated_at,
            }

    def _record_assessment_locked(
        self,
        *,
        learner_id: int,
        assessment_title: str,
        topic_scores: list[tuple[str, float]],
        passing_score: float,
    ) -> MockAssessment:
        assessment = MockAssessment(
            id=self._next_assessment_id,
            learner_id=learner_id,
            assessment_title=assessment_title,
            topic_scores=list(topic_scores),
            passing_score=passing_score,
            submitted_at=datetime.now(timezone.utc),
        )
        self._assessments[assessment.id] = assessment
        self._assessment_ids_by_learner.setdefault(learner_id, []).append(assessment.id)
        self._next_assessment_id += 1
        return assessment

    def _profile_locked(self, learner_id: int) -> MockLearningProfile:
        profile = self._profiles.get(learner_id)
        if profile is None:
            self._raise_not_found(
                "LEARNING_PROFILE_NOT_FOUND",
                "Set a learning goal and learning style before generating a learning path",
            )
        return profile

    def _gap_analysis_locked(self, assessment: MockAssessment) -> dict:
        knowledge_gaps = []
        skill_gaps = []
        for topic, score in assessment.topic_scores:
            if score >= assessment.passing_score:
                continue
            gap = round(assessment.passing_score - score, 2)
            severity = self.gap_severity(score)
            knowledge_gaps.append(
                {
                    "topic": topic,
                    "score": score,
                    "target_score": assessment.passing_score,
                    "gap_score": gap,
                    "severity": severity,
                }
            )
            skill_gaps.append(
                {
                    "skill": topic,
                    "score": score,
                    "target_score": assessment.passing_score,
                    "gap_score": gap,
                    "severity": severity,
                }
            )
        knowledge_gaps.sort(key=lambda item: (item["score"], item["topic"].casefold()))
        skill_gaps.sort(key=lambda item: (item["score"], item["skill"].casefold()))
        return {
            "assessment": self.assessment_response(assessment),
            "knowledge_gaps": knowledge_gaps,
            "skill_gaps": skill_gaps,
            "weak_topics": knowledge_gaps,
        }

    def _recommended_lessons(
        self,
        *,
        assessment: MockAssessment,
        learning_styles: list[LearningStyle],
    ) -> list[dict]:
        lessons = []
        for index, (topic, score) in enumerate(
            sorted(assessment.topic_scores, key=lambda item: (item[1], item[0].casefold())),
            start=1,
        ):
            level = self._lesson_level(score=score, passing_score=assessment.passing_score)
            if score < assessment.passing_score:
                reason = (
                    f"{topic} scored {score:g}, below the target {assessment.passing_score:g}; "
                    "prioritize remediation."
                )
            else:
                reason = (
                    f"{topic} scored {score:g}, meeting the target {assessment.passing_score:g}; "
                    "continue at the appropriate level."
                )
            lessons.append(
                {
                    "id": f"lesson-{assessment.id}-{index}",
                    "title": f"{level.value.title()} {topic}",
                    "topic": topic,
                    "level": level,
                    "estimated_minutes": 45 if score < 50 else 35 if score < assessment.passing_score else 30,
                    "reason": reason,
                    "study_recommendations": self._study_recommendations(
                        learning_styles=learning_styles,
                    ),
                }
            )
        return lessons

    @staticmethod
    def _study_recommendations(*, learning_styles: list[LearningStyle]) -> list[str]:
        """Return concrete study activities that match the learner's saved styles."""
        activities = {
            LearningStyle.VISUAL: "Review a diagram, concept map, or worked visual example first.",
            LearningStyle.AUDITORY: "Listen to a short explanation, then summarize the idea aloud.",
            LearningStyle.READING_WRITING: "Read the guide and write a concise summary in your own words.",
            LearningStyle.KINESTHETIC: "Complete a guided hands-on exercise immediately after the lesson.",
            LearningStyle.MIXED: "Combine a short visual explanation, reading, and practical exercise.",
        }
        return [activities[style] for style in learning_styles]

    def _additional_content(self, assessment: MockAssessment) -> list[dict]:
        recommendations = []
        weak_topics = [
            (topic, score)
            for topic, score in assessment.topic_scores
            if score < assessment.passing_score
        ]
        for index, (topic, score) in enumerate(
            sorted(weak_topics, key=lambda item: (item[1], item[0].casefold())),
            start=1,
        ):
            reason = f"{topic} is {assessment.passing_score - score:g} points below the target score."
            recommendations.extend(
                [
                    {
                        "id": f"content-{assessment.id}-{index}-lesson",
                        "topic": topic,
                        "content_type": RecommendationType.LESSON,
                        "title": f"Targeted lesson: {topic}",
                        "reason": reason,
                    },
                    {
                        "id": f"content-{assessment.id}-{index}-exercise",
                        "topic": topic,
                        "content_type": RecommendationType.EXERCISE,
                        "title": f"Practice exercise: {topic}",
                        "reason": reason,
                    },
                    {
                        "id": f"content-{assessment.id}-{index}-reference",
                        "topic": topic,
                        "content_type": RecommendationType.REFERENCE,
                        "title": f"Reference guide: {topic}",
                        "reason": reason,
                    },
                ]
            )
        return recommendations

    @staticmethod
    def _overall_score(assessment: MockAssessment) -> float:
        return round(
            sum(score for _, score in assessment.topic_scores) / len(assessment.topic_scores),
            2,
        )

    @staticmethod
    def learner_level(score: float) -> LearnerLevel:
        """Map the learner's overall assessment score to a learning level."""
        if score >= 85:
            return LearnerLevel.ADVANCED
        if score >= 70:
            return LearnerLevel.INTERMEDIATE
        if score >= 50:
            return LearnerLevel.BEGINNER
        return LearnerLevel.FOUNDATION

    @staticmethod
    def _lesson_level(*, score: float, passing_score: float) -> LearnerLevel:
        if score < 50:
            return LearnerLevel.FOUNDATION
        if score < passing_score:
            return LearnerLevel.BEGINNER
        if score < 85:
            return LearnerLevel.INTERMEDIATE
        return LearnerLevel.ADVANCED

    @staticmethod
    def gap_severity(score: float) -> GapSeverity:
        if score < 50:
            return GapSeverity.CRITICAL
        if score < 60:
            return GapSeverity.HIGH
        return GapSeverity.MODERATE

    @staticmethod
    def _raise_not_found(code: str, message: str) -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": code, "message": message},
        )


mock_personalized_learning_service = MockPersonalizedLearningService()
