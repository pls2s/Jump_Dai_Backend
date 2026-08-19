"""Request and response contracts for the mock authentication flow."""

from enum import Enum
from typing import Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkspaceType(str, Enum):
    """The onboarding choice shown after email verification."""

    LEARNER = "learner"
    CREATOR = "creator"
    ORGANIZATION = "organization"


class UserRole(str, Enum):
    """Application roles derived from the selected workspace type."""

    LEARNER = "LEARNER"
    CREATOR = "CREATOR"
    ADMIN = "ADMIN"


class RegisterRequest(BaseModel):
    """Payload collected by the create-account screen."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Perform lightweight validation without adding an email dependency."""
        normalized = value.lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("email must be a valid email address")
        return normalized


class LoginRequest(BaseModel):
    """Payload collected by the sign-in screen."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize the lookup key used by the in-memory store."""
        return value.lower()


class VerifyEmailRequest(BaseModel):
    """Six-digit code submitted by the email-verification screen."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(max_length=254)
    code: str = Field(pattern=r"^\d{6}$")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize the lookup key used by the in-memory store."""
        return value.lower()


class ResendVerificationRequest(BaseModel):
    """Request a new mock verification code for an account."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(max_length=254)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize the lookup key used by the in-memory store."""
        return value.lower()


class SelectWorkspaceRequest(BaseModel):
    """Payload collected by the learner / creator / organization screen."""

    workspace_type: WorkspaceType


class UserResponse(BaseModel):
    """Safe user fields returned to the frontend."""

    id: int
    name: str
    email: str
    email_verified: bool
    workspace_type: Optional[WorkspaceType] = None
    roles: list[UserRole] = Field(default_factory=list)
    onboarding_completed: bool
    is_active: bool


class UserProfileUpdateRequest(BaseModel):
    """Safe self-service profile fields available in the MVP."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)


class UserRoleUpdateRequest(BaseModel):
    """Administrator-managed role assignments for one account."""

    roles: list[UserRole] = Field(min_length=1, max_length=3)

    @field_validator("roles")
    @classmethod
    def reject_duplicate_roles(cls, value: list[UserRole]) -> list[UserRole]:
        if len(set(value)) != len(value):
            raise ValueError("roles must not contain duplicates")
        return value


class UserStatusUpdateRequest(BaseModel):
    """Administrator control for temporarily suspending an account."""

    is_active: bool


class RegisterResponseData(BaseModel):
    """Registration result including the development-only mock code."""

    user: UserResponse
    next_step: Literal["email_verification"]
    mock_verification_code: str


class VerificationResponseData(BaseModel):
    """Authentication state returned after successful email verification."""

    access_token: str
    token_type: Literal["bearer"]
    user: UserResponse
    next_step: Literal["workspace_selection", "complete"]


class LoginResponseData(BaseModel):
    """Authentication state returned after password sign-in."""

    access_token: str
    token_type: Literal["bearer"]
    user: UserResponse
    next_step: Literal["email_verification", "workspace_selection", "complete"]


class ResendVerificationResponseData(BaseModel):
    """Development-only resend result."""

    message: str
    mock_verification_code: str


class WorkspaceResponseData(BaseModel):
    """Completed onboarding state after selecting a workspace."""

    user: UserResponse
    next_step: Literal["complete"]


ResponseData = TypeVar("ResponseData")


class SuccessResponse(BaseModel, Generic[ResponseData]):
    """Shared API success envelope."""

    success: Literal[True] = True
    data: ResponseData
