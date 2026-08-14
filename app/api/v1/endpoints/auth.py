"""Authentication router handling user registration, login, token refresh, and logout."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshTokenRequest, RegisterRequest, TokenResponse, UserOut
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
        data=UserOut.model_validate(user)
    )


@router.post("/login", response_model=StandardResponse[TokenResponse])
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email or phone and receive JWT access and refresh tokens."""
    auth_service = AuthService(db)
    tokens = await auth_service.authenticate(req)
    return StandardResponse(
        success=True,
        message="Authentication successful",
        data=tokens
    )


@router.post("/refresh", response_model=StandardResponse[TokenResponse])
async def refresh_token(req: RefreshTokenRequest):
    """Obtain a new access token using a valid refresh token."""
    from app.core.security import create_access_token, decode_token
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        return StandardResponse(success=False, message="Invalid token type", data=None)
    
    new_access_token = create_access_token(subject=payload.get("sub"))
    return StandardResponse(
        success=True,
        message="Token refreshed successfully",
        data=TokenResponse(
            access_token=new_access_token,
            refresh_token=req.refresh_token,
            token_type="bearer",
            expires_in=900,
        )
    )


@router.post("/logout", response_model=StandardResponse[dict])
async def logout(current_user: User = Depends(get_current_user)):
    """Revoke user session and logout."""
    return StandardResponse(
        success=True,
        message="User logged out successfully",
        data={"user_id": str(current_user.id)}
    )
