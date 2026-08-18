"""Temporary in-memory knowledge-source store for Function 2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from threading import RLock
from typing import Optional, Union

from fastapi import HTTPException, status

from app.schemas.document import DocumentStatus, KnowledgeSourceType

MAX_SOURCES_PER_COURSE = 10


@dataclass
class MockKnowledgeSource:
    """Private metadata for a file or URL knowledge source."""

    id: int
    course_id: int
    filename: str
    file_type: str
    size: int
    source_type: KnowledgeSourceType
    content_hash: Optional[str]
    status: DocumentStatus
    chunk_count: int
    processing_error: Optional[str]
    processed_at: Optional[datetime]
    version: int
    created_at: datetime
    updated_at: datetime
    payload: Union[bytes, str]

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
            "chunk_count": self.chunk_count,
            "processing_error": self.processing_error,
            "processed_at": self.processed_at,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_list_dict(self) -> dict:
        """Return compact source metadata for source-management views."""
        return {
            "id": self.id,
            "filename": self.filename,
            "status": self.status,
            "source_type": self.source_type,
            "chunk_count": self.chunk_count,
            "processing_error": self.processing_error,
            "version": self.version,
            "updated_at": self.updated_at,
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

    def create_url(
        self,
        *,
        course_id: int,
        title: Optional[str],
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
        source_type: Optional[KnowledgeSourceType] = None,
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

    def update_url(
        self,
        *,
        source_id: int,
        title: str,
        url: str,
    ) -> MockKnowledgeSource:
        """Replace a URL source and mark it for processing again."""
        return self._update(
            source_id=source_id,
            source_type=KnowledgeSourceType.URL,
            filename=title,
            size=len(url.encode("utf-8")),
            payload=url,
        )

    def mark_processing(self, *, source_id: int) -> MockKnowledgeSource:
        """Set a source to processing before its text and chunks are rebuilt."""
        with self._lock:
            source = self._sources.get(source_id)
            if source is None:
                self._raise_not_found()
            source.status = DocumentStatus.PROCESSING
            source.chunk_count = 0
            source.processing_error = None
            source.processed_at = None
            source.updated_at = datetime.now(timezone.utc)
            return source

    def mark_ready(self, *, source_id: int, chunk_count: int) -> MockKnowledgeSource:
        """Record a successful processing result and its searchable chunk count."""
        with self._lock:
            source = self._sources.get(source_id)
            if source is None:
                self._raise_not_found()
            source.status = DocumentStatus.READY
            source.chunk_count = chunk_count
            source.processing_error = None
            source.processed_at = datetime.now(timezone.utc)
            source.updated_at = source.processed_at
            return source

    def mark_failed(self, *, source_id: int, message: str) -> MockKnowledgeSource:
        """Expose a processing failure so the creator can correct the source."""
        with self._lock:
            source = self._sources.get(source_id)
            if source is None:
                self._raise_not_found()
            source.status = DocumentStatus.FAILED
            source.chunk_count = 0
            source.processing_error = message
            source.processed_at = None
            source.updated_at = datetime.now(timezone.utc)
            return source

    def _create(
        self,
        *,
        course_id: int,
        filename: str,
        file_type: str,
        size: int,
        source_type: KnowledgeSourceType,
        payload: Union[bytes, str],
    ) -> MockKnowledgeSource:
        with self._lock:
            content_hash = (
                None
                if source_type == KnowledgeSourceType.FILE
                else self._content_hash(payload)
            )
            if self._is_duplicate_source(
                course_id=course_id,
                filename=filename,
                source_type=source_type,
                content_hash=content_hash,
            ):
                self._raise_duplicate_source()

            source_count = sum(
                source.course_id == course_id for source in self._sources.values()
            )
            if source_count >= MAX_SOURCES_PER_COURSE:
                self._raise_source_limit_exceeded()

            now = datetime.now(timezone.utc)
            source = MockKnowledgeSource(
                id=self._next_source_id,
                course_id=course_id,
                filename=filename,
                file_type=file_type,
                size=size,
                source_type=source_type,
                content_hash=content_hash,
                status=DocumentStatus.UPLOADED,
                chunk_count=0,
                processing_error=None,
                processed_at=None,
                version=1,
                created_at=now,
                updated_at=now,
                payload=payload,
            )
            self._sources[source.id] = source
            self._next_source_id += 1
            return source

    def _update(
        self,
        *,
        source_id: int,
        source_type: KnowledgeSourceType,
        filename: str,
        size: int,
        payload: str,
    ) -> MockKnowledgeSource:
        with self._lock:
            source = self._sources.get(source_id)
            if source is None:
                self._raise_not_found()
            if source.source_type != source_type:
                self._raise_invalid_source_type()

            content_hash = self._content_hash(payload)
            if self._is_duplicate_source(
                course_id=source.course_id,
                filename=filename,
                source_type=source_type,
                content_hash=content_hash,
                exclude_source_id=source_id,
            ):
                self._raise_duplicate_source()

            source.filename = filename
            source.size = size
            source.content_hash = content_hash
            source.payload = payload
            source.status = DocumentStatus.UPLOADED
            source.chunk_count = 0
            source.processing_error = None
            source.processed_at = None
            source.version += 1
            source.updated_at = datetime.now(timezone.utc)
            return source

    @staticmethod
    def _content_hash(payload: Union[bytes, str]) -> str:
        """Create a stable fingerprint for URL duplicate detection."""
        content = payload if isinstance(payload, bytes) else payload.encode("utf-8")
        return sha256(content).hexdigest()

    def _is_duplicate_source(
        self,
        *,
        course_id: int,
        filename: str,
        source_type: KnowledgeSourceType,
        content_hash: Optional[str],
        exclude_source_id: Optional[int] = None,
    ) -> bool:
        """Match files by name and URLs by their exact payload."""
        for source in self._sources.values():
            if source.id == exclude_source_id:
                continue
            if source.course_id != course_id or source.source_type != source_type:
                continue
            if source_type == KnowledgeSourceType.FILE:
                if source.filename.casefold() == filename.casefold():
                    return True
            elif source.content_hash == content_hash:
                return True
        return False

    @staticmethod
    def _raise_duplicate_source() -> None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DUPLICATE_KNOWLEDGE_SOURCE",
                "message": "This knowledge source already exists for this course",
            },
        )

    @staticmethod
    def _raise_source_limit_exceeded() -> None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "KNOWLEDGE_SOURCE_LIMIT_EXCEEDED",
                "message": "A course can contain at most 10 file and URL knowledge sources",
            },
        )

    @staticmethod
    def _raise_invalid_source_type() -> None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_SOURCE_TYPE",
                "message": "This endpoint does not support this knowledge source type",
            },
        )

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
