"""FastAPI dependencies for database, Redis, authentication, and RBAC."""

import uuid
from typing import AsyncGenerator, Callable, List, Optional
from fastapi import Depends, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import KYCStatus, UserRole
from app.core.exceptions import AuthenticationError, KYCRequiredError, PermissionDeniedError
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal, get_db
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


async def get_redis() -> AsyncGenerator[Optional[aioredis.Redis], None]:
    """Provide an async Redis client dependency."""
    client = None
    try:
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        yield client
    except Exception:
        yield None
    finally:
        if client:
            await client.aclose()


async def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate bearer token and retrieve the current authenticated User."""
    if not auth_header or not auth_header.credentials:
        raise AuthenticationError(message="Authentication credentials were not provided")
    
    payload = decode_token(auth_header.credentials)
    user_id_str = payload.get("sub")
    token_type = payload.get("type")
    
    if not user_id_str or token_type != "access":
        raise AuthenticationError(message="Invalid token format or token type")
    
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationError(message="Invalid user identifier in token")

    query = select(User).where(User.id == user_id, User.is_active == True)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError(message="User account not found or deactivated")

    return user


async def get_optional_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Retrieve user if valid token present, otherwise None."""
    if not auth_header or not auth_header.credentials:
        return None
    try:
        return await get_current_user(auth_header=auth_header, db=db)
    except Exception:
        return None


def require_roles(*allowed_roles: UserRole) -> Callable:
    """Dependency factory enforcing Role-Based Access Control."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and current_user.role != UserRole.SUPER_ADMIN:
            raise PermissionDeniedError(
                message=f"Access forbidden: User role '{current_user.role.value}' does not have required permissions"
            )
        return current_user
    return role_checker


async def require_kyc_approved(current_user: User = Depends(get_current_user)) -> User:
    """Dependency verifying that the user's KYC has been approved."""
    if not current_user.is_kyc_verified:
        raise KYCRequiredError(
            message="KYC verification is required before performing this action"
        )
    return current_user
