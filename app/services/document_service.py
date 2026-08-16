"""Temporary in-memory knowledge-source store for Function 2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock

from fastapi import HTTPException, status

from app.schemas.document import DocumentStatus, KnowledgeSourceType


@dataclass
class MockKnowledgeSource:
    """Private metadata for a file, manual note, or URL source."""

    id: int
    course_id: int
    filename: str
    file_type: str
    size: int
    source_type: KnowledgeSourceType
    status: DocumentStatus
    created_at: datetime
    payload: bytes | str

    def to_response_dict(self) -> dict:
        """Return the detailed source metadata exposed by the API."""
        return {
            "id": self.id,
            "course_id": self.course_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "size": self.size,
            "source_type": self.source_type,
            "status": self.status,
            "created_at": self.created_at,
        }

    def to_list_dict(self) -> dict:
        """Return compact source metadata for source-management views."""
        return {
            "id": self.id,
            "filename": self.filename,
            "status": self.status,
            "source_type": self.source_type,
        }


class MockDocumentService:
    """Thread-safe, process-local source metadata store for the MVP."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reset()

    def reset(self) -> None:
        """Clear source records and restore predictable IDs for tests."""
        with self._lock:
            self._sources: dict[int, MockKnowledgeSource] = {}
            self._next_source_id = 1

    def create_file(
        self,
        *,
        course_id: int,
        filename: str,
        file_type: str,
        content: bytes,
    ) -> MockKnowledgeSource:
        """Record a successfully validated uploaded file as a knowledge source."""
        return self._create(
            course_id=course_id,
            filename=filename,
            file_type=file_type,
            size=len(content),
            source_type=KnowledgeSourceType.FILE,
            payload=content,
        )

    def create_manual(
        self,
        *,
        course_id: int,
        title: str | None,
        content: str,
    ) -> MockKnowledgeSource:
        """Record creator-entered notes without persisting the content yet."""
        return self._create(
            course_id=course_id,
            filename=title or "Manual knowledge source",
            file_type="manual",
            size=len(content.encode("utf-8")),
            source_type=KnowledgeSourceType.MANUAL,
            payload=content,
        )

    def create_url(
        self,
        *,
        course_id: int,
        title: str | None,
        url: str,
    ) -> MockKnowledgeSource:
        """Record a URL reference without fetching it in the mock implementation."""
        return self._create(
            course_id=course_id,
            filename=title or url,
            file_type="url",
            size=len(url.encode("utf-8")),
            source_type=KnowledgeSourceType.URL,
            payload=url,
        )

    def list_for_course(
        self,
        *,
        course_id: int,
        source_type: KnowledgeSourceType | None = None,
    ) -> list[MockKnowledgeSource]:
        """List source records for one course, optionally limited to files."""
        with self._lock:
            return [
                source
                for source in self._sources.values()
                if source.course_id == course_id
                and (source_type is None or source.source_type == source_type)
            ]

    def get(self, *, source_id: int) -> MockKnowledgeSource:
        """Return a source record or raise the documented not-found response."""
        with self._lock:
            source = self._sources.get(source_id)
            if source is None:
                self._raise_not_found()
            return source

    def delete(self, *, source_id: int) -> MockKnowledgeSource:
        """Remove a source record after the route has verified ownership."""
        with self._lock:
            source = self._sources.get(source_id)
            if source is None:
                self._raise_not_found()
            del self._sources[source.id]
            return source

    def _create(
        self,
        *,
        course_id: int,
        filename: str,
        file_type: str,
        size: int,
        source_type: KnowledgeSourceType,
        payload: bytes | str,
    ) -> MockKnowledgeSource:
        with self._lock:
            source = MockKnowledgeSource(
                id=self._next_source_id,
                course_id=course_id,
                filename=filename,
                file_type=file_type,
                size=size,
                source_type=source_type,
                status=DocumentStatus.UPLOADED,
                created_at=datetime.now(timezone.utc),
                payload=payload,
            )
            self._sources[source.id] = source
            self._next_source_id += 1
            return source

    @staticmethod
    def _raise_not_found() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": "No knowledge source exists for this ID",
            },
        )


mock_document_service = MockDocumentService()
