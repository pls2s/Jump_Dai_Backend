"""Function 3 knowledge-processing endpoints, separate from source upload routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.knowledge import (
    KnowledgeChunkResponse,
    KnowledgeProcessingResponse,
    KnowledgeSearchResult,
)
from app.schemas.user import SuccessResponse, UserRole
from app.services.auth_service import MockUser, mock_auth_service
from app.services.course_service import mock_course_service
from app.services.document_service import mock_document_service
from app.services.knowledge_service import (
    KnowledgeProcessingFailure,
    mock_knowledge_processing_service,
)

router = APIRouter(tags=["knowledge-processing"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: object) -> dict:
    """Keep successful Function 3 responses in the shared API envelope."""
    return {"success": True, "data": data}


def _require_creator(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> MockUser:
    """Authenticate the request and require a creator workspace role."""
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"

    user = mock_auth_service.current_user(authorization)
    if UserRole.CREATOR not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "A creator workspace is required for knowledge processing",
            },
        )
    return user


def _owned_course(course_id: int, user: MockUser) -> None:
    """Confirm that a Function 3 action is scoped to an owned course."""
    mock_course_service.get_for_creator(course_id=course_id, creator_id=user.id)


@router.post(
    "/knowledge-sources/{source_id}/process",
    response_model=SuccessResponse[KnowledgeProcessingResponse],
)
def process_knowledge_source(
    source_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Extract and locally index a TXT/Markdown source for later AI retrieval."""
    user = _require_creator(credentials)
    source = mock_document_service.get(source_id=source_id)
    _owned_course(source.course_id, user)

    try:
        chunks = mock_knowledge_processing_service.process(source)
    except KnowledgeProcessingFailure as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "KNOWLEDGE_SOURCE_PROCESSING_FAILED",
                "message": str(exc),
            },
        )

    processed_source = mock_document_service.get(source_id=source_id)
    return _success(
        {
            "source": processed_source.to_response_dict(),
            "chunks_created": len(chunks),
        }
    )


@router.get(
    "/knowledge-sources/{source_id}/chunks",
    response_model=SuccessResponse[list[KnowledgeChunkResponse]],
)
def list_knowledge_source_chunks(
    source_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Return the source-grounded chunks visible to its owning creator."""
    user = _require_creator(credentials)
    source = mock_document_service.get(source_id=source_id)
    _owned_course(source.course_id, user)
    chunks = mock_knowledge_processing_service.list_for_source(source_id=source_id)
    return _success([chunk.to_response_dict() for chunk in chunks])


@router.get(
    "/courses/{course_id}/knowledge-search",
    response_model=SuccessResponse[list[KnowledgeSearchResult]],
)
def search_course_knowledge(
    course_id: int,
    query: str = Query(min_length=1, max_length=500),
    limit: int = Query(default=5, ge=1, le=20),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """Retrieve locally indexed chunks from one creator-owned course by keyword."""
    user = _require_creator(credentials)
    _owned_course(course_id, user)
    results = mock_knowledge_processing_service.search(
        course_id=course_id,
        query=query,
        limit=limit,
    )
    return _success(
        [
            {**chunk.to_response_dict(), "score": score}
            for chunk, score in results
        ]
    )
