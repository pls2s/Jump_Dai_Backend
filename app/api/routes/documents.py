"""Function 2 knowledge-upload endpoints."""

from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Security,
    UploadFile,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.document import (
    DocumentListItem,
    KnowledgeSourceListItem,
    KnowledgeSourceResponse,
    KnowledgeSourceType,
    ManualKnowledgeSourceRequest,
    UrlKnowledgeSourceRequest,
    UrlKnowledgeSourceUpdateRequest,
)
from app.schemas.user import SuccessResponse, UserRole
from app.services.auth_service import MockUser, mock_auth_service
from app.services.course_service import mock_course_service
from app.services.document_service import mock_document_service
from app.services.knowledge_service import mock_knowledge_processing_service

router = APIRouter(tags=["documents"])
bearer_scheme = HTTPBearer(auto_error=False)

ALLOWED_FILE_TYPES = {"pdf", "doc", "docx", "ppt", "pptx", "txt", "md"}
MAX_UPLOAD_BYTES = 25 * 1024


def _success(data: object) -> dict:
    """Keep successful knowledge-source responses in the documented envelope."""
    return {"success": True, "data": data}


def _require_creator(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> MockUser:
    """Authenticate the request and require the creator workspace role."""
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"

    user = mock_auth_service.current_user(authorization)
    if UserRole.CREATOR not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "A creator workspace is required for knowledge sources",
            },
        )
    return user


def _owned_course(course_id: int, user: MockUser) -> None:
    """Confirm that a Function 2 action is scoped to an owned course."""
    mock_course_service.get_for_creator(course_id=course_id, creator_id=user.id)


@router.post(
    "/courses/{course_id}/documents",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[KnowledgeSourceResponse],
)
async def upload_document(
    course_id: int,
    file: UploadFile = File(...),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Upload a PDF, document, slide, or text file as a mock knowledge source."""
    user = _require_creator(credentials)
    _owned_course(course_id, user)

    filename = file.filename or ""
    file_type = Path(filename).suffix.removeprefix(".").lower()
    if not filename or file_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "UNSUPPORTED_FILE_TYPE",
                "message": "Upload a PDF, document, slide, or text file",
            },
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_FILE", "message": "The uploaded file is empty"},
        )
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": "The uploaded file must not exceed 25 KB",
            },
        )

    source = mock_document_service.create_file(
        course_id=course_id,
        filename=filename,
        file_type=file_type,
        content=content,
    )
    return _success(source.to_response_dict())


@router.post(
    "/courses/{course_id}/knowledge-sources/url",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[KnowledgeSourceResponse],
)
def add_url_knowledge_source(
    course_id: int,
    payload: UrlKnowledgeSourceRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Add an HTTP(S) URL as a source reference without fetching it yet."""
    user = _require_creator(credentials)
    _owned_course(course_id, user)
    source = mock_document_service.create_url(
        course_id=course_id,
        title=payload.title,
        url=payload.url,
    )
    return _success(source.to_response_dict())


@router.post(
    "/courses/{course_id}/knowledge-sources/text",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[KnowledgeSourceResponse],
)
def add_manual_knowledge_source(
    course_id: int,
    payload: ManualKnowledgeSourceRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Add creator-authored text that can immediately enter local processing."""
    user = _require_creator(credentials)
    _owned_course(course_id, user)
    source = mock_document_service.create_text(
        course_id=course_id,
        title=payload.title,
        content=payload.content,
    )
    return _success(source.to_response_dict())


@router.put(
    "/knowledge-sources/{source_id}/url",
    response_model=SuccessResponse[KnowledgeSourceResponse],
)
def update_url_knowledge_source(
    source_id: int,
    payload: UrlKnowledgeSourceUpdateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Replace a URL source after verifying ownership of its course."""
    user = _require_creator(credentials)
    source = mock_document_service.get(source_id=source_id)
    _owned_course(source.course_id, user)
    updated_source = mock_document_service.update_url(
        source_id=source_id,
        title=payload.title,
        url=payload.url,
    )
    mock_knowledge_processing_service.remove_source(source_id=source_id)
    return _success(updated_source.to_response_dict())


@router.get(
    "/courses/{course_id}/documents",
    response_model=SuccessResponse[list[DocumentListItem]],
)
def list_course_documents(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """List file uploads for the creator's course."""
    user = _require_creator(credentials)
    _owned_course(course_id, user)
    documents = mock_document_service.list_for_course(
        course_id=course_id,
        source_type=KnowledgeSourceType.FILE,
    )
    return _success(
        [
            {
                "id": document.id,
                "filename": document.filename,
                "status": document.status,
            }
            for document in documents
        ]
    )


@router.get(
    "/courses/{course_id}/knowledge-sources",
    response_model=SuccessResponse[list[KnowledgeSourceListItem]],
)
def list_knowledge_sources(
    course_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """List all file and URL sources for a creator's course."""
    user = _require_creator(credentials)
    _owned_course(course_id, user)
    sources = mock_document_service.list_for_course(course_id=course_id)
    return _success([source.to_list_dict() for source in sources])


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Delete a knowledge source after verifying course ownership."""
    user = _require_creator(credentials)
    source = mock_document_service.get(source_id=document_id)
    _owned_course(source.course_id, user)
    mock_document_service.delete(source_id=document_id)
    mock_knowledge_processing_service.remove_source(source_id=document_id)
    return {"success": True}
