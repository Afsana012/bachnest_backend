"""Authentication service managing user registration, login, and token generation."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, req: RegisterRequest) -> User:
        """Register a new user after verifying unique email and phone."""
        # Check existing email or phone
        query = select(User).where(or_(User.email == req.email.lower(), User.phone == req.phone))
        result = await self.db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.email == req.email.lower():
                raise ConflictError(message="A user with this email address already exists")
            raise ConflictError(message="A user with this phone number already exists")

        # Create user
        user = User(
            email=req.email.lower(),
            phone=req.phone,
            hashed_password=get_password_hash(req.password),
            full_name=req.full_name,
            role=req.role,
            gender=req.gender,
            is_active=True,
            is_phone_verified=False,
            is_email_verified=False,
            is_kyc_verified=False,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def authenticate(self, req: LoginRequest) -> TokenResponse:
        """Authenticate user by email or phone and return access and refresh tokens."""
        identifier = req.identifier.strip().lower()
        query = select(User).where(or_(User.email == identifier, User.phone == identifier))
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not verify_password(req.password, user.hashed_password):
            raise AuthenticationError(message="Invalid credentials provided")

        if not user.is_active:
            raise AuthenticationError(message="This account has been deactivated")

        access_token = create_access_token(
            subject=user.id,
            extra_claims={"role": user.role.value, "email": user.email}
        )
        refresh_token = create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900,
        )
