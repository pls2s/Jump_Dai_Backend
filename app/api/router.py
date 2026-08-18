"""Top-level API router configuration."""

from fastapi import APIRouter

from app.api.routes import (
    assessments,
    auth,
    courses,
    dashboard,
    documents,
    health,
    learning,
    portfolio,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(courses.router)
api_router.include_router(documents.router)
api_router.include_router(dashboard.router)
api_router.include_router(portfolio.router)
api_router.include_router(learning.router)
api_router.include_router(assessments.router)
