"""Pydantic schemas for Roommate Matching & Profiles."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.constants import Gender, RoommateLookingType, RoommateOccupationCategory


class RoommateProfileBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    gender: Gender = Gender.MALE
    occupation: str = Field(..., min_length=2, max_length=255)
    occupation_category: RoommateOccupationCategory = RoommateOccupationCategory.JOB_HOLDER
    institution_or_company: str = Field(default="", max_length=255)
    preferred_areas: List[str] = Field(default_factory=list)
    budget_max: Decimal = Field(..., ge=0)
    looking_for: RoommateLookingType = RoommateLookingType.ROOM_WANTED
    move_in_date: str = Field(default="Immediate", max_length=50)
    lifestyle_tags: List[str] = Field(default_factory=list)
    bio: str = Field(default="", max_length=2000)
    phone: str = Field(default="", max_length=50)
    phone_visible: bool = True
    email: str = Field(default="", max_length=255)


class RoommateProfileCreate(RoommateProfileBase):
    pass


class RoommateProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[Gender] = None
    occupation: Optional[str] = None
    occupation_category: Optional[RoommateOccupationCategory] = None
    institution_or_company: Optional[str] = None
    preferred_areas: Optional[List[str]] = None
    budget_max: Optional[Decimal] = None
    looking_for: Optional[RoommateLookingType] = None
    move_in_date: Optional[str] = None
    lifestyle_tags: Optional[List[str]] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    phone_visible: Optional[bool] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class RoommateProfileOut(RoommateProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_active: bool
    is_kyc_verified: bool = False
    trust_score: int = 80
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoommateMessageCreate(BaseModel):
    sender_name: str = Field(..., min_length=2, max_length=255)
    sender_contact: str = Field(..., min_length=5, max_length=255, description="Phone / WhatsApp or Email")
    message: str = Field(..., min_length=3, max_length=2000)


class RoommateMessageReply(BaseModel):
    reply: str = Field(..., min_length=1, max_length=2000)


class RoommateMessageOut(BaseModel):
    id: uuid.UUID
    roommate_profile_id: Optional[uuid.UUID] = None
    sender_id: Optional[uuid.UUID] = None
    recipient_user_id: Optional[uuid.UUID] = None
    sender_name: str
    sender_contact: str
    message: str
    reply: Optional[str] = None
    is_read: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

