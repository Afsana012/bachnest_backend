"""Review service managing two-sided reviews and blind-review visibility rules."""

from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import TenancyStatus, UserRole
from app.core.exceptions import ConflictError, InvalidBookingError, PermissionDeniedError, ResourceNotFoundError
from app.models.booking import Tenancy
from app.models.emergency import Review
from app.models.user import User
from app.schemas.booking import ReviewCreateRequest


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_review(self, reviewer: User, req: ReviewCreateRequest) -> Review:
        """Create a two-sided review for a completed tenancy."""
        tenancy_query = select(Tenancy).where(Tenancy.id == req.tenancy_id)
        tenancy = (await self.db.execute(tenancy_query)).scalar_one_or_none()
        if not tenancy:
            raise ResourceNotFoundError(message="Tenancy not found")

        # Must be part of the tenancy
        if reviewer.id == tenancy.tenant_id:
            reviewee_id = tenancy.owner_id
        elif reviewer.id == tenancy.owner_id:
            reviewee_id = tenancy.tenant_id
        elif reviewer.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            reviewee_id = tenancy.tenant_id
        else:
            raise PermissionDeniedError(message="You were not a party to this tenancy agreement")

        # Check for duplicate review
        dup_query = select(Review).where(
            Review.tenancy_id == tenancy.id,
            Review.reviewer_id == reviewer.id,
        )
        existing = (await self.db.execute(dup_query)).scalar_one_or_none()
        if existing:
            raise ConflictError(message="You have already submitted a review for this tenancy")

        review = Review(
            tenancy_id=tenancy.id,
            reviewer_id=reviewer.id,
            reviewee_id=reviewee_id,
            rating=req.rating,
            comment=req.comment,
            is_public=False,  # Blind review window
        )
        self.db.add(review)

        # Check if opposite review exists to unlock public visibility
        opp_query = select(Review).where(
            Review.tenancy_id == tenancy.id,
            Review.reviewer_id == reviewee_id,
        )
        opp_review = (await self.db.execute(opp_query)).scalar_one_or_none()
        if opp_review:
            review.is_public = True
            opp_review.is_public = True

        # Update reviewee trust score
        reviewee_query = select(User).where(User.id == reviewee_id)
        reviewee = (await self.db.execute(reviewee_query)).scalar_one_or_none()
        if reviewee:
            rating_delta = (req.rating - 3) * 2.0  # 5 -> +4, 4 -> +2, 3 -> 0, 2 -> -2, 1 -> -4
            reviewee.trust_score = max(0.0, min(100.0, reviewee.trust_score + rating_delta))

        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def list_user_reviews(self, user_id: uuid.UUID) -> List[Review]:
        """List public reviews for a user."""
        query = select(Review).where(
            Review.reviewee_id == user_id,
            Review.is_public == True,
        ).order_by(Review.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
