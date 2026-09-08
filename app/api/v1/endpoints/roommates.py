"""Roommate discovery and profiles API endpoints."""

import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.roommate import RoommateProfileCreate, RoommateProfileOut, RoommateProfileUpdate
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
