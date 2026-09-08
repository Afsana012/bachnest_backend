"""Roommate profile domain service."""

import uuid
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.roommate import RoommateProfile
from app.models.user import User
from app.models.kyc import UserKYC
from app.schemas.roommate import RoommateProfileCreate, RoommateProfileOut, RoommateProfileUpdate


class RoommateService:
    @staticmethod
    async def list_profiles(
        db: AsyncSession,
        area: Optional[str] = None,
        looking_for: Optional[str] = None,
        gender: Optional[str] = None,
        max_budget: Optional[Decimal] = None,
        search: Optional[str] = None,
        limit: int = 30,
        offset: int = 0
    ) -> Tuple[List[RoommateProfileOut], int]:
        stmt = select(RoommateProfile).options(
            selectinload(RoommateProfile.user).selectinload(User.kyc)
        ).where(RoommateProfile.is_active == True)

        if looking_for and looking_for != "ALL":
            stmt = stmt.where(RoommateProfile.looking_for == looking_for)

        if gender and gender != "ALL":
            stmt = stmt.where(RoommateProfile.gender == gender)

        if max_budget:
            stmt = stmt.where(RoommateProfile.budget_max <= max_budget)

        if search:
            q = f"%{search.lower()}%"
            stmt = stmt.where(
                func.lower(RoommateProfile.full_name).like(q) |
                func.lower(RoommateProfile.occupation).like(q) |
                func.lower(RoommateProfile.institution_or_company).like(q)
            )

        stmt = stmt.order_by(RoommateProfile.created_at.desc())
        
        # Execute query
        result = await db.execute(stmt.offset(offset).limit(limit))
        records = result.scalars().all()

        out_list: List[RoommateProfileOut] = []
        for r in records:
            if area and area != "All Areas":
                areas_lower = [a.lower() for a in r.preferred_areas]
                if not any(area.lower() in a for a in areas_lower):
                    continue

            kyc = r.user.kyc if r.user else None
            is_kyc = (kyc.status.value == "APPROVED") if kyc else False
            trust = r.user.trust_score if r.user and hasattr(r.user, "trust_score") else 90

            item = RoommateProfileOut(
                id=r.id,
                user_id=r.user_id,
                full_name=r.full_name,
                gender=r.gender,
                occupation=r.occupation,
                occupation_category=r.occupation_category,
                institution_or_company=r.institution_or_company,
                preferred_areas=r.preferred_areas,
                budget_max=r.budget_max,
                looking_for=r.looking_for,
                move_in_date=r.move_in_date,
                lifestyle_tags=r.lifestyle_tags,
                bio=r.bio,
                phone=r.phone if r.phone_visible else "",
                phone_visible=r.phone_visible,
                email=r.email,
                is_active=r.is_active,
                is_kyc_verified=is_kyc,
                trust_score=trust,
                created_at=r.created_at,
                updated_at=r.updated_at
            )
            out_list.append(item)

        return out_list, len(out_list)

    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[RoommateProfileOut]:
        stmt = select(RoommateProfile).options(
            selectinload(RoommateProfile.user).selectinload(User.kyc)
        ).where(RoommateProfile.user_id == user_id)
        result = await db.execute(stmt)
        r = result.scalar_one_or_none()
        if not r:
            return None

        kyc = r.user.kyc if r.user else None
        is_kyc = (kyc.status.value == "APPROVED") if kyc else False
        trust = r.user.trust_score if r.user and hasattr(r.user, "trust_score") else 90

        return RoommateProfileOut(
            id=r.id,
            user_id=r.user_id,
            full_name=r.full_name,
            gender=r.gender,
            occupation=r.occupation,
            occupation_category=r.occupation_category,
            institution_or_company=r.institution_or_company,
            preferred_areas=r.preferred_areas,
            budget_max=r.budget_max,
            looking_for=r.looking_for,
            move_in_date=r.move_in_date,
            lifestyle_tags=r.lifestyle_tags,
            bio=r.bio,
            phone=r.phone,
            phone_visible=r.phone_visible,
            email=r.email,
            is_active=r.is_active,
            is_kyc_verified=is_kyc,
            trust_score=trust,
            created_at=r.created_at,
            updated_at=r.updated_at
        )

    @staticmethod
    async def upsert_profile(
        db: AsyncSession,
        user: User,
        data: RoommateProfileCreate
    ) -> RoommateProfileOut:
        stmt = select(RoommateProfile).where(RoommateProfile.user_id == user.id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if profile:
            for k, v in data.model_dump().items():
                setattr(profile, k, v)
            profile.is_active = True
        else:
            profile = RoommateProfile(
                user_id=user.id,
                **data.model_dump()
            )
            db.add(profile)

        await db.commit()
        await db.refresh(profile)
        return await RoommateService.get_by_user_id(db, user.id)
