"""Authentication router handling user registration, login, token refresh, verification, and logout."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
    VerifyEmailRequest,
    VerifyPhoneRequest,
)
from app.schemas.common import StandardResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=StandardResponse[UserOut], status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new bachelor or owner account."""
    auth_service = AuthService(db)
    user = await auth_service.register(req)
    return StandardResponse(
        success=True,
        message="User registered successfully. Welcome to BachNest!",
        data=UserOut.model_validate(user),
    )


@router.post("/login", response_model=StandardResponse[TokenResponse])
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email or phone and receive JWT access and refresh tokens."""
    auth_service = AuthService(db)
    tokens = await auth_service.authenticate(req)
    return StandardResponse(
        success=True,
        message="Authentication successful",
        data=tokens,
    )


@router.post("/refresh", response_model=StandardResponse[TokenResponse])
async def refresh_token(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Obtain a new access token using a valid refresh token with role claims preserved."""
    auth_service = AuthService(db)
    tokens = await auth_service.refresh_tokens(req)
    return StandardResponse(
        success=True,
        message="Token refreshed successfully",
        data=tokens,
    )


@router.post("/verify-phone", response_model=StandardResponse[dict])
async def verify_phone(
    req: VerifyPhoneRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify user phone number with OTP."""
    auth_service = AuthService(db)
    verified = await auth_service.verify_phone(current_user, req.otp)
    return StandardResponse(
        success=verified,
        message="Phone number verified successfully" if verified else "Invalid OTP provided",
        data={"is_phone_verified": current_user.is_phone_verified},
    )


@router.post("/verify-email", response_model=StandardResponse[dict])
async def verify_email(
    req: VerifyEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify user email with verification code/token."""
    auth_service = AuthService(db)
    verified = await auth_service.verify_email(current_user, req.token_or_code)
    return StandardResponse(
        success=verified,
        message="Email verified successfully" if verified else "Invalid verification code",
        data={"is_email_verified": current_user.is_email_verified},
    )


@router.post("/logout", response_model=StandardResponse[dict])
async def logout(current_user: User = Depends(get_current_user)):
    """Revoke user session and logout."""
    return StandardResponse(
        success=True,
        message="User logged out successfully",
        data={"user_id": str(current_user.id)},
    )
