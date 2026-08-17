"""Temporary course-context store for Function 2: Knowledge Upload."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock

from fastapi import HTTPException, status

from app.schemas.course import CourseStatus, DifficultyLevel


@dataclass
class MockCourse:
    """Private course representation held by the process-local MVP store."""

    id: int
    creator_id: int
    title: str
    description: str
    target_learner: str
    difficulty_level: DifficultyLevel
    certification_enabled: bool
    learning_objective: str
    status: CourseStatus
    created_at: datetime

    def to_public_dict(self) -> dict:
        """Return the course fields exposed by the API."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "target_learner": self.target_learner,
            "difficulty_level": self.difficulty_level,
            "certification_enabled": self.certification_enabled,
            "learning_objective": self.learning_objective,
            "status": self.status,
            "creator_id": self.creator_id,
            "created_at": self.created_at,
        }


class MockCourseService:
    """Thread-safe, process-local course-context store for Function 2."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reset()

    def reset(self) -> None:
        """Clear course contexts and restore predictable IDs for tests."""
        with self._lock:
            self._courses: dict[int, MockCourse] = {}
            self._next_course_id = 1

    def create(
        self,
        *,
        creator_id: int,
        title: str,
        description: str,
        target_learner: str,
        difficulty_level: DifficultyLevel,
        certification_enabled: bool,
        learning_objective: str,
    ) -> MockCourse:
        """Create the draft course context that owns Function 2 sources."""
        with self._lock:
            now = datetime.now(timezone.utc)
            course = MockCourse(
                id=self._next_course_id,
                creator_id=creator_id,
                title=title,
                description=description,
                target_learner=target_learner,
                difficulty_level=difficulty_level,
                certification_enabled=certification_enabled,
                learning_objective=learning_objective,
                status=CourseStatus.DRAFT,
                created_at=now,
            )
            self._courses[course.id] = course
            self._next_course_id += 1
            return course

    def get_for_creator(self, *, course_id: int, creator_id: int) -> MockCourse:
        """Find a Function 2 course context and enforce creator ownership."""
        with self._lock:
            course = self._courses.get(course_id)
            if course is None or course.creator_id != creator_id:
                self._raise_not_found()
            return course

    @staticmethod
    def _raise_not_found() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "COURSE_NOT_FOUND",
                "message": "No course exists for this account and ID",
            },
        )


mock_course_service = MockCourseService()
