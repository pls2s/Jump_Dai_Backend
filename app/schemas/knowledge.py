"""Function 3 request and response contracts for processed course knowledge."""

from pydantic import BaseModel, Field

from app.schemas.document import KnowledgeSourceResponse


class KnowledgeChunkResponse(BaseModel):
    """A source-grounded text segment created by Function 3 processing."""

    id: str
    source_id: int
    course_id: int
    source_filename: str
    chunk_index: int = Field(ge=1)
    content: str
    start_char: int = Field(ge=0)
    end_char: int = Field(ge=0)


class KnowledgeProcessingResponse(BaseModel):
    """Result returned after a knowledge source has been processed."""

    source: KnowledgeSourceResponse
    chunks_created: int = Field(ge=0)


class KnowledgeSearchResult(KnowledgeChunkResponse):
    """A locally retrieved chunk with its deterministic keyword score."""

    score: float = Field(gt=0, le=1)
