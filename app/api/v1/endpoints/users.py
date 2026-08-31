"""User and KYC API endpoints."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.core.constants import KYCStatus, UserRole
from app.models.user import User
from app.schemas.auth import UserOut, UserUpdate
from app.schemas.common import StandardResponse
from app.schemas.kyc import KYCAdminDecisionRequest, KYCOut, KYCSubmitRequest
from app.services.kyc_service import KYCService
from app.services.user_service import UserService

users_router = APIRouter(prefix="/users", tags=["Users"])
kyc_router = APIRouter(prefix="/kyc", tags=["KYC"])
admin_kyc_router = APIRouter(prefix="/admin/kyc", tags=["Admin KYC"])


# --- User Endpoints ---
@users_router.get("/me", response_model=StandardResponse[UserOut])
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Retrieve current logged in user's profile."""
    return StandardResponse(
        success=True,
        message="Profile retrieved successfully",
        data=UserOut.model_validate(current_user),
    )


@users_router.patch("/me", response_model=StandardResponse[UserOut])
async def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile information."""
    user_service = UserService(db)
    updated_user = await user_service.update_profile(current_user, update_data)
    return StandardResponse(
        success=True,
        message="Profile updated successfully",
        data=UserOut.model_validate(updated_user),
    )


@users_router.get("/{user_id}", response_model=StandardResponse[UserOut])
async def get_user_by_id(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve public profile of an active user."""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    return StandardResponse(
        success=True,
        message="User profile retrieved",
        data=UserOut.model_validate(user),
    )


# --- KYC Endpoints ---
@kyc_router.post("", response_model=StandardResponse[KYCOut], status_code=status.HTTP_201_CREATED)
async def submit_kyc(
    req: KYCSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit identity verification documents for review."""
    kyc_service = KYCService(db)
    kyc_entry = await kyc_service.submit_kyc(current_user, req)
    return StandardResponse(
        success=True,
        message="KYC documents submitted for review",
        data=KYCOut.model_validate(kyc_entry),
    )


@kyc_router.get("/me", response_model=StandardResponse[KYCOut])
async def get_my_kyc_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve current user's KYC verification status."""
    kyc_service = KYCService(db)
    kyc_entry = await kyc_service.get_my_kyc(current_user)
    return StandardResponse(
        success=True,
        message="KYC status retrieved",
        data=KYCOut.model_validate(kyc_entry),
    )


@kyc_router.patch("/{kyc_id}/resubmit", response_model=StandardResponse[KYCOut])
async def resubmit_kyc(
    kyc_id: uuid.UUID,
    req: KYCSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resubmit corrected KYC verification documents."""
    kyc_service = KYCService(db)
    kyc_entry = await kyc_service.resubmit_kyc(current_user, kyc_id, req)
    return StandardResponse(
        success=True,
        message="KYC documents resubmitted for review",
        data=KYCOut.model_validate(kyc_entry),
    )


# --- Admin KYC Moderation Endpoints ---
@admin_kyc_router.get("", response_model=StandardResponse[List[KYCOut]])
async def list_admin_kyc(
    status_filter: Optional[KYCStatus] = Query(None, alias="status"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List pending or filtered KYC submissions for admin review."""
    kyc_service = KYCService(db)
    items = await kyc_service.list_pending_kyc(status_filter)
    return StandardResponse(
        success=True,
        message="KYC review queue retrieved",
        data=[KYCOut.model_validate(k) for k in items],
    )


@admin_kyc_router.patch("/{kyc_id}/decision", response_model=StandardResponse[KYCOut])
async def make_kyc_decision(
    kyc_id: uuid.UUID,
    req: KYCAdminDecisionRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Admin approves or rejects a KYC submission."""
    kyc_service = KYCService(db)
    kyc_entry = await kyc_service.admin_decision(kyc_id, req)
    return StandardResponse(
        success=True,
        message=f"KYC submission {kyc_entry.status.value.lower()}",
        data=KYCOut.model_validate(kyc_entry),
    )
