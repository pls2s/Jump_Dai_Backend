"""Function 3 local text processing, chunking, and keyword retrieval service."""

from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from threading import RLock

from pypdf import PdfReader

from app.schemas.document import KnowledgeSourceType
from app.services.document_service import MockKnowledgeSource, mock_document_service

MAX_CHUNK_CHARS = 800
CHUNK_OVERLAP_CHARS = 120


class KnowledgeProcessingFailure(Exception):
    """Expected processing failure that can be returned in the API error envelope."""


@dataclass(frozen=True)
class MockKnowledgeChunk:
    """A source-grounded, searchable text segment kept in memory for the MVP."""

    id: str
    source_id: int
    course_id: int
    source_filename: str
    chunk_index: int
    content: str
    start_char: int
    end_char: int

    def to_response_dict(self) -> dict:
        """Return the chunk fields exposed to an authorized creator."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "course_id": self.course_id,
            "source_filename": self.source_filename,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "start_char": self.start_char,
            "end_char": self.end_char,
        }


class MockKnowledgeProcessingService:
    """Process TXT, Markdown, and PDF sources before LLM retrieval is added."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reset()

    def reset(self) -> None:
        """Clear the temporary chunk index; used by tests and server restarts."""
        with self._lock:
            self._chunks_by_source: dict[int, list[MockKnowledgeChunk]] = {}

    def process(self, source: MockKnowledgeSource) -> list[MockKnowledgeChunk]:
        """Extract local text, split it into overlapping chunks, and mark readiness."""
        mock_document_service.mark_processing(source_id=source.id)
        try:
            text = self._extract_text(source)
            chunks = self._build_chunks(source=source, text=text)
            if not chunks:
                raise KnowledgeProcessingFailure("The source does not contain indexable text")
        except KnowledgeProcessingFailure as exc:
            with self._lock:
                self._chunks_by_source.pop(source.id, None)
            mock_document_service.mark_failed(source_id=source.id, message=str(exc))
            raise

        with self._lock:
            self._chunks_by_source[source.id] = chunks
        mock_document_service.mark_ready(source_id=source.id, chunk_count=len(chunks))
        return chunks

    def list_for_source(self, *, source_id: int) -> list[MockKnowledgeChunk]:
        """Return the processed chunks for one source in their original order."""
        with self._lock:
            return list(self._chunks_by_source.get(source_id, []))

    def list_for_course(self, *, course_id: int) -> list[MockKnowledgeChunk]:
        """Return all ready chunks from a course in stable source/chunk order."""
        with self._lock:
            return sorted(
                [
                    chunk
                    for source_chunks in self._chunks_by_source.values()
                    for chunk in source_chunks
                    if chunk.course_id == course_id
                ],
                key=lambda chunk: (chunk.source_id, chunk.chunk_index),
            )

    def remove_source(self, *, source_id: int) -> None:
        """Remove a source's chunks when its original knowledge source changes or is deleted."""
        with self._lock:
            self._chunks_by_source.pop(source_id, None)

    def search(
        self,
        *,
        course_id: int,
        query: str,
        limit: int,
    ) -> list[tuple[MockKnowledgeChunk, float]]:
        """Return matching course chunks scored by query-term coverage, not embeddings."""
        query_terms = set(self._tokens(query))
        if not query_terms:
            return []

        with self._lock:
            chunks = [
                chunk
                for source_chunks in self._chunks_by_source.values()
                for chunk in source_chunks
                if chunk.course_id == course_id
            ]

        matches: list[tuple[MockKnowledgeChunk, float]] = []
        for chunk in chunks:
            chunk_terms = set(self._tokens(chunk.content))
            matched_terms = query_terms.intersection(chunk_terms)
            if matched_terms:
                matches.append((chunk, round(len(matched_terms) / len(query_terms), 3)))

        return sorted(
            matches,
            key=lambda item: (-item[1], item[0].source_id, item[0].chunk_index),
        )[:limit]

    @staticmethod
    def _extract_text(source: MockKnowledgeSource) -> str:
        if source.source_type is KnowledgeSourceType.URL:
            raise KnowledgeProcessingFailure(
                "URL content retrieval is not enabled in the local mock yet"
            )
        if source.file_type not in {"txt", "md", "pdf"}:
            raise KnowledgeProcessingFailure(
                "Local processing currently supports only .txt, .md, and .pdf files"
            )
        if not isinstance(source.payload, bytes):
            raise KnowledgeProcessingFailure("The uploaded file payload is invalid")

        text = (
            MockKnowledgeProcessingService._extract_pdf_text(source.payload)
            if source.file_type == "pdf"
            else source.payload.decode("utf-8", errors="replace")
        )
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _extract_pdf_text(payload: bytes) -> str:
        """Extract selectable text from a PDF without storing the original file again."""
        try:
            reader = PdfReader(BytesIO(payload))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise KnowledgeProcessingFailure("PDF text extraction failed") from exc

        if not text.strip():
            raise KnowledgeProcessingFailure("The PDF does not contain extractable text")
        return text

    def _build_chunks(self, *, source: MockKnowledgeSource, text: str) -> list[MockKnowledgeChunk]:
        chunks: list[MockKnowledgeChunk] = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + MAX_CHUNK_CHARS, text_length)
            if end < text_length:
                word_boundary = text.rfind(" ", start, end)
                if word_boundary > start:
                    end = word_boundary

            content = text[start:end].strip()
            if content:
                chunk_index = len(chunks) + 1
                chunks.append(
                    MockKnowledgeChunk(
                        id=f"source-{source.id}-chunk-{chunk_index}",
                        source_id=source.id,
                        course_id=source.course_id,
                        source_filename=source.filename,
                        chunk_index=chunk_index,
                        content=content,
                        start_char=start,
                        end_char=end,
                    )
                )

            if end >= text_length:
                break
            start = max(end - CHUNK_OVERLAP_CHARS, start + 1)

        return chunks

    @staticmethod
    def _tokens(value: str) -> list[str]:
        """Tokenize Thai/English text enough for deterministic local retrieval."""
        return re.findall(r"\w+", value.casefold(), flags=re.UNICODE)


mock_knowledge_processing_service = MockKnowledgeProcessingService()
