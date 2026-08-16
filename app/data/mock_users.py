"""Seed users available in the local mock authentication environment."""

from dataclasses import dataclass

from app.schemas.user import UserRole, WorkspaceType


@dataclass(frozen=True)
class MockUserSeed:
    """Public fixture values plus the development-only mock password."""

    id: int
    name: str
    email: str
    password: str
    workspace_type: WorkspaceType
    roles: tuple[UserRole, ...]


MOCK_USER_SEEDS: tuple[MockUserSeed, ...] = (
    MockUserSeed(
        id=1,
        name="Learner Demo",
        email="demo@skillsync.local",
        password="password123",
        workspace_type=WorkspaceType.LEARNER,
        roles=(UserRole.LEARNER,),
    ),
    MockUserSeed(
        id=2,
        name="Creator Demo",
        email="creator@skillsync.local",
        password="password123",
        workspace_type=WorkspaceType.CREATOR,
        roles=(UserRole.CREATOR,),
    ),
    MockUserSeed(
        id=3,
        name="Organization Demo",
        email="organization@skillsync.local",
        password="password123",
        workspace_type=WorkspaceType.ORGANIZATION,
        roles=(UserRole.CREATOR,),
    ),
)
