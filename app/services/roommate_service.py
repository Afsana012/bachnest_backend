"""Roommate preference and compatibility matching service."""

from typing import List, Optional, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.kyc import RoommatePreference
from app.models.user import User
from app.schemas.kyc import CompatibilityResult, RoommatePreferenceCreate


class RoommateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_preference(self, user: User, req: RoommatePreferenceCreate) -> RoommatePreference:
        """Create or update user roommate preference."""
        query = select(RoommatePreference).where(RoommatePreference.user_id == user.id)
        result = await self.db.execute(query)
        pref = result.scalar_one_or_none()

        if not pref:
            pref = RoommatePreference(
                user_id=user.id,
                **req.model_dump()
            )
            self.db.add(pref)
        else:
            for field, val in req.model_dump(exclude_unset=True).items():
                setattr(pref, field, val)

        await self.db.flush()
        await self.db.refresh(pref)
        return pref

    async def calculate_compatibility(
        self,
        current_user: User,
        candidate_user: User
    ) -> CompatibilityResult:
        """Calculate weighted roommate compatibility score between two users."""
        q1 = select(RoommatePreference).where(RoommatePreference.user_id == current_user.id)
        p1 = (await self.db.execute(q1)).scalar_one_or_none()

        q2 = select(RoommatePreference).where(RoommatePreference.user_id == candidate_user.id)
        p2 = (await self.db.execute(q2)).scalar_one_or_none()

        if not p1 or not p2:
            return CompatibilityResult(
                candidate_user_id=candidate_user.id,
                candidate_name=candidate_user.full_name,
                compatibility_score=50.0,
                matched_factors=["Default Profile Match"],
            )

        matched_factors = []
        score = 0.0

        # 1. Smoking compatibility (25%)
        if p1.smoking_allowed == p2.smoking_allowed:
            score += 25.0
            matched_factors.append("Smoking Preference Aligned")

        # 2. Sleep schedule (20%)
        if p1.sleep_schedule == p2.sleep_schedule or p1.sleep_schedule == "FLEXIBLE" or p2.sleep_schedule == "FLEXIBLE":
            score += 20.0
            matched_factors.append("Compatible Sleep Schedules")

        # 3. Cleanliness level (20%)
        diff = abs(p1.cleanliness_level - p2.cleanliness_level)
        if diff == 0:
            score += 20.0
            matched_factors.append("Identical Cleanliness Standards")
        elif diff == 1:
            score += 15.0
            matched_factors.append("Close Cleanliness Habits")
        elif diff == 2:
            score += 10.0

        # 4. Guest preference (15%)
        if p1.guests_allowed == p2.guests_allowed:
            score += 15.0
            matched_factors.append("Guest Policy Aligned")

        # 5. Dietary preference (10%)
        if p1.dietary_preference == p2.dietary_preference or p1.dietary_preference == "ANY" or p2.dietary_preference == "ANY":
            score += 10.0
            matched_factors.append("Dietary Compatibility")

        # 6. Study habit (10%)
        if p1.study_habit == p2.study_habit:
            score += 10.0
            matched_factors.append("Study Environment Aligned")

        total_score = min(100.0, round(score, 1))

        return CompatibilityResult(
            candidate_user_id=candidate_user.id,
            candidate_name=candidate_user.full_name,
            compatibility_score=total_score,
            matched_factors=matched_factors,
        )
