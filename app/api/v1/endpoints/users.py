"""User and KYC API endpoints."""

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.core.constants import KYCStatus, UserRole
from app.core.exceptions import ResourceNotFoundError
from app.models.kyc import UserKYC
from app.models.user import User
from app.schemas.auth import UserOut, UserUpdate
from app.schemas.common import StandardResponse
from app.schemas.kyc import KYCAdminDecisionRequest, KYCOut, KYCSubmitRequest

users_router = APIRouter(prefix="/users", tags=["Users"])
kyc_router = APIRouter(prefix="/kyc", tags=["KYC"])


@users_router.get("/me", response_model=StandardResponse[UserOut])
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Retrieve current logged in user's profile."""
    return StandardResponse(
        success=True,
        message="Profile retrieved successfully",
        data=UserOut.model_validate(current_user)
    )


@users_router.patch("/me", response_model=StandardResponse[UserOut])
async def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile information."""
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    await db.flush()
    await db.refresh(current_user)
    return StandardResponse(
        success=True,
        message="Profile updated successfully",
        data=UserOut.model_validate(current_user)
    )


@users_router.get("/{user_id}", response_model=StandardResponse[UserOut])
async def get_user_by_id(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve public profile of a user."""
    query = select(User).where(User.id == user_id, User.is_active == True)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise ResourceNotFoundError(message="User not found")
    return StandardResponse(
        success=True,
        message="User profile retrieved",
        data=UserOut.model_validate(user)
    )


# --- KYC Endpoints ---
@kyc_router.post("", response_model=StandardResponse[KYCOut], status_code=status.HTTP_201_CREATED)
async def submit_kyc(
    req: KYCSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit identity verification documents for review."""
    query = select(UserKYC).where(UserKYC.user_id == current_user.id)
    result = await db.execute(query)
    kyc_entry = result.scalar_one_or_none()

    if not kyc_entry:
        kyc_entry = UserKYC(
            user_id=current_user.id,
            status=KYCStatus.PENDING,
            document_type=req.document_type,
            document_number=req.document_number,
            front_document_url=req.front_document_url,
            back_document_url=req.back_document_url,
            student_or_work_id_url=req.student_or_work_id_url,
        )
        db.add(kyc_entry)
    else:
        kyc_entry.status = KYCStatus.PENDING
        kyc_entry.document_type = req.document_type
        kyc_entry.document_number = req.document_number
        kyc_entry.front_document_url = req.front_document_url
        kyc_entry.back_document_url = req.back_document_url
        kyc_entry.student_or_work_id_url = req.student_or_work_id_url
        kyc_entry.rejection_reason = None

    await db.flush()
    await db.refresh(kyc_entry)
    return StandardResponse(
        success=True,
        message="KYC documents submitted for review",
        data=KYCOut.model_validate(kyc_entry)
    )


@kyc_router.get("/me", response_model=StandardResponse[KYCOut])
async def get_my_kyc_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve current user's KYC verification status."""
    query = select(UserKYC).where(UserKYC.user_id == current_user.id)
    result = await db.execute(query)
    kyc_entry = result.scalar_one_or_none()
    if not kyc_entry:
        raise ResourceNotFoundError(message="No KYC submission found for this user")
    return StandardResponse(
        success=True,
        message="KYC status retrieved",
        data=KYCOut.model_validate(kyc_entry)
    )
