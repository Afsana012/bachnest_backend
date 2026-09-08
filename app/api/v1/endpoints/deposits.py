"""API Endpoints for Security Deposit Escrow & Refund Claims."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.deposit import DepositClaimCreate, DepositClaimOut, DepositClaimSettle
from app.services.deposit_service import DepositService

router = APIRouter(prefix="/deposits", tags=["Deposits & Move-out"])


@router.post("/claims", response_model=ResponseModel[DepositClaimOut], status_code=status.HTTP_201_CREATED)
async def request_deposit_refund(
    data: DepositClaimCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Tenant submits a move-out deposit refund request."""
    claim = await DepositService.create_claim(db, current_user, data)
    return ResponseModel(
        success=True,
        message="Deposit refund claim submitted successfully.",
        data=claim
    )


@router.get("/claims/me", response_model=ResponseModel[List[DepositClaimOut]])
async def list_my_deposit_claims(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all deposit refund claims submitted by the current tenant."""
    claims = await DepositService.list_tenant_claims(db, current_user.id)
    return ResponseModel(
        success=True,
        message="Deposit claims retrieved successfully.",
        data=claims
    )


@router.get("/claims/owner", response_model=ResponseModel[List[DepositClaimOut]])
async def list_owner_pending_claims(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve pending deposit refund claims for the landlord's properties."""
    claims = await DepositService.list_owner_claims(db, current_user.id)
    return ResponseModel(
        success=True,
        message="Owner deposit claims retrieved successfully.",
        data=claims
    )


@router.post("/claims/{claim_id}/settle", response_model=ResponseModel[DepositClaimOut])
async def settle_deposit_refund_claim(
    claim_id: uuid.UUID,
    data: DepositClaimSettle,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Landlord finalizes move-out inspection and settles refund with itemized deductions."""
    claim = await DepositService.settle_claim(db, current_user, claim_id, data)
    return ResponseModel(
        success=True,
        message="Deposit refund settled and clearance certificate generated.",
        data=claim
    )


@router.get("/claims/{claim_id}", response_model=ResponseModel[DepositClaimOut])
async def get_deposit_claim_detail(
    claim_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get full details of a specific deposit refund claim."""
    claim = await DepositService.get_claim(db, claim_id)
    return ResponseModel(
        success=True,
        message="Deposit claim detail retrieved.",
        data=claim
    )
