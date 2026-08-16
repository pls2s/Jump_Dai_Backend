"""Mock authentication and onboarding endpoints for the first frontend flow."""

from fastapi import APIRouter, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.user import (
    LoginRequest,
    LoginResponseData,
    RegisterRequest,
    RegisterResponseData,
    ResendVerificationRequest,
    ResendVerificationResponseData,
    SelectWorkspaceRequest,
    SuccessResponse,
    UserResponse,
    VerifyEmailRequest,
    VerificationResponseData,
    WorkspaceResponseData,
)
from app.services.auth_service import MOCK_VERIFICATION_CODE, MockUser, mock_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def _success(data: dict) -> dict:
    """Keep every successful auth response in the documented envelope."""
    return {"success": True, "data": data}


def _next_step(user: MockUser) -> str:
    """Describe where the client should route the user in the onboarding flow."""
    if not user.email_verified:
        return "email_verification"
    if not user.onboarding_completed:
        return "workspace_selection"
    return "complete"


def _current_user(credentials: HTTPAuthorizationCredentials | None) -> MockUser:
    """Resolve a standard HTTP Bearer credential to the current mock user."""
    authorization = None
    if credentials is not None:
        authorization = f"{credentials.scheme} {credentials.credentials}"
    return mock_auth_service.current_user(authorization)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[RegisterResponseData],
)
def register(payload: RegisterRequest) -> dict:
    """Create an account and begin its mock email-verification step."""
    user = mock_auth_service.register(
        name=payload.name,
        email=payload.email,
        password=payload.password,
    )
    return _success(
        {
            "user": user.to_public_dict(),
            "next_step": "email_verification",
            "mock_verification_code": MOCK_VERIFICATION_CODE,
        }
    )


@router.post("/verify-email", response_model=SuccessResponse[VerificationResponseData])
def verify_email(payload: VerifyEmailRequest) -> dict:
    """Verify an account with code ``123456`` and issue a mock access token."""
    user, access_token = mock_auth_service.verify_email(email=payload.email, code=payload.code)
    return _success(
        {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.to_public_dict(),
            "next_step": _next_step(user),
        }
    )


@router.post(
    "/resend-verification",
    response_model=SuccessResponse[ResendVerificationResponseData],
)
def resend_verification(payload: ResendVerificationRequest) -> dict:
    """Return the mock code instead of sending email in this development phase."""
    code = mock_auth_service.resend_verification(email=payload.email)
    return _success(
        {
            "message": "Mock verification code resent. No email was sent.",
            "mock_verification_code": code,
        }
    )


@router.post("/login", response_model=SuccessResponse[LoginResponseData])
def login(payload: LoginRequest) -> dict:
    """Sign in a verified mock user with email and password."""
    user, access_token = mock_auth_service.login(email=payload.email, password=payload.password)
    return _success(
        {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.to_public_dict(),
            "next_step": _next_step(user),
        }
    )


@router.get("/me", response_model=SuccessResponse[UserResponse])
def read_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    """Return the user associated with a mock Bearer access token."""
    user = _current_user(credentials)
    return _success(user.to_public_dict())


@router.post("/workspace", response_model=SuccessResponse[WorkspaceResponseData])
def select_workspace(
    payload: SelectWorkspaceRequest,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    """Complete onboarding by storing the selected workspace type."""
    user = _current_user(credentials)
    updated_user = mock_auth_service.select_workspace(user, payload.workspace_type)
    return _success(
        {
            "user": updated_user.to_public_dict(),
            "next_step": "complete",
        }
    )
