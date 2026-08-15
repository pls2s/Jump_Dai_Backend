"""Service health endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Confirm that the API is available."""
    return {"status": "ok"}
