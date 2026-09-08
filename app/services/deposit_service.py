"""Service layer for Security Deposit Escrow & Refund Claims."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import DepositRefundStatus, TenancyStatus
from app.core.exceptions import ForbiddenException, NotFoundException, ValidationException
from app.models.booking import Tenancy
from app.models.deposit import DepositRefundClaim
from app.models.user import User
from app.schemas.deposit import DepositClaimCreate, DepositClaimOut, DepositClaimSettle


class DepositService:
    @staticmethod
    async def create_claim(
        db: AsyncSession,
        user: User,
        data: DepositClaimCreate
    ) -> DepositClaimOut:
        stmt = select(Tenancy).options(
            selectinload(Tenancy.property),
            selectinload(Tenancy.room),
            selectinload(Tenancy.tenant),
            selectinload(Tenancy.owner)
        ).where(Tenancy.id == data.tenancy_id)
        result = await db.execute(stmt)
        tenancy = result.scalar_one_or_none()

        if not tenancy:
            raise NotFoundException(f"Tenancy with ID {data.tenancy_id} not found.")

        if tenancy.tenant_id != user.id and user.role.value != "ADMIN" and user.role.value != "SUPER_ADMIN":
            raise ForbiddenException("Only the designated tenant can request deposit refund.")

        # Check existing non-rejected claim
        existing_stmt = select(DepositRefundClaim).where(
            DepositRefundClaim.tenancy_id == tenancy.id,
            DepositRefundClaim.status != DepositRefundStatus.REJECTED
        )
        existing_res = await db.execute(existing_stmt)
        existing_claim = existing_res.scalar_one_or_none()

        if existing_claim:
            raise ValidationException(f"An active deposit refund claim ({existing_claim.status.value}) already exists for this lease.")

        deposit_amount = tenancy.agreed_security_deposit

        claim = DepositRefundClaim(
            tenancy_id=tenancy.id,
            tenant_id=tenancy.tenant_id,
            owner_id=tenancy.owner_id,
            status=DepositRefundStatus.REQUESTED,
            total_deposit_amount=deposit_amount,
            requested_refund_amount=deposit_amount,
            deduction_amount=Decimal("0.00"),
            net_refund_amount=deposit_amount,
            deduction_breakdown=[],
            tenant_payout_method=data.tenant_payout_method,
            tenant_payout_account=data.tenant_payout_account,
            move_out_date=data.move_out_date,
            tenant_notes=data.tenant_notes
        )
        db.add(claim)
        
        # Mark tenancy notice if still active
        if tenancy.status == TenancyStatus.ACTIVE:
            tenancy.status = TenancyStatus.NOTICE_SERVED

        await db.commit()
        await db.refresh(claim)

        return DepositService._build_out(claim, tenancy)

    @staticmethod
    async def settle_claim(
        db: AsyncSession,
        user: User,
        claim_id: uuid.UUID,
        data: DepositClaimSettle
    ) -> DepositClaimOut:
        stmt = select(DepositRefundClaim).options(
            selectinload(DepositRefundClaim.tenancy).selectinload(Tenancy.property),
            selectinload(DepositRefundClaim.tenancy).selectinload(Tenancy.room),
            selectinload(DepositRefundClaim.tenant),
            selectinload(DepositRefundClaim.owner)
        ).where(DepositRefundClaim.id == claim_id)
        result = await db.execute(stmt)
        claim = result.scalar_one_or_none()

        if not claim:
            raise NotFoundException(f"Claim with ID {claim_id} not found.")

        if claim.owner_id != user.id and user.role.value != "ADMIN" and user.role.value != "SUPER_ADMIN":
            raise ForbiddenException("Only the property landlord or admin can settle deposit refunds.")

        total_deduction = sum((Decimal(str(d.amount)) for d in data.deductions), Decimal("0.00"))
        
        if total_deduction > claim.total_deposit_amount:
            raise ValidationException("Total deductions cannot exceed the original security deposit amount.")

        net_refund = claim.total_deposit_amount - total_deduction

        claim.deduction_amount = total_deduction
        claim.net_refund_amount = net_refund
        claim.deduction_breakdown = [d.model_dump() for d in data.deductions]
        claim.transaction_reference = data.transaction_reference
        claim.landlord_remarks = data.landlord_remarks
        claim.status = DepositRefundStatus.SETTLED
        claim.settled_at = datetime.utcnow()

        # Terminate tenancy upon complete deposit settlement
        if claim.tenancy:
            claim.tenancy.status = TenancyStatus.TERMINATED

        await db.commit()
        await db.refresh(claim)

        return DepositService._build_out(claim, claim.tenancy)

    @staticmethod
    async def get_claim(db: AsyncSession, claim_id: uuid.UUID) -> Optional[DepositClaimOut]:
        stmt = select(DepositRefundClaim).options(
            selectinload(DepositRefundClaim.tenancy).selectinload(Tenancy.property),
            selectinload(DepositRefundClaim.tenancy).selectinload(Tenancy.room),
            selectinload(DepositRefundClaim.tenant),
            selectinload(DepositRefundClaim.owner)
        ).where(DepositRefundClaim.id == claim_id)
        result = await db.execute(stmt)
        claim = result.scalar_one_or_none()
        if not claim:
            return None
        return DepositService._build_out(claim, claim.tenancy)

    @staticmethod
    async def list_tenant_claims(db: AsyncSession, tenant_id: uuid.UUID) -> List[DepositClaimOut]:
        stmt = select(DepositRefundClaim).options(
            selectinload(DepositRefundClaim.tenancy).selectinload(Tenancy.property),
            selectinload(DepositRefundClaim.tenancy).selectinload(Tenancy.room),
            selectinload(DepositRefundClaim.tenant),
            selectinload(DepositRefundClaim.owner)
        ).where(DepositRefundClaim.tenant_id == tenant_id).order_by(DepositRefundClaim.created_at.desc())
        result = await db.execute(stmt)
        claims = result.scalars().all()
        return [DepositService._build_out(c, c.tenancy) for c in claims]

    @staticmethod
    async def list_owner_claims(db: AsyncSession, owner_id: uuid.UUID) -> List[DepositClaimOut]:
        stmt = select(DepositRefundClaim).options(
            selectinload(DepositRefundClaim.tenancy).selectinload(Tenancy.property),
            selectinload(DepositRefundClaim.tenancy).selectinload(Tenancy.room),
            selectinload(DepositRefundClaim.tenant),
            selectinload(DepositRefundClaim.owner)
        ).where(DepositRefundClaim.owner_id == owner_id).order_by(DepositRefundClaim.created_at.desc())
        result = await db.execute(stmt)
        claims = result.scalars().all()
        return [DepositService._build_out(c, c.tenancy) for c in claims]

    @staticmethod
    def _build_out(claim: DepositRefundClaim, tenancy: Optional[Tenancy]) -> DepositClaimOut:
        prop_title = tenancy.property.title if tenancy and tenancy.property else "BachNest Accommodation"
        room_name = tenancy.room.room_number_or_name if tenancy and tenancy.room else "Assigned Room"
        t_name = claim.tenant.full_name if claim.tenant else "Tenant"
        o_name = claim.owner.full_name if claim.owner else "Landlord"

        return DepositClaimOut(
            id=claim.id,
            tenancy_id=claim.tenancy_id,
            tenant_id=claim.tenant_id,
            owner_id=claim.owner_id,
            status=claim.status,
            total_deposit_amount=claim.total_deposit_amount,
            requested_refund_amount=claim.requested_refund_amount,
            deduction_amount=claim.deduction_amount,
            net_refund_amount=claim.net_refund_amount,
            deduction_breakdown=claim.deduction_breakdown,
            tenant_payout_method=claim.tenant_payout_method,
            tenant_payout_account=claim.tenant_payout_account,
            move_out_date=claim.move_out_date,
            tenant_notes=claim.tenant_notes,
            landlord_remarks=claim.landlord_remarks,
            transaction_reference=claim.transaction_reference,
            settled_at=claim.settled_at,
            created_at=claim.created_at,
            updated_at=claim.updated_at,
            property_title=prop_title,
            room_name=room_name,
            tenant_name=t_name,
            owner_name=o_name
        )
