"""Authentication and User schemas."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import EmailStr, Field, field_validator

from app.core.constants import Gender, UserRole
from app.schemas.common import BaseSchema


class RegisterRequest(BaseSchema):
    email: EmailStr
    phone: str = Field(..., min_length=11, max_length=15, description="BD Phone number e.g., 017XXXXXXXX")
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = Field(default=UserRole.BACHELOR)
    gender: Gender = Field(default=Gender.OTHER)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if not v.startswith("+880") and not v.startswith("01"):
            raise ValueError("Phone number must be a valid Bangladesh number")
        return v


class LoginRequest(BaseSchema):
    identifier: str = Field(..., description="Email address or phone number")
    password: str


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # seconds


class UserOut(BaseSchema):
    id: uuid.UUID
    email: EmailStr
    phone: str
    full_name: str
    role: UserRole
    gender: Gender
    is_active: bool
    is_phone_verified: bool
    is_email_verified: bool
    is_kyc_verified: bool
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    occupation: Optional[str] = None
    institution_or_company: Optional[str] = None
    trust_score: float
    created_at: datetime


class UserUpdate(BaseSchema):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    occupation: Optional[str] = None
    institution_or_company: Optional[str] = None
    gender: Optional[Gender] = None


class VerifyPhoneRequest(BaseSchema):
    otp: str = Field(..., min_length=4, max_length=6, description="SMS OTP code e.g. 123456")


class VerifyEmailRequest(BaseSchema):
    token_or_code: str = Field(..., min_length=4, max_length=100, description="Email verification code or token")

