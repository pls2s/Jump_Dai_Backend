"""Top-level API router configuration."""

from fastapi import APIRouter

from app.api.routes import (
    ai,
    assessments,
    auth,
    courses,
    dashboard,
    documents,
    health,
    knowledge,
    learner,
    learning,
    notifications,
    organization,
    portfolio,
    publication,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(courses.router)
api_router.include_router(documents.router)
api_router.include_router(knowledge.router)
api_router.include_router(ai.router)
api_router.include_router(publication.router)
api_router.include_router(dashboard.router)
api_router.include_router(portfolio.router)
api_router.include_router(learning.router)
api_router.include_router(learner.router)
api_router.include_router(assessments.router)
api_router.include_router(organization.router)
api_router.include_router(notifications.router)
