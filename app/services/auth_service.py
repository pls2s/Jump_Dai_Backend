"""Temporary in-memory implementation of the authentication user flow.

This module deliberately has no database, password hashing, email provider, or
JWT dependency.  It lets the frontend integrate the onboarding screens before
those production pieces are introduced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock

from fastapi import HTTPException, status

from app.schemas.user import UserRole, WorkspaceType

MOCK_VERIFICATION_CODE = "123456"


@dataclass
class MockUser:
    """Private representation of a user held only for the server process."""

    id: int
    name: str
    email: str
    password: str
    email_verified: bool = False
    workspace_type: WorkspaceType | None = None
    roles: list[UserRole] = field(default_factory=list)

    @property
    def onboarding_completed(self) -> bool:
        """A user is ready only after verification and workspace selection."""
        return self.email_verified and self.workspace_type is not None

    def to_public_dict(self) -> dict:
        """Return fields that are safe for an API response."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "email_verified": self.email_verified,
            "workspace_type": self.workspace_type,
            "roles": self.roles,
            "onboarding_completed": self.onboarding_completed,
        }


class MockAuthService:
    """Thread-safe, process-local user and token store for the MVP mock."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reset()

    def reset(self) -> None:
        """Restore a predictable demo account; primarily useful to tests."""
        with self._lock:
            demo_user = MockUser(
                id=1,
                name="SkillSync Demo",
                email="demo@skillsync.local",
                password="password123",
                email_verified=True,
                workspace_type=WorkspaceType.LEARNER,
                roles=[UserRole.LEARNER],
            )
            self._users_by_email = {demo_user.email: demo_user}
            self._tokens: dict[str, int] = {}
            self._next_user_id = 2

    def register(self, *, name: str, email: str, password: str) -> MockUser:
        """Create an unverified mock user."""
        with self._lock:
            if email in self._users_by_email:
                self._raise_error(
                    status.HTTP_409_CONFLICT,
                    "EMAIL_ALREADY_REGISTERED",
                    "An account with this email already exists",
                )

            user = MockUser(
                id=self._next_user_id,
                name=name,
                email=email,
                password=password,
            )
            self._users_by_email[email] = user
            self._next_user_id += 1
            return user

    def verify_email(self, *, email: str, code: str) -> tuple[MockUser, str]:
        """Mark the user verified when the known development code is provided."""
        with self._lock:
            user = self._find_user(email)
            if code != MOCK_VERIFICATION_CODE:
                self._raise_error(
                    status.HTTP_400_BAD_REQUEST,
                    "INVALID_VERIFICATION_CODE",
                    "The verification code is incorrect",
                )
            user.email_verified = True
            return user, self._issue_token(user)

    def resend_verification(self, *, email: str) -> str:
        """Validate the account and return the fixed mock code; no email is sent."""
        with self._lock:
            self._find_user(email)
            return MOCK_VERIFICATION_CODE

    def login(self, *, email: str, password: str) -> tuple[MockUser, str]:
        """Validate mock credentials and issue a process-local access token."""
        with self._lock:
            user = self._find_user(email, hide_missing=True)
            if user.password != password:
                self._raise_error(
                    status.HTTP_401_UNAUTHORIZED,
                    "INVALID_CREDENTIALS",
                    "Email or password is incorrect",
                )
            if not user.email_verified:
                self._raise_error(
                    status.HTTP_403_FORBIDDEN,
                    "EMAIL_NOT_VERIFIED",
                    "Verify your email before signing in",
                )
            return user, self._issue_token(user)

    def current_user(self, authorization: str | None) -> MockUser:
        """Resolve the user represented by an Authorization bearer token."""
        with self._lock:
            if not authorization or not authorization.startswith("Bearer "):
                self._raise_error(
                    status.HTTP_401_UNAUTHORIZED,
                    "UNAUTHORIZED",
                    "A Bearer access token is required",
                )
            token = authorization.removeprefix("Bearer ").strip()
            user_id = self._tokens.get(token)
            if user_id is None:
                self._raise_error(
                    status.HTTP_401_UNAUTHORIZED,
                    "UNAUTHORIZED",
                    "The access token is invalid or has expired",
                )

            for user in self._users_by_email.values():
                if user.id == user_id:
                    return user
            self._raise_error(
                status.HTTP_401_UNAUTHORIZED,
                "UNAUTHORIZED",
                "The user for this access token no longer exists",
            )

    def select_workspace(self, user: MockUser, workspace_type: WorkspaceType) -> MockUser:
        """Save the post-verification onboarding choice for the current user."""
        with self._lock:
            if not user.email_verified:
                self._raise_error(
                    status.HTTP_403_FORBIDDEN,
                    "EMAIL_NOT_VERIFIED",
                    "Verify your email before selecting a workspace",
                )

            user.workspace_type = workspace_type
            user.roles = (
                [UserRole.LEARNER]
                if workspace_type is WorkspaceType.LEARNER
                else [UserRole.CREATOR]
            )
            return user

    def _find_user(self, email: str, *, hide_missing: bool = False) -> MockUser:
        user = self._users_by_email.get(email)
        if user is None:
            self._raise_error(
                status.HTTP_401_UNAUTHORIZED if hide_missing else status.HTTP_404_NOT_FOUND,
                "INVALID_CREDENTIALS" if hide_missing else "USER_NOT_FOUND",
                "Email or password is incorrect" if hide_missing else "No account exists for this email",
            )
        return user

    def _issue_token(self, user: MockUser) -> str:
        token = f"mock-access-token-{user.id}"
        self._tokens[token] = user.id
        return token

    @staticmethod
    def _raise_error(status_code: int, code: str, message: str) -> None:
        raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


mock_auth_service = MockAuthService()
