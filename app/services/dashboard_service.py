"""Temporary in-memory analytics used by the Function 9 Creator Dashboard."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from threading import RLock
from textwrap import wrap
from typing import Optional

from app.services.course_service import MockCourse


@dataclass(frozen=True)
class MockLearnerAnalytics:
    """A mock learner activity record supplied until learning data is persisted."""

    learner_id: int
    learner_name: str
    progress_percentage: float
    assessment_score: float
    completed: bool
    last_activity_at: datetime
    common_errors: tuple[str, ...]
    skill_gaps: tuple[str, ...]


@dataclass(frozen=True)
class CourseAnalyticsSnapshot:
    """Analytics records belonging to one exact in-memory course instance."""

    course_created_at: datetime
    records: tuple[MockLearnerAnalytics, ...]


class MockDashboardService:
    """Build deterministic dashboard analytics for creator-owned mock courses."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reset()

    def reset(self) -> None:
        """Clear analytics snapshots so tests do not share report data."""
        with self._lock:
            self._snapshots: dict[int, CourseAnalyticsSnapshot] = {}

    def build_dashboard(
        self,
        *,
        courses: list[MockCourse],
        course_id: Optional[int],
        date_from: Optional[date],
        date_to: Optional[date],
    ) -> dict:
        """Return all Function 9 metrics after applying course and date filters."""
        with self._lock:
            records_by_course = {
                course.id: self._records_for_course(
                    course=course,
                    date_from=date_from,
                    date_to=date_to,
                )
                for course in courses
            }

        course_metrics = [
            self._course_metrics(course=course, records=records_by_course[course.id])
            for course in courses
        ]
        all_records = [
            (course, record)
            for course in courses
            for record in records_by_course[course.id]
        ]
        learner_count = len(all_records)
        completed_learner_count = sum(record.completed for _, record in all_records)
        total_scores = sum(record.assessment_score for _, record in all_records)

        return {
            "filters": {
                "course_id": course_id,
                "date_from": date_from,
                "date_to": date_to,
            },
            "summary": {
                "course_count": len(courses),
                "learner_count": learner_count,
                "completed_learner_count": completed_learner_count,
                "completion_rate": self._percentage(completed_learner_count, learner_count),
                "average_assessment_score": self._average(total_scores, learner_count),
            },
            "courses": course_metrics,
            "learners": self._learner_progress(all_records),
            "common_errors": self._common_errors(all_records),
            "skill_gaps": self._skill_gaps(all_records),
            "course_improvement_insights": self._improvement_insights(
                courses=courses,
                records_by_course=records_by_course,
            ),
        }

    @staticmethod
    def export_rows(report: dict) -> list[dict[str, object]]:
        """Flatten learner analytics for the CSV version of the dashboard report."""
        return [
            {
                "course_id": learner["course_id"],
                "course_title": learner["course_title"],
                "learner_id": learner["learner_id"],
                "learner_name": learner["learner_name"],
                "progress_percentage": learner["progress_percentage"],
                "completed": learner["completed"],
                "assessment_score": learner["assessment_score"],
                "last_activity_at": learner["last_activity_at"].isoformat(),
                "common_errors": "; ".join(learner["common_errors"]),
                "skill_gaps": "; ".join(learner["skill_gaps"]),
            }
            for learner in report["learners"]
        ]

    @classmethod
    def export_pdf(cls, report: dict) -> bytes:
        """Create a dependency-free PDF report for the mock dashboard export."""
        filters = report["filters"]
        summary = report["summary"]
        course_filter = filters["course_id"] or "All owned courses"
        lines = [
            "Creator Dashboard Report",
            f"Course filter: {course_filter}",
            f"Date range: {filters['date_from'] or 'All time'} to {filters['date_to'] or 'All time'}",
            "",
            "Summary",
            f"Courses: {summary['course_count']}",
            f"Learners: {summary['learner_count']}",
            f"Completed learners: {summary['completed_learner_count']}",
            f"Completion rate: {summary['completion_rate']}%",
            f"Average assessment score: {summary['average_assessment_score']}%",
            "",
            "Course Metrics",
        ]
        lines.extend(
            (
                f"[{course['course_id']}] {course['course_title']} | "
                f"Learners: {course['learner_count']} | "
                f"Completion: {course['completion_rate']}% | "
                f"Average score: {course['average_assessment_score']}%"
            )
            for course in report["courses"]
        )
        lines.append("")
        lines.append("Learner Details")
        lines.extend(
            (
                f"[{learner['course_id']}] {learner['learner_name']} | "
                f"Progress: {learner['progress_percentage']}% | "
                f"Score: {learner['assessment_score']}% | "
                f"Completed: {learner['completed']}"
            )
            for learner in report["learners"]
        )
        lines.append("")
        lines.append("Common Errors")
        lines.extend(
            (
                f"[{error['course_id']}] {error['topic']} | "
                f"Occurrences: {error['occurrence_count']} | "
                f"Affected learners: {error['affected_learner_count']}"
            )
            for error in report["common_errors"]
        )
        lines.append("")
        lines.append("Skill Gaps")
        lines.extend(
            (
                f"[{gap['course_id']}] {gap['skill']} | "
                f"Affected learners: {gap['affected_learner_count']}"
            )
            for gap in report["skill_gaps"]
        )
        lines.append("")
        lines.append("Course Improvement Insights")
        lines.extend(
            f"[{insight['course_id']}] {insight['code']}: {insight['recommendation']}"
            for insight in report["course_improvement_insights"]
        )
        return cls._build_pdf(lines)

    @staticmethod
    def _build_pdf(lines: list[str]) -> bytes:
        """Build a small, valid multi-page PDF without an additional dependency."""
        wrapped_lines = [
            fragment
            for line in lines
            for fragment in (wrap(line, width=92) or [""])
        ]
        page_line_count = 48
        pages = [
            wrapped_lines[index : index + page_line_count]
            for index in range(0, len(wrapped_lines), page_line_count)
        ] or [["No data matches the selected filters."]]
        page_object_ids = [4 + index * 2 for index in range(len(pages))]
        objects: list[bytes] = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            (
                b"<< /Type /Pages /Kids ["
                + b" ".join(f"{page_id} 0 R".encode() for page_id in page_object_ids)
                + f"] /Count {len(pages)} >>".encode()
            ),
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
        for page_index, page_lines in enumerate(pages):
            page_object_id = page_object_ids[page_index]
            content_object_id = page_object_id + 1
            stream = MockDashboardService._pdf_text_stream(page_lines)
            objects.extend(
                [
                    (
                        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                        b"/Resources << /Font << /F1 3 0 R >> >> "
                        + f"/Contents {content_object_id} 0 R >>".encode()
                    ),
                    (
                        f"<< /Length {len(stream)} >>\nstream\n".encode()
                        + stream
                        + b"endstream"
                    ),
                ]
            )

        document = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for object_id, object_content in enumerate(objects, start=1):
            offsets.append(len(document))
            document.extend(f"{object_id} 0 obj\n".encode())
            document.extend(object_content)
            document.extend(b"\nendobj\n")
        xref_offset = len(document)
        document.extend(f"xref\n0 {len(objects) + 1}\n".encode())
        document.extend(b"0000000000 65535 f \n")
        document.extend(
            b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
        )
        document.extend(
            (
                f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
                f"startxref\n{xref_offset}\n%%EOF\n"
            ).encode()
        )
        return bytes(document)

    @staticmethod
    def _pdf_text_stream(lines: list[str]) -> bytes:
        """Encode report lines for a standard Helvetica PDF text stream."""
        commands = [b"BT", b"/F1 10 Tf", b"50 760 Td", b"14 TL"]
        for line in lines:
            text = line.encode("cp1252", errors="replace")
            escaped = text.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
            commands.extend([b"(" + escaped + b") Tj", b"T*"])
        commands.append(b"ET")
        return b"\n".join(commands) + b"\n"

    def _records_for_course(
        self,
        *,
        course: MockCourse,
        date_from: Optional[date],
        date_to: Optional[date],
    ) -> list[MockLearnerAnalytics]:
        snapshot = self._snapshot_for_course(course)
        return [
            record
            for record in snapshot.records
            if (date_from is None or record.last_activity_at.date() >= date_from)
            and (date_to is None or record.last_activity_at.date() <= date_to)
        ]

    def _snapshot_for_course(self, course: MockCourse) -> CourseAnalyticsSnapshot:
        existing = self._snapshots.get(course.id)
        if existing is not None and existing.course_created_at == course.created_at:
            return existing

        now = datetime.now(timezone.utc).replace(microsecond=0)
        learner_base_id = course.id * 1_000
        snapshot = CourseAnalyticsSnapshot(
            course_created_at=course.created_at,
            records=(
                MockLearnerAnalytics(
                    learner_id=learner_base_id + 1,
                    learner_name="Aom Learner",
                    progress_percentage=92,
                    assessment_score=88,
                    completed=True,
                    last_activity_at=now,
                    common_errors=("Foreign key relationships",),
                    skill_gaps=(),
                ),
                MockLearnerAnalytics(
                    learner_id=learner_base_id + 2,
                    learner_name="Beam Learner",
                    progress_percentage=64,
                    assessment_score=58,
                    completed=False,
                    last_activity_at=now - timedelta(days=7),
                    common_errors=("JOIN conditions", "Database normalization"),
                    skill_gaps=("Database normalization",),
                ),
                MockLearnerAnalytics(
                    learner_id=learner_base_id + 3,
                    learner_name="Chai Learner",
                    progress_percentage=40,
                    assessment_score=45,
                    completed=False,
                    last_activity_at=now - timedelta(days=14),
                    common_errors=("JOIN conditions", "Primary keys"),
                    skill_gaps=("SQL joins", "Database normalization"),
                ),
            ),
        )
        self._snapshots[course.id] = snapshot
        return snapshot

    def _course_metrics(
        self,
        *,
        course: MockCourse,
        records: list[MockLearnerAnalytics],
    ) -> dict:
        learner_count = len(records)
        completed_learner_count = sum(record.completed for record in records)
        total_scores = sum(record.assessment_score for record in records)
        return {
            "course_id": course.id,
            "course_title": course.title,
            "learner_count": learner_count,
            "completed_learner_count": completed_learner_count,
            "completion_rate": self._percentage(completed_learner_count, learner_count),
            "average_assessment_score": self._average(total_scores, learner_count),
        }

    @staticmethod
    def _learner_progress(
        records: list[tuple[MockCourse, MockLearnerAnalytics]],
    ) -> list[dict]:
        return [
            {
                "learner_id": record.learner_id,
                "learner_name": record.learner_name,
                "course_id": course.id,
                "course_title": course.title,
                "progress_percentage": record.progress_percentage,
                "assessment_score": record.assessment_score,
                "completed": record.completed,
                "last_activity_at": record.last_activity_at,
                "common_errors": list(record.common_errors),
                "skill_gaps": list(record.skill_gaps),
            }
            for course, record in records
        ]

    @staticmethod
    def _common_errors(
        records: list[tuple[MockCourse, MockLearnerAnalytics]],
    ) -> list[dict]:
        occurrences: Counter[tuple[int, str, str]] = Counter()
        affected_learners: dict[tuple[int, str, str], set[int]] = defaultdict(set)
        for course, record in records:
            for topic in record.common_errors:
                key = (course.id, course.title, topic)
                occurrences[key] += 1
                affected_learners[key].add(record.learner_id)

        return [
            {
                "course_id": course_id,
                "course_title": course_title,
                "topic": topic,
                "occurrence_count": occurrence_count,
                "affected_learner_count": len(affected_learners[key]),
            }
            for key, occurrence_count in sorted(
                occurrences.items(),
                key=lambda item: (-item[1], item[0][2], item[0][0]),
            )
            for course_id, course_title, topic in (key,)
        ]

    @staticmethod
    def _skill_gaps(
        records: list[tuple[MockCourse, MockLearnerAnalytics]],
    ) -> list[dict]:
        affected_learners: dict[tuple[int, str, str], set[int]] = defaultdict(set)
        for course, record in records:
            for skill in record.skill_gaps:
                affected_learners[(course.id, course.title, skill)].add(record.learner_id)

        return [
            {
                "course_id": course_id,
                "course_title": course_title,
                "skill": skill,
                "affected_learner_count": len(learners),
            }
            for (course_id, course_title, skill), learners in sorted(
                affected_learners.items(),
                key=lambda item: (-len(item[1]), item[0][2], item[0][0]),
            )
        ]

    def _improvement_insights(
        self,
        *,
        courses: list[MockCourse],
        records_by_course: dict[int, list[MockLearnerAnalytics]],
    ) -> list[dict]:
        insights: list[dict] = []
        for course in courses:
            records = records_by_course[course.id]
            learner_count = len(records)
            if learner_count == 0:
                insights.append(
                    {
                        "course_id": course.id,
                        "course_title": course.title,
                        "code": "NO_LEARNER_ACTIVITY",
                        "severity": "MEDIUM",
                        "message": "No learner activity matches the selected filters.",
                        "recommendation": "Adjust the date filter or invite learners to start the course.",
                    }
                )
                continue

            completed_count = sum(record.completed for record in records)
            completion_rate = self._percentage(completed_count, learner_count)
            average_score = self._average(
                sum(record.assessment_score for record in records),
                learner_count,
            )
            if completion_rate < 80:
                insights.append(
                    {
                        "course_id": course.id,
                        "course_title": course.title,
                        "code": "LOW_COMPLETION_RATE",
                        "severity": "HIGH",
                        "message": f"Completion rate is {completion_rate}%.",
                        "recommendation": "Review lesson pacing and add checkpoints before difficult sections.",
                    }
                )
            if average_score < 70:
                insights.append(
                    {
                        "course_id": course.id,
                        "course_title": course.title,
                        "code": "LOW_ASSESSMENT_SCORE",
                        "severity": "HIGH",
                        "message": f"Average assessment score is {average_score}%.",
                        "recommendation": "Add worked examples and practice before the assessment.",
                    }
                )

            common_errors = self._common_errors([(course, record) for record in records])
            if common_errors:
                top_error = common_errors[0]
                insights.append(
                    {
                        "course_id": course.id,
                        "course_title": course.title,
                        "code": "COMMON_ERROR_PATTERN",
                        "severity": "HIGH",
                        "message": (
                            f"{top_error['affected_learner_count']} learner(s) commonly miss "
                            f"{top_error['topic']}."
                        ),
                        "recommendation": f"Clarify {top_error['topic']} in the course content.",
                    }
                )

            skill_gaps = self._skill_gaps([(course, record) for record in records])
            if skill_gaps:
                top_gap = skill_gaps[0]
                insights.append(
                    {
                        "course_id": course.id,
                        "course_title": course.title,
                        "code": "SKILL_GAP_PATTERN",
                        "severity": "HIGH",
                        "message": (
                            f"{top_gap['affected_learner_count']} learner(s) need support in "
                            f"{top_gap['skill']}."
                        ),
                        "recommendation": f"Add targeted practice for {top_gap['skill']}.",
                    }
                )
        return insights

    @staticmethod
    def _percentage(numerator: int, denominator: int) -> float:
        return round((numerator / denominator) * 100, 2) if denominator else 0.0

    @staticmethod
    def _average(total: float, count: int) -> float:
        return round(total / count, 2) if count else 0.0


mock_dashboard_service = MockDashboardService()
