"""Request and response contracts for Function 2: Knowledge Upload."""

from datetime import datetime
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentStatus(str, Enum):
    """Lifecycle states for a knowledge source."""

    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class KnowledgeSourceType(str, Enum):
    """Supported source types from the Function 2 specification."""

    FILE = "FILE"
    URL = "URL"


class UrlKnowledgeSourceRequest(BaseModel):
    """A public HTTP(S) URL supplied as a knowledge source reference."""

    model_config = ConfigDict(str_strip_whitespace=True)

    url: str = Field(min_length=1, max_length=2_048)
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        """Accept only absolute HTTP(S) addresses without fetching them yet."""
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be an absolute HTTP or HTTPS address")
        return value


class UrlKnowledgeSourceUpdateRequest(BaseModel):
    """Full replacement data for an HTTP(S) URL knowledge source."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=1, max_length=2_048)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        """Accept only absolute HTTP(S) addresses without fetching them yet."""
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be an absolute HTTP or HTTPS address")
        return value


class KnowledgeSourceResponse(BaseModel):
    """Detailed knowledge-source data returned after creation."""

    id: int
    course_id: int
    filename: str
    file_type: str
    size: int
    source_type: KnowledgeSourceType
    status: DocumentStatus
    version: int
    created_at: datetime
    updated_at: datetime


class DocumentListItem(BaseModel):
    """Compact file representation used by the documented documents endpoint."""

    id: int
    filename: str
    status: DocumentStatus


class KnowledgeSourceListItem(DocumentListItem):
    """Source-management list item that also identifies its source type."""

    source_type: KnowledgeSourceType
    version: int
    updated_at: datetime
