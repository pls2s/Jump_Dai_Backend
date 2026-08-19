"""In-memory learner enrollment and generated-lesson progress service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock

from fastapi import HTTPException, status

from app.schemas.ai import GeneratedLearningPath
from app.services.course_service import MockCourse, mock_course_service


@dataclass
class MockEnrollment:
    """Progress state for one learner in one published course."""

    learner_id: int
    course_id: int
    enrolled_at: datetime
    completed_lesson_ids: set[str] = field(default_factory=set)
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MockLearnerCourseService:
    """Thread-safe enrollment and lesson completion store for the MVP."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reset()

    def reset(self) -> None:
        """Clear all learner enrollment and completion data."""
        with self._lock:
            self._enrollments: dict[tuple[int, int], MockEnrollment] = {}

    def enroll(self, *, learner_id: int, course: MockCourse) -> MockEnrollment:
        """Create an idempotent enrollment for a published course."""
        with self._lock:
            key = (learner_id, course.id)
            enrollment = self._enrollments.get(key)
            if enrollment is None:
                now = datetime.now(timezone.utc)
                enrollment = MockEnrollment(
                    learner_id=learner_id,
                    course_id=course.id,
                    enrolled_at=now,
                    last_activity_at=now,
                )
                self._enrollments[key] = enrollment
            return enrollment

    def enrollment_for(self, *, learner_id: int, course_id: int) -> MockEnrollment:
        """Return the learner's course enrollment or a documented not-found error."""
        with self._lock:
            enrollment = self._enrollments.get((learner_id, course_id))
            if enrollment is None:
                self._raise_not_enrolled()
            return enrollment

    def is_enrolled(self, *, learner_id: int, course_id: int) -> bool:
        """Check enrollment without raising when an assessment is submitted."""
        with self._lock:
            return (learner_id, course_id) in self._enrollments

    def enrollment_response(self, *, enrollment: MockEnrollment, course: MockCourse) -> dict:
        """Serialize a new or existing enrollment."""
        return {
            "course_id": course.id,
            "course_title": course.title,
            "enrolled_at": enrollment.enrolled_at,
        }

    def path_for(self, *, learner_id: int, course_id: int) -> dict:
        """Build one enrolled learner's view of a verified published course path."""
        with self._lock:
            enrollment = self.enrollment_for(learner_id=learner_id, course_id=course_id)
            course = mock_course_service.get_published(course_id=course_id)
            lessons = self._course_lessons(course)
            return {
                "course_id": course.id,
                "course_title": course.title,
                "overview": GeneratedLearningPath.model_validate(
                    course.generated_learning_path
                ).overview,
                "enrolled_at": enrollment.enrolled_at,
                **self._progress_fields(enrollment=enrollment, lessons=lessons),
                "lessons": [
                    {
                        **lesson,
                        "completed": lesson["id"] in enrollment.completed_lesson_ids,
                    }
                    for lesson in lessons
                ],
            }

    def lesson_for(self, *, learner_id: int, lesson_id: str) -> dict:
        """Find a lesson only within courses that belong to the current learner."""
        with self._lock:
            for (enrolled_learner_id, course_id), enrollment in self._enrollments.items():
                if enrolled_learner_id != learner_id:
                    continue
                course = mock_course_service.get_published(course_id=course_id)
                for lesson in self._course_lessons(course):
                    if lesson["id"] == lesson_id:
                        return {
                            **lesson,
                            "completed": lesson_id in enrollment.completed_lesson_ids,
                        }
            self._raise_lesson_not_found()

    def complete_lesson(self, *, learner_id: int, lesson_id: str) -> dict:
        """Mark one enrolled lesson complete and return the course progress."""
        with self._lock:
            for (enrolled_learner_id, course_id), enrollment in self._enrollments.items():
                if enrolled_learner_id != learner_id:
                    continue
                course = mock_course_service.get_published(course_id=course_id)
                lessons = self._course_lessons(course)
                if any(lesson["id"] == lesson_id for lesson in lessons):
                    enrollment.completed_lesson_ids.add(lesson_id)
                    enrollment.last_activity_at = datetime.now(timezone.utc)
                    return {
                        "lesson": {
                            "id": lesson_id,
                            "course_id": course_id,
                            "completed": True,
                        },
                        "progress": {
                            "course_id": course_id,
                            **self._progress_fields(enrollment=enrollment, lessons=lessons),
                            "last_activity_at": enrollment.last_activity_at,
                        },
                    }
            self._raise_lesson_not_found()

    def progress_for(self, *, learner_id: int, course_id: int) -> dict:
        """Return completion percentage and counts for an enrolled course."""
        with self._lock:
            enrollment = self.enrollment_for(learner_id=learner_id, course_id=course_id)
            course = mock_course_service.get_published(course_id=course_id)
            lessons = self._course_lessons(course)
            return {
                "course_id": course_id,
                **self._progress_fields(enrollment=enrollment, lessons=lessons),
                "last_activity_at": enrollment.last_activity_at,
            }

    @staticmethod
    def _course_lessons(course: MockCourse) -> list[dict]:
        """Give generated lessons stable learner-facing IDs without mutating the draft."""
        learning_path = GeneratedLearningPath.model_validate(course.generated_learning_path)
        lessons = []
        for module_index, module in enumerate(learning_path.modules, start=1):
            for lesson_index, lesson in enumerate(module.lessons, start=1):
                lessons.append(
                    {
                        "id": f"course-{course.id}-lesson-{module_index}-{lesson_index}",
                        "course_id": course.id,
                        "module_title": module.title,
                        "title": lesson.title,
                        "summary": lesson.summary,
                        "source_references": lesson.source_references,
                    }
                )
        return lessons

    @staticmethod
    def _progress_fields(*, enrollment: MockEnrollment, lessons: list[dict]) -> dict:
        total = len(lessons)
        completed_count = sum(
            lesson["id"] in enrollment.completed_lesson_ids for lesson in lessons
        )
        percentage = round(completed_count * 100 / total, 2)
        return {
            "progress_percentage": percentage,
            "completed_lesson_count": completed_count,
            "total_lesson_count": total,
            "completed": completed_count == total,
        }

    @staticmethod
    def _raise_not_enrolled() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ENROLLMENT_NOT_FOUND",
                "message": "Enroll in this course before accessing its learning path",
            },
        )

    @staticmethod
    def _raise_lesson_not_found() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "LESSON_NOT_FOUND",
                "message": "No accessible enrolled lesson exists with this ID",
            },
        )


mock_learner_course_service = MockLearnerCourseService()
