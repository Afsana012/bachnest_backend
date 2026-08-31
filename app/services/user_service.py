"""User service managing profile retrievals, updates, and public details."""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.models.user import User
from app.schemas.auth import UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        """Retrieve an active user by ID."""
        query = select(User).where(User.id == user_id, User.is_active == True)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise ResourceNotFoundError(message="User not found")
        return user

    async def update_profile(self, user: User, update_data: UserUpdate) -> User:
        """Update current user profile fields."""
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)
        return user
