"""Top-level API router configuration."""

from fastapi import APIRouter

from app.api.routes import (
    assessments,
    auth,
    courses,
    documents,
    health,
    learning,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(courses.router)
api_router.include_router(documents.router)
api_router.include_router(learning.router)
api_router.include_router(assessments.router)
