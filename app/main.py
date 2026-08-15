"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(title="SkillSync AI API", version="0.1.0")
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    """Return a simple service status response."""
    return {"message": "SkillSync AI API", "status": "running"}
