"""Temporary in-memory implementation of course management."""

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
    goal: str
    difficulty_level: DifficultyLevel
    certification_enabled: bool
    status: CourseStatus
    created_at: datetime
    updated_at: datetime

    def to_public_dict(self) -> dict:
        """Return the course fields exposed by the API."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "goal": self.goal,
            "difficulty_level": self.difficulty_level,
            "certification_enabled": self.certification_enabled,
            "status": self.status,
            "creator_id": self.creator_id,
            "created_at": self.created_at,
        }


class MockCourseService:
    """Thread-safe, process-local course store for the MVP."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reset()

    def reset(self) -> None:
        """Clear courses and restore predictable IDs for tests and local work."""
        with self._lock:
            self._courses: dict[int, MockCourse] = {}
            self._next_course_id = 1

    def create(
        self,
        *,
        creator_id: int,
        title: str,
        description: str,
        goal: str,
        difficulty_level: DifficultyLevel,
        certification_enabled: bool,
    ) -> MockCourse:
        """Create a new draft course for the authenticated creator."""
        with self._lock:
            now = datetime.now(timezone.utc)
            course = MockCourse(
                id=self._next_course_id,
                creator_id=creator_id,
                title=title,
                description=description,
                goal=goal,
                difficulty_level=difficulty_level,
                certification_enabled=certification_enabled,
                status=CourseStatus.DRAFT,
                created_at=now,
                updated_at=now,
            )
            self._courses[course.id] = course
            self._next_course_id += 1
            return course

    def list_for_creator(self, *, creator_id: int) -> list[MockCourse]:
        """Return only courses owned by the authenticated creator."""
        with self._lock:
            return [
                course
                for course in self._courses.values()
                if course.creator_id == creator_id
            ]

    def get_for_creator(self, *, course_id: int, creator_id: int) -> MockCourse:
        """Find a course and enforce ownership at the service boundary."""
        with self._lock:
            course = self._courses.get(course_id)
            if course is None or course.creator_id != creator_id:
                self._raise_not_found()
            return course

    def update(
        self,
        *,
        course_id: int,
        creator_id: int,
        updates: dict[str, object],
    ) -> MockCourse:
        """Update the supplied metadata fields on an owned course."""
        with self._lock:
            course = self._get_for_creator_locked(course_id, creator_id)
            for field_name, value in updates.items():
                setattr(course, field_name, value)
            course.updated_at = datetime.now(timezone.utc)
            return course

    def delete(self, *, course_id: int, creator_id: int) -> MockCourse:
        """Delete an owned course and return the deleted representation."""
        with self._lock:
            course = self._get_for_creator_locked(course_id, creator_id)
            del self._courses[course.id]
            return course

    def _get_for_creator_locked(self, course_id: int, creator_id: int) -> MockCourse:
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
