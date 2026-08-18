"""Temporary course-context store for Function 2: Knowledge Upload."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Optional

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
    learning_objective: str
    status: CourseStatus
    created_at: datetime
    generation_progress: int = 0
    generation_error: Optional[str] = None
    generated_at: Optional[datetime] = None
    generated_learning_path: Optional[dict] = None
    verified_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    def to_public_dict(self) -> dict:
        """Return the course fields exposed by the API."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "target_learner": self.target_learner,
            "difficulty_level": self.difficulty_level,
            "certificate_available": self.difficulty_level is DifficultyLevel.ADVANCED,
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

    def list_for_creator(self, *, creator_id: int) -> list[MockCourse]:
        """List only the course contexts owned by one creator."""
        with self._lock:
            return [
                course
                for course in self._courses.values()
                if course.creator_id == creator_id
            ]

    def start_generation(self, *, course_id: int, creator_id: int) -> MockCourse:
        """Move a creator-owned course into the generation state."""
        with self._lock:
            course = self._get_owned_course(course_id=course_id, creator_id=creator_id)
            if course.status is CourseStatus.GENERATING:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "GENERATION_IN_PROGRESS",
                        "message": "This course is already being generated",
                    },
                )
            course.status = CourseStatus.GENERATING
            course.generation_progress = 10
            course.generation_error = None
            course.generated_at = None
            course.generated_learning_path = None
            course.verified_at = None
            course.published_at = None
            return course

    def complete_generation(
        self,
        *,
        course_id: int,
        creator_id: int,
        learning_path: dict,
    ) -> MockCourse:
        """Save a generated draft for mandatory creator verification."""
        with self._lock:
            course = self._get_owned_course(course_id=course_id, creator_id=creator_id)
            course.status = CourseStatus.WAITING_VERIFICATION
            course.generation_progress = 100
            course.generation_error = None
            course.generated_at = datetime.now(timezone.utc)
            course.generated_learning_path = learning_path
            course.verified_at = None
            course.published_at = None
            return course

    def fail_generation(
        self,
        *,
        course_id: int,
        creator_id: int,
        message: str,
    ) -> MockCourse:
        """Store a safe failure reason for a generation request."""
        with self._lock:
            course = self._get_owned_course(course_id=course_id, creator_id=creator_id)
            course.status = CourseStatus.FAILED
            course.generation_progress = 0
            course.generation_error = message
            course.generated_at = None
            course.generated_learning_path = None
            course.verified_at = None
            course.published_at = None
            return course

    def generation_status(self, *, course_id: int, creator_id: int) -> MockCourse:
        """Return the generation state only after creator ownership is verified."""
        with self._lock:
            return self._get_owned_course(course_id=course_id, creator_id=creator_id)

    def update_learning_path(
        self,
        *,
        course_id: int,
        creator_id: int,
        learning_path: dict,
    ) -> MockCourse:
        """Save Creator edits while a generated draft awaits verification."""
        with self._lock:
            course = self._get_owned_course(course_id=course_id, creator_id=creator_id)
            if course.status is not CourseStatus.WAITING_VERIFICATION:
                self._raise_review_state_conflict()
            course.generated_learning_path = learning_path
            return course

    def verify_learning_path(self, *, course_id: int, creator_id: int) -> MockCourse:
        """Accept a reviewed draft; publication remains a later function."""
        with self._lock:
            course = self._get_owned_course(course_id=course_id, creator_id=creator_id)
            if (
                course.status is not CourseStatus.WAITING_VERIFICATION
                or course.generated_learning_path is None
            ):
                self._raise_review_state_conflict()
            course.status = CourseStatus.VERIFIED
            course.verified_at = datetime.now(timezone.utc)
            return course

    def publish_course(self, *, course_id: int, creator_id: int) -> MockCourse:
        """Make a verified course available in the public catalog."""
        with self._lock:
            course = self._get_owned_course(course_id=course_id, creator_id=creator_id)
            if (
                course.status is not CourseStatus.VERIFIED
                or course.generated_learning_path is None
            ):
                self._raise_publish_state_conflict()
            course.status = CourseStatus.PUBLISHED
            course.published_at = datetime.now(timezone.utc)
            return course

    def list_published(self) -> list[MockCourse]:
        """Return catalog-visible courses, newest publication first."""
        with self._lock:
            courses = [
                course
                for course in self._courses.values()
                if course.status is CourseStatus.PUBLISHED
                and course.generated_learning_path is not None
                and course.published_at is not None
            ]
            return sorted(courses, key=lambda course: course.published_at, reverse=True)

    def get_published(self, *, course_id: int) -> MockCourse:
        """Find a course only if it has been published to the public catalog."""
        with self._lock:
            course = self._courses.get(course_id)
            if (
                course is None
                or course.status is not CourseStatus.PUBLISHED
                or course.generated_learning_path is None
                or course.published_at is None
            ):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "PUBLISHED_COURSE_NOT_FOUND",
                        "message": "No published course exists with this ID",
                    },
                )
            return course

    def _get_owned_course(self, *, course_id: int, creator_id: int) -> MockCourse:
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

    @staticmethod
    def _raise_review_state_conflict() -> None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "LEARNING_PATH_NOT_READY_FOR_VERIFICATION",
                "message": "Generate a learning path and review it before this action",
            },
        )

    @staticmethod
    def _raise_publish_state_conflict() -> None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "COURSE_NOT_READY_TO_PUBLISH",
                "message": "Verify the learning path before publishing this course",
            },
        )


mock_course_service = MockCourseService()
