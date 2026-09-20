"""Roommate discovery and profiles API endpoints."""

import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_user, get_db
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.roommate import (
    RoommateMessageCreate,
    RoommateMessageOut,
    RoommateMessageReply,
    RoommateProfileCreate,
    RoommateProfileOut,
    RoommateProfileUpdate,
)
from app.services.roommate_service import RoommateService

router = APIRouter(prefix="/roommates", tags=["Roommates"])


@router.get("", response_model=ResponseModel[List[RoommateProfileOut]])
async def list_roommates(
    area: Optional[str] = Query(None, description="Preferred Dhaka area"),
    looking_for: Optional[str] = Query(None, description="ROOM_WANTED, FLATSHARE, HAVE_ROOM_NEED_ROOMMATE"),
    gender: Optional[str] = Query(None, description="MALE, FEMALE"),
    max_budget: Optional[Decimal] = Query(None, description="Max budget ceiling"),
    search: Optional[str] = Query(None, description="Keyword search in name/occupation/institution"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Browse and filter active verified bachelor roommate ads in Dhaka."""
    profiles, total = await RoommateService.list_profiles(
        db,
        area=area,
        looking_for=looking_for,
        gender=gender,
        max_budget=max_budget,
        search=search,
        limit=limit,
        offset=offset
    )
    return ResponseModel(
        success=True,
        message="Roommate profiles retrieved successfully",
        data=profiles
    )


@router.get("/me", response_model=ResponseModel[Optional[RoommateProfileOut]])
async def get_my_roommate_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the authenticated bachelor's roommate ad profile."""
    profile = await RoommateService.get_by_user_id(db, current_user.id)
    return ResponseModel(
        success=True,
        message="My profile retrieved",
        data=profile
    )


@router.post("", response_model=ResponseModel[RoommateProfileOut], status_code=status.HTTP_201_CREATED)
async def upsert_my_roommate_profile(
    data: RoommateProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Publish or update current bachelor's roommate profile or flatshare offer."""
    profile = await RoommateService.upsert_profile(db, current_user, data)
    return ResponseModel(
        success=True,
        message="Roommate profile published successfully",
        data=profile
    )


@router.post("/{profile_id}/message", response_model=ResponseModel[RoommateMessageOut], status_code=status.HTTP_201_CREATED)
async def send_roommate_message(
    profile_id: str,
    data: RoommateMessageCreate,
    optional_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Send inquiry or connect message to a roommate ad."""
    msg = await RoommateService.send_message(db, profile_id, data, sender_user=optional_user)
    return ResponseModel(
        success=True,
        message="Roommate match inquiry sent successfully",
        data=msg,
    )


@router.get("/messages/me", response_model=ResponseModel[List[RoommateMessageOut]])
async def get_my_roommate_messages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all roommate messages and inquiries for current bachelor."""
    messages = await RoommateService.list_user_messages(db, current_user)
    return ResponseModel(
        success=True,
        message="Roommate messages retrieved",
        data=messages,
    )


@router.patch("/messages/{message_id}/reply", response_model=ResponseModel[RoommateMessageOut])
async def reply_to_roommate_message(
    message_id: uuid.UUID,
    data: RoommateMessageReply,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reply to an inquiry from a prospective roommate."""
    msg = await RoommateService.reply_message(db, message_id, data.reply, current_user)
    return ResponseModel(
        success=True,
        message="Reply sent successfully",
        data=msg,
    )

